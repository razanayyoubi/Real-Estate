from app.models.base import db
from app.models.users import Users, Role, UserSession, LoginLog, AuditLog
from app.models.customer import Customer
import bcrypt
from werkzeug.security import check_password_hash
import secrets
import os
import pyotp
import urllib.parse
from datetime import datetime

def check_password(password_hash, password):
    if not password_hash:
        return False
    if password_hash.startswith(('scrypt:', 'pbkdf2:', 'bcrypt:')):
        return check_password_hash(password_hash, password)
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except ValueError:
        try:
            return check_password_hash(password_hash, password)
        except Exception:
            return False

class AuthService:
    @staticmethod
    def get_user_by_id(user_id):
        """Retrieve user by database ID."""
        return Users.query.get(user_id)

    @staticmethod
    def register_customer(full_name, email, phone_number, password, address):
        # Check for unique constraints in DB
        existing_email = Users.query.filter_by(email=email).first()
        if existing_email:
            return {"success": False, "error": "This email address is already registered.", "code": 400}

        # Dynamic role resolution: Ensure 'Customer' role exists
        customer_role = Role.query.filter_by(roleName='Customer').first()
        if not customer_role:
            try:
                customer_role = Role(roleName='Customer')
                db.session.add(customer_role)
                db.session.commit()
            except Exception as role_err:
                db.session.rollback()
                print(f"Role creation failed: {role_err}")
                return {"success": False, "error": "Database setup error: Customer role could not be seeded.", "code": 500}

        # Hash password with bcrypt
        hashed_pwd = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Atomic transaction to create User & Customer profile
        try:
            # Create user record
            new_user = Users(
                fullName=full_name,
                email=email,
                phoneNumber=phone_number if phone_number else None,
                passwordHash=hashed_pwd,
                roleID=customer_role.roleID,
                status='Active'
            )
            db.session.add(new_user)
            db.session.flush()  # Populates new_user.userID without committing transaction

            # Create customer record linked to user
            new_customer = Customer(
                userID=new_user.userID,
                nationalID=None,
                address=address if address else None
            )
            db.session.add(new_customer)
            db.session.flush()

            from flask import session
            actor_id = session.get('user_id') or new_user.userID
            AuditLog.log_action(
                action='ADD',
                table_name='customer',
                record_id=new_customer.customerID,
                description=f"Registered new customer '{full_name}' (email: '{email}')",
                user_id=actor_id
            )

            db.session.commit()

            return {"success": True}

        except Exception as db_err:
            db.session.rollback()
            print(f"Registration database error: {db_err}")
            return {"success": False, "error": "An internal error occurred. Please try again.", "code": 500}

    @staticmethod
    def verify_credentials(email, password):
        user = Users.query.filter_by(email=email).first()
        if not user:
            return {"success": False, "error": "Invalid email or password.", "code": 401}

        # Compare password hash
        if check_password(user.passwordHash, password):
            return {
                "success": True,
                "user_id": user.userID,
                "role_id": user.roleID,
                "full_name": user.fullName,
                "role_name": user.role.roleName if user.role else 'Customer'
            }
        else:
            return {"success": False, "error": "Invalid email or password.", "code": 401}

    @staticmethod
    def create_user_session(user_id, ip_address, user_agent):
        """Create user session log in DB and return token."""
        session_token = secrets.token_hex(16)
        try:
            new_sess = UserSession(
                userID=user_id,
                token=session_token,
                ipAddress=ip_address,
                userAgent=user_agent[:255] if user_agent else ''
            )
            db.session.add(new_sess)
            db.session.commit()
            return session_token
        except Exception as e:
            db.session.rollback()
            print(f"Failed to record session: {e}")
            return None

    @staticmethod
    def log_login_attempt(user_id, ip_address, user_agent, status):
        """Log a successful or failed login attempt."""
        try:
            new_log = LoginLog(
                userID=user_id,
                ipAddress=ip_address,
                userAgent=user_agent[:255] if user_agent else '',
                status=status
            )
            db.session.add(new_log)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Failed to log login: {e}")

    @staticmethod
    def delete_user_session(user_id, session_token):
        """Delete session on logout."""
        try:
            UserSession.query.filter_by(userID=user_id, token=session_token).delete()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Failed to delete session on logout: {e}")

    @staticmethod
    def verify_forgot_password_totp(email, totp_code):
        """Verify 2FA TOTP code for password recovery."""
        user = Users.query.filter_by(email=email).first()
        if not user:
            return {"success": False, "error": "Account not found.", "code": 404}
        if not user.twoFactorEnabled:
            return {"success": False, "error": "Two-Factor Authentication is not enabled for this account.", "code": 400}
        if not totp_code:
            return {"success": False, "error": "6-digit verification code is required.", "code": 400}

        totp = pyotp.TOTP(user.twoFactorSecret)
        if totp.verify(totp_code):
            return {"success": True, "user_id": user.userID}
        else:
            return {"success": False, "error": "Invalid 2FA verification code.", "code": 400}

    @staticmethod
    def reset_password(user_id, new_password, ip_address, user_agent):
        """Reset password, log direct login, and return session token."""
        user = Users.query.get(user_id)
        if not user:
            return {"success": False, "error": "User not found.", "code": 404}

        hashed_pwd = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user.passwordHash = hashed_pwd

        try:
            # Log successful password reset login
            new_log = LoginLog(
                userID=user.userID,
                ipAddress=ip_address,
                userAgent=user_agent[:255] if user_agent else '',
                status='Success'
            )
            db.session.add(new_log)
            
            # Log the user in directly
            session_token = secrets.token_hex(16)
            new_sess = UserSession(
                userID=user.userID,
                token=session_token,
                ipAddress=ip_address,
                userAgent=user_agent[:255] if user_agent else ''
            )
            db.session.add(new_sess)
            db.session.commit()

            role_name = user.role.roleName if user.role else 'Customer'
            redirect_url = '/dashboard' if role_name.lower() in ['admin', 'employee', 'accountant'] else '/'

            return {
                "success": True,
                "session_token": session_token,
                "role_id": user.roleID,
                "full_name": user.fullName,
                "role_name": role_name,
                "redirect_url": redirect_url
            }
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": f"Failed to reset password: {str(e)}", "code": 500}

    @staticmethod
    def get_profile_data(user_id):
        """Fetch user sessions and login history."""
        user = Users.query.get(user_id)
        if not user:
            return None
        sessions = UserSession.query.filter_by(userID=user.userID).order_by(UserSession.lastActive.desc()).all()
        login_history = LoginLog.query.filter_by(userID=user.userID).order_by(LoginLog.loginAt.desc()).limit(5).all()
        return {
            'user': user,
            'sessions': sessions,
            'login_history': login_history
        }

    @staticmethod
    def update_profile_details(user_id, full_name, phone_number, avatar_file=None):
        """Update profile details and avatar."""
        user = Users.query.get(user_id)
        if not user:
            return {"success": False, "error": "User not found", "code": 404}

        if not full_name:
            return {"success": False, "error": "Full Name is required.", "code": 400}

        if avatar_file and avatar_file.filename != '':
            allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif'}
            _, ext = os.path.splitext(avatar_file.filename.lower())
            if ext not in allowed_extensions:
                return {"success": False, "error": "Invalid file type. Allowed formats: PNG, JPG, JPEG, GIF.", "code": 400}

            try:
                user.avatar = avatar_file.read()
            except Exception as e:
                return {"success": False, "error": f"Failed to save profile picture: {str(e)}", "code": 500}

        user.fullName = full_name
        user.phoneNumber = phone_number if phone_number else None

        try:
            db.session.commit()
            return {"success": True, "full_name": user.fullName}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": "Failed to update profile details in database.", "code": 500}

    @staticmethod
    def get_user_avatar(user_id):
        """Fetch avatar image blob and mimetype."""
        user = Users.query.get(user_id)
        if not user or not user.avatar:
            return None, None
        
        avatar_data = user.avatar
        content_type = 'image/jpeg'
        if avatar_data.startswith(b'\x89PNG\r\n\x1a\n'):
            content_type = 'image/png'
        elif avatar_data.startswith(b'GIF87a') or avatar_data.startswith(b'GIF89a'):
            content_type = 'image/gif'
        elif avatar_data.startswith(b'\xff\xd8'):
            content_type = 'image/jpeg'
        return avatar_data, content_type

    @staticmethod
    def change_user_password(user_id, current_password, new_password):
        """Verify current password and hash/update new password."""
        user = Users.query.get(user_id)
        if not user:
            return {"success": False, "error": "User not found", "code": 404}

        if not check_password(user.passwordHash, current_password):
            return {"success": False, "error": "Incorrect current password.", "code": 400}

        hashed_pwd = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user.passwordHash = hashed_pwd

        try:
            db.session.commit()
            return {"success": True}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": "Failed to change password.", "code": 500}

    @staticmethod
    def toggle_user_2fa(user_id):
        """Toggle 2FA state, generating secrets if enabling."""
        user = Users.query.get(user_id)
        if not user:
            return {"success": False, "error": "User not found", "code": 404}

        user.twoFactorEnabled = not user.twoFactorEnabled
        qr_url = None
        if user.twoFactorEnabled:
            user.twoFactorSecret = pyotp.random_base32()
            prov_uri = pyotp.TOTP(user.twoFactorSecret).provisioning_uri(name=user.email, issuer_name="LebEstates")
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={urllib.parse.quote(prov_uri)}"
        else:
            user.twoFactorSecret = None

        try:
            db.session.commit()
            status = "enabled" if user.twoFactorEnabled else "disabled"
            return {
                "success": True,
                "message": f"2FA setup has been {status}.",
                "enabled": user.twoFactorEnabled,
                "secret": user.twoFactorSecret,
                "qr_url": qr_url
            }
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": "Failed to toggle 2FA.", "code": 500}

    @staticmethod
    def revoke_user_session(user_id, session_id, current_token):
        """Revoke a specific device session."""
        target_sess = UserSession.query.filter_by(sessionID=session_id, userID=user_id).first()
        if not target_sess:
            return {"success": False, "error": "Session not found or unauthorized.", "code": 404}

        is_current = (target_sess.token == current_token)

        try:
            db.session.delete(target_sess)
            db.session.commit()
            return {"success": True, "logged_out": is_current}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": "Failed to revoke session.", "code": 500}

    @staticmethod
    def revoke_all_other_user_sessions(user_id, current_token):
        """Revoke all other active device sessions."""
        try:
            UserSession.query.filter(UserSession.userID == user_id, UserSession.token != current_token).delete()
            db.session.commit()
            return {"success": True}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": "Failed to revoke other sessions.", "code": 500}

