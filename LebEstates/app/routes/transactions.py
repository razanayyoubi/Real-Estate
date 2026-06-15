from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from app.services.auth_service import AuthService
from app.services.transaction_service import TransactionService

transactions_bp = Blueprint('transactions', __name__)

@transactions_bp.route('/control-panel/transactions')
def transactions_list():
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return redirect(url_for('auth.login_page'))
    user = AuthService.get_user_by_id(session['user_id'])
    return render_template('transactions.html', user=user)

@transactions_bp.route('/control-panel/transactions/ledger')
def transactions_ledger():
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return redirect(url_for('auth.login_page'))

    data = TransactionService.get_ledger_data()
    user = AuthService.get_user_by_id(session['user_id'])

    return render_template(
        'transactions_ledger.html',
        user=user,
        transactions=data['transactions'],
        stats=data['stats'],
        properties=data['properties'],
        customers=data['customers'],
        employees=data['employees']
    )

@transactions_bp.route('/control-panel/transactions/revenue-dashboard')
def transactions_revenue_dashboard():
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return redirect(url_for('auth.login_page'))

    data = TransactionService.get_revenue_dashboard_data()
    user = AuthService.get_user_by_id(session['user_id'])

    return render_template(
        'transactions_revenue.html',
        user=user,
        kpis=data['kpis'],
        charts=data['charts'],
        top_agents=data['top_agents'],
        insights=data['insights'],
        recent_transactions=data['recent_transactions'],
        profitability=data['profitability']
    )

@transactions_bp.route('/control-panel/transactions/revenue-dashboard/data')
def transactions_revenue_dashboard_data():
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return jsonify({'success': False, 'error': 'Unauthorized access.'}), 403

    try:
        data = TransactionService.get_revenue_dashboard_data()
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@transactions_bp.route('/control-panel/transactions/payment-tracking')
def transactions_payment_tracking():
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return redirect(url_for('auth.login_page'))

    data = TransactionService.get_payment_tracking_data()
    user = AuthService.get_user_by_id(session['user_id'])

    return render_template(
        'transactions_payments.html',
        user=user,
        kpis=data['kpis'],
        charts=data['charts'],
        critical_balances=data['critical_balances'],
        aging_report=data['aging_report'],
        ledger=data['ledger']
    )


@transactions_bp.route('/control-panel/transactions/payment-tracking/data')
def transactions_payment_tracking_data():
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return jsonify({'success': False, 'error': 'Unauthorized access.'}), 403

    try:
        data = TransactionService.get_payment_tracking_data()
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



# --- COMMISSION SETTINGS MANAGEMENT ---

@transactions_bp.route('/control-panel/commission-settings', methods=['GET'])
def commission_settings():
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return redirect(url_for('auth.login_page'))

    user = AuthService.get_user_by_id(session['user_id'])
    settings = TransactionService.get_commission_settings()

    return render_template(
        'commission_settings.html',
        user=user,
        rent_rule=settings['rent_rule'],
        buyer_rate=settings['buyer_rate'],
        seller_rate=settings['seller_rate'],
        agent_split=settings['agent_split']
    )

@transactions_bp.route('/control-panel/commission-settings/save', methods=['POST'])
def commission_settings_save():
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return jsonify({'success': False, 'error': 'Unauthorized access.'}), 403

    data = request.get_json() or {}
    res = TransactionService.save_commission_settings(session['user_id'], data)
    if res.get('success'):
        return jsonify({'success': True, 'message': res.get('message')}), 200
    else:
        return jsonify({'success': False, 'error': res.get('error')}), res.get('code', 400)

@transactions_bp.route('/control-panel/commission-settings/reset', methods=['POST'])
def commission_settings_reset():
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return jsonify({'success': False, 'error': 'Unauthorized access.'}), 403

    res = TransactionService.reset_commission_settings(session['user_id'])
    if res.get('success'):
        return jsonify({'success': True, 'message': res.get('message')}), 200
    else:
        return jsonify({'success': False, 'error': res.get('error')}), res.get('code', 500)


# --- TRANSACTION OPERATIONS ENDPOINTS ---

@transactions_bp.route('/control-panel/transactions/<int:trans_id>/update-status', methods=['POST'])
def update_transaction_status(trans_id):
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return jsonify({'success': False, 'error': 'Unauthorized access.'}), 403

    data = request.get_json() or {}
    res = TransactionService.update_status(session['user_id'], trans_id, data.get('status'))
    if res.get('success'):
        return jsonify({
            'success': True,
            'message': res.get('message'),
            'stats': res.get('stats')
        }), 200
    else:
        return jsonify({'success': False, 'error': res.get('error')}), res.get('code', 400)


@transactions_bp.route('/control-panel/transactions/<int:trans_id>/details', methods=['GET'])
def transaction_details(trans_id):
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return jsonify({'success': False, 'error': 'Unauthorized access.'}), 403

    res = TransactionService.get_details(trans_id)
    if res.get('success'):
        return jsonify({'success': True, 'details': res.get('details')}), 200
    else:
        return jsonify({'success': False, 'error': res.get('error')}), res.get('code', 404)


@transactions_bp.route('/control-panel/transactions/create', methods=['POST'])
def create_transaction():
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return redirect(url_for('auth.login_page'))

    res = TransactionService.create_transaction(session['user_id'], request.form)
    return redirect(url_for('transactions.transactions_ledger'))

@transactions_bp.route('/control-panel/transactions/<int:trans_id>/edit', methods=['POST'])
def edit_transaction_submit(trans_id):
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return redirect(url_for('auth.login_page'))

    res = TransactionService.edit_transaction(session['user_id'], trans_id, request.form)
    return redirect(url_for('transactions.transactions_ledger'))

