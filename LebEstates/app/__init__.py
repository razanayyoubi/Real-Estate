from flask import Flask
from app.models.base import db
from app.config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    # Import models to ensure they are known to SQLAlchemy
    from app.models.users import Role, Users, Blacklist, AuditLog
    from app.models.property import Property, PropertyImage, PropertyRequest, Favorite
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

    return app
