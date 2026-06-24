from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, current_app, flash, Response
from app.services.auth_service import AuthService
from app.models.users import Users

auth_bp = Blueprint('auth', __name__)

RESET_TOKENS = {}

@auth_bp.route('/register', methods=['GET'])
def register_page():
    return render_template('signup.html')

@auth_bp.route('/register', methods=['POST'])
def register_submit():
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip()
    phone_number = data.get('phone_number', '').strip()
    password = data.get('password', '')
    address = data.get('address', '').strip()

    if not full_name:
        return jsonify({'error': 'Full Name is required.'}), 400
    if not email:
        return jsonify({'error': 'Email address is required.'}), 400
    if not password or len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters long.'}), 400

    if phone_number:
        import re
        if not re.match(r'^\+?[0-9\s\-()]+$', phone_number):
            return jsonify({'error': 'Phone number must contain only numbers.'}), 400
        if len(re.sub(r'\D', '', phone_number)) < 6:
            return jsonify({'error': 'Phone number must contain at least 6 digits.'}), 400

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
    code = data.get('code', '').strip()

    if not email or not password:
        return jsonify({'error': 'Email and Password are required.'}), 400

    result = AuthService.verify_credentials(email, password)
    if result["success"]:
        user_id = result['user_id']
        role_id = result['role_id']
        full_name = result['full_name']
        role_name = result['role_name']

        # Check if 2FA is enabled for this user
        user_obj = AuthService.get_user_by_id(user_id)
        if user_obj and user_obj.twoFactorEnabled:
            if not code:
                return jsonify({
                    'two_factor_required': True,
                    'message': 'Two-Factor Authentication is required.'
                }), 200
            
            # Verify the TOTP code or backup code
            code_clean = code.strip().upper()
            verified = False
            
            # Check backup code format
            if len(code_clean) == 9 and '-' in code_clean:
                if user_obj.twoFactorBackupCodes:
                    from app.models.base import db
                    codes_list = [c.strip().upper() for c in user_obj.twoFactorBackupCodes.split(',') if c.strip()]
                    if code_clean in codes_list:
                        codes_list.remove(code_clean)
                        user_obj.twoFactorBackupCodes = ",".join(codes_list)
                        try:
                            db.session.commit()
                            verified = True
                        except Exception:
                            db.session.rollback()
                            return jsonify({'error': 'Database error while consuming backup code.'}), 500
            else:
                # Check standard 6-digit TOTP
                if len(code_clean) == 6 and code_clean.isdigit():
                    import pyotp
                    totp = pyotp.TOTP(user_obj.twoFactorSecret)
                    if totp.verify(code_clean):
                        verified = True

            if not verified:
                AuthService.log_login_attempt(user_id, request.remote_addr, request.headers.get('User-Agent', ''), 'Failed')
                return jsonify({'error': 'Invalid 2FA verification code or backup code.'}), 400

        # Delegate session creation to service
        session_token = AuthService.create_user_session(user_id, request.remote_addr, request.headers.get('User-Agent', ''))
        if session_token:
            AuthService.log_login_attempt(user_id, request.remote_addr, request.headers.get('User-Agent', ''), 'Success')
            
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
            return jsonify({'error': 'Failed to create active session.'}), 500
    else:
        # Check if email is registered to log failed attempt
        from app.models.users import Users
        user = Users.query.filter_by(email=email).first() if email else None
        if user:
            AuthService.log_login_attempt(user.userID, request.remote_addr, request.headers.get('User-Agent', ''), 'Failed')

        return jsonify({'error': result['error']}), result['code']

@auth_bp.route('/logout', methods=['GET'])
def logout():
    user_id = session.get('user_id')
    session_token = session.get('session_token')
    
    if user_id and session_token:
        AuthService.delete_user_session(user_id, session_token)

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
    recovery_method = data.get('method', '2fa')
    totp_code = data.get('code', '').strip()

    if not email:
        return jsonify({'error': 'Email address is required.'}), 400

    if recovery_method != '2fa':
        return jsonify({'error': 'Invalid recovery method.'}), 400

    result = AuthService.verify_forgot_password_totp(email, totp_code)
    if result["success"]:
        session['reset_password_user_id'] = result['user_id']
        return jsonify({
            'message': 'Code verified successfully.',
            'redirect_url': '/reset-password'
        }), 200
    else:
        return jsonify({'error': result['error']}), result['code']

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

    result = AuthService.reset_password(reset_uid, new_password, request.remote_addr, request.headers.get('User-Agent', ''))
    if result["success"]:
        session['user_id'] = result['session_token'] # Wait, user_id is the user ID, let's assign user_id not token!
        # Ah, let's fix that. The service reset_password returns "success": True, "session_token", "role_id", "full_name", "role_name", "redirect_url"
        # We need to assign session variables.
        # But wait! Let's check what we did: user.userID is returned in verify_forgot_password_totp.
        # Let's map it correctly:
        user_obj = AuthService.get_user_by_id(reset_uid)
        session['user_id'] = user_obj.userID
        session['role_id'] = result['role_id']
        session['full_name'] = result['full_name']
        session['role_name'] = result['role_name']
        session['session_token'] = result['session_token']
        session.pop('reset_password_user_id', None)

        return jsonify({
            'message': 'Password reset successful! Logging in...',
            'redirect_url': result['redirect_url']
        }), 200
    else:
        return jsonify({'error': result['error']}), result.get('code', 500)

