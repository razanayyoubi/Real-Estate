from app.models.customer import Customer
from app.models.users import Users
from app.models.base import db

def get_all_customers():
    """Retrieve all customers with their associated user data."""
    # Query all customers joining with Users to get full name, email, status, etc.
    customers = db.session.query(Customer, Users).join(Users, Customer.userID == Users.userID).all()
    
    # Format the data for the template
    result = []
    for customer, user in customers:
        result.append({
            'customer_id': f"#CUST-{customer.customerID}", # Formatting for display
            'full_name': user.fullName,
            'email': user.email,
            'phone': user.phoneNumber,
            'location': customer.address,
            'status': user.status, # e.g. Active, Inactive, Blacklisted
            'created_at': customer.createdAt.strftime("%b %d, %Y") if customer.createdAt else "N/A",
            'avatar_url': f"https://ui-avatars.com/api/?name={user.fullName.replace(' ', '+')}&background=random", # Placeholder for avatar
            'raw_customer': customer,
            'raw_user': user
        })
    return result

def get_customer_by_id(customer_id):
    """Retrieve a single customer by ID."""
    return db.session.query(Customer, Users).join(Users, Customer.userID == Users.userID).filter(Customer.customerID == customer_id).first()

def add_customer(data):
    """Placeholder for adding a customer"""
    pass

def update_customer(customer_id, data):
    """Update a customer and their associated user details."""
    try:
        customer_and_user = db.session.query(Customer, Users).join(Users, Customer.userID == Users.userID).filter(Customer.customerID == customer_id).first()
        if not customer_and_user:
            return {"success": False, "error": "Customer not found.", "code": 404}
        
        customer, user = customer_and_user
        
        full_name = data.get('full_name')
        email = data.get('email')
        phone = data.get('phone')
        location = data.get('location')
        
        if email and email != user.email:
            existing = Users.query.filter_by(email=email).first()
            if existing:
                return {"success": False, "error": "This email address is already in use.", "code": 400}
            user.email = email
            
        if full_name is not None:
            user.fullName = full_name
        if phone is not None:
            user.phoneNumber = phone
            
        if location is not None:
            customer.address = location
            
        db.session.commit()
        return {"success": True}
    except Exception as e:
        db.session.rollback()
        print(f"Update customer error: {e}")
        return {"success": False, "error": "An internal error occurred while updating the customer.", "code": 500}

def delete_customer(customer_id):
    """Delete a customer or soft-disable them if they have database relationships."""
    from app.models.operations import Visit, Consultation, Transaction
    from sqlalchemy.exc import IntegrityError
    
    try:
        customer_and_user = db.session.query(Customer, Users).join(Users, Customer.userID == Users.userID).filter(Customer.customerID == customer_id).first()
        if not customer_and_user:
            return {"success": False, "error": "Customer not found.", "code": 404}
            
        customer, user = customer_and_user
        
        # 1. Proactive check for active DB relations/actions
        has_visit = db.session.query(Visit).filter_by(customerID=customer_id).first() is not None
        has_consultation = db.session.query(Consultation).filter_by(customerID=customer_id).first() is not None
        has_transaction = db.session.query(Transaction).filter((Transaction.customerID == customer_id) | (Transaction.ownerID == customer_id)).first() is not None
        
        # Proactively check favorites/requests safely
        has_favorite = False
        has_property_request = False
        try:
            from app.models.property import Favorite, PropertyRequest
            has_favorite = db.session.query(Favorite).filter_by(customerID=customer_id).first() is not None
            has_property_request = db.session.query(PropertyRequest).filter_by(customerID=customer_id).first() is not None
        except Exception as relation_err:
            print(f"Skipping favorite/property request check: {relation_err}")
            
        has_actions = has_visit or has_consultation or has_transaction or has_favorite or has_property_request
        
        if has_actions:
            # Soft-disable the customer by setting status to Inactive
            user.status = 'Inactive'
            db.session.commit()
            return {"success": True, "message": "Customer has active database records. Account has been soft-disabled (Inactive).", "soft_deleted": True}
            
        # 2. Hard delete since no database actions were found
        try:
            # Delete related customer documents first
            from app.models.customer import CustomerDocument
            CustomerDocument.query.filter_by(customerID=customer_id).delete()
            
            db.session.delete(customer)
            db.session.delete(user)
            db.session.commit()
            return {"success": True, "message": "Customer deleted successfully.", "soft_deleted": False}
        except IntegrityError:
            # Roll back if a constraint was triggered
            db.session.rollback()
            # Retry to soft-disable instead
            customer_and_user = db.session.query(Customer, Users).join(Users, Customer.userID == Users.userID).filter(Customer.customerID == customer_id).first()
            if customer_and_user:
                customer, user = customer_and_user
                user.status = 'Inactive'
                db.session.commit()
                return {"success": True, "message": "Constraint conflict. Account soft-disabled instead.", "soft_deleted": True}
            return {"success": False, "error": "Failed to delete or disable customer.", "code": 500}
            
    except Exception as e:
        db.session.rollback()
        print(f"Delete customer error: {e}")
        return {"success": False, "error": "An internal error occurred while deleting the customer.", "code": 500}
