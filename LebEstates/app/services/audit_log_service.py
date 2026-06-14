import math
from app.models.base import db
from app.models.users import AuditLog, Users

def get_audit_logs_paginated_and_stats(page=1, per_page=10, action_filter='', module_filter='', search_query=''):
    """
    Retrieve audit logs paginated, filtered, and general stats.
    """
    query = AuditLog.query.outerjoin(Users, AuditLog.userID == Users.userID)

    if action_filter:
        query = query.filter(AuditLog.action == action_filter)
    if module_filter:
        query = query.filter(AuditLog.tableName == module_filter)
    if search_query:
        query = query.filter(AuditLog.description.like(f"%{search_query}%"))

    # Order by newest first
    query = query.order_by(AuditLog.createdAt.desc())

    total_records = query.count()
    total_pages = math.ceil(total_records / per_page) if total_records > 0 else 1
    page = max(1, min(page, total_pages))

    offset = (page - 1) * per_page
    logs = query.offset(offset).limit(per_page).all()

    # Stats calculations (overall stats, unfiltered)
    total_actions = AuditLog.query.count()
    add_count = AuditLog.query.filter_by(action='ADD').count()
    edit_count = AuditLog.query.filter_by(action='EDIT').count()
    delete_count = AuditLog.query.filter_by(action='DELETE').count()

    stats = {
        'total': total_actions,
        'add': add_count,
        'edit': edit_count,
        'delete': delete_count
    }

    # Extract unique table/module names for the filter dropdown
    modules = [r[0] for r in db.session.query(AuditLog.tableName).distinct().all() if r[0]]

    return {
        'logs': logs,
        'stats': stats,
        'modules': modules,
        'current_page': page,
        'total_pages': total_pages,
        'total_records': total_records
    }
