from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, current_app, flash
from app.services.auth_service import AuthService
from app.models.base import db
from app.models.users import Users, UserSession, LoginLog
import bcrypt
import secrets
import os
import time
from datetime import datetime
from werkzeug.utils import secure_filename

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET'])
def register_page():
    return render_template('signup.html')

@auth_bp.route('/register', methods=['POST'])
def register_submit():
    # Supports both AJAX JSON payloads and standard form payloads
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip()
    phone_number = data.get('phone_number', '').strip()
    password = data.get('password', '')
    address = data.get('address', '').strip()

    # 1. Server-side required validation
    if not full_name:
        return jsonify({'error': 'Full Name is required.'}), 400
    if not email:
        return jsonify({'error': 'Email address is required.'}), 400
    if not password or len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters long.'}), 400

    # 2. Delegate registration logic to AuthService
    result = AuthService.register_customer(full_name, email, phone_number, password, address)
    if result["success"]:
        return jsonify({'message': 'Registration successful!'}), 201
    else:
        return jsonify({'error': result["error"]}), result["code"]

@auth_bp.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

@auth_bp.route('/login', methods=['POST'])
def login_submit():
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and Password are required.'}), 400

    # Delegate verification logic to AuthService
    result = AuthService.verify_credentials(email, password)
    if result["success"]:
        user_id = result['user_id']
        role_id = result['role_id']
        full_name = result['full_name']
        role_name = result['role_name']

        # Generate unique session token for active sessions tracking
        session_token = secrets.token_hex(16)

        try:
            # Create session log in DB
            new_sess = UserSession(
                userID=user_id,
                token=session_token,
                ipAddress=request.remote_addr,
                userAgent=request.headers.get('User-Agent', '')[:255]
            )
            db.session.add(new_sess)

            # Log successful login
            new_log = LoginLog(
                userID=user_id,
                ipAddress=request.remote_addr,
                userAgent=request.headers.get('User-Agent', '')[:255],
                status='Success'
            )
            db.session.add(new_log)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Failed to record session / login log: {e}")

        session['user_id'] = user_id
        session['role_id'] = role_id
        session['full_name'] = full_name
        session['role_name'] = role_name
        session['session_token'] = session_token
        
        return jsonify({
            'message': 'Login successful',
            'redirect_url': '/' 
        }), 200
    else:
        # Log failed login attempt if email exists
        try:
            user = Users.query.filter_by(email=email).first()
            if user:
                new_log = LoginLog(
                    userID=user.userID,
                    ipAddress=request.remote_addr,
                    userAgent=request.headers.get('User-Agent', '')[:255],
                    status='Failed'
                )
                db.session.add(new_log)
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Failed to record login failure: {e}")

        return jsonify({'error': result['error']}), result['code']

@auth_bp.route('/logout', methods=['GET'])
def logout():
    user_id = session.get('user_id')
    session_token = session.get('session_token')
    
    if user_id and session_token:
        try:
            UserSession.query.filter_by(userID=user_id, token=session_token).delete()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Failed to delete session on logout: {e}")

    session.clear()
    return redirect(url_for('auth.login_page'))

# --- PASSWORD RECOVERY WITH 2FA BYPASS FLOW ---

