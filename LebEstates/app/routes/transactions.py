from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from app.services.auth_service import AuthService
from app.services.transaction_service import TransactionService

transactions_bp = Blueprint('transactions', __name__)

@transactions_bp.route('/control-panel/transactions')
def transactions_list():
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee', 'accountant']:
        return redirect(url_for('auth.login_page'))
    user = AuthService.get_user_by_id(session['user_id'])
    return render_template('transactions.html', user=user)

@transactions_bp.route('/control-panel/transactions/<int:trans_id>/receipt')
def transaction_receipt(trans_id):
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee', 'accountant']:
        return redirect(url_for('auth.login_page'))

    from app.models.operations import Transaction
    transaction = Transaction.query.get_or_404(trans_id)
    return render_template('transaction_receipt.html', transaction=transaction)

@transactions_bp.route('/control-panel/transactions/ledger')
def transactions_ledger():
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee', 'accountant']:
        return redirect(url_for('auth.login_page'))

    filters = {
        'server_q': request.args.get('server_q', ''),
        'type': request.args.get('type', 'All'),
        'status': request.args.get('status', 'All'),
        'customer_id': request.args.get('customer_id', 'All'),
        'property_id': request.args.get('property_id', 'All')
    }

    data = TransactionService.get_ledger_data(filters)
    user = AuthService.get_user_by_id(session['user_id'])
    
    from app.models.hr import Employee
    user_employee = Employee.query.filter_by(userID=session['user_id']).first()
    if not user_employee:
        from datetime import date
        from app.models.base import db
        user_employee = Employee(userID=session['user_id'], position='Agent', hireDate=date.today())
        db.session.add(user_employee)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            user_employee = Employee.query.filter_by(userID=session['user_id']).first()

    return render_template(
        'transactions_ledger.html',
        user=user,
        user_employee=user_employee,
        transactions=data['transactions'],
        total_count=data['total_count'],
        stats=data['stats'],
        properties=data['properties'],
        customers=data['customers'],
        employees=data['employees'],
        filters=filters
    )

