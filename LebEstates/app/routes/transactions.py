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

def run_migration_and_seed():
    # 1. Execute DB Alter command to support the new payment status ENUM
    try:
        db.session.execute(text("ALTER TABLE transaction MODIFY COLUMN paymentStatus ENUM('Escrow', 'Legal', 'Closed', 'Cancelled') DEFAULT 'Escrow'"))
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        # Log or ignore if the enum values already exist

    # 2. Seeding check
    if Transaction.query.count() == 0:
        try:
            # Check for Employee Role
            emp_role = Role.query.filter_by(roleName='Employee').first()
            if not emp_role:
                emp_role = Role(roleID=2, roleName='Employee')
                db.session.add(emp_role)
                db.session.commit()

            # Seed a default Agent User
            import bcrypt
            agent_user = Users.query.filter_by(email='agent.marcelle@lebestates.com').first()
            if not agent_user:
                pwd_hash = bcrypt.hashpw('agent123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                agent_user = Users(
                    fullName='Marcelle T.',
                    email='agent.marcelle@lebestates.com',
                    passwordHash=pwd_hash,
                    roleID=emp_role.roleID,
                    status='Active'
                )
                db.session.add(agent_user)
                db.session.commit()

            # Seed Employee profile for Agent
            agent_emp = Employee.query.filter_by(userID=agent_user.userID).first()
            if not agent_emp:
                agent_emp = Employee(
                    userID=agent_user.userID,
                    position='Senior Sales Representative',
                    hireDate=date.today() - timedelta(days=365),
                    status='Active'
                )
                db.session.add(agent_emp)
                db.session.commit()

            # Check properties count, seed if empty
            if Property.query.count() == 0:
                prop1 = Property(
                    ownerID=1, # CustomerID 1 (Fatima)
                    createdBy=4, # Creator (Admin User)
                    title='Luxury Penthouse Beirut Central',
                    description='Stunning 3-bedroom penthouse with panoramic city and Mediterranean Sea views, designer finishes, and private terrace.',
                    propertyType='Apartment',
                    listingType='Sell',
                    location='Beirut',
                    address='Achrafieh Main Street, Beirut',
                    price=850000.00,
                    area=250.00,
                    rooms=3,
                    bathrooms=4,
                    floorNumber=12,
                    parkingAvailable=True,
                    status='Sold'
                )
                prop2 = Property(
                    ownerID=2, # CustomerID 2 (mohammad)
                    createdBy=4,
                    title='Modern Beachfront Villa',
                    description='Exquisite beachfront villa with private pool, direct sea access, and high-end security. Perfect family holiday home.',
                    propertyType='Villa',
                    listingType='Sell',
                    location='Batroun',
                    address='Batroun Coastline Road',
                    price=1200000.00,
                    area=450.00,
                    rooms=5,
                    bathrooms=6,
                    floorNumber=0,
                    parkingAvailable=True,
                    status='Sold'
                )
                prop3 = Property(
                    ownerID=1, # CustomerID 1 (Fatima)
                    createdBy=4,
                    title='Duplex in Faraya Hills',
                    description='Cozy chalet-style duplex located 2 minutes from the ski slopes. Built-in fireplace and spacious balcony.',
                    propertyType='Duplex',
                    listingType='Rent',
                    location='Faraya',
                    address='Faraya Ski Road',
                    price=24000.00,
                    area=180.00,
                    rooms=2,
                    bathrooms=2,
                    floorNumber=2,
                    parkingAvailable=True,
                    status='Rented'
                )
                db.session.add_all([prop1, prop2, prop3])
                db.session.commit()

            # Seed transactions
            p1 = Property.query.filter_by(title='Luxury Penthouse Beirut Central').first()
            p2 = Property.query.filter_by(title='Modern Beachfront Villa').first()
            p3 = Property.query.filter_by(title='Duplex in Faraya Hills').first()

            t1 = Transaction(
                propertyID=p1.propertyID,
                customerID=2, # Buyer: mohammad (CustomerID 2)
                ownerID=1,    # Seller: Fatima (CustomerID 1)
                employeeID=agent_emp.employeeID,
                transactionType='Sell',
                finalPrice=820000.00,
                commissionRate=2.50,
                commissionAmount=20500.00,
                paymentStatus='Closed',
                transactionDate=datetime.now() - timedelta(days=22)
            )

            t2 = Transaction(
                propertyID=p2.propertyID,
                customerID=1, # Buyer: Fatima (CustomerID 1)
                ownerID=2,    # Seller: mohammad (CustomerID 2)
                employeeID=agent_emp.employeeID,
                transactionType='Sell',
                finalPrice=1150000.00,
                commissionRate=3.00,
                commissionAmount=34500.00,
                paymentStatus='Closed',
                transactionDate=datetime.now() - timedelta(days=5)
            )

            t3 = Transaction(
                propertyID=p3.propertyID,
                customerID=2, # Tenant: mohammad (CustomerID 2)
                ownerID=1,    # Landlord: Fatima (CustomerID 1)
                employeeID=agent_emp.employeeID,
                transactionType='Rent',
                finalPrice=24000.00,
                commissionRate=5.00,
                commissionAmount=1200.00,
                paymentStatus='Escrow',
                transactionDate=datetime.now() - timedelta(days=2)
            )

            db.session.add_all([t1, t2, t3])
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error seeding transactions: {e}")

@transactions_bp.route('/control-panel/transactions')
def transactions_list():
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return redirect(url_for('auth.login_page'))

    # Run migration & auto-seeding
    run_migration_and_seed()

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

@transactions_bp.route('/control-panel/transactions/<int:trans_id>/update-status', methods=['POST'])
def update_transaction_status(trans_id):
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({'error': 'Status is required.'}), 400

    new_status = data['status']
    if new_status not in ['Escrow', 'Legal', 'Closed', 'Cancelled']:
        return jsonify({'error': 'Invalid status value.'}), 400

    transaction = Transaction.query.get_or_404(trans_id)
    transaction.paymentStatus = new_status

    try:
        db.session.commit()

        # Recalculate stats dynamically for the client dashboard update
        gross_volume = db.session.query(func.sum(Transaction.finalPrice)).filter_by(paymentStatus='Closed').scalar() or 0.0
        total_commission = db.session.query(func.sum(Transaction.commissionAmount)).filter_by(paymentStatus='Closed').scalar() or 0.0
        pending_escrows = db.session.query(func.sum(Transaction.finalPrice)).filter(Transaction.paymentStatus.in_(['Escrow', 'Legal'])).scalar() or 0.0
        total_deals = Transaction.query.filter_by(paymentStatus='Closed').count()

        return jsonify({
            'success': True,
            'message': f"Transaction #{trans_id} status updated to {new_status}.",
            'new_status': new_status,
            'stats': {
                'gross_volume': f"${gross_volume:,.2f}",
                'total_commission': f"${total_commission:,.2f}",
                'pending_escrows': f"${pending_escrows:,.2f}",
                'total_deals': total_deals
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f"Database error: {str(e)}"}), 500