@auth_bp.route('/forgot-password', methods=['GET'])
def forgot_password_page():
    return render_template('forgot_password.html')

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password_submit():
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    email = data.get('email', '').strip()
    recovery_method = data.get('method', 'email') # 'email' or '2fa'
    totp_code = data.get('code', '').strip()

    if not email:
        return jsonify({'error': 'Email address is required.'}), 400

    user = Users.query.filter_by(email=email).first()
    if not user:
        if recovery_method == '2fa':
            return jsonify({'error': 'Account not found.'}), 404
        return jsonify({'message': 'Simulated email recovery instructions sent to your email.'}), 200

    if recovery_method == '2fa':
        if not user.twoFactorEnabled:
            return jsonify({'error': 'Two-Factor Authentication is not enabled for this account. Standard email recovery is required.'}), 400
        
        if not totp_code:
            return jsonify({'error': '6-digit verification code is required.'}), 400
            
        import pyotp
        totp = pyotp.TOTP(user.twoFactorSecret)
        if totp.verify(totp_code):
            # Authorize password reset session
            session['reset_password_user_id'] = user.userID
            return jsonify({
                'message': 'Code verified successfully.',
                'redirect_url': '/reset-password'
            }), 200
        else:
            return jsonify({'error': 'Invalid 2FA verification code. Please check your authenticator app.'}), 400
    else:
        # Simulated standard email recovery
        return jsonify({'message': f'A recovery email has been sent to {email} (Simulated).'}), 200

