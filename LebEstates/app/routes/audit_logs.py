from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from functools import wraps
from app.services.audit_log_service import get_audit_logs_paginated_and_stats

audit_logs_bp = Blueprint('audit_logs', __name__, url_prefix='/control-panel/audit-logs')

def admin_or_employee_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('auth.login_page'))
        role = session.get('role_name', '').lower()
        if role not in ['admin', 'employee']:
            flash("You do not have permission to access this page.", "error")
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@audit_logs_bp.route('/')
@admin_or_employee_required
def index():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Filters
    action_filter = request.args.get('action', '').strip()
    module_filter = request.args.get('module', '').strip()
    search_query = request.args.get('q', '').strip()

    data = get_audit_logs_paginated_and_stats(
        page=page,
        per_page=per_page,
        action_filter=action_filter,
        module_filter=module_filter,
        search_query=search_query
    )

    return render_template(
        'audit_logs/index.html',
        logs=data['logs'],
        stats=data['stats'],
        modules=data['modules'],
        current_page=data['current_page'],
        total_pages=data['total_pages'],
        per_page=per_page,
        total_records=data['total_records'],
        action_filter=action_filter,
        module_filter=module_filter,
        search_query=search_query
    )

