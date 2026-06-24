from app.models.base import db
from app.models.users import Users, Role, UserSession, LoginLog, AuditLog
from app.models.customer import Customer
import bcrypt
from werkzeug.security import check_password_hash
import secrets
import os
import pyotp
import urllib.parse
import random
import string
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

        if user.status != 'Active':
            return {"success": False, "error": "Your account has been deactivated. Please contact support.", "code": 403}

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
        #Stores information about the user's browser and device
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
        """Verify 2FA TOTP code or backup code for password recovery."""
        user = Users.query.filter_by(email=email).first()
        if not user:
            return {"success": False, "error": "Account not found.", "code": 404}
        if not user.twoFactorEnabled:
            return {"success": False, "error": "Two-Factor Authentication is not enabled for this account.", "code": 400}
        if not totp_code:
            return {"success": False, "error": "Verification code is required.", "code": 400}

        # Check if it is a backup code format (XXXX-XXXX)
        totp_code_clean = totp_code.strip().upper()
        if len(totp_code_clean) == 9 and '-' in totp_code_clean:
            if user.twoFactorBackupCodes:
                codes_list = [c.strip().upper() for c in user.twoFactorBackupCodes.split(',') if c.strip()]
                if totp_code_clean in codes_list:
                    # Valid backup code
                    codes_list.remove(totp_code_clean)
                    user.twoFactorBackupCodes = ",".join(codes_list)
                    try:
                        db.session.commit()
                        return {"success": True, "user_id": user.userID}
                    except Exception as commit_err:
                        db.session.rollback()
                        return {"success": False, "error": "Failed to update backup codes in database.", "code": 500}
            return {"success": False, "error": "Invalid backup code or code already used.", "code": 400}

        # Standard 6-digit TOTP validation
        totp = pyotp.TOTP(user.twoFactorSecret)
        if totp.verify(totp_code_clean):
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
        """Fetch user sessions, login history, and profile counts."""
        user = Users.query.get(user_id)
        if not user:
            return None
        sessions = UserSession.query.filter_by(userID=user.userID).order_by(UserSession.lastActive.desc()).all()
        login_history = LoginLog.query.filter_by(userID=user.userID).order_by(LoginLog.loginAt.desc()).limit(5).all()
        
        # Import models inside method to avoid circular import issues
        from app.models.property import Favorite
        from app.models.operations import Visit, Consultation
        
        favorites_count = 0
        tours_count = 0
        inquiries_count = 0
        
        if user.customer_profile:
            favorites_count = Favorite.query.filter_by(customerID=user.customer_profile.customerID).count()
            tours_count = Visit.query.filter_by(customerID=user.customer_profile.customerID).count()
            inquiries_count = Consultation.query.filter_by(customerID=user.customer_profile.customerID).count()
        elif user.employee_profile:
            tours_count = Visit.query.filter_by(employeeID=user.employee_profile.employeeID).count()
            inquiries_count = Consultation.query.filter_by(assignedEmployeeID=user.employee_profile.employeeID).count()
            
        return {
            'user': user,
            'sessions': sessions,
            'login_history': login_history,
            'favorites_count': favorites_count,
            'tours_count': tours_count,
            'inquiries_count': inquiries_count
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
        """Toggle 2FA state, generating secrets to verify if enabling, or disabling directly."""
        user = Users.query.get(user_id)
        if not user:
            return {"success": False, "error": "User not found", "code": 404}

        qr_url = None
        if user.twoFactorEnabled:
            # Disable immediately
            user.twoFactorEnabled = False
            user.twoFactorSecret = None
            user.twoFactorBackupCodes = None
            status = "disabled"
        else:
            # Do NOT enable yet. Generate secret & QR code for verification step
            user.twoFactorSecret = pyotp.random_base32()
            prov_uri = pyotp.TOTP(user.twoFactorSecret).provisioning_uri(name=user.email, issuer_name="LebEstates")
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={urllib.parse.quote(prov_uri)}"
            status = "setup initiated"

        try:
            db.session.commit()
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
    def verify_and_enable_2fa(user_id, totp_code):
        """Verify the initial setup TOTP code, enable 2FA, and generate backup codes."""
        user = Users.query.get(user_id)
        if not user:
            return {"success": False, "error": "User not found", "code": 404}
        if not user.twoFactorSecret:
            return {"success": False, "error": "2FA setup secret not generated. Please toggle 2FA switch again.", "code": 400}

        totp = pyotp.TOTP(user.twoFactorSecret)
        if not totp.verify(totp_code.strip()):
            return {"success": False, "error": "Invalid verification code. Please try again.", "code": 400}

        # Generate 8 backup codes of format XXXX-XXXX
        backup_codes = []
        chars = string.ascii_uppercase + string.digits
        for _ in range(8):
            part1 = ''.join(random.choices(chars, k=4))
            part2 = ''.join(random.choices(chars, k=4))
            backup_codes.append(f"{part1}-{part2}")

        user.twoFactorBackupCodes = ",".join(backup_codes)
        user.twoFactorEnabled = True

        try:
            db.session.commit()
            return {
                "success": True,
                "backup_codes": backup_codes
            }
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": "Failed to enable 2FA in the database.", "code": 500}

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

    @staticmethod
    def get_customer_dashboard_data(user_id):
        """Fetch all dashboard data for a customer user."""
        from app.models.customer import Customer
        from app.models.property import Favorite
        from app.models.operations import Visit, Consultation, Transaction
        
        user = Users.query.get(user_id)
        if not user or not user.customer_profile:
            return {
                'favorites': [],
                'visits': [],
                'consultations': [],
                'transactions': [],
                'favorites_count': 0,
                'visits_count': 0,
                'consultations_count': 0,
                'transactions_count': 0,
                'active_deal': None
            }
            
        customer_id = user.customer_profile.customerID
        
        # 1. Favorites
        favorites = Favorite.query.filter_by(customerID=customer_id).order_by(Favorite.createdAt.desc()).all()
        
        # 2. Visits
        visits = Visit.query.filter_by(customerID=customer_id).order_by(Visit.visitDate.asc(), Visit.visitTime.asc()).all()
        
        # 3. Consultations
        consultations = Consultation.query.filter_by(customerID=customer_id).order_by(Consultation.createdAt.desc()).all()
        
        # 4. Transactions
        transactions = Transaction.query.filter(
            (Transaction.customerID == customer_id) | (Transaction.ownerID == customer_id)
        ).order_by(Transaction.transactionDate.desc()).all()
        
        # Active deal selection
        active_deal = None
        for t in transactions:
            if t.paymentStatus in ['Escrow', 'Legal']:
                active_deal = t
                break
        if not active_deal and transactions:
            for t in transactions:
                if t.paymentStatus.lower() != 'cancelled':
                    active_deal = t
                    break
            
        return {
            'favorites': favorites,
            'visits': visits,
            'consultations': consultations,
            'transactions': transactions,
            'favorites_count': len(favorites),
            'visits_count': len(visits),
            'consultations_count': len(consultations),
            'transactions_count': len(transactions),
            'active_deal': active_deal
        }
