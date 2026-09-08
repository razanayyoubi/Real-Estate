from flask import Blueprint, render_template, redirect, url_for, session, jsonify, request
from app.services.auth_service import AuthService
from app.services.commission_service import CommissionService

commissions_bp = Blueprint('commissions', __name__)

@commissions_bp.route('/control-panel/commissions')
def commissions_dashboard():
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee', 'accountant']:
        return redirect(url_for('auth.login_page'))
    
    period_type = request.args.get('period_type', 'all')
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)

    user = AuthService.get_user_by_id(session['user_id'])
    data = CommissionService.get_commissions_dashboard_data(period_type=period_type, selected_year=year, selected_month=month)

    return render_template(
        'agent_commissions.html',
        user=user,
        kpis=data['kpis'],
        top_agents=data['top_agents'],
        ledger=data['ledger'],
        expenses=data['expenses'],
        filter_meta=data['filter_meta']
    )

@commissions_bp.route('/control-panel/commissions/data')
def commissions_data():
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee', 'accountant']:
        return jsonify({'success': False, 'error': 'Unauthorized access.'}), 403

    try:
        period_type = request.args.get('period_type', 'all')
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)

        data = CommissionService.get_commissions_dashboard_data(period_type=period_type, selected_year=year, selected_month=month)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
