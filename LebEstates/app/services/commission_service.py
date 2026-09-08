import calendar
from datetime import datetime, date, timedelta
from sqlalchemy import func, extract
from app.models.base import db
from app.models.operations import Transaction
from app.models.property import Property
from app.models.customer import Customer
from app.models.hr import Employee, CommissionSetting
from app.models.users import Users
from sqlalchemy.orm import joinedload

class CommissionService:
    @staticmethod
    def get_commissions_dashboard_data(period_type='all', selected_year=None, selected_month=None):
        """
        Dynamically calculates commission stats, agent leaderboard,
        recent commissions ledger, and mock operations expenses according to period parameters.
        """
        now = datetime.now()
        
        if not selected_year:
            selected_year = now.year
        if not selected_month:
            selected_month = now.month

        start_date = None
        end_date = None

        if period_type == 'monthly' or period_type == 'month':
            period_type = 'monthly'
            start_date = date(selected_year, selected_month, 1)
            num_days = calendar.monthrange(selected_year, selected_month)[1]
            end_date = date(selected_year, selected_month, num_days) + timedelta(days=1)
        elif period_type == 'yearly' or period_type == 'year':
            period_type = 'yearly'
            start_date = date(selected_year, 1, 1)
            end_date = date(selected_year + 1, 1, 1)
        else:
            period_type = 'all'

        # Fetch available years dynamically
        available_years_query = db.session.query(extract('year', Transaction.transactionDate)).distinct().all()
        available_years = sorted([int(r[0]) for r in available_years_query if r[0] is not None], reverse=True)
        if selected_year not in available_years:
            available_years.insert(0, selected_year)

        # 1. Fetch Agent Split Setting
        agent_split_setting = CommissionSetting.query.filter_by(commissionType='agent_split').first()
        agent_split = float(agent_split_setting.ratePercentage) if agent_split_setting else 30.0

        # Helper formatter
        def format_currency(val):
            return f"${val:,.2f}"

        # 2. Compute KPI Metrics with optional date bounds
        vol_query = db.session.query(func.sum(Transaction.commissionAmount)).filter(
            Transaction.paymentStatus != 'Cancelled'
        )
        payout_query = db.session.query(
            func.sum(Transaction.commissionAmount * (func.coalesce(Transaction.agentCommissionRate, 30.0) / 100.0))
        ).filter(
            Transaction.paymentStatus == 'Closed'
        )
        unpaid_query = db.session.query(
            func.sum(Transaction.commissionAmount * (func.coalesce(Transaction.agentCommissionRate, 30.0) / 100.0))
        ).filter(
            Transaction.paymentStatus.in_(['Escrow', 'Legal'])
        )
        rate_query = db.session.query(func.avg(Transaction.commissionRate)).filter(
            Transaction.transactionType == 'Sell',
            Transaction.paymentStatus != 'Cancelled'
        )
        agents_query = db.session.query(func.count(func.distinct(Transaction.employeeID))).filter(
            Transaction.paymentStatus != 'Cancelled'
        )

        if start_date and end_date:
            vol_query = vol_query.filter(Transaction.transactionDate >= start_date, Transaction.transactionDate < end_date)
            payout_query = payout_query.filter(Transaction.transactionDate >= start_date, Transaction.transactionDate < end_date)
            unpaid_query = unpaid_query.filter(Transaction.transactionDate >= start_date, Transaction.transactionDate < end_date)
            rate_query = rate_query.filter(Transaction.transactionDate >= start_date, Transaction.transactionDate < end_date)
            agents_query = agents_query.filter(Transaction.transactionDate >= start_date, Transaction.transactionDate < end_date)

        total_comm_volume = float(vol_query.scalar() or 0.0)
        ready_for_payout_agent_share = float(payout_query.scalar() or 0.0)
        unpaid_payout_agent_share = float(unpaid_query.scalar() or 0.0)
        avg_comm_rate = rate_query.scalar() or 3.80
        active_agents_count = agents_query.scalar() or 0

        kpis = {
            'total_commission_volume': format_currency(total_comm_volume),
            'ready_for_payout': format_currency(ready_for_payout_agent_share),
            'unpaid_payout': format_currency(unpaid_payout_agent_share),
            'avg_commission_rate': f"{float(avg_comm_rate):.2f}%",
            'active_agents': active_agents_count,
            'agent_split': f"{agent_split:.0f}%"
        }

        # 3. Top Performing Agents (Top 3 active employees by closed commission)
        top_q = db.session.query(
            Employee.employeeID,
            Users.userID,
            Users.fullName,
            Employee.position,
            Users.avatar.isnot(None).label('has_avatar'),
            func.sum(Transaction.commissionAmount).label('total_comm'),
            func.sum(Transaction.commissionAmount * (func.coalesce(Transaction.agentCommissionRate, 30.0) / 100.0)).label('total_agent_share'),
            func.count(Transaction.transactionID).label('deal_count')
        ).join(Users, Employee.userID == Users.userID)\
         .join(Transaction, Transaction.employeeID == Employee.employeeID)\
         .filter(Transaction.paymentStatus == 'Closed')

        if start_date and end_date:
            top_q = top_q.filter(Transaction.transactionDate >= start_date, Transaction.transactionDate < end_date)

        top_agents_query = top_q.group_by(Employee.employeeID, Users.userID, Users.fullName, Employee.position, Users.avatar)\
                                .order_by(func.sum(Transaction.commissionAmount).desc())\
                                .limit(3)\
                                .all()

        top_agents = []
        for idx, row in enumerate(top_agents_query):
            agent_comm = float(row.total_comm)
            agent_share = float(row.total_agent_share or 0.0)
            agent_name = row.fullName

            if row.has_avatar:
                avatar_url = f"/profile/avatar/{row.userID}"
            else:
                avatar_url = f"https://ui-avatars.com/api/?name={agent_name.replace(' ', '+')}&background=random"

            top_agents.append({
                'rank': idx + 1,
                'name': agent_name,
                'position': row.position,
                'deal_count': row.deal_count,
                'total_commission': format_currency(agent_comm),
                'agent_share': format_currency(agent_share),
                'avatar_url': avatar_url
            })

        # 4. Recent Commissions Ledger (Eager load relationships for speed)
        ledger_base = Transaction.query.options(
            joinedload(Transaction.property_obj),
            joinedload(Transaction.customer).joinedload(Customer.user),
            joinedload(Transaction.employee).joinedload(Employee.user)
        )

        if start_date and end_date:
            ledger_base = ledger_base.filter(Transaction.transactionDate >= start_date, Transaction.transactionDate < end_date)

        ledger_query = ledger_base.order_by(Transaction.transactionDate.desc()).all()

        ledger = []
        for t in ledger_query:
            comm_val = float(t.commissionAmount)
            row_split = float(t.agentCommissionRate or 30.0)
            agent_share_val = comm_val * (row_split / 100.0)

            is_paid = t.paymentStatus == 'Closed'

            ledger.append({
                'id': f"TX-{t.transactionID}",
                'raw_id': t.transactionID,
                'property_title': t.property_obj.title,
                'agent_name': t.employee.user.fullName if t.employee else 'N/A',
                'agent_position': t.employee.position if t.employee else 'Agent',
                'client_name': t.customer.user.fullName if t.customer else 'N/A',
                'type': t.transactionType,
                'final_price': float(t.finalPrice),
                'final_price_formatted': format_currency(float(t.finalPrice)),
                'commission_rate': f"{float(t.commissionRate):.1f}%",
                'commission_amount': comm_val,
                'commission_amount_formatted': format_currency(comm_val),
                'agent_share': agent_share_val,
                'agent_share_formatted': format_currency(agent_share_val),
                'status': 'Closed' if t.paymentStatus == 'Closed' else 'Escrow' if t.paymentStatus == 'Escrow' else 'Legal' if t.paymentStatus == 'Legal' else 'Cancelled',
                'is_paid': is_paid,
                'date': t.transactionDate.strftime('%b %d, %Y')
            })

        # 5. Agency Operations Expense (Mocked)
        mock_expenses = [
            {
                'id': 'EXP-801',
                'item': 'LebEstates Premium CRM Server Hosting',
                'category': 'Software',
                'amount': 450.00,
                'amount_formatted': format_currency(450.00),
                'status': 'Paid',
                'date': 'Jun 15, 2026'
            },
            {
                'id': 'EXP-802',
                'item': 'Beirut Office Rent - Q2',
                'category': 'Office Rent',
                'amount': 3500.00,
                'amount_formatted': format_currency(3500.00),
                'status': 'Paid',
                'date': 'Jun 01, 2026'
            },
            {
                'id': 'EXP-803',
                'item': 'Targeted Social Media Ads (Beirut Penthouses)',
                'category': 'Marketing',
                'amount': 1200.00,
                'amount_formatted': format_currency(1200.00),
                'status': 'Paid',
                'date': 'May 28, 2026'
            },
            {
                'id': 'EXP-804',
                'item': 'Legal Contract Drafting Fees',
                'category': 'Legal',
                'amount': 600.00,
                'amount_formatted': format_currency(600.00),
                'status': 'Paid',
                'date': 'May 14, 2026'
            },
            {
                'id': 'EXP-805',
                'item': 'Office Supplies & Coffee Bar Stock',
                'category': 'Office Supplies',
                'amount': 250.00,
                'amount_formatted': format_currency(250.00),
                'status': 'Pending',
                'date': 'Jun 18, 2026'
            }
        ]

        filter_meta = {
            'period_type': period_type,
            'selected_year': selected_year,
            'selected_month': selected_month,
            'available_years': available_years
        }

        return {
            'kpis': kpis,
            'top_agents': top_agents,
            'ledger': ledger,
            'expenses': mock_expenses,
            'filter_meta': filter_meta
        }
