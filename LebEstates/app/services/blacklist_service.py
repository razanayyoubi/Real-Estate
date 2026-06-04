from app.models.users import Users, Blacklist
from app.models.customer import Customer
from app.models.hr import Employee
from app.models.base import db
from datetime import datetime
from sqlalchemy.orm import aliased

def get_all_blacklist_entries():
    """Retrieve all blacklist entries with target user and admin profiles."""
    TargetUser = aliased(Users)
    AdminUser = aliased(Users)

    entries = (
        db.session.query(Blacklist, TargetUser, AdminUser, Customer, Employee)
        .join(TargetUser, Blacklist.userID == TargetUser.userID)
        .join(AdminUser, Blacklist.blacklistedBy == AdminUser.userID)
        .outerjoin(Customer, TargetUser.userID == Customer.userID)
        .outerjoin(Employee, AdminUser.userID == Employee.userID)
        .order_by(Blacklist.blacklistedAt.desc())
        .all()
    )

    result = []
    for entry, target, admin_u, customer, employee in entries:
        result.append({
            'blacklist_id': f"#BL-{entry.blacklistID}",
            'raw_id': entry.blacklistID,
            'reason': entry.reason,
            'status': entry.status or 'Active',
            'restricted_at_date': entry.blacklistedAt.strftime("%b %d, %Y") if entry.blacklistedAt else "N/A",
            'restricted_at_time': entry.blacklistedAt.strftime("%I:%M %p") if entry.blacklistedAt else "N/A",
            
            # Target User Details
            'user': {
                'user_id': target.userID,
                'full_name': target.fullName,
                'email': target.email,
                'phone': target.phoneNumber or 'N/A',
                'national_id': customer.nationalID if customer else 'N/A',
                'address': customer.address if customer else 'N/A',
                'status': target.status or 'Active',
                'avatar_url': f"https://ui-avatars.com/api/?name={target.fullName.replace(' ', '+')}&background=random"
            },
            
            # Admin who blacklisted
            'admin': {
                'user_id': admin_u.userID,
                'full_name': admin_u.fullName,
                'email': admin_u.email,
                'phone': admin_u.phoneNumber or 'N/A',
                'hire_date': employee.hireDate.strftime("%b %d, %Y") if (employee and employee.hireDate) else 'N/A',
                'position': employee.position if employee else 'Administrator',
                'status': employee.status if employee else 'Active'
            }
        })
    return result

def get_blacklist_stats():
    """Calculate and return blacklist statistics."""
    now = datetime.utcnow()
    start_of_month = datetime(now.year, now.month, 1)

    total_blacklisted = db.session.query(Blacklist).count()
    active_blocks = db.session.query(Blacklist).filter_by(status='Active').count()
    resolved_cases = db.session.query(Blacklist).filter_by(status='Resolved').count()
    monthly_restrictions = db.session.query(Blacklist).filter(Blacklist.blacklistedAt >= start_of_month).count()

    return {
        'total': total_blacklisted,
        'active': active_blocks,
        'resolved': resolved_cases,
        'monthly': monthly_restrictions
    }

def blacklist_user(user_id, reason, blacklisted_by):
    """Blacklist a user and update their status."""
    try:
        user = Users.query.get(user_id)
        if not user:
            return {"success": False, "error": f"User with ID {user_id} not found.", "code": 404}
        
        # Check if already blacklisted actively
        existing = Blacklist.query.filter_by(userID=user_id, status='Active').first()
        if existing:
            return {"success": False, "error": "This user is already actively blacklisted.", "code": 400}
        
        # Create blacklist entry
        entry = Blacklist(
            userID=user_id,
            reason=reason,
            blacklistedBy=blacklisted_by,
            blacklistedAt=datetime.utcnow(),
            status='Active'
        )
        db.session.add(entry)
        
        # Update user status
        user.status = 'Blacklisted'
        
        db.session.commit()
        return {"success": True, "blacklist_id": entry.blacklistID}
    except Exception as e:
        db.session.rollback()
        print(f"Blacklist user error: {e}")
        return {"success": False, "error": "An internal database error occurred.", "code": 500}

def resolve_blacklist_entry(blacklist_id):
    """Mark a blacklist entry as resolved and restore user status."""
    try:
        entry = Blacklist.query.get(blacklist_id)
        if not entry:
            return {"success": False, "error": "Blacklist record not found.", "code": 404}
        
        entry.status = 'Resolved'
        
        # Revert user status
        user = Users.query.get(entry.userID)
        if user:
            # Revert only if no other active blacklist exists
            other_active = Blacklist.query.filter(
                Blacklist.userID == user.userID,
                Blacklist.blacklistID != blacklist_id,
                Blacklist.status == 'Active'
            ).first()
            if not other_active:
                user.status = 'Active'
                
        db.session.commit()
        return {"success": True}
    except Exception as e:
        db.session.rollback()
        print(f"Resolve blacklist error: {e}")
        return {"success": False, "error": "An internal database error occurred.", "code": 500}

def update_blacklist_reason(blacklist_id, reason, status):
    """Update reason and status of a blacklist entry."""
    try:
        entry = Blacklist.query.get(blacklist_id)
        if not entry:
            return {"success": False, "error": "Blacklist record not found.", "code": 404}
        
        entry.reason = reason
        
        # If status changed
        if status and status != entry.status:
            entry.status = status
            user = Users.query.get(entry.userID)
            if user:
                if status == 'Resolved':
                    other_active = Blacklist.query.filter(
                        Blacklist.userID == user.userID,
                        Blacklist.blacklistID != blacklist_id,
                        Blacklist.status == 'Active'
                    ).first()
                    if not other_active:
                        user.status = 'Active'
                elif status == 'Active':
                    user.status = 'Blacklisted'
                    
        db.session.commit()
        return {"success": True}
    except Exception as e:
        db.session.rollback()
        print(f"Update blacklist error: {e}")
        return {"success": False, "error": "An internal database error occurred.", "code": 500}

def delete_blacklist_entry(blacklist_id):
    """Delete a blacklist entry and restore user status if needed."""
    try:
        entry = Blacklist.query.get(blacklist_id)
        if not entry:
            return {"success": False, "error": "Blacklist record not found.", "code": 404}
        
        user = Users.query.get(entry.userID)
        if user and entry.status == 'Active':
            # Check if there are other active restrictions before restoring
            other_active = Blacklist.query.filter(
                Blacklist.userID == user.userID,
                Blacklist.blacklistID != blacklist_id,
                Blacklist.status == 'Active'
            ).first()
            if not other_active:
                user.status = 'Active'
                
        db.session.delete(entry)
        db.session.commit()
        return {"success": True}
    except Exception as e:
        db.session.rollback()
        print(f"Delete blacklist error: {e}")
        return {"success": False, "error": "An internal database error occurred.", "code": 500}