@transactions_bp.route('/control-panel/transactions/ledger/data')
def transactions_ledger_data():
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee', 'accountant']:
        return jsonify({'success': False, 'error': 'Unauthorized access.'}), 403

    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        offset = request.args.get('offset')
        if offset is not None:
            offset = int(offset)

        filters = {
            'server_q': request.args.get('server_q', ''),
            'type': request.args.get('type', 'All'),
            'status': request.args.get('status', 'All'),
            'customer_id': request.args.get('customer_id', 'All'),
            'property_id': request.args.get('property_id', 'All')
        }

        data = TransactionService.get_ledger_data(filters, page=page, per_page=per_page, offset=offset)

        serialized = []
        for t in data['transactions']:
            main_image = None
            if t.property_obj and t.property_obj.images:
                for img in t.property_obj.images:
                    if getattr(img, 'isMainImage', False):
                        main_image = img.imageURL
                        break
                if not main_image and len(t.property_obj.images) > 0:
                    main_image = t.property_obj.images[0].imageURL
            if not main_image:
                main_image = "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=800&q=80"

            status_display = 'Pending' if t.paymentStatus == 'Escrow' else 'In progress' if t.paymentStatus == 'Legal' else 'Completed' if t.paymentStatus == 'Closed' else 'Cancelled'

            serialized.append({
                'transactionID': t.transactionID,
                'transactionType': t.transactionType,
                'paymentStatus': t.paymentStatus,
                'statusDisplay': status_display,
                'date': t.transactionDate.strftime('%Y-%m-%d') if t.transactionDate else '',
                'finalPrice': float(t.finalPrice or 0.0),
                'commissionAmount': float(t.commissionAmount or 0.0),
                'commissionRate': float(t.commissionRate or 0.0),
                'paymentMethod': t.paymentMethod or 'Bank Wire / Escrow',
                'property': {
                    'id': t.propertyID,
                    'title': t.property_obj.title if t.property_obj else 'Unknown Property',
                    'location': t.property_obj.location if t.property_obj else 'Lebanon',
                    'image': main_image
                },
                'customer': {
                    'id': t.customerID,
                    'name': t.customer.user.fullName if (t.customer and t.customer.user) else 'Unknown Client'
                },
                'employee': {
                    'id': t.employeeID,
                    'name': t.employee.user.fullName if (t.employee and t.employee.user) else 'Unassigned'
                }
            })

        return jsonify({
            'success': True,
            'transactions': serialized,
            'total_count': data['total_count'],
            'page': page,
            'per_page': per_page,
            'stats': data['stats']
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@transactions_bp.route('/control-panel/transactions/api/search-properties')
def api_search_properties():
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee', 'accountant']:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    q = request.args.get('q', '').strip()
    from app.models.property import Property
    query = Property.query
    if q:
        if q.isdigit():
            query = query.filter((Property.propertyID == int(q)) | Property.title.ilike(f'%{q}%') | Property.location.ilike(f'%{q}%'))
        else:
            query = query.filter(Property.title.ilike(f'%{q}%') | Property.location.ilike(f'%{q}%'))

    properties = query.limit(20).all()
    results = []
    for p in properties:
        results.append({
            'id': p.propertyID,
            'title': p.title or '',
            'price': float(p.price or 0.0),
            'listingType': p.listingType or 'Sell',
            'location': p.location or ''
        })

    return jsonify({'success': True, 'properties': results})

@transactions_bp.route('/control-panel/transactions/api/search-customers')
def api_search_customers():
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee', 'accountant']:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    q = request.args.get('q', '').strip()
    from app.models.stakeholders import Customer
    from app.models.users import Users
    query = Customer.query.join(Users, Customer.userID == Users.userID)
    if q:
        if q.isdigit():
            query = query.filter((Customer.customerID == int(q)) | Users.fullName.ilike(f'%{q}%') | Users.email.ilike(f'%{q}%') | Users.phoneNumber.ilike(f'%{q}%'))
        else:
            query = query.filter(Users.fullName.ilike(f'%{q}%') | Users.email.ilike(f'%{q}%') | Users.phoneNumber.ilike(f'%{q}%'))

    customers = query.limit(20).all()
    results = []
    for c in customers:
        results.append({
            'id': c.customerID,
            'name': c.user.fullName if (c.user and c.user.fullName) else f'Client #{c.customerID}',
            'email': c.user.email if (c.user and c.user.email) else '',
            'phone': c.user.phoneNumber if (c.user and c.user.phoneNumber) else '',
            'username': (c.user.email.split('@')[0]) if (c.user and c.user.email) else ''
        })

    return jsonify({'success': True, 'customers': results})

@transactions_bp.route('/control-panel/transactions/report/generate')
def transactions_report_generate():
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee', 'accountant']:
        return redirect(url_for('auth.login_page'))

    cust_ids = request.args.getlist('customer_ids') or request.args.get('customer_ids') or request.args.get('customer_id') or 'All'
    filters = {
        'from_date': request.args.get('from_date', ''),
        'to_date': request.args.get('to_date', ''),
        'type': request.args.get('type', 'All'),
        'status': request.args.get('status', 'All'),
        'customer_ids': cust_ids,
        'property_id': request.args.get('property_id', 'All')
    }

    report_data = TransactionService.generate_custom_report_data(filters)
    user = AuthService.get_user_by_id(session['user_id'])

    return render_template(
        'transactions_report_print.html',
        user=user,
        report=report_data,
        now=datetime.now()
    )

@transactions_bp.route('/control-panel/transactions/revenue-dashboard')
def transactions_revenue_dashboard():
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee', 'accountant']:
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
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee', 'accountant']:
        return jsonify({'success': False, 'error': 'Unauthorized access.'}), 403

    try:
        data = TransactionService.get_revenue_dashboard_data()
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@transactions_bp.route('/control-panel/transactions/payment-tracking')
def transactions_payment_tracking():
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee', 'accountant']:
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
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee', 'accountant']:
        return jsonify({'success': False, 'error': 'Unauthorized access.'}), 403

    try:
        data = TransactionService.get_payment_tracking_data()
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@transactions_bp.route('/control-panel/transactions/<int:trans_id>/record-payment', methods=['POST'])
def record_transaction_payment(trans_id):
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee', 'accountant']:
        return jsonify({'success': False, 'error': 'Unauthorized access.'}), 403

    from app.models.base import db
    from app.models.operations import Transaction
    from app.models.users import AuditLog
    from datetime import datetime

    data = request.get_json() or {}
    amount_str = data.get('amount')
    due_date_str = data.get('next_due_date')

    if not amount_str:
        return jsonify({'success': False, 'error': 'Payment amount is required.'}), 400

    try:
        amount = float(amount_str)
        if amount <= 0:
            return jsonify({'success': False, 'error': 'Payment amount must be greater than zero.'}), 400
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid payment amount.'}), 400

    try:
        transaction = Transaction.query.get(trans_id)
        if not transaction:
            return jsonify({'success': False, 'error': 'Transaction not found.'}), 404

        old_paid = float(transaction.amountPaid or 0.0)
        new_paid = old_paid + amount
        final_price = float(transaction.finalPrice)

        if new_paid > final_price:
            return jsonify({'success': False, 'error': f'Payment exceeds final contract price. Maximum remaining: ${final_price - old_paid:,.2f}'}), 400

        transaction.amountPaid = new_paid

        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                transaction.nextDueDate = due_date
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid due date format. Expected YYYY-MM-DD.'}), 400
        else:
            transaction.nextDueDate = None

        # Update status dynamically
        if new_paid >= final_price:
            transaction.paymentStatus = 'Closed'
            transaction.nextDueDate = None
        else:
            today = datetime.now().date()
            if transaction.nextDueDate and transaction.nextDueDate < today:
                transaction.paymentStatus = 'Legal'
            else:
                transaction.paymentStatus = 'Escrow'

        AuditLog.log_action(
            action='UPDATE',
            table_name='transaction',
            record_id=trans_id,
            description=f"Recorded payment of ${amount:,.2f} for Transaction #{trans_id}. Total Paid: ${new_paid:,.2f}.",
            user_id=session['user_id']
        )

        db.session.commit()
        return jsonify({'success': True, 'message': 'Payment recorded successfully!'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Database error: {str(e)}'}), 500




# --- COMMISSION SETTINGS MANAGEMENT ---

@transactions_bp.route('/control-panel/commission-settings', methods=['GET'])
def commission_settings():
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee', 'accountant']:
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
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee', 'accountant']:
        return jsonify({'success': False, 'error': 'Unauthorized access.'}), 403

    data = request.get_json() or {}
    res = TransactionService.save_commission_settings(session['user_id'], data)
    if res.get('success'):
        return jsonify({'success': True, 'message': res.get('message')}), 200
    else:
        return jsonify({'success': False, 'error': res.get('error')}), res.get('code', 400)

@transactions_bp.route('/control-panel/commission-settings/reset', methods=['POST'])
def commission_settings_reset():
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee', 'accountant']:
        return jsonify({'success': False, 'error': 'Unauthorized access.'}), 403

    res = TransactionService.reset_commission_settings(session['user_id'])
    if res.get('success'):
        return jsonify({'success': True, 'message': res.get('message')}), 200
    else:
        return jsonify({'success': False, 'error': res.get('error')}), res.get('code', 500)


# --- TRANSACTION OPERATIONS ENDPOINTS ---

@transactions_bp.route('/control-panel/transactions/<int:trans_id>/update-status', methods=['POST'])
def update_transaction_status(trans_id):
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee', 'accountant']:
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
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee', 'accountant']:
        return jsonify({'success': False, 'error': 'Unauthorized access.'}), 403

    res = TransactionService.get_details(trans_id)
    if res.get('success'):
        return jsonify({'success': True, 'details': res.get('details')}), 200
    else:
        return jsonify({'success': False, 'error': res.get('error')}), res.get('code', 404)


@transactions_bp.route('/control-panel/transactions/create', methods=['POST'])
def create_transaction():
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee', 'accountant']:
        return redirect(url_for('auth.login_page'))

    res = TransactionService.create_transaction(session['user_id'], request.form)
    return redirect(url_for('transactions.transactions_ledger'))

@transactions_bp.route('/control-panel/transactions/<int:trans_id>/edit', methods=['POST'])
def edit_transaction_submit(trans_id):
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee', 'accountant']:
        return redirect(url_for('auth.login_page'))

    res = TransactionService.edit_transaction(session['user_id'], trans_id, request.form)
    return redirect(url_for('transactions.transactions_ledger'))


# --- EMPLOYEES SALARIES (TREASURY) ---

@transactions_bp.route('/control-panel/salaries')
def salaries_payroll_ledger():
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee', 'accountant']:
        return redirect(url_for('auth.login_page'))

    from datetime import datetime
    month = request.args.get('month', '').strip()
    if not month:
        month = datetime.utcnow().strftime("%Y-%m")

    from app.services.salary_service import SalaryService
    data = SalaryService.get_payroll_data(month)
    user = AuthService.get_user_by_id(session['user_id'])

    return render_template(
        'salaries_payroll.html',
        user=user,
        ledger=data['ledger'],
        selected_month=data['selected_month'],
        months=data['months'],
        stats=data['stats'],
        timeline=data['timeline']
    )

@transactions_bp.route('/control-panel/salaries/approve/<int:employee_id>', methods=['POST'])
def salaries_approve_payout(employee_id):
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee', 'accountant']:
        return jsonify({'success': False, 'error': 'Unauthorized access.'}), 403

    from datetime import datetime
    month = request.args.get('month', '').strip()
    if not month:
        month = datetime.utcnow().strftime("%Y-%m")

    from app.services.salary_service import SalaryService
    res = SalaryService.approve_payout(employee_id, month)
    return jsonify(res)


 