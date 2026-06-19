from datetime import datetime
from sqlalchemy import func
from app.models.base import db
from app.models.operations import Transaction
from app.models.property import Property
from app.models.customer import Customer
from app.models.hr import Employee, CommissionSetting
from app.models.users import Users
from sqlalchemy.orm import joinedload

class CommissionService:
    @staticmethod
    def get_commissions_dashboard_data():
        """
        Dynamically calculates commission stats, agent leaderboard,
        recent commissions ledger, and mock operations expenses.
        """
        # 1. Fetch Agent Split Setting
        agent_split_setting = CommissionSetting.query.filter_by(commissionType='agent_split').first()
        agent_split = float(agent_split_setting.ratePercentage) if agent_split_setting else 30.0

        # Helper formatter
        def format_currency(val):
            return f"${val:,.2f}"

        # 2. Compute KPI Metrics
        # Total Commission Volume: Sum of commissionAmount for all non-cancelled transactions
        total_comm_volume = float(db.session.query(func.sum(Transaction.commissionAmount)).filter(
            Transaction.paymentStatus != 'Cancelled'
        ).scalar() or 0.0)

        # Ready for Payout: Sum of agent's split for Closed transactions
        ready_for_payout_agent_share = float(db.session.query(
            func.sum(Transaction.commissionAmount * (func.coalesce(Transaction.agentCommissionRate, 30.0) / 100.0))
        ).filter(
            Transaction.paymentStatus == 'Closed'
        ).scalar() or 0.0)

        # Average Commission Rate: Average of commissionRate for 'Sell' transactions
        avg_comm_rate = db.session.query(func.avg(Transaction.commissionRate)).filter(
            Transaction.transactionType == 'Sell',
            Transaction.paymentStatus != 'Cancelled'
        ).scalar() or 3.80

        # Active Sales Agents with Closed Transactions
        active_agents_count = db.session.query(func.count(func.distinct(Transaction.employeeID))).filter(
            Transaction.paymentStatus != 'Cancelled'
        ).scalar() or 0

        # Compile KPIs
        kpis = {
            'total_commission_volume': format_currency(total_comm_volume),
            'ready_for_payout': format_currency(ready_for_payout_agent_share),
            'avg_commission_rate': f"{float(avg_comm_rate):.2f}%",
            'active_agents': active_agents_count,
            'agent_split': f"{agent_split:.0f}%"
        }

        # 3. Top Performing Agents (Top 3 active employees by closed commission)
        top_agents_query = db.session.query(
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
         .filter(Transaction.paymentStatus == 'Closed')\
         .group_by(Employee.employeeID, Users.userID, Users.fullName, Employee.position, Users.avatar)\
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
        ledger_query = Transaction.query.options(
            joinedload(Transaction.property_obj),
            joinedload(Transaction.customer).joinedload(Customer.user),
            joinedload(Transaction.employee).joinedload(Employee.user)
        ).order_by(Transaction.transactionDate.desc()).all()

        ledger = []
        for t in ledger_query:
            comm_val = float(t.commissionAmount)
            row_split = float(t.agentCommissionRate or 30.0)
            agent_share_val = comm_val * (row_split / 100.0)

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
                'date': t.transactionDate.strftime('%b %d, %Y')
            })

        # 5. Agency Operations Expense (Mocked)
        # Emulating the operations expense ledger since there is no database table for general office expenses.
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

        return {
            'kpis': kpis,
            'top_agents': top_agents,
            'ledger': ledger,
            'expenses': mock_expenses
        }
