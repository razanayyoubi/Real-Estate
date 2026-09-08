from datetime import datetime
from sqlalchemy.orm import joinedload
from app.models.base import db
from app.models.users import Users, Blacklist
from app.models.customer import Customer
from app.models.hr import Employee

def get_all_blacklist_entries(status_filter='', search_query=''):
    """Retrieve all blacklist entries with target user and admin profiles."""
    query = Blacklist.query.options(
        joinedload(Blacklist.user).joinedload(Users.role),
        joinedload(Blacklist.user).joinedload(Users.customer_profile),
        joinedload(Blacklist.admin).joinedload(Users.role),
        joinedload(Blacklist.admin).joinedload(Users.employee_profile)
    ).order_by(Blacklist.blacklistedAt.desc())

    if status_filter and status_filter != 'All':
        query = query.filter(Blacklist.status == status_filter)

    if search_query:
        query = query.outerjoin(Users, Blacklist.userID == Users.userID).filter(
            (Users.fullName.like(f"%{search_query}%")) |
            (Users.email.like(f"%{search_query}%")) |
            (Blacklist.reason.like(f"%{search_query}%"))
        )

    return query.all()

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
        db.session.flush()
        
        from app.models.users import AuditLog
        AuditLog.log_action(
            action='ADD',
            table_name='blacklist',
            record_id=entry.blacklistID,
            description=f"Blacklisted user '{user.fullName}' (ID: {user_id}). Reason: {reason}",
            user_id=blacklisted_by
        )
        
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
                
        from app.models.users import AuditLog
        AuditLog.log_action(
            action='EDIT',
            table_name='blacklist',
            record_id=blacklist_id,
            description=f"Resolved blacklist entry for user '{user.fullName if user else 'Unknown'}'"
        )
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
                    
        from app.models.users import AuditLog
        AuditLog.log_action(
            action='EDIT',
            table_name='blacklist',
            record_id=blacklist_id,
            description=f"Updated blacklist entry details for user '{user.fullName if user else 'Unknown'}' (New Status: {status or entry.status})"
        )
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
                
        from app.models.users import AuditLog
        AuditLog.log_action(
            action='DELETE',
            table_name='blacklist',
            record_id=blacklist_id,
            description=f"Deleted blacklist entry for user '{user.fullName if user else 'Unknown'}' (Reason was: {entry.reason})"
        )
        db.session.delete(entry)
        db.session.commit()
        return {"success": True}
    except Exception as e:
        db.session.rollback()
        print(f"Delete blacklist error: {e}")
        return {"success": False, "error": "An internal database error occurred.", "code": 500}

def search_users_for_blacklist(q):
    """Query users matching search query (name or email) who are not blacklisted."""
    users = Users.query.filter(
        (Users.fullName.like(f"%{q}%")) | (Users.email.like(f"%{q}%")),
        Users.status != 'Blacklisted'
    ).limit(10).all()
    
    return [{
        'userID': u.userID,
        'fullName': u.fullName,
        'email': u.email
    } for u in users]
