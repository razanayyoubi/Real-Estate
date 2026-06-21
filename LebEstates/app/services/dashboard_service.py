from app.models.base import db
from app.models.property import Property
from app.models.users import Users, AuditLog
from app.models.operations import Visit, Consultation, Transaction
from datetime import datetime, timedelta
from sqlalchemy import func

class DashboardService:
    @staticmethod
    def get_admin_employee_stats():
        """Fetch dynamic statistics and charts for Admin and Employee dashboards."""
        now = datetime.now()
        thirty_days_ago = now - timedelta(days=30)
        
        # 1. Total Properties & Growth
        total_properties = Property.query.count()
        old_properties = Property.query.filter(Property.createdAt < thirty_days_ago).count()
        prop_growth = ((total_properties - old_properties) / old_properties * 100) if old_properties > 0 else 100.0
        if total_properties > 0 and old_properties == 0:
            prop_growth = 100.0
            
        # 2. Total Users & Growth
        total_users = Users.query.count()
        old_users = Users.query.filter(Users.createdAt < thirty_days_ago).count()
        user_growth = ((total_users - old_users) / old_users * 100) if old_users > 0 else 100.0
        if total_users > 0 and old_users == 0:
            user_growth = 100.0
            
        # 3. Consultations & Growth
        total_consultations = Consultation.query.count()
        old_consultations = Consultation.query.filter(Consultation.createdAt < thirty_days_ago).count()
        cons_growth = ((total_consultations - old_consultations) / old_consultations * 100) if old_consultations > 0 else 100.0
        if total_consultations > 0 and old_consultations == 0:
            cons_growth = 100.0
            
        # 4. Scheduled Visits
        scheduled_visits = Visit.query.filter_by(status='Scheduled').count()
        
        # 5. Total Transactions
        total_transactions = Transaction.query.count()
        
        # 6. Pending Requests (Pending Properties + Pending Consultations)
        pending_properties = Property.query.filter_by(status='Pending').count()
        pending_consultations = Consultation.query.filter_by(status='Pending').count()
        pending_requests = pending_properties + pending_consultations
        
        # 7. Distribution Donut Chart (Inventory by Property Type)
        types_query = db.session.query(Property.propertyType, func.count(Property.propertyID))\
                                .group_by(Property.propertyType).all()
        inventory_distribution = {}
        for prop_type, count in types_query:
            inventory_distribution[prop_type] = count
            
        # 8. Today's/Upcoming Schedule (Limit 5)
        upcoming_schedule = Visit.query.filter(Visit.status == 'Scheduled')\
                                      .order_by(Visit.visitDate.asc(), Visit.visitTime.asc())\
                                      .limit(5).all()
                                      
        # 9. Top Regions (Limit 4)
        regions_query = db.session.query(Property.location, func.count(Property.propertyID))\
                                  .group_by(Property.location)\
                                  .order_by(func.count(Property.propertyID).desc())\
                                  .limit(4).all()
        total_props = total_properties or 1
        regions = []
        for loc, count in regions_query:
            regions.append({
                'name': loc,
                'count': count,
                'percentage': round((count / total_props) * 100)
            })
            
        # 10. Recent Activity (Limit 4)
        recent_activity = AuditLog.query.order_by(AuditLog.createdAt.desc()).limit(4).all()
        
        # 11. Weekly Transaction Volume for Chart (Last 10 Weeks)
        weekly_volume = []
        for i in range(9, -1, -1):
            start_date = now - timedelta(weeks=i+1)
            end_date = now - timedelta(weeks=i)
            vol = db.session.query(func.sum(Transaction.finalPrice))\
                            .filter(Transaction.transactionDate >= start_date)\
                            .filter(Transaction.transactionDate < end_date).scalar() or 0
            weekly_volume.append({
                'week_num': 10 - i,
                'volume_k': round(float(vol) / 1000, 1),
                'label': f"W{10-i}"
            })
            
        return {
            'total_properties': total_properties,
            'prop_growth': round(prop_growth, 1),
            'total_users': total_users,
            'user_growth': round(user_growth, 1),
            'total_consultations': total_consultations,
            'cons_growth': round(cons_growth, 1),
            'scheduled_visits': scheduled_visits,
            'total_transactions': total_transactions,
            'pending_requests': pending_requests,
            'inventory_distribution': inventory_distribution,
            'upcoming_schedule': upcoming_schedule,
            'regions': regions,
            'recent_activity': recent_activity,
            'weekly_volume': weekly_volume
        }
        
    @staticmethod
    def get_accountant_stats():
        """Fetch dynamic statistics and charts for Accountant dashboard."""
        now = datetime.now()
        thirty_days_ago = now - timedelta(days=30)
        
        transactions = Transaction.query.all()
        
        # 1. Gross Volume
        gross_volume = sum(float(t.finalPrice) for t in transactions)
        
        # 2. Company Revenue
        company_revenue = sum(float(t.commissionAmount) for t in transactions)
        
        # 3. Agent Commissions Paid
        commissions_paid = sum(float(t.commissionAmount) * (float(t.agentCommissionRate) / 100.0) for t in transactions)
        
        # 4. Net Profit
        net_profit = company_revenue - commissions_paid
        
        # 5. Growth Rates (Compare against prior 30 days)
        old_transactions = Transaction.query.filter(Transaction.transactionDate < thirty_days_ago).all()
        old_gross_volume = sum(float(t.finalPrice) for t in old_transactions)
        
        if old_gross_volume > 0:
            volume_growth = ((gross_volume - old_gross_volume) / old_gross_volume) * 100
        else:
            volume_growth = 100.0 if gross_volume > 0 else 0.0
            
        # 6. Sales vs Rental Distribution
        sales_count = Transaction.query.filter_by(transactionType='Sell').count()
        rental_count = Transaction.query.filter_by(transactionType='Rent').count()
        total_deals = sales_count + rental_count
        sales_pct = round((sales_count / total_deals * 100)) if total_deals > 0 else 70
        rental_pct = round((rental_count / total_deals * 100)) if total_deals > 0 else 30
        
        # 7. Recent Audit Log (Last 4 Transactions)
        recent_audits = Transaction.query.order_by(Transaction.transactionDate.desc()).limit(4).all()
        
        # 8. Monthly Net Profit Trend for Chart (Last 4 Weeks)
        weekly_net_profit = []
        for i in range(3, -1, -1):
            start_date = now - timedelta(weeks=i+1)
            end_date = now - timedelta(weeks=i)
            week_trans = Transaction.query.filter(Transaction.transactionDate >= start_date)\
                                          .filter(Transaction.transactionDate < end_date).all()
            week_rev = sum(float(t.commissionAmount) for t in week_trans)
            week_comm = sum(float(t.commissionAmount) * (float(t.agentCommissionRate) / 100.0) for t in week_trans)
            week_profit = week_rev - week_comm
            weekly_net_profit.append({
                'label': f"Week {4-i}",
                'profit_k': round(week_profit / 1000, 1)
            })
            
        return {
            'gross_volume': gross_volume,
            'company_revenue': company_revenue,
            'commissions_paid': commissions_paid,
            'net_profit': net_profit,
            'volume_growth': round(volume_growth, 1),
            'sales_count': sales_count,
            'rental_count': rental_count,
            'sales_pct': sales_pct,
            'rental_pct': rental_pct,
            'recent_audits': recent_audits,
            'weekly_net_profit': weekly_net_profit
        }
