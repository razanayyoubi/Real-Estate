from flask import Flask
from app.models.base import db
from app.config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    # Import models to ensure they are known to SQLAlchemy
    from app.models.users import Role, Users, Blacklist, AuditLog, UserSession, LoginLog, PasswordResetToken, SupportSession, SupportMessage
    from app.models.property import Property, PropertyImage, Favorite
    from app.models.hr import Employee, Salary, CommissionSetting
    from app.models.customer import Customer, CustomerDocument
    from app.models.operations import Visit, Consultation, Transaction
    from app.models.notification import Notification

    from app.routes.main import main_bp
    app.register_blueprint(main_bp)

    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    from app.routes.customers import customers_bp
    app.register_blueprint(customers_bp)

    from app.routes.employees import employees_bp
    app.register_blueprint(employees_bp)

    from app.routes.roles import roles_bp
    app.register_blueprint(roles_bp)

    from app.routes.blacklist import blacklist_bp
    app.register_blueprint(blacklist_bp)

    from app.routes.properties import properties_bp
    app.register_blueprint(properties_bp)

    from app.routes.visits import visits_bp
    app.register_blueprint(visits_bp)

    from app.routes.consultations import consultations_bp
    app.register_blueprint(consultations_bp)

    from app.routes.transactions import transactions_bp
    app.register_blueprint(transactions_bp)

    from app.routes.commissions import commissions_bp
    app.register_blueprint(commissions_bp)

    from app.routes.audit_logs import audit_logs_bp
    app.register_blueprint(audit_logs_bp)

    from app.routes.notifications import notifications_bp
    app.register_blueprint(notifications_bp)

    from app.routes.email_hub import email_hub_bp
    app.register_blueprint(email_hub_bp)

    from app.routes.support import support_bp
    app.register_blueprint(support_bp)

    from app.routes.expenses import expenses_bp
    app.register_blueprint(expenses_bp)

    # Global session checker middleware
    from flask import session, redirect, url_for, request
    from datetime import datetime

    @app.before_request
    def check_user_session():
        # Skip static assets
        if request.endpoint == 'static' or request.path.startswith('/static'):
            return

        if 'user_id' in session:
            session_token = session.get('session_token')
            if not session_token:
                session.clear()
                if request.endpoint and request.endpoint not in ['auth.login_page', 'auth.login_submit', 'auth.register_page', 'auth.register_submit', 'auth.logout']:
                    return redirect(url_for('auth.login_page'))
                return

            from app.models.users import UserSession
            user_sess = UserSession.query.filter_by(userID=session['user_id'], token=session_token).first()
            if not user_sess:
                session.clear()
                if request.endpoint and request.endpoint not in ['auth.login_page', 'auth.login_submit', 'auth.register_page', 'auth.register_submit', 'auth.logout']:
                    return redirect(url_for('auth.login_page'))
                return
            
            # Session is valid, update last active timestamp
            try:
                user_sess.lastActive = datetime.utcnow()
                db.session.commit()
            except Exception:
                db.session.rollback()

    @app.context_processor
    def inject_user():
        if 'user_id' in session:
            from app.models.users import Users
            try:
                user = Users.query.get(session['user_id'])
                return dict(current_user=user)
            except Exception:
                pass
        return dict(current_user=None)

    # Import email hub models to ensure they are registered with SQLAlchemy
    from app.models.email_hub import EmailTemplate, SenderIdentity, EmailFeatureConfig, DistributionList, DistributionListMember, DistributionListRule, EmailLog, EmailDraft

    # Auto-migration & Database seeding
    with app.app_context():
        # Ensure all tables are created first
        try:
            db.create_all()
        except Exception as create_err:
            app.logger.error(f"Database creation failed: {create_err}")

        # Auto-migration for 2FA backup codes column
        try:
            db.session.execute(db.text("SELECT twoFactorBackupCodes FROM users LIMIT 1"))
        except Exception:
            db.session.rollback()
            try:
                db.session.execute(db.text("ALTER TABLE users ADD COLUMN twoFactorBackupCodes TEXT NULL"))
                db.session.commit()
                app.logger.info("Database migration: Added twoFactorBackupCodes column to users table.")
            except Exception as migrate_err:
                db.session.rollback()
                app.logger.error(f"Database migration failed: {migrate_err}")

        try:
            # Seed Default Roles
            from app.models.users import Users, Role
            for rname in ['Admin', 'Employee', 'Customer', 'Accountant']:
                if not Role.query.filter_by(roleName=rname).first():
                    db.session.add(Role(roleName=rname))
            db.session.commit()

            # Seed Default Users
            import bcrypt
            from datetime import date
            roles = {r.roleName: r.roleID for r in Role.query.all()}
            default_users = [
                {'fullName': 'Admin User', 'email': 'admin@lebestates.com', 'roleName': 'Admin'},
                {'fullName': 'Employee User', 'email': 'employee@lebestates.com', 'roleName': 'Employee'},
                {'fullName': 'Customer User', 'email': 'customer@lebestates.com', 'roleName': 'Customer'},
                {'fullName': 'Accountant User', 'email': 'accountant@lebestates.com', 'roleName': 'Accountant'}
            ]
            for u in default_users:
                existing_user = Users.query.filter_by(email=u['email']).first()
                if not existing_user:
                    dummy_hash = bcrypt.hashpw('123456'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    existing_user = Users(
                        fullName=u['fullName'],
                        email=u['email'],
                        passwordHash=dummy_hash,
                        roleID=roles[u['roleName']],
                        status='Active'
                    )
                    db.session.add(existing_user)
                    db.session.flush()
                
                # Ensure customer / employee profile tables exist
                if u['roleName'] == 'Customer':
                    if not Customer.query.filter_by(userID=existing_user.userID).first():
                        db.session.add(Customer(userID=existing_user.userID, address='Lebanon'))
                elif u['roleName'] in ['Employee', 'Admin', 'Accountant']:
                    if not Employee.query.filter_by(userID=existing_user.userID).first():
                        db.session.add(Employee(userID=existing_user.userID, position=u['roleName'], hireDate=date.today(), status='Active'))
            db.session.commit()

            # Seed AI Assistant User
            ai_user = Users.query.filter_by(email='ai@lebestates.com').first()
            if not ai_user:
                employee_role = Role.query.filter_by(roleName='Employee').first()
                role_id = employee_role.roleID if employee_role else 1
                
                import bcrypt
                import secrets
                dummy_hash = bcrypt.hashpw(secrets.token_hex(16).encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                
                ai_user = Users(
                    fullName='AI Assistant',
                    email='ai@lebestates.com',
                    passwordHash=dummy_hash,
                    roleID=role_id,
                    status='Active'
                )
                db.session.add(ai_user)
                db.session.commit()
            
            # Seed default Sender Identity
            if not SenderIdentity.query.first():
                default_sender = SenderIdentity(
                    displayName=app.config.get('MAILJET_SENDER_NAME', 'LebEstates'),
                    fromEmail=app.config.get('MAILJET_SENDER_EMAIL', 'no-reply@lebestates.com'),
                    isDefault=True,
                    isActive=True
                )
                db.session.add(default_sender)
                db.session.commit()
            
            # Seed default feature configs
            features_to_seed = [
                ("ForgotPassword", "Forgot Password Link", "Auth", "AUTH-RESET-V1"),
                ("Otp2FA", "2FA Verification Code", "Auth", "AUTH-OTP-SECURE"),
                ("VisitStatusChanged", "Property Visit Update", "Operations", "CUST-VISIT-UPDATE")
            ]
            for fkey, fname, fcat, tkey in features_to_seed:
                if not EmailFeatureConfig.query.filter_by(featureKey=fkey).first():
                    db.session.add(EmailFeatureConfig(
                        featureKey=fkey,
                        featureName=fname,
                        category=fcat,
                        templateKey=tkey,
                        enabled=True
                    ))
            
            # Seed default templates
            templates_to_seed = [
                ("AUTH-RESET-V1", "Forgot Password Email Template", "Auth", "Reset your LebEstates password", 
                 "<h2>Reset Password</h2><p>Hello {{CustomerName}},</p><p>Please reset your password by clicking the link below:</p><p><a href='{{ActionUrl}}'>Reset Password</a></p><p>Thank you!</p>"),
                ("AUTH-OTP-SECURE", "2FA Verification Code Template", "Auth", "Your LebEstates verification code",
                 "<h2>2FA Security Code</h2><p>Hello {{CustomerName}},</p><p>Your secure verification code is: <strong>{{OtpCode}}</strong></p><p>If you didn't request this, contact support.</p>"),
                ("CUST-VISIT-UPDATE", "Visit Request Status Template", "Operations", "Property visit update",
                 "<h2>Visit Update</h2><p>Hello {{CustomerName}},</p><p>The status of your visit request for property {{PropertyTitle}} has been updated to: <strong>{{VisitStatus}}</strong>.</p><p>Scheduled Date: {{VisitDate}} at {{VisitTime}}</p>")
            ]
            for tkey, tname, tcat, tsubj, tbody in templates_to_seed:
                if not EmailTemplate.query.filter_by(templateKey=tkey).first():
                    db.session.add(EmailTemplate(
                        templateKey=tkey,
                        name=tname,
                        category=tcat,
                        subject=tsubj,
                        body=tbody,
                        isActive=True
                    ))
            db.session.commit()
        except Exception as seed_err:
            db.session.rollback()
            app.logger.error(f"Email Hub db setup/seeding failed: {seed_err}")

    return app

