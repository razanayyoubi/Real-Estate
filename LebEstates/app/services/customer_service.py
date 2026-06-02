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
            'customer_id': f"#LBE-{customer.customerID + 8000}", # Formatting for display
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
    """Placeholder for updating customer data"""
    pass

def delete_customer(customer_id):
    """Placeholder for deleting a customer"""
    pass
