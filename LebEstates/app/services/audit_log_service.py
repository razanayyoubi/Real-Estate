import math
from app.models.base import db
from app.models.users import AuditLog, LoginLog, Users

def get_audit_logs_paginated_and_stats(page=1, per_page=10, action_filter='', module_filter='', search_query=''):
    """
    Retrieve audit logs paginated, filtered, and general stats including login events.
    """
    # 1. Fetch AuditLog entries
    query_audit = AuditLog.query.outerjoin(Users, AuditLog.userID == Users.userID)

    if action_filter and action_filter != 'LOGIN':
        query_audit = query_audit.filter(AuditLog.action == action_filter)
    elif action_filter == 'LOGIN':
        query_audit = query_audit.filter(AuditLog.action == 'LOGIN')
        
    if module_filter:
        query_audit = query_audit.filter(AuditLog.tableName == module_filter)
    if search_query:
        query_audit = query_audit.filter(AuditLog.description.like(f"%{search_query}%"))

    audit_logs = query_audit.all()

    # 2. Fetch LoginLog entries if action filter allows LOGIN
    login_logs = []
    if (not action_filter or action_filter == 'LOGIN') and (not module_filter or module_filter.lower() in ['auth', 'users']):
        login_query = LoginLog.query.outerjoin(Users, LoginLog.userID == Users.userID)
        if search_query:
            login_query = login_query.filter(
                (Users.fullName.like(f"%{search_query}%")) | 
                (Users.email.like(f"%{search_query}%")) |
                (LoginLog.ipAddress.like(f"%{search_query}%"))
            )
        login_logs = login_query.all()

    # Unify into single list
    combined = list(audit_logs)
    for llog in login_logs:
        class MockAuditLog:
            pass
        item = MockAuditLog()
        item.logID = f"L-{llog.logID}"
        item.userID = llog.userID
        item.user = llog.user
        item.action = 'LOGIN'
        item.tableName = 'auth'
        item.recordID = llog.logID
        item.description = f"User authentication attempt ({llog.status or 'Success'}) from IP {llog.ipAddress or 'Unknown'}"
        item.createdAt = llog.loginAt
        combined.append(item)

    # Sort descending by createdAt
    combined.sort(key=lambda x: x.createdAt if x.createdAt else 0, reverse=True)

    total_records = len(combined)
    total_pages = math.ceil(total_records / per_page) if total_records > 0 else 1
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total_records)
    paginated_logs = combined[start_idx:end_idx]

    # Stats
    total_actions = AuditLog.query.count() + LoginLog.query.count()
    add_count = AuditLog.query.filter_by(action='ADD').count()
    edit_count = AuditLog.query.filter_by(action='EDIT').count()
    delete_count = AuditLog.query.filter_by(action='DELETE').count()
    login_count = LoginLog.query.count()

    stats = {
        'total': total_actions,
        'add': add_count,
        'edit': edit_count,
        'delete': delete_count,
        'login': login_count
    }

    modules = [r[0] for r in db.session.query(AuditLog.tableName).distinct().all() if r[0]]
    if 'auth' not in modules:
        modules.append('auth')

    return {
        'logs': paginated_logs,
        'stats': stats,
        'modules': modules,
        'current_page': page,
        'total_pages': total_pages,
        'total_records': total_records
    }
