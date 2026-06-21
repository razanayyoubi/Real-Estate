from datetime import datetime
from app.models.base import db
from app.models.customer import Customer
from app.models.operations import Consultation
from app.models.hr import Employee
from app.models.users import Users

def request_consultation(user_id, data):
    """
    Handle requesting a consultation by a user.
    """
    customer = Customer.query.filter_by(userID=user_id).first()
    if not customer:
        return {'success': False, 'message': 'Only registered customers can request consultations.', 'code': 403}

    consult_type = data.get('consult_type')
    contact_method = data.get('contact_method')
    message = data.get('message')
    pref_date_str = data.get('pref_date')
    pref_time_str = data.get('pref_time')

    if not consult_type:
        return {'success': False, 'message': 'Consultation type is required.', 'code': 400}

    try:
        new_consultation = Consultation(
            customerID=customer.customerID,
            consultationType=consult_type,
            preferredMethod=contact_method,
            message=message,
            status='Pending',
            scheduledDate=pref_date_str if pref_date_str else None,
            scheduledTime=pref_time_str if pref_time_str else None
        )
        db.session.add(new_consultation)
        db.session.commit()
        
        # Send notifications (wrapped)
        try:
            from app.services.notification_service import NotificationService
            from app.models.users import Users, Role
            
            # 1. Notify Customer
            NotificationService.create_notification(
                user_id=user_id,
                message=f"Your consultation request for '{consult_type}' has been submitted. Our team will coordinate with you shortly.",
                action_url="/dashboard"
            )
            
            # 2. Notify Staff (admin / employee)
            staff_users = Users.query.join(Role).filter(Role.roleName.in_(['admin', 'employee', 'Admin', 'Employee'])).all()
            for staff in staff_users:
                NotificationService.create_notification(
                    user_id=staff.userID,
                    message=f"New consultation request for '{consult_type}' submitted by customer {customer.user.fullName if customer.user else 'Customer'}.",
                    action_url="/control-panel"
                )
        except Exception as notif_err:
            print(f"[Warning] Failed to send consultation request notifications: {str(notif_err)}")

        return {'success': True, 'message': 'Request Received!', 'code': 201}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'An error occurred while saving your request: {str(e)}', 'code': 500}


