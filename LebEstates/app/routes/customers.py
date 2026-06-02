from flask import Blueprint, render_template, session, redirect, request, url_for, flash
from functools import wraps
from app.services.customer_service import get_all_customers

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
    new_this_month = 0 # Placeholder for actual calculation
    
    stats = {
        'total': total_customers,
        'active': active_customers,
        'disabled': disabled_customers,
        'new_this_month': new_this_month
    }
    
    return render_template('customers/index.html', customers=customers, stats=stats)
