from app.models.base import db
from app.models.users import Users, Role
from app.models.customer import Customer
import bcrypt

class AuthService:
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
            db.session.commit()

            return {"success": True}

        except Exception as db_err:
            db.session.rollback()
            print(f"Registration database error: {db_err}")
            return {"success": False, "error": "An internal error occurred. Please try again.", "code": 500}
# login logic
    @staticmethod
    def verify_credentials(email, password):
        user = Users.query.filter_by(email=email).first()
        if not user:
            return {"success": False, "error": "Invalid email or password.", "code": 401}

        # Compare password hash
        if bcrypt.checkpw(password.encode('utf-8'), user.passwordHash.encode('utf-8')):
            return {
                "success": True,
                "user_id": user.userID,
                "role_id": user.roleID,
                "full_name": user.fullName,
                "role_name": user.role.roleName if user.role else 'Customer'
            }
        else:
            return {"success": False, "error": "Invalid email or password.", "code": 401}