class ConsultationService:
    @staticmethod
    def get_consultations_list_data():
        """
        Fetch all consultations, stats, active employees, and recent notes.
        """
        consultations = Consultation.query.order_by(Consultation.createdAt.desc()).all()

        total_requests = len(consultations)
        today_date = datetime.now().date()
        
        # Pending today: scheduled for today and status in ['Pending', 'Scheduled']
        pending_today = Consultation.query.filter(
            Consultation.scheduledDate == today_date,
            Consultation.status.in_(['Pending', 'Scheduled'])
        ).count()
        
        scheduled_consultations = Consultation.query.filter_by(status='Scheduled').count()
        completed_count = Consultation.query.filter_by(status='Completed').count()
        completion_rate = (completed_count / total_requests * 100) if total_requests > 0 else 0.0

        # Fetch all active employees to populate the consultant dropdowns
        employees = Employee.query.join(Users).filter(Employee.status == 'Active').order_by(Users.fullName).all()

        # Fetch 3 recent consultations with non-empty notes
        recent_notes = Consultation.query.filter(
            Consultation.notes != None, 
            Consultation.notes != ''
        ).order_by(Consultation.updatedAt.desc()).limit(3).all()

        return {
            'consultations': consultations,
            'total_requests': total_requests,
            'pending_today': pending_today,
            'scheduled_consultations': scheduled_consultations,
            'completion_rate': completion_rate,
            'employees': employees,
            'recent_notes': recent_notes
        }

    @staticmethod
    def update_status(consultation_id, new_status):
        """
        Update consultation status.
        """
        consultation = Consultation.query.get(consultation_id)
        if not consultation:
            return {'success': False, 'error': 'Consultation not found', 'code': 404}

        if new_status not in ['Pending', 'Scheduled', 'Completed', 'Cancelled']:
            return {'success': False, 'error': 'Invalid status', 'code': 400}

        try:
            consultation.status = new_status
            consultation.updatedAt = datetime.now()
            db.session.commit()
            
            # Send notifications (wrapped)
            try:
                from app.services.notification_service import NotificationService
                cust_user_id = consultation.customer.userID if (consultation.customer and consultation.customer.user) else None
                if cust_user_id:
                    NotificationService.create_notification(
                        user_id=cust_user_id,
                        message=f"Your consultation request '{consultation.consultationType}' status has been updated to: {new_status}.",
                        action_url="/dashboard"
                    )
            except Exception as notif_err:
                print(f"[Warning] Failed to send status update notification: {str(notif_err)}")

            return {'success': True, 'message': 'Status updated successfully'}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'Failed to update status: {str(e)}', 'code': 500}

    @staticmethod
    def update_consultant(consultation_id, employee_id):
        """
        Assign a consultant to a consultation.
        """
        consultation = Consultation.query.get(consultation_id)
        if not consultation:
            return {'success': False, 'error': 'Consultation not found', 'code': 404}

        employee = None
        # employeeID can be null/None if unassigning
        if employee_id:
            employee = Employee.query.get(employee_id)
            if not employee:
                return {'success': False, 'error': 'Employee not found', 'code': 404}
            consultation.assignedEmployeeID = employee_id
        else:
            consultation.assignedEmployeeID = None

        try:
            consultation.updatedAt = datetime.now()
            db.session.commit()
            
            # Send notifications (wrapped)
            try:
                from app.services.notification_service import NotificationService
                
                # 1. Notify Employee
                if employee_id and employee:
                    NotificationService.create_notification(
                        user_id=employee.userID,
                        message=f"You have been assigned to handle the consultation request for '{consultation.consultationType}' (Customer ID: {consultation.customerID}).",
                        action_url="/control-panel"
                    )
                
                # 2. Notify Customer
                cust_user_id = consultation.customer.userID if (consultation.customer and consultation.customer.user) else None
                if cust_user_id:
                    emp_name = employee.user.fullName if (employee_id and employee and employee.user) else "a specialist"
                    NotificationService.create_notification(
                        user_id=cust_user_id,
                        message=f"A consultant ({emp_name}) has been assigned to your consultation request '{consultation.consultationType}'.",
                        action_url="/dashboard"
                    )
            except Exception as notif_err:
                print(f"[Warning] Failed to send consultant assignment notifications: {str(notif_err)}")

            return {'success': True, 'message': 'Consultant updated successfully'}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'Failed to update consultant: {str(e)}', 'code': 500}

    @staticmethod
    def update_schedule(consultation_id, date_str, time_str):
        """
        Set or update scheduled date and time.
        """
        consultation = Consultation.query.get(consultation_id)
        if not consultation:
            return {'success': False, 'error': 'Consultation not found', 'code': 404}

        try:
            if date_str:
                consultation.scheduledDate = datetime.strptime(date_str, '%Y-%m-%d').date()
            else:
                consultation.scheduledDate = None

            if time_str:
                try:
                    consultation.scheduledTime = datetime.strptime(time_str, '%H:%M').time()
                except ValueError:
                    consultation.scheduledTime = datetime.strptime(time_str, '%H:%M:%S').time()
            else:
                consultation.scheduledTime = None

            # Auto transition status to Scheduled if it's currently Pending
            if consultation.status == 'Pending' and consultation.scheduledDate:
                consultation.status = 'Scheduled'

            consultation.updatedAt = datetime.now()
            db.session.commit()
            
            # Send notifications (wrapped)
            try:
                from app.services.notification_service import NotificationService
                cust_user_id = consultation.customer.userID if (consultation.customer and consultation.customer.user) else None
                if cust_user_id and consultation.scheduledDate:
                    NotificationService.create_notification(
                        user_id=cust_user_id,
                        message=f"Your consultation request '{consultation.consultationType}' has been scheduled for {consultation.scheduledDate} at {consultation.scheduledTime}.",
                        action_url="/dashboard"
                    )
            except Exception as notif_err:
                print(f"[Warning] Failed to send schedule update notification: {str(notif_err)}")

            return {'success': True, 'message': 'Schedule updated successfully'}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'Failed to update schedule: {str(e)}', 'code': 500}

    @staticmethod
    def update_notes(consultation_id, notes):
        """
        Update notes.
        """
        consultation = Consultation.query.get(consultation_id)
        if not consultation:
            return {'success': False, 'error': 'Consultation not found', 'code': 404}

        try:
            consultation.notes = notes
            consultation.updatedAt = datetime.now()
            db.session.commit()
            return {'success': True, 'message': 'Notes updated successfully'}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'Failed to update notes: {str(e)}', 'code': 500}
