from flask import Blueprint, render_template, session, redirect, request, url_for, flash, jsonify
from functools import wraps
from app.services.role_service import get_all_roles, get_staff_users_paginated, change_user_role, get_staff_stats

roles_bp = Blueprint('roles', __name__, url_prefix='/roles')

def admin_required(f):
    """Enforce that only administrators can access this route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('auth.login'))
        role = session.get('role_name', '').lower()
        if role != 'admin':
            flash("Access denied. Only administrators are allowed to manage system roles.", "error")
            return redirect(url_for('main.homepage'))
        return f(*args, **kwargs)
    return decorated_function

@roles_bp.route('/')
@admin_required
def index():
    import math
    from app.services.role_service import get_staff_users_paginated
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 6, type=int)
    
    staff_users, total = get_staff_users_paginated(page, per_page)
    roles = get_all_roles()
    
    # Exclude customer role from the dropdown selector options in the template
    filtered_roles = [r for r in roles if r.roleName.lower() != 'customer']
    
    stats = get_staff_stats()
    
    total_pages = math.ceil(total / per_page) if total > 0 else 1
    
    return render_template(
        'roles/index.html', 
        staff_users=staff_users, 
        roles=filtered_roles, 
        stats=stats,
        current_page=page,
        total_pages=total_pages,
        per_page=per_page
    )

@roles_bp.route('/change/<int:user_id>', methods=['POST'])
@admin_required
def change_role_route(user_id):
    data = request.get_json() if request.is_json else request.form
    new_role_id = data.get('role_id')
    
    if not new_role_id:
        return jsonify({'error': 'Role ID is required.'}), 400
        
    try:
        role_id_val = int(new_role_id)
    except ValueError:
        return jsonify({'error': 'Invalid Role ID value.'}), 400
        
    result = change_user_role(user_id, role_id_val)
    if result["success"]:
        return jsonify({'message': 'User role updated successfully!'}), 200
    else:
        return jsonify({'error': result.get('error', 'Failed to update role.')}), result.get('code', 400)

