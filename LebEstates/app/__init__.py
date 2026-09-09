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
            
            # Seed Sender Identities
            default_sender_email = app.config.get('MAILJET_SENDER_EMAIL', 'mohamadayoubi050@gmail.com')
            default_sender_name = app.config.get('MAILJET_SENDER_NAME', 'LebEstates')
            sender_profiles = [
                (default_sender_name, default_sender_email, "support@lebestates.com", True),
                ("LebEstates Support", "support@lebestates.com", "support@lebestates.com", False),
                ("LebEstates Operations", "operations@lebestates.com", "operations@lebestates.com", False),
                ("LebEstates Billing & Escrow", "billing@lebestates.com", "billing@lebestates.com", False)
            ]
            for sname, semail, sreply, sdef in sender_profiles:
                sender_rec = SenderIdentity.query.filter_by(fromEmail=semail).first()
                if not sender_rec:
                    db.session.add(SenderIdentity(
                        displayName=sname,
                        fromEmail=semail,
                        replyToEmail=sreply,
                        isDefault=sdef,
                        isActive=True
                    ))
                elif sdef:
                    SenderIdentity.query.filter(SenderIdentity.senderIdentityID != sender_rec.senderIdentityID).update({'isDefault': False})
                    sender_rec.isDefault = True
                    sender_rec.displayName = sname
            db.session.commit()

            # Seed Distribution Lists
            dist_lists_seed = [
                ("All Active Customers", "Broadcast list reaching all verified active registered customers.", False, False, True),
                ("Real Estate Agents & Staff", "Operations broadcast list reaching all active agents and staff members.", True, False, False),
                ("System Administrators", "Critical administrative notifications and escalation alert list.", False, True, False),
                ("VIP Landlords & Property Owners", "Exclusive updates and compliance announcements for property owners.", False, False, True)
            ]
            for dl_name, dl_desc, inc_emp, inc_adm, inc_cust in dist_lists_seed:
                dl_obj = DistributionList.query.filter_by(name=dl_name).first()
                if not dl_obj:
                    dl_obj = DistributionList(name=dl_name, description=dl_desc, isActive=True)
                    db.session.add(dl_obj)
                    db.session.flush()
                    rule = DistributionListRule(
                        distributionListID=dl_obj.distributionListID,
                        includeEmployees=inc_emp,
                        includeAdmins=inc_adm,
                        includeCustomers=inc_cust,
                        onlyActiveUsers=True,
                        excludeBlacklistedCustomers=True
                    )
                    db.session.add(rule)
            db.session.commit()
            
            # Seed all feature configs with descriptions
            features_to_seed = [
                # 1. Auth & Security
                ("ForgotPassword", "Password Reset Link", "Auth", "AUTH-RESET-V1", "Sends a secure password reset link with a 1-hour expiration token when requested by a customer or staff member."),
                ("Otp2FA", "Two Factor Authentication", "Auth", "AUTH-OTP-SECURE", "Dispatches a 6-digit one-time verification code for multi-factor authentication security during user login."),
                ("WelcomeRegistration", "Welcome / Registration Confirmation", "Auth", "AUTH-WELCOME-V1", "Sends a welcome confirmation acknowledging account creation and verified membership status."),
                
                # 2. Property Listings
                ("PropertySubmitted", "Property Listing Submitted", "Property", "PROP-SUBMITTED-V1", "Notifies the property owner that their submitted listing was received and is under review by our verification team."),
                ("PropertyApproved", "Property Listing Approved & Live", "Property", "PROP-APPROVED-V1", "Alerts the property owner that their listing has passed quality review and is now publicly live on the marketplace."),
                ("PropertyRejected", "Property Listing Rejected", "Property", "PROP-REJECTED-V1", "Notifies the property owner if their submission was declined, including specific feedback and required corrections."),

                # 3. Operations: Visits & Viewings
                ("VisitScheduled", "Visit Request Scheduled", "Operations", "VISIT-BOOKED-V1", "Sends an initial viewing confirmation to the customer with scheduled date, time, and property address."),
                ("VisitStatusChanged", "Visit Update / Status Changed", "Operations", "CUST-VISIT-UPDATE", "Sends real-time updates to the customer whenever a visit is rescheduled, completed, or cancelled."),
                ("VisitConsultantAssignedCustomer", "Visit Consultant Assigned (Customer)", "Operations", "VISIT-AGENT-CUST-V1", "Notifies the customer with contact details of the dedicated agent assigned to guide their property viewing."),
                ("VisitConsultantAssignedEmployee", "Visit Viewing Assignment (Employee)", "Operations", "VISIT-AGENT-EMP-V1", "Sends viewing assignment details, property specifications, and client contact notes to the assigned agent."),

                # 4. Visit Reminders (Background)
                ("VisitReminder24h", "Visit Reminder (24h Before)", "Reminders", "VISIT-REMIND-24H", "Scheduled background task: Sends an automated reminder 24 hours before a property viewing to both client and agent."),
                ("VisitReminder1h", "Visit Reminder (1h Before)", "Reminders", "VISIT-REMIND-1H", "Scheduled background task: Sends an urgent reminder 1 hour before a property viewing with location directions."),
                ("VisitFeedback2h", "Visit Feedback (2h Post-Visit)", "Reminders", "VISIT-FEEDBACK-2H", "Scheduled background task: Sends an automated survey 2 hours after a viewing to collect customer feedback on the property."),

                # 5. Operations: Consultations
                ("ConsultationBooked", "Consultation Booked & Confirmed", "Operations", "CONS-BOOKED-V1", "Confirms appointment booking for real estate advisory, property valuation, or investment consultation."),
                ("ConsultationStatusChanged", "Consultation Update / Status Changed", "Operations", "CONS-STATUS-V1", "Notifies the customer when an advisory consultation appointment is rescheduled, completed, or cancelled."),
                ("ConsultationConsultantAssignedCustomer", "Consultation Advisor Assigned (Customer)", "Operations", "CONS-AGENT-CUST-V1", "Sends advisor contact profile, meeting link, and preparation notes to the customer."),
                ("ConsultationConsultantAssignedEmployee", "Consultation Assigned (Employee)", "Operations", "CONS-AGENT-EMP-V1", "Dispatches consultation briefing, client goals, and meeting agenda to the assigned advisor."),

                # 6. Consultation Reminders (Background)
                ("ConsultationReminder1h", "Consultation Reminder (1h Before)", "Reminders", "CONS-REMIND-1H", "Scheduled background task: Sends an automated reminder 1 hour prior to a consultation with video link or room info."),
                ("ConsultationSurvey1d", "Consultation CSAT Survey (1d Post-Meeting)", "Reminders", "CONS-SURVEY-1D", "Scheduled background task: Dispatches a post-consultation CSAT survey 24 hours after an advisory session."),

                # 7. Transactions & Payments
                ("TransactionInitiated", "Transaction Initiated (Buyer & Landlord)", "Transactions", "TRANS-INIT-V1", "Alerts both Buyer/Tenant and Landlord/Seller that a new purchase or rental transaction has commenced."),
                ("TransactionStatusUpdated", "Transaction Status Updated (Buyer & Landlord)", "Transactions", "TRANS-STATUS-V1", "Notifies parties when a deal status advances (e.g., Pending, Escrow, Legal Verification, Closed)."),
                ("TransactionReceipt", "Transaction Official Receipt PDF", "Transactions", "TRANS-RECEIPT-V1", "Automatically attaches and emails an official PDF payment receipt ledger upon transaction closing or payment."),

                # 8. Rent / Installment Payment Reminders (Background)
                ("PaymentReminder7d", "Payment Reminder (7 Days Before Due)", "Reminders", "PAY-REMIND-7D", "Scheduled background task: Sends an upcoming payment notice 7 days before rent or installment due date."),
                ("PaymentReminder3d", "Payment Reminder (3 Days Before Due)", "Reminders", "PAY-REMIND-3D", "Scheduled background task: Sends an urgent payment notice 3 days before rent or installment due date."),
                ("PaymentOverdue1d", "Payment Overdue Notice (1 Day After Due)", "Reminders", "PAY-OVERDUE-1D", "Scheduled background task: Sends an overdue notice with late policy details 1 day after a missed due date."),
                ("PaymentOverdue7d", "Late Payment Warning & Escalation (7 Days After Due)", "Reminders", "PAY-OVERDUE-7D", "Scheduled background task: Sends a 7-day severe overdue escalation notice with late fee penalty calculation and cc's agent."),

                # 9. Customer Support
                ("SupportTicketClosed", "Support Ticket Closed", "Support", "SUPP-CLOSED-V1", "Notifies the customer that their support inquiry has been resolved and invites them to submit a satisfaction rating.")
            ]
            for fkey, fname, fcat, tkey, fdesc in features_to_seed:
                feat = EmailFeatureConfig.query.filter_by(featureKey=fkey).first()
                if not feat:
                    db.session.add(EmailFeatureConfig(
                        featureKey=fkey,
                        featureName=fname,
                        category=fcat,
                        templateKey=tkey,
                        description=fdesc,
                        enabled=True
                    ))
                elif not feat.description:
                    feat.description = fdesc
            db.session.commit()
            
            # Helper for HTML email styling
            def email_shell(title, content):
                return (
                    f"<div style=\"font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 10px; border: 1px solid #e2e8f0; overflow: hidden;\">"
                    f"<div style=\"background: #00081e; padding: 24px; text-align: center; border-bottom: 3px solid #d4af37;\">"
                    f"<h1 style=\"color: #ffffff; margin: 0; font-size: 24px; letter-spacing: 1px;\">LEB<span style=\"color: #d4af37;\">ESTATES</span></h1>"
                    f"</div>"
                    f"<div style=\"padding: 30px; color: #1a202c; line-height: 1.6;\">"
                    f"<h2 style=\"color: #00081e; margin-top: 0;\">{title}</h2>"
                    f"{content}"
                    f"</div>"
                    f"<div style=\"background: #f7fafc; padding: 16px; text-align: center; font-size: 12px; color: #a0aec0; border-top: 1px solid #edf2f7;\">"
                    f"&copy; LebEstates Luxury Real Estate &bull; Beirut, Lebanon"
                    f"</div>"
                    f"</div>"
                )

            # Seed all default templates (standardizing all 46 template keys with LebEstates Luxury theme)
            templates_to_seed = [
                # 1. Auth & Security
                ("AUTH-RESET-V1", "Forgot Password Email Template", "Auth", "Reset your LebEstates password", 
                 email_shell("Password Reset Request", "<p>Hello <strong>{{CustomerName}}</strong>,</p><p>We received a request to reset your password. Click the button below:</p><div style='text-align:center; margin:30px 0;'><a href='{{ActionUrl}}' style='background:#00081e; color:#ffffff; padding:14px 28px; text-decoration:none; border-radius:6px; font-weight:600; display:inline-block;'>Reset Password</a></div><p style='color:#718096; font-size:13px;'>Link expires in {{expiry}}.</p>")),
                
                ("AUTH-OTP-SECURE", "2FA Verification Code Template", "Auth", "Your LebEstates 2FA Security Code: {{OtpCode}}",
                 email_shell("Two-Factor Authentication", "<p>Hello <strong>{{CustomerName}}</strong>,</p><p>Use the verification code below to complete your login securely:</p><div style='background:#f8fafc; border:2px dashed #d4af37; border-radius:8px; padding:20px; text-align:center; margin:25px 0;'><span style='font-size:32px; font-weight:800; letter-spacing:6px; color:#00081e;'>{{OtpCode}}</span></div><p style='color:#718096; font-size:13px;'>This code is single-use and valid for 10 minutes.</p>")),

                ("AUTH-WELCOME-V1", "Welcome Registration Template", "Auth", "Welcome to LebEstates, {{CustomerName}}!",
                 email_shell("Welcome to LebEstates!", "<p>Hello <strong>{{CustomerName}}</strong>,</p><p>Welcome to Lebanon's premier luxury real estate destination. Your account (<strong>{{CustomerEmail}}</strong>) is now active and ready.</p><div style='text-align:center; margin:30px 0;'><a href='{{LoginUrl}}' style='background:#00081e; color:#d4af37; padding:14px 28px; text-decoration:none; border-radius:6px; font-weight:600; display:inline-block;'>Explore Properties</a></div>")),

                ("AUTH-WELCOME", "Welcome & Registration Confirmation", "Auth", "Welcome to LebEstates Luxury Real Estate",
                 email_shell("Welcome to LebEstates!", "<p>Hello <strong>{{CustomerName}}</strong>,</p><p>Welcome to Lebanon's premier luxury real estate destination. Your account has been successfully created.</p><div style='background:#f8fafc; border-left:4px solid #d4af37; padding:16px; margin:20px 0; border-radius:4px;'><p style='margin:4px 0;'><strong>Account Name:</strong> {{CustomerName}}</p><p style='margin:4px 0;'><strong>Access Level:</strong> Verified Member</p></div><p style='color:#718096; font-size:13px;'>You can now browse exclusive listings, schedule private viewings, and request consultations.</p>")),

                # 2. Property Listings
                ("PROP-SUBMITTED-V1", "Property Listing Submitted Template", "Property", "Property Listing Submitted: {{PropertyTitle}}",
                 email_shell("Listing Submission Received", "<p>Hello <strong>{{CustomerName}}</strong>,</p><p>Thank you for submitting your property. Our team has received your submission:</p><div style='background:#f8fafc; border-left:4px solid #d4af37; padding:16px; margin:20px 0; border-radius:4px;'><p style='margin:4px 0;'><strong>Property:</strong> {{PropertyTitle}}</p><p style='margin:4px 0;'><strong>Type:</strong> {{PropertyType}} &bull; <strong>Price:</strong> {{Price}}</p><p style='margin:4px 0;'><strong>Location:</strong> {{Location}}</p><p style='margin:4px 0;'><strong>Status:</strong> <span style='background:#fef3c7; color:#92400e; padding:2px 8px; border-radius:4px;'>Pending Review</span></p></div><p>Our quality verification team will review your submission shortly.</p>")),

                ("PROP-SUBMITTED", "Property Listing Submitted Template", "Property", "Property Listing Submitted: {{PropertyTitle}}",
                 email_shell("Listing Submission Received", "<p>Hello <strong>{{CustomerName}}</strong>,</p><p>Thank you for submitting your property listing. Our team is currently reviewing your submission:</p><div style='background:#f8fafc; border-left:4px solid #d4af37; padding:16px; margin:20px 0; border-radius:4px;'><p style='margin:4px 0;'><strong>Property:</strong> {{PropertyTitle}}</p><p style='margin:4px 0;'><strong>Type:</strong> {{PropertyType}} &bull; <strong>Price:</strong> {{Price}}</p><p style='margin:4px 0;'><strong>Location:</strong> {{Location}}</p><p style='margin:4px 0;'><strong>Status:</strong> <span style='background:#fef3c7; color:#92400e; padding:2px 8px; border-radius:4px;'>Pending Review</span></p></div><p style='color:#718096; font-size:13px;'>You will receive an automated notification once your listing is approved and published.</p>")),

                ("PROP-APPROVED-V1", "Property Approved & Live Template", "Property", "Your Property Listing is Now Live: {{PropertyTitle}}",
                 email_shell("Listing Approved & Live!", "<p>Hello <strong>{{CustomerName}}</strong>,</p><p>Great news! Your property listing <strong>\"{{PropertyTitle}}\"</strong> has been approved and is now live on LebEstates.</p><div style='background:#f0fdf4; border:1px solid #bbf7d0; padding:16px; margin:20px 0; border-radius:6px;'><p style='margin:4px 0; color:#166534;'><strong>Price:</strong> {{Price}} &bull; <strong>Location:</strong> {{Location}}</p></div><div style='text-align:center; margin:25px 0;'><a href='{{PropertyUrl}}' style='background:#00081e; color:#d4af37; padding:12px 24px; text-decoration:none; border-radius:6px; font-weight:600; display:inline-block;'>View Live Listing</a></div>")),

                ("PROP-APPROVED", "Property Listing Approved & Live Template", "Property", "Your Property Listing is Now Live: {{PropertyTitle}}",
                 email_shell("Listing Approved & Live!", "<p>Hello <strong>{{CustomerName}}</strong>,</p><p>Great news! Your property listing <strong>\"{{PropertyTitle}}\"</strong> has been approved and is now live on LebEstates.</p><div style='background:#f0fdf4; border:1px solid #bbf7d0; padding:16px; margin:20px 0; border-radius:6px;'><p style='margin:4px 0; color:#166534;'><strong>Status:</strong> Active & Live for Prospective Buyers</p></div><div style='text-align:center; margin:25px 0;'><a href='{{PropertyUrl}}' style='background:#00081e; color:#d4af37; padding:12px 24px; text-decoration:none; border-radius:6px; font-weight:600; display:inline-block;'>View Live Listing</a></div>")),

                ("PROP-REJECTED-V1", "Property Rejected Template", "Property", "Update regarding your listing: {{PropertyTitle}}",
                 email_shell("Listing Review Notice", "<p>Hello <strong>{{CustomerName}}</strong>,</p><p>Our verification team reviewed your property submission <strong>\"{{PropertyTitle}}\"</strong> and could not approve it at this time.</p><div style='background:#fef2f2; border-left:4px solid #dc2626; padding:16px; margin:20px 0; border-radius:4px;'><p style='margin:4px 0; color:#991b1b;'><strong>Reason / Feedback:</strong> {{Reason}}</p></div><p>You can edit and resubmit your listing or contact our team for assistance.</p>")),

                ("PROP-REJECTED", "Property Listing Rejected Template", "Property", "Update regarding your listing: {{PropertyTitle}}",
                 email_shell("Listing Review Notice", "<p>Hello <strong>{{CustomerName}}</strong>,</p><p>Our verification team reviewed your property submission <strong>\"{{PropertyTitle}}\"</strong> and could not approve it at this time.</p><div style='background:#fef2f2; border-left:4px solid #dc2626; padding:16px; margin:20px 0; border-radius:4px;'><p style='margin:4px 0; color:#991b1b;'><strong>Reason / Feedback:</strong> {{RejectionReason}}</p></div><p style='color:#718096; font-size:13px;'>Please update the necessary documentation or photos and submit again.</p>")),

                # 3. Operations: Visits & Viewings
                ("VISIT-BOOKED-V1", "Visit Request Scheduled Template", "Operations", "Property Visit Confirmed: {{PropertyTitle}}",
                 email_shell("Visit Booking Confirmed", "<p>Hello <strong>{{CustomerName}}</strong>,</p><p>Your property viewing request has been confirmed:</p><div style='background:#f8fafc; border-left:4px solid #00081e; padding:16px; margin:20px 0; border-radius:4px;'><p style='margin:4px 0;'><strong>Property:</strong> {{PropertyTitle}}</p><p style='margin:4px 0;'><strong>Date & Time:</strong> {{VisitDate}} at {{VisitTime}}</p><p style='margin:4px 0;'><strong>Address:</strong> {{Address}}</p></div>")),

                ("VISIT-SCHEDULED", "Visit Request Scheduled Confirmation", "Operations", "Property Visit Confirmed: {{PropertyTitle}}",
                 email_shell("Property Visit Confirmed", "<p>Hello <strong>{{CustomerName}}</strong>,</p><p>Your property tour request for <strong>\"{{PropertyTitle}}\"</strong> has been scheduled:</p><div style='background:#f8fafc; border-left:4px solid #d4af37; padding:16px; margin:20px 0; border-radius:4px;'><p style='margin:4px 0;'><strong>Property:</strong> {{PropertyTitle}}</p><p style='margin:4px 0;'><strong>Date & Time:</strong> {{VisitDate}} at {{VisitTime}}</p></div><p style='color:#718096; font-size:13px;'>Our agent will meet you at the property. Please arrive 5 minutes early.</p>")),

                ("CUST-VISIT-UPDATE", "Visit Request Status Template", "Operations", "Visit Status Updated: {{PropertyTitle}} ({{VisitStatus}})",
                 email_shell("Property Visit Update", "<p>Hello <strong>{{CustomerName}}</strong>,</p><p>The status of your visit request for <strong>\"{{PropertyTitle}}\"</strong> has been updated:</p><div style='background:#f8fafc; border-left:4px solid #d4af37; padding:16px; margin:20px 0; border-radius:4px;'><p style='margin:4px 0;'><strong>Status:</strong> <strong>{{VisitStatus}}</strong></p><p style='margin:4px 0;'><strong>Date & Time:</strong> {{VisitDate}} at {{VisitTime}}</p></div>")),

                ("VISIT-AGENT-CUST-V1", "Visit Agent Assigned (Customer) Template", "Operations", "Agent Assigned to your Viewing: {{PropertyTitle}}",
                 email_shell("Viewing Consultant Assigned", "<p>Hello <strong>{{CustomerName}}</strong>,</p><p>A dedicated LebEstates agent has been assigned to guide your property viewing:</p><div style='background:#f8fafc; border-left:4px solid #d4af37; padding:16px; margin:20px 0; border-radius:4px;'><p style='margin:4px 0;'><strong>Consultant:</strong> {{ConsultantName}}</p><p style='margin:4px 0;'><strong>Contact:</strong> {{ConsultantPhone}} &bull; {{ConsultantEmail}}</p><p style='margin:4px 0;'><strong>Viewing:</strong> {{VisitDate}} at {{VisitTime}}</p></div>")),

                ("VISIT-CONSULTANT-ASSIGNED", "Agent Assigned to Property Visit", "Operations", "Agent Assigned to Your Property Visit: {{PropertyTitle}}",
                 email_shell("Viewing Consultant Assigned", "<p>Hello <strong>{{CustomerName}}</strong>,</p><p>A dedicated agent has been assigned to host your viewing for <strong>\"{{PropertyTitle}}\"</strong>:</p><div style='background:#f8fafc; border-left:4px solid #d4af37; padding:16px; margin:20px 0; border-radius:4px;'><p style='margin:4px 0;'><strong>Agent Name:</strong> {{AgentName}}</p><p style='margin:4px 0;'><strong>Contact:</strong> {{AgentPhone}} &bull; {{AgentEmail}}</p><p style='margin:4px 0;'><strong>Schedule:</strong> {{VisitDate}} at {{VisitTime}}</p></div>")),

                ("VISIT-AGENT-EMP-V1", "Visit Viewing Assignment (Employee) Template", "Operations", "Viewing Assigned to You: {{PropertyTitle}} ({{VisitDate}})",
                 email_shell("New Viewing Assignment", "<p>Hello <strong>{{EmployeeName}}</strong>,</p><p>You have been assigned as the consultant for an upcoming property viewing:</p><div style='background:#f8fafc; border-left:4px solid #00081e; padding:16px; margin:20px 0; border-radius:4px;'><p style='margin:4px 0;'><strong>Property:</strong> {{PropertyTitle}}</p><p style='margin:4px 0;'><strong>Client:</strong> {{CustomerName}} (Phone: {{CustomerPhone}})</p><p style='margin:4px 0;'><strong>Date & Time:</strong> {{VisitDate}} at {{VisitTime}}</p><p style='margin:4px 0;'><strong>Address:</strong> {{Address}}</p></div>")),

                # 4. Visit Reminders
                ("VISIT-REMIND-24H", "Visit Reminder (24h Before) Template", "Reminders", "Reminder: Property Visit for {{PropertyTitle}} Tomorrow at {{VisitTime}}",
                 email_shell("24-Hour Visit Reminder", "<p>Hello <strong>{{RecipientName}}</strong>,</p><p>This is a reminder for your scheduled property tour tomorrow:</p><div style='background:#f8fafc; border-left:4px solid #d4af37; padding:16px; margin:20px 0; border-radius:4px;'><p style='margin:4px 0;'><strong>Property:</strong> {{PropertyTitle}}</p><p style='margin:4px 0;'><strong>Time:</strong> {{VisitDate}} at {{VisitTime}}</p><p style='margin:4px 0;'><strong>Address:</strong> {{Address}}</p><p style='margin:4px 0;'><strong>Meeting With:</strong> {{OtherPartyName}}</p></div>")),

                ("VISIT-REMINDER-24H", "Visit Reminder 24 Hours Before", "Reminders", "Reminder: Property Visit for {{PropertyTitle}} Tomorrow",
                 email_shell("24-Hour Visit Reminder", "<p>Hello <strong>{{RecipientName}}</strong>,</p><p>This is a friendly reminder of your upcoming property visit tomorrow:</p><div style='background:#f8fafc; border-left:4px solid #d4af37; padding:16px; margin:20px 0; border-radius:4px;'><p style='margin:4px 0;'><strong>Property:</strong> {{PropertyTitle}}</p><p style='margin:4px 0;'><strong>Date & Time:</strong> {{VisitDate}} at {{VisitTime}}</p></div><p style='color:#718096; font-size:13px;'>If you need to reschedule, please notify our team in advance.</p>")),

                ("VISIT-REMIND-1H", "Visit Reminder (1h Before) Template", "Reminders", "1-Hour Reminder: Visit for {{PropertyTitle}} at {{VisitTime}}",
                 email_shell("Viewing in 1 Hour", "<p>Hello <strong>{{RecipientName}}</strong>,</p><p>Your property tour begins in approximately 1 hour:</p><div style='background:#f8fafc; border-left:4px solid #00081e; padding:16px; margin:20px 0; border-radius:4px;'><p style='margin:4px 0;'><strong>Property:</strong> {{PropertyTitle}}</p><p style='margin:4px 0;'><strong>Time:</strong> Today at {{VisitTime}}</p><p style='margin:4px 0;'><strong>Address:</strong> {{Address}}</p></div>")),

                ("VISIT-REMINDER-1H", "Visit Reminder 1 Hour Before", "Reminders", "Reminder: Property Visit for {{PropertyTitle}} Starting in 1 Hour",
                 email_shell("Viewing Starting in 1 Hour", "<p>Hello <strong>{{RecipientName}}</strong>,</p><p>Your property viewing for <strong>\"{{PropertyTitle}}\"</strong> is starting in approximately 1 hour:</p><div style='background:#f8fafc; border-left:4px solid #00081e; padding:16px; margin:20px 0; border-radius:4px;'><p style='margin:4px 0;'><strong>Property:</strong> {{PropertyTitle}}</p><p style='margin:4px 0;'><strong>Time:</strong> Today at {{VisitTime}}</p></div>")),

                ("VISIT-FEEDBACK-2H", "Visit Feedback (2h Post-Visit) Template", "Reminders", "How was your visit to {{PropertyTitle}}?",
                 email_shell("We Value Your Feedback!", "<p>Hello <strong>{{CustomerName}}</strong>,</p><p>Thank you for touring <strong>\"{{PropertyTitle}}\"</strong> today. We would love to hear your feedback!</p><div style='text-align:center; margin:30px 0;'><a href='{{FeedbackUrl}}' style='background:#00081e; color:#d4af37; padding:14px 28px; text-decoration:none; border-radius:6px; font-weight:600; display:inline-block;'>Share Your Feedback</a></div>")),

                # 5. Operations: Consultations
                ("CONS-BOOKED-V1", "Consultation Booked Template", "Operations", "Consultation Confirmed: {{ConsultationType}}",
                 email_shell("Consultation Confirmed", "<p>Hello <strong>{{CustomerName}}</strong>,</p><p>Your consultation appointment has been scheduled:</p><div style='background:#f8fafc; border-left:4px solid #d4af37; padding:16px; margin:20px 0; border-radius:4px;'><p style='margin:4px 0;'><strong>Service:</strong> {{ConsultationType}}</p><p style='margin:4px 0;'><strong>Date:</strong> {{ScheduledDate}} &bull; <strong>Time:</strong> {{ScheduledTime}}</p><p style='margin:4px 0;'><strong>Preferred Method:</strong> {{PreferredMethod}}</p></div>")),

                ("CONSULT-BOOKED", "Consultation Booked Confirmation", "Operations", "Consultation Confirmed: {{ConsultationType}}",
                 email_shell("Consultation Confirmed", "<p>Hello <strong>{{CustomerName}}</strong>,</p><p>Your advisory consultation booking is confirmed:</p><div style='background:#f8fafc; border-left:4px solid #d4af37; padding:16px; margin:20px 0; border-radius:4px;'><p style='margin:4px 0;'><strong>Consultation:</strong> {{ConsultationType}}</p><p style='margin:4px 0;'><strong>Date & Time:</strong> {{ScheduledDate}} at {{ScheduledTime}}</p><p style='margin:4px 0;'><strong>Method:</strong> {{PreferredMethod}}</p></div>")),

                ("CONS-STATUS-V1", "Consultation Status Changed Template", "Operations", "Consultation Update: {{ConsultationType}} ({{Status}})",
                 email_shell("Consultation Status Update", "<p>Hello <strong>{{CustomerName}}</strong>,</p><p>The status of your consultation session for <strong>\"{{ConsultationType}}\"</strong> has changed:</p><div style='background:#f8fafc; border-left:4px solid #00081e; padding:16px; margin:20px 0; border-radius:4px;'><p style='margin:4px 0;'><strong>Status:</strong> <strong>{{Status}}</strong></p><p style='margin:4px 0;'><strong>Date & Time:</strong> {{ScheduledDate}} at {{ScheduledTime}}</p></div>")),

                ("CONSULT-STATUS-CHANGED", "Consultation Status Update", "Operations", "Consultation Status Update: {{ConsultationType}} ({{Status}})",
                 email_shell("Consultation Status Update", "<p>Hello <strong>{{CustomerName}}</strong>,</p><p>The status of your consultation session for <strong>\"{{ConsultationType}}\"</strong> has been updated:</p><div style='background:#f8fafc; border-left:4px solid #00081e; padding:16px; margin:20px 0; border-radius:4px;'><p style='margin:4px 0;'><strong>New Status:</strong> <strong>{{Status}}</strong></p><p style='margin:4px 0;'><strong>Date & Time:</strong> {{ScheduledDate}} at {{ScheduledTime}}</p></div>")),

                ("CONS-AGENT-CUST-V1", "Consultation Advisor Assigned (Customer) Template", "Operations", "Advisor Assigned for your Consultation: {{ConsultationType}}",
                 email_shell("Advisor Assigned", "<p>Hello <strong>{{CustomerName}}</strong>,</p><p>Senior advisor <strong>{{ConsultantName}}</strong> has been assigned to your session:</p><div style='background:#f8fafc; border-left:4px solid #d4af37; padding:16px; margin:20px 0; border-radius:4px;'><p style='margin:4px 0;'><strong>Topic:</strong> {{ConsultationType}}</p><p style='margin:4px 0;'><strong>Advisor:</strong> {{ConsultantName}}</p><p style='margin:4px 0;'><strong>Schedule:</strong> {{ScheduledDate}} at {{ScheduledTime}} ({{PreferredMethod}})</p></div>")),

                ("CONSULT-ASSIGNED", "Consultant Assigned to Meeting", "Operations", "Consultant Assigned: {{ConsultationType}}",
                 email_shell("Advisor Assigned", "<p>Hello <strong>{{CustomerName}}</strong>,</p><p>An advisor has been assigned to your upcoming consultation session:</p><div style='background:#f8fafc; border-left:4px solid #d4af37; padding:16px; margin:20px 0; border-radius:4px;'><p style='margin:4px 0;'><strong>Advisor:</strong> {{ConsultantName}}</p><p style='margin:4px 0;'><strong>Service:</strong> {{ConsultationType}}</p><p style='margin:4px 0;'><strong>Schedule:</strong> {{ScheduledDate}} at {{ScheduledTime}}</p></div>")),

                ("CONS-AGENT-EMP-V1", "Consultation Assigned (Employee) Template", "Operations", "Consultation Assignment: {{ConsultationType}} with {{CustomerName}}",
                 email_shell("New Consultation Meeting", "<p>Hello <strong>{{EmployeeName}}</strong>,</p><p>You have been assigned to lead an advisory consultation:</p><div style='background:#f8fafc; border-left:4px solid #00081e; padding:16px; margin:20px 0; border-radius:4px;'><p style='margin:4px 0;'><strong>Client:</strong> {{CustomerName}} ({{CustomerEmail}} &bull; {{CustomerPhone}})</p><p style='margin:4px 0;'><strong>Type:</strong> {{ConsultationType}}</p><p style='margin:4px 0;'><strong>Schedule:</strong> {{ScheduledDate}} at {{ScheduledTime}}</p></div>")),

                # 6. Consultation Reminders
                ("CONS-REMIND-1H", "Consultation Reminder (1h Before) Template", "Reminders", "1-Hour Reminder: Consultation on {{ConsultationType}} at {{ScheduledTime}}",
                 email_shell("Consultation Starting in 1 Hour", "<p>Hello <strong>{{RecipientName}}</strong>,</p><p>Your consultation session begins in approximately 1 hour:</p><div style='background:#f8fafc; border-left:4px solid #d4af37; padding:16px; margin:20px 0; border-radius:4px;'><p style='margin:4px 0;'><strong>Service:</strong> {{ConsultationType}}</p><p style='margin:4px 0;'><strong>Time:</strong> Today at {{ScheduledTime}}</p><p style='margin:4px 0;'><strong>Method:</strong> {{PreferredMethod}}</p></div>")),

                ("CONSULT-REMINDER-1H", "Consultation Reminder 1 Hour Before", "Reminders", "1-Hour Reminder: Consultation on {{ConsultationType}}",
                 email_shell("Consultation in 1 Hour", "<p>Hello <strong>{{RecipientName}}</strong>,</p><p>Your consultation on <strong>\"{{ConsultationType}}\"</strong> starts in approximately 1 hour:</p><div style='background:#f8fafc; border-left:4px solid #d4af37; padding:16px; margin:20px 0; border-radius:4px;'><p style='margin:4px 0;'><strong>Service:</strong> {{ConsultationType}}</p><p style='margin:4px 0;'><strong>Time:</strong> Today at {{ScheduledTime}}</p></div>")),

                ("CONS-SURVEY-1D", "Consultation CSAT Survey (1d Post-Meeting) Template", "Reminders", "Thank You: How was your LebEstates Consultation?",
                 email_shell("Thank You for Consulting with Us!", "<p>Hello <strong>{{CustomerName}}</strong>,</p><p>Thank you for meeting with <strong>{{ConsultantName}}</strong> yesterday regarding <em>\"{{ConsultationType}}\"</em>.</p><div style='text-align:center; margin:30px 0;'><a href='{{SurveyUrl}}' style='background:#00081e; color:#d4af37; padding:14px 28px; text-decoration:none; border-radius:6px; font-weight:600; display:inline-block;'>Take 1-Minute CSAT Survey</a></div>")),

                ("CONSULT-FOLLOWUP-1D", "Consultation Thank You & Survey 1 Day After", "Reminders", "Thank You for Your Consultation - LebEstates",
                 email_shell("Thank You for Consulting With Us!", "<p>Hello <strong>{{CustomerName}}</strong>,</p><p>Thank you for your recent consultation meeting on <em>\"{{ConsultationType}}\"</em>. We hope our advisory was valuable to your property search.</p><p style='color:#718096; font-size:13px;'>If you have any further questions, feel free to reach out to your dedicated advisor anytime.</p>")),

                # 7. Transactions & Payments
                ("TRANS-INIT-V1", "Transaction Initiated Template", "Transactions", "Deal Initiated: {{PropertyTitle}} (#TRX-{{TransactionID}})",
                 email_shell("Real Estate Transaction Initiated", "<p>Hello <strong>{{RecipientName}}</strong>,</p><p>A new real estate deal has been initiated on LebEstates (Role: <strong>{{Role}}</strong>):</p><div style='background:#f8fafc; border-left:4px solid #d4af37; padding:16px; margin:20px 0; border-radius:4px;'><p style='margin:4px 0;'><strong>Transaction:</strong> #TRX-{{TransactionID}}</p><p style='margin:4px 0;'><strong>Property:</strong> {{PropertyTitle}} ({{TransactionType}})</p><p style='margin:4px 0;'><strong>Agreed Price:</strong> {{FinalPrice}}</p><p style='margin:4px 0;'><strong>Payment Terms:</strong> {{PaymentType}} ({{PaymentMethod}})</p></div>")),

                ("TRANS-INITIATED", "Transaction Initiated Notice", "Transactions", "Transaction Initiated for {{PropertyTitle}}",
                 email_shell("Transaction Initiated", "<p>Hello,</p><p>A deal has been formally initiated for <strong>{{PropertyTitle}}</strong> on LebEstates:</p><div style='background:#f8fafc; border-left:4px solid #d4af37; padding:16px; margin:20px 0; border-radius:4px;'><p style='margin:4px 0;'><strong>Property:</strong> {{PropertyTitle}}</p><p style='margin:4px 0;'><strong>Type:</strong> {{TransactionType}}</p><p style='margin:4px 0;'><strong>Agreed Price:</strong> {{FinalPrice}}</p><p style='margin:4px 0;'><strong>Next Due Date:</strong> {{NextDueDate}}</p></div>")),

                ("TRANS-STATUS-V1", "Transaction Status Updated Template", "Transactions", "Deal Status Update: {{PropertyTitle}} (#TRX-{{TransactionID}})",
                 email_shell("Transaction Status Update", "<p>Hello <strong>{{RecipientName}}</strong>,</p><p>The status for <strong>\"{{PropertyTitle}}\"</strong> (#TRX-{{TransactionID}}) has transitioned:</p><div style='background:#f8fafc; border-left:4px solid #00081e; padding:16px; margin:20px 0; border-radius:4px;'><p style='margin:4px 0;'><strong>Status:</strong> <strong>{{NewStatus}}</strong> (was {{OldStatus}})</p><p style='margin:4px 0;'><strong>Amount Paid:</strong> {{AmountPaid}}</p><p style='margin:4px 0;'><strong>Next Due Date:</strong> {{NextDueDate}}</p></div>")),

                ("TRANS-STATUS-UPDATED", "Transaction Status Update", "Transactions", "Transaction Status Update: {{PropertyTitle}}",
                 email_shell("Transaction Status Update", "<p>Hello <strong>{{RecipientName}}</strong>,</p><p>The status of your transaction for <strong>\"{{PropertyTitle}}\"</strong> has transitioned:</p><div style='background:#f8fafc; border-left:4px solid #00081e; padding:16px; margin:20px 0; border-radius:4px;'><p style='margin:4px 0;'><strong>Payment Status:</strong> <strong>{{PaymentStatus}}</strong></p><p style='margin:4px 0;'><strong>Amount Paid:</strong> {{AmountPaid}}</p><p style='margin:4px 0;'><strong>Next Due Date:</strong> {{NextDueDate}}</p></div>")),

                ("TRANS-RECEIPT-V1", "Transaction Official Receipt PDF Template", "Transactions", "Official Receipt for Transaction #TRX-{{TransactionID}} - LebEstates",
                 email_shell("Official Payment Receipt", "<p>Hello <strong>{{CustomerName}}</strong>,</p><p>Thank you for your payment. Your official PDF receipt for <strong>{{PropertyTitle}}</strong> (#TRX-{{TransactionID}}) is attached.</p><div style='background:#f8fafc; border:1px solid #e2e8f0; padding:16px; margin:20px 0; border-radius:6px;'><p style='margin:4px 0;'><strong>Amount Paid:</strong> <strong style='color:#16a34a;'>{{AmountPaid}}</strong> of {{FinalPrice}}</p><p style='margin:4px 0;'><strong>Payment Method:</strong> {{PaymentMethod}}</p><p style='margin:4px 0;'><strong>Date:</strong> {{Date}}</p></div><p style='color:#718096; font-size:13px;'>Please find the attached PDF document for your official records.</p>")),

                ("TRANS-RECEIPT-PDF", "Transaction Payment Receipt PDF", "Transactions", "Official Payment Receipt: {{PropertyTitle}} (#{{TransactionID}})",
                 email_shell("Official Payment Receipt", "<p>Hello <strong>{{CustomerName}}</strong>,</p><p>Thank you for your payment. Please find attached your official receipt for <strong>{{PropertyTitle}}</strong>:</p><div style='background:#f8fafc; border:1px solid #e2e8f0; padding:16px; margin:20px 0; border-radius:6px;'><p style='margin:4px 0;'><strong>Transaction Ref:</strong> #{{TransactionID}}</p><p style='margin:4px 0;'><strong>Amount Paid:</strong> <strong style='color:#16a34a;'>{{AmountPaid}}</strong></p></div><p style='color:#718096; font-size:13px;'>Please find the attached PDF document for your official records.</p>")),

                # 8. Rent / Installment Payment Reminders
                ("PAY-REMIND-7D", "Payment Reminder (7 Days Before Due) Template", "Reminders", "Upcoming Payment Reminder: {{PropertyTitle}} (Due in 7 Days)",
                 email_shell("7-Day Payment Reminder", "<p>Hello <strong>{{CustomerName}}</strong>,</p><p>Your scheduled payment for <strong>\"{{PropertyTitle}}\"</strong> (#TRX-{{TransactionID}}) is due in 7 days:</p><div style='background:#f8fafc; border-left:4px solid #d4af37; padding:16px; margin:20px 0; border-radius:4px;'><p style='margin:4px 0;'><strong>Amount Due:</strong> <strong style='font-size:18px;'>{{AmountDue}}</strong></p><p style='margin:4px 0;'><strong>Due Date:</strong> {{DueDate}}</p><p style='margin:4px 0;'><strong>Method:</strong> {{PaymentMethod}}</p></div>")),

                ("PAY-REMINDER-7D", "Payment Reminder 7 Days Before", "Reminders", "Upcoming Payment Reminder (7 Days): {{PropertyTitle}}",
                 email_shell("Upcoming Payment Reminder", "<p>Hello <strong>{{CustomerName}}</strong>,</p><p>This is a reminder that an installment for <strong>\"{{PropertyTitle}}\"</strong> is due in 7 days:</p><div style='background:#f8fafc; border-left:4px solid #d4af37; padding:16px; margin:20px 0; border-radius:4px;'><p style='margin:4px 0;'><strong>Amount Due:</strong> <strong style='font-size:18px;'>{{AmountDue}}</strong></p><p style='margin:4px 0;'><strong>Due Date:</strong> {{NextDueDate}}</p></div>")),

                ("PAY-REMIND-3D", "Payment Reminder (3 Days Before Due) Template", "Reminders", "Action Required: Payment Due in 3 Days - {{PropertyTitle}}",
                 email_shell("Payment Due in 3 Days", "<p>Hello <strong>{{CustomerName}}</strong>,</p><p>Your upcoming payment for <strong>\"{{PropertyTitle}}\"</strong> (#TRX-{{TransactionID}}) is due on <strong>{{DueDate}}</strong>:</p><div style='background:#fefce8; border-left:4px solid #ca8a04; padding:16px; margin:20px 0; border-radius:4px;'><p style='margin:4px 0;'><strong>Amount Due:</strong> <strong>{{AmountDue}}</strong></p><p style='margin:4px 0;'><strong>Due Date:</strong> {{DueDate}}</p></div>")),

                ("PAY-REMINDER-3D", "Payment Reminder 3 Days Before", "Reminders", "Upcoming Payment Reminder (3 Days): {{PropertyTitle}}",
                 email_shell("Payment Due in 3 Days", "<p>Hello <strong>{{CustomerName}}</strong>,</p><p>This is a reminder that your payment for <strong>\"{{PropertyTitle}}\"</strong> is due in 3 days:</p><div style='background:#fefce8; border-left:4px solid #ca8a04; padding:16px; margin:20px 0; border-radius:4px;'><p style='margin:4px 0;'><strong>Amount Due:</strong> <strong>{{AmountDue}}</strong></p><p style='margin:4px 0;'><strong>Due Date:</strong> {{NextDueDate}}</p></div>")),

                ("PAY-OVERDUE-1D", "Payment Overdue Notice (1 Day After Due) Template", "Reminders", "Notice: Missed Payment for {{PropertyTitle}} (Due {{DueDate}})",
                 email_shell("Payment Past Due Notice", "<p>Hello <strong>{{CustomerName}}</strong>,</p><p>Our records show that your scheduled payment of <strong>{{AmountDue}}</strong> for <strong>\"{{PropertyTitle}}\"</strong> (#TRX-{{TransactionID}}) was due yesterday ({{DueDate}}) and remains unpaid.</p><div style='background:#fff7ed; border-left:4px solid #ea580c; padding:16px; margin:20px 0; border-radius:4px;'><p style='margin:4px 0; color:#9a3412;'><strong>Outstanding Amount:</strong> {{AmountDue}}</p></div><p>Please arrange payment promptly to prevent late fees.</p>")),

                ("PAY-OVERDUE-7D", "Late Payment Warning & Escalation (7 Days After Due) Template", "Reminders", "Urgent: Late Payment Escalation for {{PropertyTitle}} (7+ Days Overdue)",
                 email_shell("Overdue Payment & Late Fee Escalation", "<p>Hello <strong>{{CustomerName}}</strong>,</p><p>Your scheduled payment for <strong>\"{{PropertyTitle}}\"</strong> (#TRX-{{TransactionID}}) is now <strong>more than 7 days overdue</strong> (Due: {{DueDate}}).</p><div style='background:#fef2f2; border:1px solid #fecaca; padding:16px; margin:20px 0; border-radius:6px;'><p style='margin:4px 0; color:#991b1b;'><strong>Unpaid Balance:</strong> {{AmountDue}}</p><p style='margin:4px 0; color:#991b1b;'><strong>Notice:</strong> {{LateFeeNotice}}</p><p style='margin:4px 0; color:#991b1b;'><strong>Landlord:</strong> {{LandlordName}} &bull; <strong>Agent:</strong> {{AgentName}}</p></div><p>Please settle this balance immediately to prevent legal escalation.</p>")),

                # 9. Customer Support
                ("SUPP-CLOSED-V1", "Support Ticket Closed Template", "Support", "Support Request #{{SessionID}} has been Closed",
                 email_shell("Support Request Closed", "<p>Hello <strong>{{CustomerName}}</strong>,</p><p>Your support ticket #<strong>{{SessionID}}</strong> (<em>\"{{Subject}}\"</em>) was marked as <strong>Closed</strong> on {{ClosedDate}}.</p><div style='text-align:center; margin:30px 0;'><a href='{{FeedbackUrl}}' style='background:#00081e; color:#d4af37; padding:12px 24px; text-decoration:none; border-radius:6px; font-weight:600; display:inline-block;'>View Ticket & Leave Rating</a></div>")),

                ("SUPPORT-TICKET-CLOSED", "Support Session Closed Notice", "Support", "Support Session #{{SessionID}} Closed",
                 email_shell("Support Ticket Resolved", "<p>Hello <strong>{{CustomerName}}</strong>,</p><p>Your support inquiry #<strong>{{SessionID}}</strong> (<em>\"{{Subject}}\"</em>) has been marked as <strong>Closed</strong> (Closed at: {{ClosedAt}}).</p><p style='color:#718096; font-size:13px;'>If you require additional help, you can open a new session in your account portal.</p>"))
            ]
            for tkey, tname, tcat, tsubj, tbody in templates_to_seed:
                tpl = EmailTemplate.query.filter_by(templateKey=tkey).first()
                if not tpl:
                    db.session.add(EmailTemplate(
                        templateKey=tkey,
                        name=tname,
                        category=tcat,
                        subject=tsubj,
                        body=tbody,
                        isActive=True
                    ))
                else:
                    # Update body/subject to ensure all rich template markup is present
                    tpl.name = tname
                    tpl.category = tcat
                    tpl.subject = tsubj
                    tpl.body = tbody
            db.session.commit()
        except Exception as seed_err:
            db.session.rollback()
            app.logger.error(f"Email Hub db setup/seeding failed: {seed_err}")

    # Start Background Reminder Scheduler Thread
    def run_background_reminders():
        import time
        from app.services.reminder_service import ReminderService
        time.sleep(10) # Brief delay after startup
        while True:
            try:
                with app.app_context():
                    ReminderService.process_all_reminders(app)
            except Exception as bg_err:
                app.logger.error(f"Background reminder error: {bg_err}")
            time.sleep(300) # Run every 5 minutes

    import threading
    import os
    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        reminder_thread = threading.Thread(target=run_background_reminders, daemon=True)
        reminder_thread.start()

    return app

