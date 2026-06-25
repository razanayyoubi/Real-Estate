from flask import Blueprint, render_template, session, redirect, request, url_for, flash, jsonify
from functools import wraps
import math
from app.services.blacklist_service import (
    get_all_blacklist_entries,
    get_blacklist_stats,
    blacklist_user,
    resolve_blacklist_entry,
    update_blacklist_reason,
    delete_blacklist_entry,
    search_users_for_blacklist
)

blacklist_bp = Blueprint('blacklist', __name__, url_prefix='/blacklist')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('auth.login_page'))
        role = session.get('role_name', '').lower()
        if role != 'admin':
            flash("You do not have permission to access this page.", "error")
            return redirect(url_for('main.homepage'))
        return f(*args, **kwargs)
    return decorated_function

@blacklist_bp.route('/')
@admin_required
def index():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Retrieve all entries and stats
    all_entries = get_all_blacklist_entries()
    stats = get_blacklist_stats()
    
    total = len(all_entries)
    total_pages = math.ceil(total / per_page) if total > 0 else 1
    
    # Slice the results for pagination
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_entries = all_entries[start_idx:end_idx]
    
    return render_template(
        'blacklist/index.html',
        entries=paginated_entries,
        stats=stats,
        current_page=page,
        total_pages=total_pages,
        per_page=per_page,
        total_records=total
    )

@blacklist_bp.route('/search-users')
@admin_required
def search_users():
    q = request.args.get('q', '').strip()
    if not q or len(q) < 2:
        return jsonify([])
        
    result = search_users_for_blacklist(q)
    return jsonify(result)

@blacklist_bp.route('/add', methods=['POST'])
@admin_required
def add_blacklist_route():
    data = request.get_json() if request.is_json else request.form
    
    user_id = data.get('user_id')
    reason = data.get('reason', '').strip()
    level = data.get('level', 'Permanent Ban').strip()
    
    if not user_id:
        return jsonify({'error': 'Please select a user to blacklist.'}), 400
    if not reason:
        return jsonify({'error': 'Reason for restriction is required.'}), 400
        
    try:
        user_id_val = int(user_id)
    except ValueError:
        return jsonify({'error': 'Invalid User ID.'}), 400
        
    # Check if target is trying to blacklist themselves
    if user_id_val == session.get('user_id'):
        return jsonify({'error': 'You cannot blacklist yourself.'}), 400
        
    # Append the restriction level as a prefix to save in the reason column
    full_reason = f"[{level}] {reason}"
    
    result = blacklist_user(user_id_val, full_reason, session['user_id'])
    if result["success"]:
        return jsonify({'message': 'User has been blacklisted successfully!'}), 201
    else:
        return jsonify({'error': result.get('error', 'Operation failed')}), result.get('code', 400)

@blacklist_bp.route('/edit/<int:blacklist_id>', methods=['POST'])
@admin_required
def edit_blacklist_route(blacklist_id):
    data = request.get_json() if request.is_json else request.form
    
    reason = data.get('reason', '').strip()
    status = data.get('status', '').strip()
    
    if not reason:
        return jsonify({'error': 'Reason for restriction is required.'}), 400
    if not status:
        return jsonify({'error': 'Status is required.'}), 400
        
    result = update_blacklist_reason(blacklist_id, reason, status)
    if result["success"]:
        return jsonify({'message': 'Blacklist record updated successfully!'}), 200
    else:
        return jsonify({'error': result.get('error', 'Update failed')}), result.get('code', 400)

@blacklist_bp.route('/resolve/<int:blacklist_id>', methods=['POST'])
@admin_required
def resolve_blacklist_route(blacklist_id):
    result = resolve_blacklist_entry(blacklist_id)
    if result["success"]:
        return jsonify({'message': 'Restriction resolved and user restored successfully!'}), 200
    else:
        return jsonify({'error': result.get('error', 'Operation failed')}), result.get('code', 400)

@blacklist_bp.route('/delete/<int:blacklist_id>', methods=['POST'])
@admin_required
def delete_blacklist_route(blacklist_id):
    result = delete_blacklist_entry(blacklist_id)
    if result["success"]:
        return jsonify({'message': 'Blacklist record deleted successfully!'}), 200
    else:
        return jsonify({'error': result.get('error', 'Deletion failed')}), result.get('code', 400)

