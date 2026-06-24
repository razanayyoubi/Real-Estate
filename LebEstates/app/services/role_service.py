from app.models.users import Users, Role
from app.models.hr import Employee
from app.models.base import db

def get_all_roles():
    """Retrieve all roles in the database."""
    return Role.query.all()

def get_staff_users_paginated(page=1, per_page=6):
    """Retrieve a paginated list of staff users (who are not Customers)."""
    # Resolve 'Customer' role to exclude customer accounts from staff listing
    customer_role = Role.query.filter_by(roleName='Customer').first()
    
    query = db.session.query(Users, Role).join(Role, Users.roleID == Role.roleID)
    if customer_role:
        query = query.filter(Users.roleID != customer_role.roleID)
        
    query = query.filter(Users.status == 'Active')
        
    total = query.count()
    
    # Calculate offset and limit
    offset = (page - 1) * per_page
    users_with_roles = query.offset(offset).limit(per_page).all()
    
    result = []
    for user, role in users_with_roles:
        # Check if they have a matching employee profile to pull their specific position
        employee_profile = Employee.query.filter_by(userID=user.userID).first()
        position = employee_profile.position if employee_profile else 'N/A'
        
        # Display ID Offsetting: shift by +5000 for a professional enterprise representation
        display_id = user.userID + 5000
        
        result.append({
            'user_id': user.userID,
            'display_user_id': f"#USER-{display_id}",
            'full_name': user.fullName,
            'email': user.email,
            'phone': user.phoneNumber,
            'role_id': user.roleID,
            'role_name': role.roleName,
            'position': position,
            'status': user.status,
            'avatar_url': f"https://ui-avatars.com/api/?name={user.fullName.replace(' ', '+')}&background=random"
        })
    return result, total

def change_user_role(user_id, new_role_id):
    """Change a staff member's role safely in the database, protecting customer profiles."""
    try:
        user = Users.query.get(user_id)
        if not user:
            return {"success": False, "error": "User not found.", "code": 404}
            
        new_role = Role.query.get(new_role_id)
        if not new_role:
            return {"success": False, "error": "Selected role does not exist.", "code": 404}
            
        # Security boundaries: Prevent changing to Customer role or changing Customer accounts
        customer_role = Role.query.filter_by(roleName='Customer').first()
        if customer_role:
            if user.roleID == customer_role.roleID:
                return {"success": False, "error": "Customer profiles cannot have their roles modified from this panel.", "code": 403}
            if int(new_role_id) == customer_role.roleID:
                return {"success": False, "error": "Staff members cannot be changed to the Customer role.", "code": 403}
                
        # Apply role change
        user.roleID = new_role_id
        
        from app.models.users import AuditLog
        AuditLog.log_action(
            action='EDIT',
            table_name='users',
            record_id=user_id,
            description=f"Changed user '{user.fullName}' role to '{new_role.roleName}'"
        )
        db.session.commit()
        return {"success": True}
    except Exception as e:
        db.session.rollback()
        print(f"Change user role service error: {e}")
        return {"success": False, "error": "An internal error occurred while updating the role.", "code": 500}

def get_staff_stats():
    """Calculate counts of admin/employee staff users."""
    customer_role = Role.query.filter_by(roleName='Customer').first()
    query = Users.query
    if customer_role:
        query = query.filter(Users.roleID != customer_role.roleID)
        
    total_staff = query.count()
    admin_role = Role.query.filter_by(roleName='Admin').first()
    employee_role = Role.query.filter_by(roleName='Employee').first()
    
    admins = query.filter_by(roleID=admin_role.roleID).count() if admin_role else 0
    employees = query.filter_by(roleID=employee_role.roleID).count() if employee_role else 0
    
    return {
        'total': total_staff,
        'admins': admins,
        'employees': employees
    }