@auth_bp.route('/reset-password', methods=['GET'])
def reset_password_page():
    if 'reset_password_user_id' not in session:
        return redirect(url_for('auth.login_page'))
    return render_template('reset_password.html')

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password_submit():
    reset_uid = session.get('reset_password_user_id')
    if not reset_uid:
        return jsonify({'error': 'Unauthorized password reset session.'}), 401

    user = Users.query.get(reset_uid)
    if not user:
        session.clear()
        return jsonify({'error': 'User not found.'}), 404

    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')

    if not new_password or not confirm_password:
        return jsonify({'error': 'Password fields are required.'}), 400

    if new_password != confirm_password:
        return jsonify({'error': 'Passwords do not match.'}), 400

    if len(new_password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters.'}), 400

    # Hash and save password
    hashed_pwd = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user.passwordHash = hashed_pwd

    try:
        db.session.commit()
        
        # Log successful password reset login
        new_log = LoginLog(
            userID=user.userID,
            ipAddress=request.remote_addr,
            userAgent=request.headers.get('User-Agent', '')[:255],
            status='Success'
        )
        db.session.add(new_log)
        
        # Log the user in directly for friendly UX
        session_token = secrets.token_hex(16)
        new_sess = UserSession(
            userID=user.userID,
            token=session_token,
            ipAddress=request.remote_addr,
            userAgent=request.headers.get('User-Agent', '')[:255]
        )
        db.session.add(new_sess)
        db.session.commit()

        session['user_id'] = user.userID
        session['role_id'] = user.roleID
        session['full_name'] = user.fullName
        session['role_name'] = user.role.roleName if user.role else 'Customer'
        session['session_token'] = session_token
        session.pop('reset_password_user_id', None)

        return jsonify({
            'message': 'Password reset successful! Logging in...',
            'redirect_url': '/dashboard' if (user.role and user.role.roleName.lower() in ['admin', 'employee']) else '/'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to reset password: {str(e)}'}), 500

# --- PROFILE SETTINGS HUB ROUTES ---

@auth_bp.route('/profile', methods=['GET'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
        
    user = Users.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.login_page'))

    # Fetch active sessions and last 5 login history
    sessions = UserSession.query.filter_by(userID=user.userID).order_by(UserSession.lastActive.desc()).all()
    login_history = LoginLog.query.filter_by(userID=user.userID).order_by(LoginLog.loginAt.desc()).limit(5).all()

    return render_template('profile.html', 
                           user=user, 
                           sessions=sessions, 
                           login_history=login_history,
                           current_token=session.get('session_token'))

@auth_bp.route('/profile/edit-details', methods=['POST'])
def edit_profile_details():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    user = Users.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404

    fullName = request.form.get('full_name', '').strip()
    phoneNumber = request.form.get('phone_number', '').strip()

    if not fullName:
        return jsonify({'error': 'Full Name is required.'}), 400

    # Handling avatar file upload
    avatar_file = request.files.get('avatar')
    if avatar_file and avatar_file.filename != '':
        # Validate file type
        allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif'}
        _, ext = os.path.splitext(avatar_file.filename.lower())
        if ext not in allowed_extensions:
            return jsonify({'error': 'Invalid file type. Allowed formats: PNG, JPG, JPEG, GIF.'}), 400

        # Build clean filename
        filename = f"user_{user.userID}_{int(time.time())}{ext}"
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'avatars')
        os.makedirs(upload_folder, exist_ok=True)
        
        filepath = os.path.join(upload_folder, filename)
        try:
            avatar_file.save(filepath)
            user.avatar = filename
        except Exception as e:
            return jsonify({'error': f"Failed to save profile picture: {str(e)}"}), 500

    user.fullName = fullName
    user.phoneNumber = phoneNumber if phoneNumber else None

    try:
        db.session.commit()
        # Keep Flask session details updated
        session['full_name'] = user.fullName
        return jsonify({'message': 'Profile details updated successfully.'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update profile details in database.'}), 500

@auth_bp.route('/profile/change-password', methods=['POST'])
def change_password():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    user = Users.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')

    if not current_password or not new_password or not confirm_password:
        return jsonify({'error': 'All password fields are required.'}), 400

    if new_password != confirm_password:
        return jsonify({'error': 'New passwords do not match.'}), 400

    if len(new_password) < 6:
        return jsonify({'error': 'New password must be at least 6 characters.'}), 400

    # Verify current password
    if not bcrypt.checkpw(current_password.encode('utf-8'), user.passwordHash.encode('utf-8')):
        return jsonify({'error': 'Incorrect current password.'}), 400

    # Hash new password
    hashed_pwd = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user.passwordHash = hashed_pwd

    try:
        db.session.commit()
        return jsonify({'message': 'Password changed successfully.'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to change password.'}), 500

@auth_bp.route('/profile/toggle-2fa', methods=['POST'])
def toggle_2fa():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    user = Users.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404

    user.twoFactorEnabled = not user.twoFactorEnabled
    qr_url = None
    if user.twoFactorEnabled:
        import pyotp
        import urllib.parse
        user.twoFactorSecret = pyotp.random_base32()
        
        # Create provisioning URI for authenticator app
        prov_uri = pyotp.TOTP(user.twoFactorSecret).provisioning_uri(name=user.email, issuer_name="LebEstates")
        # Generate dynamic QR Server URL
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={urllib.parse.quote(prov_uri)}"
    else:
        user.twoFactorSecret = None

    try:
        db.session.commit()
        status = "enabled" if user.twoFactorEnabled else "disabled"
        return jsonify({
            'message': f"2FA setup has been {status}.",
            'enabled': user.twoFactorEnabled,
            'secret': user.twoFactorSecret,
            'qr_url': qr_url
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to toggle 2FA.'}), 500

@auth_bp.route('/profile/revoke-session/<int:session_id>', methods=['POST'])
def revoke_session(session_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    user = Users.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404

    target_sess = UserSession.query.filter_by(sessionID=session_id, userID=user.userID).first()
    if not target_sess:
        return jsonify({'error': 'Session not found or unauthorized.'}), 404

    is_current = (target_sess.token == session.get('session_token'))

    try:
        db.session.delete(target_sess)
        db.session.commit()
        
        # If revoking current device's session, clear browser session to log out
        if is_current:
            session.clear()
            return jsonify({'message': 'Session revoked. Logging out...', 'logged_out': True}), 200

        return jsonify({'message': 'Device session revoked successfully.', 'logged_out': False}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to revoke session.'}), 500

@auth_bp.route('/profile/revoke-others', methods=['POST'])
def revoke_other_sessions():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    user = Users.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404

    current_token = session.get('session_token')
    if not current_token:
        return jsonify({'error': 'Current session token not found.'}), 400

    try:
        UserSession.query.filter(UserSession.userID == user.userID, UserSession.token != current_token).delete()
        db.session.commit()
        return jsonify({'message': 'All other device sessions revoked successfully.'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to revoke other sessions.'}), 500