# --- PROFILE SETTINGS HUB ROUTES ---

@auth_bp.route('/profile', methods=['GET'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
        
    data = AuthService.get_profile_data(session['user_id'])
    if not data:
        session.clear()
        return redirect(url_for('auth.login_page'))

    return render_template('profile.html', 
                           user=data['user'], 
                           sessions=data['sessions'], 
                           login_history=data['login_history'],
                           current_token=session.get('session_token'))

@auth_bp.route('/control-panel/settings', methods=['GET'])
def settings_page():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
        
    data = AuthService.get_profile_data(session['user_id'])
    if not data:
        session.clear()
        return redirect(url_for('auth.login_page'))

    user = data['user']
    backup_codes = [c.strip() for c in user.twoFactorBackupCodes.split(',') if c.strip()] if user.twoFactorBackupCodes else []

    return render_template('settings.html', 
                           user=user, 
                           sessions=data['sessions'], 
                           login_history=data['login_history'],
                           backup_codes=backup_codes,
                           current_token=session.get('session_token'))


@auth_bp.route('/profile/edit-details', methods=['POST'])
def edit_profile_details():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    fullName = request.form.get('full_name', '').strip()
    phoneNumber = request.form.get('phone_number', '').strip()
    avatar_file = request.files.get('avatar')

    res = AuthService.update_profile_details(session['user_id'], fullName, phoneNumber, avatar_file)
    if res.get('success'):
        session['full_name'] = res['full_name']
        return jsonify({'message': 'Profile details updated successfully.'}), 200
    else:
        return jsonify({'error': res.get('error')}), res.get('code', 400)

@auth_bp.route('/profile/avatar/<int:user_id>', methods=['GET'])
def get_avatar(user_id):
    avatar_data, content_type = AuthService.get_user_avatar(user_id)
    if not avatar_data:
        user = AuthService.get_user_by_id(user_id)
        name = user.fullName if user else 'User'
        return redirect(f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}&background=random")
    
    return Response(avatar_data, mimetype=content_type)

@auth_bp.route('/profile/change-password', methods=['POST'])
def change_password():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
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

    res = AuthService.change_user_password(session['user_id'], current_password, new_password)
    if res.get('success'):
        return jsonify({'message': 'Password changed successfully.'}), 200
    else:
        return jsonify({'error': res.get('error')}), res.get('code', 400)

@auth_bp.route('/profile/toggle-2fa', methods=['POST'])
def toggle_2fa():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    res = AuthService.toggle_user_2fa(session['user_id'])
    if res.get('success'):
        return jsonify({
            'message': res['message'],
            'enabled': res['enabled'],
            'secret': res['secret'],
            'qr_url': res['qr_url']
        }), 200
    else:
        return jsonify({'error': res.get('error')}), res.get('code', 500)

@auth_bp.route('/profile/verify-2fa', methods=['POST'])
def verify_2fa():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    code = data.get('code', '').strip()
    if not code:
        return jsonify({'error': 'Verification code is required.'}), 400

    res = AuthService.verify_and_enable_2fa(session['user_id'], code)
    if res.get('success'):
        return jsonify({
            'message': 'Two-Factor Authentication activated successfully!',
            'backup_codes': res['backup_codes']
        }), 200
    else:
        return jsonify({'error': res.get('error')}), res.get('code', 400)

@auth_bp.route('/profile/revoke-session/<int:session_id>', methods=['POST'])
def revoke_session(session_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    res = AuthService.revoke_user_session(session['user_id'], session_id, session.get('session_token'))
    if res.get('success'):
        if res.get('logged_out'):
            session.clear()
            return jsonify({'message': 'Session revoked. Logging out...', 'logged_out': True}), 200
        return jsonify({'message': 'Device session revoked successfully.', 'logged_out': False}), 200
    else:
        return jsonify({'error': res.get('error')}), res.get('code', 500)

@auth_bp.route('/profile/revoke-others', methods=['POST'])
def revoke_other_sessions():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    res = AuthService.revoke_all_other_user_sessions(session['user_id'], session.get('session_token'))
    if res.get('success'):
        return jsonify({'message': 'All other device sessions revoked successfully.'}), 200
    else:
        return jsonify({'error': res.get('error')}), res.get('code', 500)


