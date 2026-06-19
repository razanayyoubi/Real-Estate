from flask import Blueprint, render_template, session, redirect, request, url_for, flash, jsonify
from functools import wraps
from app.services.employee_service import get_all_employees, add_employee, update_employee, delete_employee, get_employee_stats

employees_bp = Blueprint('employees', __name__, url_prefix='/employees')

def admin_or_employee_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('auth.login'))
        role = session.get('role_name', '').lower()
        if role not in ['admin', 'employee', 'accountant']:
            flash("You do not have permission to access this page.", "error")
            return redirect(url_for('main.homepage'))
        return f(*args, **kwargs)
    return decorated_function

@employees_bp.route('/')
@admin_or_employee_required
def index():
    employees = get_all_employees()
    stats = get_employee_stats(employees)
    return render_template('employees/index.html', employees=employees, stats=stats)

@employees_bp.route('/add', methods=['POST'])
@admin_or_employee_required
def add_employee_route():
    data = request.get_json() if request.is_json else request.form
    
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    position = data.get('position', '').strip()
    base_salary = data.get('base_salary')
    password = data.get('password', '')
    
    if not first_name or not last_name:
        return jsonify({'error': 'First name and Last name are required.'}), 400
    if not email:
        return jsonify({'error': 'Email address is required.'}), 400
    if not password or len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters long.'}), 400
        
    try:
        sal_val = float(base_salary) if base_salary else 0.0
    except ValueError:
        return jsonify({'error': 'Invalid base salary value.'}), 400
        
    full_name = f"{first_name} {last_name}"
    
    service_data = {
        'email': email,
        'full_name': full_name,
        'phone': phone,
        'password': password,
        'position': position if position else 'Agent',
        'base_salary': sal_val
    }
    
    result = add_employee(service_data)
    if result["success"]:
        return jsonify({'message': 'Employee registered successfully!'}), 201
    else:
        return jsonify({'error': result.get('error', 'Registration failed')}), result.get('code', 400)

@employees_bp.route('/edit/<int:employee_id>', methods=['POST'])
@admin_or_employee_required
def edit_employee_route(employee_id):
    data = request.get_json() if request.is_json else request.form
    
    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    position = data.get('position', '').strip()
    status = data.get('status', '').strip()
    base_salary = data.get('base_salary')
    
    if not full_name:
        return jsonify({'error': 'Full Name is required.'}), 400
    if not email:
        return jsonify({'error': 'Email address is required.'}), 400
        
    try:
        sal_val = float(base_salary) if base_salary else 0.0
    except ValueError:
        return jsonify({'error': 'Invalid base salary value.'}), 400
        
    update_data = {
        'full_name': full_name,
        'email': email,
        'phone': phone,
        'position': position,
        'status': status if status else 'Active',
        'base_salary': sal_val
    }
    
    result = update_employee(employee_id, update_data)
    if result["success"]:
        return jsonify({'message': 'Employee updated successfully!'}), 200
    else:
        return jsonify({'error': result.get('error', 'Update failed')}), result.get('code', 400)

@employees_bp.route('/delete/<int:employee_id>', methods=['POST'])
@admin_or_employee_required
def delete_employee_route(employee_id):
    result = delete_employee(employee_id)
    if result["success"]:
        message = result.get('message', 'Employee deleted successfully!')
        return jsonify({'message': message, 'soft_deleted': result.get('soft_deleted', False)}), 200
    else:
        return jsonify({'error': result.get('error', 'Deletion failed')}), result.get('code', 400)

