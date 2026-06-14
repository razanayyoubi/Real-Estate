from datetime import datetime
from sqlalchemy import func
from app.models.base import db
from app.models.operations import Transaction
from app.models.property import Property
from app.models.customer import Customer
from app.models.hr import Employee, CommissionSetting
from app.models.users import AuditLog

class TransactionService:
    @staticmethod
    def get_ledger_data():
        """
        Fetch all transactions and ledger statistics, along with helper lists.
        """
        transactions = Transaction.query.order_by(Transaction.transactionDate.desc()).all()

        gross_volume = db.session.query(func.sum(Transaction.finalPrice)).filter_by(paymentStatus='Closed').scalar() or 0.0
        total_commission = db.session.query(func.sum(Transaction.commissionAmount)).filter_by(paymentStatus='Closed').scalar() or 0.0
        pending_escrows = db.session.query(func.sum(Transaction.finalPrice)).filter(Transaction.paymentStatus.in_(['Escrow', 'Legal'])).scalar() or 0.0
        total_deals = Transaction.query.filter_by(paymentStatus='Closed').count()

        total_transactions_count = Transaction.query.count()
        sales_count = Transaction.query.filter_by(transactionType='Sell').count()
        rent_count = Transaction.query.filter_by(transactionType='Rent').count()
        paid_count = Transaction.query.filter_by(paymentStatus='Closed').count()

        stats = {
            'gross_volume': f"${gross_volume:,.2f}",
            'total_commission': f"${total_commission:,.2f}",
            'pending_escrows': f"${pending_escrows:,.2f}",
            'total_deals': total_deals,
            'total_transactions': total_transactions_count,
            'sales_transactions': sales_count,
            'rental_transactions': rent_count,
            'paid_transactions': paid_count
        }

        properties = Property.query.order_by(Property.title.asc()).all()
        customers = Customer.query.all()
        employees = Employee.query.filter_by(status='Active').all()

        return {
            'transactions': transactions,
            'stats': stats,
            'properties': properties,
            'customers': customers,
            'employees': employees
        }

    @staticmethod
    def get_commission_settings():
        """
        Retrieve commission settings values from DB.
        """
        rent_rule_setting = CommissionSetting.query.filter_by(commissionType='rent_rule').first()
        buyer_rate_setting = CommissionSetting.query.filter_by(commissionType='buyer_rate').first()
        seller_rate_setting = CommissionSetting.query.filter_by(commissionType='seller_rate').first()
        agent_split_setting = CommissionSetting.query.filter_by(commissionType='agent_split').first()

        rent_rule = rent_rule_setting.ratePercentage if rent_rule_setting else 1.0
        if rent_rule == 5.0:
            rent_rule_str = "5% of Annual"
        elif rent_rule == 10.0:
            rent_rule_str = "10% of Annual"
        else:
            rent_rule_str = "1 Month"

        buyer_rate = float(buyer_rate_setting.ratePercentage) if buyer_rate_setting else 2.5
        seller_rate = float(seller_rate_setting.ratePercentage) if seller_rate_setting else 2.5
        agent_split = int(agent_split_setting.ratePercentage) if agent_split_setting else 30

        return {
            'rent_rule': rent_rule_str,
            'buyer_rate': buyer_rate,
            'seller_rate': seller_rate,
            'agent_split': agent_split
        }

    @staticmethod
    def save_commission_settings(user_id, data):
        """
        Save custom commission settings to DB.
        """
        rent_rule_str = data.get('rent_rule')
        buyer_rate = data.get('buyer_rate')
        seller_rate = data.get('seller_rate')
        agent_split = data.get('agent_split')

        if not rent_rule_str or buyer_rate is None or seller_rate is None or agent_split is None:
            return {'success': False, 'error': 'All fields are required.', 'code': 400}

        try:
            buyer_rate = float(buyer_rate)
            seller_rate = float(seller_rate)
            agent_split = float(agent_split)
            
            if not (0 <= buyer_rate <= 100) or not (0 <= seller_rate <= 100) or not (0 <= agent_split <= 100):
                return {'success': False, 'error': 'Percentages must be between 0 and 100.', 'code': 400}

            if rent_rule_str == "5% of Annual":
                rent_rule_val = 5.0
            elif rent_rule_str == "10% of Annual":
                rent_rule_val = 10.0
            else:
                rent_rule_val = 1.0

            def upsert_setting(c_type, val):
                setting = CommissionSetting.query.filter_by(commissionType=c_type).first()
                if not setting:
                    setting = CommissionSetting(commissionType=c_type)
                    db.session.add(setting)
                setting.ratePercentage = val
                setting.updatedBy = user_id
                setting.updatedAt = datetime.now()
                return setting

            upsert_setting('rent_rule', rent_rule_val)
            upsert_setting('buyer_rate', buyer_rate)
            upsert_setting('seller_rate', seller_rate)
            upsert_setting('agent_split', agent_split)

            db.session.commit()

            changes = {
                'rent_rule': rent_rule_str,
                'buyer_rate': buyer_rate,
                'seller_rate': seller_rate,
                'agent_split': agent_split
            }
            AuditLog.log_action(
                action='UPDATE',
                table_name='commission_setting',
                record_id=0,
                description="Updated global commission settings",
                user_id=user_id,
                changes=changes
            )
            db.session.commit()
            return {'success': True, 'message': 'Commission settings saved successfully!'}

        except ValueError:
            return {'success': False, 'error': 'Invalid numeric values provided.', 'code': 400}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'Database error: {str(e)}', 'code': 500}

    @staticmethod
    def reset_commission_settings(user_id):
        """
        Reset commission settings to default.
        """
        try:
            CommissionSetting.query.filter(CommissionSetting.commissionType.in_(['rent_rule', 'buyer_rate', 'seller_rate', 'agent_split'])).delete(synchronize_session=False)
            db.session.commit()

            AuditLog.log_action(
                action='DELETE',
                table_name='commission_setting',
                record_id=0,
                description="Reset global commission settings to system defaults",
                user_id=user_id
            )
            db.session.commit()
            return {'success': True, 'message': 'Reverted to system default settings.'}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'Database error: {str(e)}', 'code': 500}

    @staticmethod
    def update_status(user_id, trans_id, frontend_status):
        """
        Update status of a transaction and calculate fresh metrics.
        """
        status_map = {
            'Pending': 'Escrow',
            'In progress': 'Legal',
            'Completed': 'Closed',
            'Cancelled': 'Cancelled'
        }
        
        new_status = status_map.get(frontend_status)
        if not new_status:
            return {'success': False, 'error': f'Invalid status value: {frontend_status}.', 'code': 400}

        transaction = Transaction.query.get(trans_id)
        if not transaction:
            return {'success': False, 'error': 'Transaction not found.', 'code': 404}

        old_status = transaction.paymentStatus
        transaction.paymentStatus = new_status
        
        AuditLog.log_action(
            action='UPDATE',
            table_name='transaction',
            record_id=trans_id,
            description=f"Updated transaction status from {old_status} to {new_status} (Frontend: {frontend_status})",
            user_id=user_id,
            changes={'paymentStatus': new_status}
        )
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'Database error: {str(e)}', 'code': 500}

        # Recalculate metrics
        gross_volume = db.session.query(func.sum(Transaction.finalPrice)).filter_by(paymentStatus='Closed').scalar() or 0.0
        total_commission = db.session.query(func.sum(Transaction.commissionAmount)).filter_by(paymentStatus='Closed').scalar() or 0.0
        pending_escrows = db.session.query(func.sum(Transaction.finalPrice)).filter(Transaction.paymentStatus.in_(['Escrow', 'Legal'])).scalar() or 0.0
        total_deals = Transaction.query.filter_by(paymentStatus='Closed').count()
        
        total_transactions_count = Transaction.query.count()
        sales_count = Transaction.query.filter_by(transactionType='Sell').count()
        rent_count = Transaction.query.filter_by(transactionType='Rent').count()
        paid_count = Transaction.query.filter_by(paymentStatus='Closed').count()

        stats = {
            'total_transactions': total_transactions_count,
            'sales_transactions': sales_count,
            'rental_transactions': rent_count,
            'paid_transactions': paid_count,
            'gross_volume': f"${gross_volume:,.2f}",
            'total_commission': f"${total_commission:,.2f}",
            'pending_escrows': f"${pending_escrows:,.2f}",
            'total_deals': total_deals
        }

        return {'success': True, 'message': 'Transaction status updated successfully!', 'stats': stats}

    @staticmethod
    def get_details(trans_id):
        """
        Retrieve details of a single transaction.
        """
        transaction = Transaction.query.get(trans_id)
        if not transaction:
            return {'success': False, 'error': 'Transaction not found.', 'code': 404}

        main_image = next((img.imageURL for img in transaction.property_obj.images if img.isMainImage), None)
        if not main_image and transaction.property_obj.images:
            main_image = transaction.property_obj.images[0].imageURL
        if not main_image:
            main_image = "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=800&q=80"

        frontend_status_map = {
            'Escrow': 'Pending',
            'Legal': 'In progress',
            'Closed': 'Completed',
            'Cancelled': 'Cancelled'
        }
        frontend_status = frontend_status_map.get(transaction.paymentStatus, 'Pending')

        progress_map = {
            'Closed': 100,
            'Escrow': 50,
            'Legal': 25,
            'Cancelled': 0
        }
        progress_percent = progress_map.get(transaction.paymentStatus, 0)
        progress_text = {
            'Closed': 'Completed',
            'Escrow': 'Pending',
            'Legal': 'In progress',
            'Cancelled': 'Cancelled'
        }.get(transaction.paymentStatus, 'Unknown')

        date_str = transaction.transactionDate.strftime('%b %d, %Y')
        
        details = {
            'transactionID': transaction.transactionID,
            'propertyTitle': transaction.property_obj.title,
            'propertyLocation': transaction.property_obj.location,
            'imageURL': main_image,
            'customerID': transaction.customerID,
            'employeeID': transaction.employeeID,
            'buyerName': transaction.customer.user.fullName if transaction.customer else 'N/A',
            'buyerRole': 'Buyer' if transaction.transactionType == 'Sell' else 'Tenant',
            'agentName': transaction.employee.user.fullName if transaction.employee else 'N/A',
            'agentPosition': transaction.employee.position if transaction.employee else 'Agent',
            'ownerName': transaction.owner.user.fullName if transaction.owner else 'N/A',
            'ownerEmail': transaction.owner.user.email if transaction.owner else 'N/A',
            'finalPrice': float(transaction.finalPrice),
            'commissionRate': float(transaction.commissionRate),
            'commissionAmount': float(transaction.commissionAmount),
            'paymentStatus': frontend_status,
            'progressPercent': progress_percent,
            'progressText': progress_text,
            'transactionDate': date_str,
            'transactionType': transaction.transactionType,
            'paymentType': transaction.paymentType or 'Full Payment',
            'paymentMethod': transaction.paymentMethod or 'Bank Transfer (Wire)'
        }

        return {'success': True, 'details': details}

    @staticmethod
    def create_transaction(user_id, form_data):
        """
        Create a new transaction and update the property status.
        """
        property_id = form_data.get('propertyID')
        customer_id = form_data.get('customerID')
        employee_id = form_data.get('employeeID')
        transaction_type = form_data.get('transactionType')
        final_price_str = form_data.get('finalPrice')
        payment_type = form_data.get('paymentType', 'Full Payment')
        payment_method = form_data.get('paymentMethod', 'Bank Transfer (Wire)')

        if not property_id or not customer_id or not employee_id or not transaction_type or not final_price_str:
            return {'success': False, 'error': 'Missing required fields'}

        try:
            final_price = float(final_price_str)
            property_obj = Property.query.get(property_id)
            if not property_obj:
                return {'success': False, 'error': 'Property not found'}

            if transaction_type == 'Sell':
                commission_rate = 5.0
                commission_amount = final_price * 0.05
            else:
                commission_rate = 100.0
                commission_amount = final_price

            owner_id = property_obj.ownerID

            new_trans = Transaction(
                propertyID=int(property_id),
                customerID=int(customer_id),
                ownerID=int(owner_id),
                employeeID=int(employee_id),
                transactionType=transaction_type,
                finalPrice=final_price,
                commissionRate=commission_rate,
                commissionAmount=commission_amount,
                paymentStatus='Escrow',
                paymentType=payment_type,
                paymentMethod=payment_method,
                transactionDate=datetime.now(),
                createdAt=datetime.now()
            )

            db.session.add(new_trans)
            
            if transaction_type == 'Sell':
                property_obj.status = 'Sold'
            else:
                property_obj.status = 'Rented'

            db.session.flush()
            AuditLog.log_action(
                action='INSERT',
                table_name='transaction',
                record_id=new_trans.transactionID,
                description=f"Created new transaction #{new_trans.transactionID} for property {property_obj.title}",
                user_id=user_id
            )
            db.session.commit()
            return {'success': True}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    @staticmethod
    def edit_transaction(user_id, trans_id, form_data):
        """
        Edit details of an existing transaction.
        """
        transaction = Transaction.query.get(trans_id)
        if not transaction:
            return {'success': False, 'error': 'Transaction not found'}

        customer_id = form_data.get('customerID')
        employee_id = form_data.get('employeeID')
        payment_type = form_data.get('paymentType')
        payment_method = form_data.get('paymentMethod')
        payment_status_frontend = form_data.get('paymentStatus')

        if not customer_id or not employee_id or not payment_type or not payment_method or not payment_status_frontend:
            return {'success': False, 'error': 'Missing required fields'}

        status_map = {
            'Pending': 'Escrow',
            'In progress': 'Legal',
            'Completed': 'Closed',
            'Cancelled': 'Cancelled'
        }
        db_status = status_map.get(payment_status_frontend, 'Escrow')
        
        transaction.customerID = int(customer_id)
        transaction.employeeID = int(employee_id)
        transaction.paymentType = payment_type
        transaction.paymentMethod = payment_method
        transaction.paymentStatus = db_status

        changes = {
            'customerID': customer_id,
            'employeeID': employee_id,
            'paymentType': payment_type,
            'paymentMethod': payment_method,
            'paymentStatus': db_status
        }

        AuditLog.log_action(
            action='UPDATE',
            table_name='transaction',
            record_id=trans_id,
            description=f"Updated transaction #{trans_id} details via Edit Modal",
            user_id=user_id,
            changes=changes
        )

        try:
            db.session.commit()
            return {'success': True}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
