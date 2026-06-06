from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from app.models.base import db
from app.models.users import Users, Role
from app.models.property import Property
from app.models.customer import Customer
from app.models.hr import Employee
from app.models.operations import Transaction
from sqlalchemy import text, func
from datetime import datetime, date, timedelta

transactions_bp = Blueprint('transactions', __name__)

@transactions_bp.route('/control-panel/transactions')
def transactions_list():
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return redirect(url_for('auth.login_page'))

    # Run migration & auto-seeding

    # Query all transactions
    transactions = Transaction.query.order_by(Transaction.transactionDate.desc()).all()

    # Calculate statistics based on real-estate terminology:
    # 1. Gross Volume: Sum of finalPrice for 'Closed'
    gross_volume = db.session.query(func.sum(Transaction.finalPrice)).filter_by(paymentStatus='Closed').scalar() or 0.0

    # 2. Total Commissions: Sum of commissionAmount for 'Closed'
    total_commission = db.session.query(func.sum(Transaction.commissionAmount)).filter_by(paymentStatus='Closed').scalar() or 0.0

    # 3. Pending Escrows: Sum of finalPrice for 'Escrow' and 'Legal'
    pending_escrows = db.session.query(func.sum(Transaction.finalPrice)).filter(Transaction.paymentStatus.in_(['Escrow', 'Legal'])).scalar() or 0.0

    # 4. Total Deals: Count of 'Closed' transactions
    total_deals = Transaction.query.filter_by(paymentStatus='Closed').count()

    # Format numbers for presentation
    stats = {
        'gross_volume': f"${gross_volume:,.2f}",
        'total_commission': f"${total_commission:,.2f}",
        'pending_escrows': f"${pending_escrows:,.2f}",
        'total_deals': total_deals
    }

    # Fetch user for base page injection
    user = Users.query.get(session['user_id'])

    return render_template(
        'transactions.html',
        user=user,
        transactions=transactions,
        stats=stats
    )

