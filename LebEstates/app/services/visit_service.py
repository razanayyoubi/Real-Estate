from datetime import datetime
from app.models.base import db
from app.models.operations import Visit
from app.models.customer import Customer
from app.models.hr import Employee
from app.models.users import Users

class VisitService:
    @staticmethod
    def schedule_visit(user_id, data):
        """
        Schedule a property visit for a customer.
        """
        customer = Customer.query.filter_by(userID=user_id).first()
        if not customer:
            return {'success': False, 'message': 'Only registered customers can schedule visits.', 'code': 403}

        property_id = data.get('property_id')
        visit_date = data.get('visit_date')
        visit_time = data.get('visit_time')
        notes = data.get('notes', '')

        if not property_id or not visit_date or not visit_time:
            return {'success': False, 'message': 'Property, date, and time are required.', 'code': 400}

        try:
            new_visit = Visit(
                propertyID=property_id,
                customerID=customer.customerID,
                employeeID=None,
                visitDate=visit_date,
                visitTime=visit_time,
                status='Pending',
                notes=notes
            )
            db.session.add(new_visit)
            db.session.flush()

            from app.models.users import AuditLog
            AuditLog.log_action(
                action='ADD',
                table_name='visit',
                record_id=new_visit.visitID,
                description=f"Scheduled property visit #{new_visit.visitID} for property ID {property_id} on {visit_date} at {visit_time}",
                user_id=user_id
            )
            db.session.commit()
            
            # Send notifications (wrapped to prevent errors from breaking main action)
            try:
                from app.services.notification_service import NotificationService
                from app.models.property import Property
                
                prop = Property.query.get(property_id)
                prop_title = prop.title if prop else "Property"
                
                # 1. Notify Customer
                NotificationService.create_notification(
                    user_id=user_id,
                    message=f"Your visit request for property '{prop_title}' on {visit_date} at {visit_time} has been scheduled successfully.",
                    action_url="/dashboard"
                )
            except Exception as notif_err:
                print(f"[Warning] Failed to send visit scheduling notifications: {str(notif_err)}")

            return {'success': True, 'message': 'Visit Scheduled Successfully!', 'code': 201}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'An error occurred while saving your visit: {str(e)}', 'code': 500}

    @staticmethod
    def get_visits_list_data(filters=None):
        """
        Fetch visits with optional server-side filtering, stats, active employees, and recent notes.
        """
        query = Visit.query

        if filters:
            q = filters.get('server_q', '').strip()
            if q:
                from sqlalchemy import or_
                from app.models.property import Property
                query = query.outerjoin(Property).outerjoin(Customer, Visit.customerID == Customer.customerID).outerjoin(Users, Customer.userID == Users.userID).filter(or_(
                    Property.title.ilike(f'%{q}%'),
                    Property.location.ilike(f'%{q}%'),
                    Users.fullName.ilike(f'%{q}%'),
                    Visit.notes.ilike(f'%{q}%')
                ))

            status = filters.get('status', 'All').strip()
            if status and status.lower() != 'all':
                query = query.filter(Visit.status.ilike(status))

            consultant_id = filters.get('consultant_id')
            if consultant_id and str(consultant_id).lower() != 'all':
                query = query.filter(Visit.employeeID == int(consultant_id))

        visits = query.order_by(Visit.visitDate.desc(), Visit.visitTime.desc()).all()

        total_requests = Visit.query.count()
        today_date = datetime.now().date()
        pending_today = Visit.query.filter(Visit.visitDate == today_date, Visit.status == 'Scheduled').count()
        confirmed_visits = Visit.query.filter_by(status='Scheduled').count()
        completed_count = Visit.query.filter_by(status='Completed').count()
        completion_rate = (completed_count / total_requests * 100) if total_requests > 0 else 0.0

        # Fetch all active employees to populate the consultant dropdowns
        employees = Employee.query.join(Users).filter(Employee.status == 'Active').order_by(Users.fullName).all()

        # Fetch 3 recent visits with non-empty notes
        recent_notes = Visit.query.filter(Visit.notes != None, Visit.notes != '').order_by(Visit.updatedAt.desc()).limit(3).all()

        return {
            'visits': visits,
            'total_requests': total_requests,
            'pending_today': pending_today,
            'confirmed_visits': confirmed_visits,
            'completion_rate': completion_rate,
            'employees': employees,
            'recent_notes': recent_notes
        }

    @staticmethod
    def update_status(visit_id, new_status):
        """
        Update visit status.
        """
        visit = Visit.query.get(visit_id)
        if not visit:
            return {'success': False, 'error': 'Visit not found', 'code': 404}

        if new_status not in ['Scheduled', 'Completed', 'Cancelled']:
            return {'success': False, 'error': 'Invalid status', 'code': 400}

        try:
            old_status = visit.status
            visit.status = new_status
            visit.updatedAt = datetime.now()

            from app.models.users import AuditLog
            prop_title = visit.property_obj.title if visit.property_obj else f"ID {visit.propertyID}"
            AuditLog.log_action(
                action='EDIT',
                table_name='visit',
                record_id=visit_id,
                description=f"Updated status of visit #{visit_id} for '{prop_title}' from '{old_status}' to '{new_status}'"
            )
            db.session.commit()
            
            # Send notifications (wrapped)
            try:
                from app.services.notification_service import NotificationService
                cust_user_id = visit.customer.userID if (visit.customer and visit.customer.user) else None
                if cust_user_id:
                    NotificationService.create_notification(
                        user_id=cust_user_id,
                        message=f"The status of your visit request for property '{prop_title}' on {visit.visitDate} has been updated to: {new_status}.",
                        action_url="/dashboard"
                    )
            except Exception as notif_err:
                print(f"[Warning] Failed to send status update notification: {str(notif_err)}")

            return {'success': True, 'message': 'Visit status updated successfully'}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'Failed to update status: {str(e)}', 'code': 500}

    @staticmethod
    def update_consultant(visit_id, employee_id):
        """
        Assign a consultant to a visit.
        """
        visit = Visit.query.get(visit_id)
        if not visit:
            return {'success': False, 'error': 'Visit not found', 'code': 404}

        employee = Employee.query.get(employee_id)
        if not employee:
            return {'success': False, 'error': 'Employee not found', 'code': 404}

        try:
            visit.employeeID = employee_id
            visit.updatedAt = datetime.now()

            from app.models.users import AuditLog
            prop_title = visit.property_obj.title if visit.property_obj else f"ID {visit.propertyID}"
            emp_name = employee.user.fullName if (employee and employee.user) else f"ID {employee_id}"
            AuditLog.log_action(
                action='EDIT',
                table_name='visit',
                record_id=visit_id,
                description=f"Assigned consultant '{emp_name}' to visit #{visit_id} for property '{prop_title}'"
            )
            db.session.commit()
            
            # Send notifications (wrapped)
            try:
                from app.services.notification_service import NotificationService
                
                # 1. Notify Employee
                if employee:
                    NotificationService.create_notification(
                        user_id=employee.userID,
                        message=f"You have been assigned as the consultant for a visit to property '{prop_title}' on {visit.visitDate} at {visit.visitTime}.",
                        action_url="/control-panel/visits"
                    )
                
                # 2. Notify Customer
                cust_user_id = visit.customer.userID if (visit.customer and visit.customer.user) else None
                if cust_user_id:
                    NotificationService.create_notification(
                        user_id=cust_user_id,
                        message=f"A consultant ({emp_name}) has been assigned to guide you through your visit for property '{prop_title}' on {visit.visitDate} at {visit.visitTime}.",
                        action_url="/dashboard"
                    )
            except Exception as notif_err:
                print(f"[Warning] Failed to send consultant assignment notifications: {str(notif_err)}")

            return {'success': True, 'message': 'Consultant assigned successfully'}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'Failed to update consultant: {str(e)}', 'code': 500}
