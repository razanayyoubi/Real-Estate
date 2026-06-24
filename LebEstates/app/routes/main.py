from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from app.services.auth_service import AuthService
from app.services.consultation_service import request_consultation
from app.services.visit_service import VisitService

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def homepage():
    from app.services.property_service import PropertyService
    from flask import session
    
    filters = {'sort': 'newest'}
    properties, _, _ = PropertyService.browse_properties(session.get('user_id'), filters, limit=3)
    stats = PropertyService.get_homepage_stats()
    return render_template('homepage.html', properties=properties, stats=stats)


@main_bp.route('/about')
def about():
    return render_template('about.html')


@main_bp.route('/consultation', methods=['GET', 'POST'])
def consultation():
    if request.method == 'POST':
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'You must be logged in to request a consultation.'}), 401
            
        data = request.get_json() if request.is_json else request.form
        res = request_consultation(session['user_id'], data)
        return jsonify(res), res.get('code', 200)

    from app.models.property import Property
    from app.models.operations import Transaction
    from app.models.customer import Customer

    # Fetch active properties count
    properties_count = Property.query.filter_by(status='Published').count()

    # Fetch total customers count as clients served
    clients_served = Customer.query.count()

    return render_template(
        'consultation.html',
        properties_count=properties_count,
        clients_served=clients_served
    )

@main_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
    user = AuthService.get_user_by_id(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.login_page'))
        
    role_name = session.get('role_name', '').lower()
    if role_name == 'customer':
        customer_data = AuthService.get_customer_dashboard_data(session['user_id'])
        return render_template('dashboard.html', user=user, customer_data=customer_data)
        
    from app.services.dashboard_service import DashboardService
    if role_name == 'accountant':
        accountant_stats = DashboardService.get_accountant_stats()
        return render_template('dashboard.html', user=user, accountant_stats=accountant_stats)
        
    admin_stats = DashboardService.get_admin_employee_stats()
    return render_template('dashboard.html', user=user, admin_stats=admin_stats)

@main_bp.route('/control-panel')
def control_panel():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
    user = AuthService.get_user_by_id(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.login_page'))
    return render_template('control_panel.html', user=user)

@main_bp.route('/contact')
def contact():
    return render_template('contact.html')


@main_bp.route('/visit', methods=['POST'])
def schedule_visit():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'You must be logged in to schedule a visit.'}), 401
        
    data = request.get_json() if request.is_json else request.form
    res = VisitService.schedule_visit(session['user_id'], data)
    return jsonify(res), res.get('code', 200)


@main_bp.route('/api/search')
def api_search():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
        
    from app.models.property import Property
    from app.models.operations import Transaction
    from app.models.users import Users
    
    results = []
    
    # Check if user is logged in and is admin/employee/accountant
    role_name = session.get('role_name', '').lower() if session else ''
    is_admin = role_name in ['admin', 'employee', 'accountant']
    
    # 1. Search Properties
    props = Property.query.filter(
        (Property.title.like(f'%{q}%')) | 
        (Property.location.like(f'%{q}%')) | 
        (Property.propertyType.like(f'%{q}%'))
    ).limit(5).all()
    for p in props:
        results.append({
            'name': f"Property: {p.title} ({p.location})",
            'url': f"/properties?q={p.title}" if not is_admin else f"/control-panel/properties",
            'icon': 'apartment'
        })
        
    if is_admin:
        # 2. Search Users
        users = Users.query.filter(
            (Users.fullName.like(f'%{q}%')) | 
            (Users.email.like(f'%{q}%'))
        ).limit(5).all()
        for u in users:
            role_str = u.role.roleName if u.role else 'User'
            results.append({
                'name': f"User: {u.fullName} ({role_str})",
                'url': f"/customers/" if role_str.lower() == 'customer' else f"/employees/",
                'icon': 'person'
            })
            
        # 3. Search Transactions
        trans_query = Transaction.query
        try:
            val = int(q)
            trans_query = trans_query.filter((Transaction.transactionID == val) | (Transaction.transactionType.like(f'%{q}%')))
        except ValueError:
            trans_query = trans_query.filter(Transaction.transactionType.like(f'%{q}%'))
            
        transactions = trans_query.limit(5).all()
        for t in transactions:
            results.append({
                'name': f"Transaction #{t.transactionID} ({t.transactionType})",
                'url': f"/control-panel/transactions",
                'icon': 'payments'
            })
            
    return jsonify(results)


