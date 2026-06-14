from flask import Flask
from app.models.base import db
from app.config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    # Import models to ensure they are known to SQLAlchemy
    from app.models.users import Role, Users, Blacklist, AuditLog, UserSession, LoginLog
    from app.models.property import Property, PropertyImage, Favorite
    from app.models.hr import Employee, Salary, CommissionSetting
    from app.models.customer import Customer, CustomerDocument
    from app.models.operations import Visit, Consultation, Transaction

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

    from app.routes.transactions import transactions_bp
    app.register_blueprint(transactions_bp)

    from app.routes.audit_logs import audit_logs_bp
    app.register_blueprint(audit_logs_bp)

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

    return app
