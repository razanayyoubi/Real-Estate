from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from app.services.auth_service import AuthService
from app.services.expense_service import ExpenseService

expenses_bp = Blueprint('expenses', __name__, url_prefix='/control-panel/expenses')

def admin_or_employee_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee', 'accountant']:
            return redirect(url_for('auth.login_page'))
        return f(*args, **kwargs)
    return decorated

@expenses_bp.route('/')
@admin_or_employee_required
def index():
    user = AuthService.get_user_by_id(session['user_id'])
    filters = {
        'server_q': request.args.get('server_q', ''),
        'status': request.args.get('status', 'All'),
        'category': request.args.get('category', 'All')
    }
    data = ExpenseService.get_all_expenses(filters)
    return render_template(
        'expenses/index.html',
        user=user,
        expenses=data['expenses'],
        total_amount=data['total_amount'],
        paid_amount=data['paid_amount'],
        pending_amount=data['pending_amount'],
        categories=data['categories'],
        category_totals=data['category_totals'],
        filters=filters
    )

@expenses_bp.route('/add', methods=['POST'])
@admin_or_employee_required
def add_expense():
    data = request.get_json() if request.is_json else request.form
    res = ExpenseService.create_expense(data, session['user_id'])
    if res.get('success'):
        return jsonify({'success': True, 'message': res.get('message')}), 201
    else:
        return jsonify({'error': res.get('error')}), res.get('code', 400)

@expenses_bp.route('/edit/<int:expense_id>', methods=['POST'])
@admin_or_employee_required
def edit_expense(expense_id):
    data = request.get_json() if request.is_json else request.form
    res = ExpenseService.update_expense(expense_id, data, session['user_id'])
    if res.get('success'):
        return jsonify({'success': True, 'message': res.get('message')})
    else:
        return jsonify({'error': res.get('error')}), res.get('code', 400)

@expenses_bp.route('/delete/<int:expense_id>', methods=['POST'])
@admin_or_employee_required
def delete_expense(expense_id):
    res = ExpenseService.delete_expense(expense_id, session['user_id'])
    if res.get('success'):
        return jsonify({'success': True, 'message': res.get('message')})
    else:
        return jsonify({'error': res.get('error')}), res.get('code', 400)
