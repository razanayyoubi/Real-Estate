from flask import Blueprint, render_template, session, redirect, request, url_for, flash, jsonify
from functools import wraps
from app.services.customer_service import get_all_customers, update_customer, delete_customer
from app.services.auth_service import AuthService

customers_bp = Blueprint('customers', __name__, url_prefix='/customers')

def admin_or_employee_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('auth.login'))
        role = session.get('role_name', '').lower()
        if role not in ['admin', 'employee']:
            flash("You do not have permission to access this page.", "error")
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@customers_bp.route('/')
@admin_or_employee_required
def index():
    customers = get_all_customers()
    
    # Calculate some stats
    total_customers = len(customers)
    active_customers = sum(1 for c in customers if c['status'].lower() == 'active')
    disabled_customers = sum(1 for c in customers if c['status'].lower() in ['inactive', 'blacklisted'])
    
    # Calculate dynamic new customers registered in the current calendar month
    from datetime import datetime
    now = datetime.utcnow()
    new_this_month = sum(1 for c in customers if c['raw_customer'].createdAt and c['raw_customer'].createdAt.year == now.year and c['raw_customer'].createdAt.month == now.month)
    
    stats = {
        'total': total_customers,
        'active': active_customers,
        'disabled': disabled_customers,
        'new_this_month': new_this_month
    }
    
    return render_template('customers/index.html', customers=customers, stats=stats)

@customers_bp.route('/add', methods=['POST'])
@admin_or_employee_required
def add_customer_route():
    data = request.get_json() if request.is_json else request.form
    
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    address = data.get('address', '').strip()
    password = data.get('password', '')
    
    if not first_name or not last_name:
        return jsonify({'error': 'First name and Last name are required.'}), 400
    if not email:
        return jsonify({'error': 'Email address is required.'}), 400
    if not password or len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters long.'}), 400
        
    full_name = f"{first_name} {last_name}"
    
    result = AuthService.register_customer(full_name, email, phone, password, address)
    if result["success"]:
        return jsonify({'message': 'Customer registered successfully!'}), 201
    else:
        return jsonify({'error': result.get('error', 'Registration failed')}), result.get('code', 400)

@customers_bp.route('/edit/<int:customer_id>', methods=['POST'])
@admin_or_employee_required
def edit_customer_route(customer_id):
    data = request.get_json() if request.is_json else request.form
    
    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    location = data.get('location', '').strip()
    
    if not full_name:
        return jsonify({'error': 'Full Name is required.'}), 400
    if not email:
        return jsonify({'error': 'Email address is required.'}), 400
        
    update_data = {
        'full_name': full_name,
        'email': email,
        'phone': phone,
        'location': location
    }
    
    result = update_customer(customer_id, update_data)
    if result["success"]:
        return jsonify({'message': 'Customer updated successfully!'}), 200
    else:
        return jsonify({'error': result.get('error', 'Update failed')}), result.get('code', 400)

@customers_bp.route('/delete/<int:customer_id>', methods=['POST'])
@admin_or_employee_required
def delete_customer_route(customer_id):
    result = delete_customer(customer_id)
    if result["success"]:
        message = result.get('message', 'Customer deleted successfully!')
        return jsonify({'message': message, 'soft_deleted': result.get('soft_deleted', False)}), 200
    else:
        return jsonify({'error': result.get('error', 'Deletion failed')}), result.get('code', 400)
