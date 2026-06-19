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

        properties = Property.query.filter_by(status='Published').order_by(Property.title.asc()).all()
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

            # Fetch current global agent split setting
            agent_split_setting = CommissionSetting.query.filter_by(commissionType='agent_split').first()
            agent_split = float(agent_split_setting.ratePercentage) if agent_split_setting else 30.0

            new_trans = Transaction(
                propertyID=int(property_id),
                customerID=int(customer_id),
                ownerID=int(owner_id),
                employeeID=int(employee_id),
                transactionType=transaction_type,
                finalPrice=final_price,
                commissionRate=commission_rate,
                commissionAmount=commission_amount,
                agentCommissionRate=agent_split,
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

    @staticmethod
    def get_revenue_dashboard_data():
        """
        Gathers comprehensive revenue, sales trend, agent leaderboard,
        recent transaction, and profitability analytics for the dashboard.
        """
        from app.models.users import Users
        from app.models.hr import Salary, Employee
        from app.models.property import Property
        from app.models.customer import Customer
        from datetime import datetime, timedelta
        from sqlalchemy.orm import joinedload
        import calendar

        # Helper currency formatter
        def format_currency(val):
            if val >= 1_000_000:
                return f"${val / 1_000_000:.1f}M"
            elif val >= 1_000:
                return f"${val / 1_000:.1f}K"
            else:
                return f"${val:,.2f}"

        # 1. Base database aggregate queries for closed transactions (no in-memory looping of model objects)
        closed_stats = db.session.query(
            func.count(Transaction.transactionID).label('cnt'),
            func.sum(Transaction.commissionAmount).label('total_comm'),
            func.sum(Transaction.finalPrice).label('total_price'),
            func.avg(Transaction.finalPrice).label('avg_price')
        ).filter(Transaction.paymentStatus == 'Closed').first()

        all_transactions_count = db.session.query(func.count(Transaction.transactionID)).scalar() or 0
        closed_count = closed_stats.cnt or 0
        total_commission = float(closed_stats.total_comm or 0.0)
        commission_revenue = total_commission
        gross_revenue = float(closed_stats.total_price or 0.0)
        avg_deal_value = float(closed_stats.avg_price or 0.0)

        # Current month's revenue query
        now = datetime.now()
        this_month_start = datetime(now.year, now.month, 1)
        revenue_this_month = db.session.query(func.sum(Transaction.commissionAmount)).filter(
            Transaction.paymentStatus == 'Closed',
            Transaction.transactionDate >= this_month_start
        ).scalar() or 0.0

        # Percentages / trends comparison (relative to previous month for realistic trend)
        prev_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
        prev_month_end = this_month_start - timedelta(seconds=1)
        revenue_prev_month = db.session.query(func.sum(Transaction.commissionAmount)).filter(
            Transaction.paymentStatus == 'Closed',
            Transaction.transactionDate >= prev_month_start,
            Transaction.transactionDate <= prev_month_end
        ).scalar() or 0.0

        if revenue_prev_month > 0:
            rev_month_change = ((float(revenue_this_month) - float(revenue_prev_month)) / float(revenue_prev_month)) * 100
        else:
            rev_month_change = 8.0 # default fallback trend percentage

        # 2. Pre-fetch monthly salaries & transactions globally to prevent N+1 loop queries
        # salaryMonth format is 'YYYY-MM'
        monthly_salaries_stats = db.session.query(
            Salary.salaryMonth,
            func.sum(Salary.totalSalary).label('total_salary')
        ).group_by(Salary.salaryMonth).all()
        salary_map = {row.salaryMonth: float(row.total_salary or 0.0) for row in monthly_salaries_stats}

        # Last 12 calendar months list generation
        months_list = []
        for i in range(11, -1, -1):
            year_offset = (now.month - 1 - i) // 12
            month_index = (now.month - 1 - i) % 12 + 1
            month_year = now.year + year_offset
            months_list.append((month_year, month_index))

        min_start_date = datetime(months_list[0][0], months_list[0][1], 1)
        
        # Batch query transaction metrics grouped by year/month
        monthly_trans_stats = db.session.query(
            func.year(Transaction.transactionDate).label('yr'),
            func.month(Transaction.transactionDate).label('mo'),
            func.sum(Transaction.commissionAmount).label('total_comm'),
            func.sum(Transaction.finalPrice).label('total_price')
        ).filter(
            Transaction.paymentStatus == 'Closed',
            Transaction.transactionDate >= min_start_date
        ).group_by(
            func.year(Transaction.transactionDate),
            func.month(Transaction.transactionDate)
        ).all()
        trans_map = {(row.yr, row.mo): (float(row.total_comm or 0.0), float(row.total_price or 0.0)) for row in monthly_trans_stats}

        # Monthly lists populating
        trend_months = []
        trend_revenue = []
        trend_volume = []
        trend_profit = []
        trend_expenses = []

        best_month_name = "N/A"
        best_month_val = 0.0

        for year, month in months_list:
            month_label = f"{calendar.month_abbr[month]} {str(year)[2:]}"
            trend_months.append(month_label)

            monthly_rev, monthly_vol = trans_map.get((year, month), (0.0, 0.0))
            trend_revenue.append(monthly_rev)
            trend_volume.append(monthly_vol)

            # Retrieve pre-fetched salaries using dictionary mapping
            salary_month_str = f"{year:04d}-{month:02d}"
            monthly_salaries = salary_map.get(salary_month_str, 0.0)

            monthly_exp = monthly_salaries + (monthly_rev * 0.15)
            if monthly_exp == 0.0 and monthly_rev > 0:
                monthly_exp = monthly_rev * 0.25

            trend_expenses.append(monthly_exp)
            trend_profit.append(monthly_rev - monthly_exp)

            if monthly_rev > best_month_val:
                best_month_val = monthly_rev
                best_month_name = f"{calendar.month_name[month]} {year}"

        # 3. Revenue Sources breakdown (Sales vs Rentals) in a single optimized group-by query
        sales_rental_stats = db.session.query(
            Transaction.transactionType,
            func.sum(Transaction.commissionAmount).label('total_comm')
        ).filter(Transaction.paymentStatus == 'Closed').group_by(Transaction.transactionType).all()

        sales_total = 0.0
        rental_total = 0.0
        for row in sales_rental_stats:
            if row.transactionType == 'Sell':
                sales_total = float(row.total_comm or 0.0)
            elif row.transactionType == 'Rent':
                rental_total = float(row.total_comm or 0.0)

        source_total = sales_total + rental_total
        if source_total > 0:
            sales_percentage = int((sales_total / source_total) * 100)
            rental_percentage = 100 - sales_percentage
        else:
            sales_percentage = 75
            rental_percentage = 25

        # 4. Top Revenue Agents
        # Including avatar checks inside the query to prevent N+1 lazy lookup loops
        top_agents_query = db.session.query(
            Employee.employeeID,
            Users.userID,
            Users.fullName,
            Employee.position,
            Users.avatar.isnot(None).label('has_avatar'),
            func.sum(Transaction.commissionAmount).label('total_comm'),
            func.count(Transaction.transactionID).label('deal_count')
        ).join(Users, Employee.userID == Users.userID)\
         .join(Transaction, Transaction.employeeID == Employee.employeeID)\
         .filter(Transaction.paymentStatus == 'Closed')\
         .group_by(Employee.employeeID, Users.userID, Users.fullName, Employee.position, Users.avatar)\
         .order_by(func.sum(Transaction.commissionAmount).desc())\
         .limit(5)\
         .all()

        top_agents = []
        best_agent_name = "N/A"
        best_agent_val = 0.0
        best_agent_avatar = None
        
        for idx, row in enumerate(top_agents_query):
            agent_comm = float(row.total_comm)
            agent_name = row.fullName
            
            if row.has_avatar:
                avatar_url = f"/profile/avatar/{row.userID}"
            else:
                avatar_url = f"https://ui-avatars.com/api/?name={agent_name.replace(' ', '+')}&background=random"

            if idx == 0:
                best_agent_name = agent_name
                best_agent_val = agent_comm
                best_agent_avatar = avatar_url

            display_id = row.employeeID + 8000
            
            top_agents.append({
                'id': f"#EMP-{display_id}",
                'name': agent_name,
                'position': row.position,
                'deal_count': row.deal_count,
                'revenue': format_currency(agent_comm * 20.0),
                'commission': format_currency(agent_comm),
                'commission_val': agent_comm,
                'avatar_url': avatar_url
            })

        if not top_agents:
            top_agents.append({
                'id': 'N/A',
                'name': 'No active sales agents',
                'position': 'Staff',
                'deal_count': 0,
                'revenue': '$0.00',
                'commission': '$0.00',
                'commission_val': 0.0,
                'avatar_url': 'https://ui-avatars.com/api/?name=No+Agents'
            })

        # 5. Revenue Insights (Eager loaded queries to prevent child attribute query loops)
        largest_trans = Transaction.query.options(
            joinedload(Transaction.property_obj),
            joinedload(Transaction.employee).joinedload(Employee.user)
        ).filter_by(paymentStatus='Closed').order_by(Transaction.finalPrice.desc()).first()

        if largest_trans:
            largest_trans_title = f"{largest_trans.property_obj.title} ({format_currency(float(largest_trans.finalPrice))})"
            largest_trans_val = float(largest_trans.finalPrice)
            largest_trans_agent = largest_trans.employee.user.fullName if largest_trans.employee else "N/A"
        else:
            largest_trans_title = "No closed deals"
            largest_trans_val = 0.0
            largest_trans_agent = "N/A"

        highest_prop_query = db.session.query(
            Property.title,
            func.sum(Transaction.commissionAmount).label('prop_comm')
        ).join(Transaction, Transaction.propertyID == Property.propertyID)\
         .filter(Transaction.paymentStatus == 'Closed')\
         .group_by(Property.propertyID, Property.title)\
         .order_by(func.sum(Transaction.commissionAmount).desc())\
         .first()

        if highest_prop_query:
            highest_revenue_prop_title = highest_prop_query.title
            highest_revenue_prop_val = float(highest_prop_query.prop_comm)
        else:
            highest_revenue_prop_title = "N/A"
            highest_revenue_prop_val = 0.0

        # 6. Recent Revenue Transactions Table (Eager joinedloads to avoid N+1 loading in templates)
        recent_trans_query = Transaction.query.options(
            joinedload(Transaction.property_obj).joinedload(Property.images),
            joinedload(Transaction.customer).joinedload(Customer.user),
            joinedload(Transaction.employee).joinedload(Employee.user)
        ).order_by(Transaction.transactionDate.desc()).limit(8).all()

        recent_transactions = []
        for t in recent_trans_query:
            main_image = next((img.imageURL for img in t.property_obj.images if img.isMainImage), None)
            if not main_image and t.property_obj.images:
                main_image = t.property_obj.images[0].imageURL
            if not main_image:
                main_image = "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=800&q=80"

            recent_transactions.append({
                'id': f"TX-{t.transactionID}",
                'property_title': t.property_obj.title,
                'property_type': t.property_obj.propertyType,
                'listing_type': t.transactionType,
                'image_url': main_image,
                'client_name': t.customer.user.fullName if t.customer else 'N/A',
                'agent_name': t.employee.user.fullName if t.employee else 'N/A',
                'final_price': float(t.finalPrice),
                'final_price_formatted': format_currency(float(t.finalPrice)),
                'commission': float(t.commissionAmount),
                'commission_formatted': format_currency(float(t.commissionAmount)),
                'status': 'Completed' if t.paymentStatus == 'Closed' else 'Pending' if t.paymentStatus == 'Escrow' else 'In progress' if t.paymentStatus == 'Legal' else 'Cancelled',
                'date': t.transactionDate.strftime('%b %d, %Y')
            })

        # 7. Profitability Details
        total_salaries_expense = float(total_salaries_expense) if 'total_salaries_expense' in locals() else sum(salary_map.values())
        computed_op_expenses = total_commission * 0.15
        total_expenses = total_salaries_expense + computed_op_expenses

        net_profit = total_commission - total_expenses
        profit_margin = int((net_profit / total_commission) * 100) if total_commission > 0 else 0

        # Quarterly details: Pre-fetched all-time monthly sums to compile metrics in-memory (No database substring splits)
        all_time_monthly_stats = db.session.query(
            func.month(Transaction.transactionDate).label('mo'),
            func.sum(Transaction.commissionAmount).label('total_comm')
        ).filter(Transaction.paymentStatus == 'Closed').group_by(func.month(Transaction.transactionDate)).all()

        quarter_rev = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}
        for row in all_time_monthly_stats:
            q = (row.mo - 1) // 3 + 1
            quarter_rev[q] += float(row.total_comm or 0.0)

        quarterly_trend = []
        for q in range(1, 5):
            q_rev = quarter_rev[q]
            
            # Map suffix month identifiers ('01', '02', etc.) in-memory to accumulate salaries database-agnostically
            q_months = [f"{(q-1)*3+1:02d}", f"{(q-1)*3+2:02d}", f"{(q-1)*3+3:02d}"]
            q_salaries = sum(val for key, val in salary_map.items() if len(key) >= 7 and key[5:7] in q_months)

            q_exp = float(q_salaries) + (q_rev * 0.15)
            if q_exp == 0.0 and q_rev > 0:
                q_exp = q_rev * 0.25
                
            q_prof = q_rev - q_exp
            quarterly_trend.append({
                'label': f"Q{q}",
                'revenue': q_rev,
                'profit': q_prof
            })

        return {
            'kpis': {
                'total_revenue': format_currency(total_commission),
                'revenue_this_month': format_currency(revenue_this_month),
                'total_transactions': all_transactions_count,
                'closed_transactions': closed_count,
                'avg_deal_value': format_currency(avg_deal_value),
                'trend_pct_revenue': "+12%",
                'trend_pct_month': f"+{int(rev_month_change)}%" if rev_month_change >= 0 else f"{int(rev_month_change)}%",
                'trend_pct_tx': "+5%",
                'trend_pct_deal': "-2%"
            },
            'charts': {
                'trend_labels': trend_months,
                'trend_revenue': trend_revenue,
                'trend_volume': trend_volume,
                'trend_profit': trend_profit,
                'trend_expenses': trend_expenses,
                'sources_sales': sales_total,
                'sources_rentals': rental_total,
                'sales_pct': sales_percentage,
                'rental_pct': rental_percentage,
                'quarterly': quarterly_trend
            },
            'top_agents': top_agents,
            'insights': {
                'best_month_name': best_month_name,
                'best_month_val': format_currency(best_month_val),
                'largest_transaction_title': largest_trans_title,
                'largest_transaction_val': format_currency(largest_trans_val),
                'largest_transaction_agent': largest_trans_agent,
                'best_agent_name': best_agent_name,
                'best_agent_val': format_currency(best_agent_val),
                'best_agent_avatar': best_agent_avatar or f"https://ui-avatars.com/api/?name={best_agent_name.replace(' ', '+')}&background=random",
                'highest_revenue_prop_title': highest_revenue_prop_title,
                'highest_revenue_prop_val': format_currency(highest_revenue_prop_val)
            },
            'recent_transactions': recent_transactions,
            'profitability': {
                'gross_revenue': format_currency(gross_revenue),
                'commission_revenue': format_currency(commission_revenue),
                'expenses': format_currency(total_expenses),
                'net_profit': format_currency(net_profit),
                'profit_margin': profit_margin
            }
        }

    @staticmethod
    def get_payment_tracking_data():
        """
        Gathers comprehensive payment tracking, outstanding balances,
        aging, and ledger distribution reports for LebEstates.
        """
        from app.models.operations import Transaction
        from app.models.customer import Customer
        from app.models.hr import Employee
        from app.models.users import Users
        from datetime import datetime, timedelta
        from sqlalchemy.orm import joinedload
        import calendar

        def format_currency(val):
            return f"${val:,.0f}"

        now = datetime.now()

        # Eager load related customer, employee, property, and user records
        transactions = Transaction.query.options(
            joinedload(Transaction.customer).joinedload(Customer.user),
            joinedload(Transaction.employee).joinedload(Employee.user),
            joinedload(Transaction.property_obj)
        ).order_by(Transaction.transactionDate.desc()).all()

        total_receivables = 0.0
        total_collected = 0.0
        overdue_amount = 0.0
        collected_this_month = 0.0

        paid_count = 0
        partial_count = 0
        overdue_count = 0

        current_aging = 0.0
        aging_31_60 = 0.0
        aging_61_90 = 0.0
        aging_90_plus = 0.0

        ledger_entries = []
        critical_balances = []

        this_month_start = datetime(now.year, now.month, 1)

        for t in transactions:
            final_price = float(t.finalPrice or 0.0)
            age_in_days = (now - t.transactionDate).days

            if t.paymentStatus == 'Closed':
                paid = final_price
                balance = 0.0
                due_date = None
                status = 'PAID'
                paid_count += 1
            elif t.paymentStatus == 'Escrow':
                paid = final_price * 0.5
                balance = final_price * 0.5
                due_date = t.transactionDate + timedelta(days=30)
                status = 'PARTIAL'
                partial_count += 1
            elif t.paymentStatus == 'Legal':
                paid = final_price * 0.7
                balance = final_price * 0.3
                due_date = t.transactionDate + timedelta(days=15)
                status = 'OVERDUE'
                overdue_count += 1
                overdue_amount += balance
            elif t.paymentStatus == 'Cancelled':
                paid = 0.0
                balance = 0.0
                due_date = None
                status = 'CANCELLED'
            else:
                continue

            if t.paymentStatus != 'Cancelled':
                total_receivables += final_price
                total_collected += paid

                if t.transactionDate >= this_month_start:
                    collected_this_month += paid

                if balance > 0:
                    if age_in_days < 30:
                        current_aging += balance
                    elif age_in_days <= 60:
                        aging_31_60 += balance
                    elif age_in_days <= 90:
                        aging_61_90 += balance
                    else:
                        aging_90_plus += balance

                    initials = "NA"
                    if t.customer and t.customer.user and t.customer.user.fullName:
                        parts = t.customer.user.fullName.split()
                        if len(parts) >= 2:
                            initials = (parts[0][0] + parts[-1][0]).upper()
                        elif len(parts) == 1:
                            initials = parts[0][:2].upper()

                    critical_balances.append({
                        'name': t.customer.user.fullName if t.customer else 'N/A',
                        'initials': initials,
                        'property': t.property_obj.title if t.property_obj else 'N/A',
                        'amount': format_currency(balance),
                        'amount_raw': balance,
                        'overdue_days': age_in_days,
                        'status': 'Overdue' if t.paymentStatus == 'Legal' else 'Pending',
                        'avatar_url': t.customer.user.avatar_url if t.customer and t.customer.user else 'https://ui-avatars.com/api/?name=Unknown'
                    })

            ledger_entries.append({
                'id': f"#TR-{t.transactionID}",
                'raw_id': t.transactionID,
                'client': t.customer.user.fullName if t.customer else 'N/A',
                'total': format_currency(final_price),
                'total_raw': final_price,
                'paid': format_currency(paid),
                'paid_raw': paid,
                'balance': format_currency(balance),
                'balance_raw': balance,
                'due_date': due_date.strftime('%b %d, %Y') if due_date else '—',
                'status': status
            })

        # Calculate Collection Rate
        collection_rate = int((total_collected / total_receivables) * 100) if total_receivables > 0 else 0

        # Sort and take top 4 critical balances
        critical_balances.sort(key=lambda x: x['amount_raw'], reverse=True)
        critical_balances = critical_balances[:4]

        # Generate last 6 months trend data
        months_list = []
        for i in range(5, -1, -1):
            year_offset = (now.month - 1 - i) // 12
            month_index = (now.month - 1 - i) % 12 + 1
            month_year = now.year + year_offset
            months_list.append((month_year, month_index))

        trend_labels = []
        trend_collected = []
        trend_outstanding = []

        for year, month in months_list:
            trend_labels.append(calendar.month_abbr[month])
            m_collected = 0.0
            m_outstanding = 0.0
            for t in transactions:
                if t.paymentStatus != 'Cancelled' and t.transactionDate.year == year and t.transactionDate.month == month:
                    final_price = float(t.finalPrice or 0.0)
                    if t.paymentStatus == 'Closed':
                        m_collected += final_price
                    elif t.paymentStatus == 'Escrow':
                        m_collected += final_price * 0.5
                        m_outstanding += final_price * 0.5
                    elif t.paymentStatus == 'Legal':
                        m_collected += final_price * 0.7
                        m_outstanding += final_price * 0.3
            trend_collected.append(m_collected)
            trend_outstanding.append(m_outstanding)

        total_status_count = paid_count + partial_count + overdue_count
        if total_status_count > 0:
            paid_pct = int((paid_count / total_status_count) * 100)
            partial_pct = int((partial_count / total_status_count) * 100)
            overdue_pct = 100 - (paid_pct + partial_pct)
        else:
            paid_pct, partial_pct, overdue_pct = 0, 0, 0

        def format_kpi(val):
            if val >= 1_000_000:
                return f"${val / 1_000_000:.1f}M"
            elif val >= 1_000:
                return f"${val / 1_000:.0f}K"
            else:
                return f"${val:,.0f}"

        kpis = {
            'total_receivables': format_kpi(total_receivables),
            'collected_this_month': format_kpi(collected_this_month),
            'overdue_amount': format_kpi(overdue_amount),
            'collection_rate': collection_rate
        }

        total_aging = current_aging + aging_31_60 + aging_61_90 + aging_90_plus
        if total_aging > 0:
            current_aging_pct = int((current_aging / total_aging) * 100)
            aging_31_60_pct = int((aging_31_60 / total_aging) * 100)
            aging_61_90_pct = int((aging_61_90 / total_aging) * 100)
            aging_90_plus_pct = 100 - (current_aging_pct + aging_31_60_pct + aging_61_90_pct)
        else:
            current_aging_pct, aging_31_60_pct, aging_61_90_pct, aging_90_plus_pct = 0, 0, 0, 0

        aging_report = {
            'current': format_kpi(current_aging),
            'current_pct': current_aging_pct,
            'days_31_60': format_kpi(aging_31_60),
            'days_31_60_pct': aging_31_60_pct,
            'days_61_90': format_kpi(aging_61_90),
            'days_61_90_pct': aging_61_90_pct,
            'days_90_plus': format_kpi(aging_90_plus),
            'days_90_plus_pct': aging_90_plus_pct
        }

        charts = {
            'trend_labels': trend_labels,
            'trend_collected': trend_collected,
            'trend_outstanding': trend_outstanding,
            'paid_pct': paid_pct,
            'partial_pct': partial_pct,
            'overdue_pct': overdue_pct,
            'paid_count': paid_count,
            'partial_count': partial_count,
            'overdue_count': overdue_count
        }

        return {
            'kpis': kpis,
            'charts': charts,
            'critical_balances': critical_balances,
            'aging_report': aging_report,
            'ledger': ledger_entries
        }

