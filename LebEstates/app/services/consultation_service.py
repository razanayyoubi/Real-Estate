from datetime import datetime
from app.models.base import db
from app.models.customer import Customer
from app.models.operations import Consultation
from app.models.hr import Employee
from app.models.users import Users

def request_consultation(user_id, data):
    """
    Handle requesting a consultation by a user or staff member on behalf of a customer.
    """
    from app.models.users import Users
    user = Users.query.get(user_id)
    on_behalf_customer_id = data.get('on_behalf_customer_id')

    if user and user.role and user.role.roleName.lower() in ['admin', 'employee', 'supervisor']:
        if on_behalf_customer_id:
            customer = Customer.query.get(int(on_behalf_customer_id))
            if not customer:
                return {'success': False, 'message': 'Selected customer was not found.', 'code': 404}
        else:
            # Fallback if staff user is also registered as customer
            customer = Customer.query.filter_by(userID=user_id).first()
            if not customer:
                return {'success': False, 'message': 'Please select a customer to create a consultation.', 'code': 400}
    else:
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
        db.session.flush()

        from app.models.users import AuditLog
        AuditLog.log_action(
            action='ADD',
            table_name='consultation',
            record_id=new_consultation.consultationID,
            description=f"Requested new consultation #{new_consultation.consultationID} (Type: '{consult_type}', Method: '{contact_method}')",
            user_id=user_id
        )
        db.session.commit()
        
        # Send notifications & emails (wrapped)
        try:
            from app.services.notification_service import NotificationService
            from app.services.email_service import EmailService
            from app.models.users import Users, Role
            
            # 1. Notify Customer
            NotificationService.create_notification(
                user_id=user_id,
                message=f"Your consultation request for '{consult_type}' has been submitted. Our team will coordinate with you shortly.",
                action_url="/dashboard"
            )

            cust_user = customer.user
            if cust_user and cust_user.email:
                date_display = pref_date_str if pref_date_str else "To Be Scheduled"
                time_display = pref_time_str if pref_time_str else "To Be Coordinated"
                EmailService.send_templated_email(
                    recipient=cust_user.email,
                    feature_key='ConsultationBooked',
                    default_template_key='CONS-BOOKED-V1',
                    placeholders={
                        'CustomerName': cust_user.fullName,
                        'ConsultationType': consult_type,
                        'ScheduledDate': date_display,
                        'ScheduledTime': time_display,
                        'PreferredMethod': contact_method or 'Office / Phone'
                    },
                    fallback_subject=f"Consultation Confirmed: {consult_type}",
                    fallback_body=f"Hello {cust_user.fullName}, your consultation request for '{consult_type}' has been received and confirmed.",
                    email_type="ConsultationBooked",
                    user_id=user_id
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
    def get_consultations_list_data(filters=None, page=1, per_page=10):
        """
        Fetch consultations with server-side filtering, 10-per-page pagination, stats, active employees, and recent notes.
        """
        import math
        query = Consultation.query

        if filters:
            q = filters.get('server_q', '').strip()
            if q:
                from sqlalchemy import or_
                query = query.outerjoin(Customer, Consultation.customerID == Customer.customerID).outerjoin(Users, Customer.userID == Users.userID).filter(or_(
                    Consultation.consultationType.ilike(f'%{q}%'),
                    Consultation.preferredMethod.ilike(f'%{q}%'),
                    Users.fullName.ilike(f'%{q}%'),
                    Consultation.notes.ilike(f'%{q}%')
                ))

            status = filters.get('status', 'All').strip()
            if status and status.lower() != 'all':
                query = query.filter(Consultation.status.ilike(status))

            consultant_id = filters.get('consultant_id')
            if consultant_id:
                if str(consultant_id).lower() == 'unassigned':
                    query = query.filter(Consultation.assignedEmployeeID == None)
                elif str(consultant_id).lower() != 'all':
                    query = query.filter(Consultation.assignedEmployeeID == int(consultant_id))

            method = filters.get('method', 'All').strip()
            if method and method.lower() != 'all':
                query = query.filter(Consultation.preferredMethod.ilike(method))

        total_filtered_count = query.count()
        total_pages = max(1, math.ceil(total_filtered_count / per_page))
        current_page = max(1, min(page, total_pages))

        consultations = query.order_by(Consultation.createdAt.desc()).offset((current_page - 1) * per_page).limit(per_page).all()

        total_requests = Consultation.query.count()
        today_date = datetime.now().date()
        
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
            'recent_notes': recent_notes,
            'page': current_page,
            'per_page': per_page,
            'total_pages': total_pages,
            'total_filtered_count': total_filtered_count
        }

    @staticmethod
    def get_customer_details(customer_id):
        customer = Customer.query.get(customer_id)
        if not customer:
            return None
        user = customer.user
        total_consultations = Consultation.query.filter_by(customerID=customer_id).count()
        return {
            'customerID': customer.customerID,
            'fullName': user.fullName if user else 'N/A',
            'email': user.email if user else 'N/A',
            'phone': user.phoneNumber if user else 'N/A',
            'location': customer.address or 'Not specified',
            'created_at': user.createdAt.strftime('%b %d, %Y') if (user and user.createdAt) else 'N/A',
            'total_consultations': total_consultations
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
            old_status = consultation.status
            consultation.status = new_status
            consultation.updatedAt = datetime.now()

            from app.models.users import AuditLog
            AuditLog.log_action(
                action='EDIT',
                table_name='consultation',
                record_id=consultation_id,
                description=f"Updated status of consultation #{consultation_id} ('{consultation.consultationType}') from '{old_status}' to '{new_status}'"
            )
            db.session.commit()
            
            # Send notifications & emails (wrapped)
            try:
                from app.services.notification_service import NotificationService
                from app.services.email_service import EmailService
                cust_user = consultation.customer.user if (consultation.customer and consultation.customer.user) else None
                if cust_user:
                    NotificationService.create_notification(
                        user_id=cust_user.userID,
                        message=f"Your consultation request '{consultation.consultationType}' status has been updated to: {new_status}.",
                        action_url="/dashboard"
                    )

                    if cust_user.email:
                        date_str = consultation.scheduledDate.strftime('%B %d, %Y') if consultation.scheduledDate else "Not Set"
                        time_str = consultation.scheduledTime.strftime('%I:%M %p') if consultation.scheduledTime else ""
                        EmailService.send_templated_email(
                            recipient=cust_user.email,
                            feature_key='ConsultationStatusChanged',
                            default_template_key='CONS-STATUS-V1',
                            placeholders={
                                'CustomerName': cust_user.fullName,
                                'ConsultationType': consultation.consultationType,
                                'Status': new_status,
                                'ScheduledDate': date_str,
                                'ScheduledTime': time_str
                            },
                            fallback_subject=f"Consultation Update: {consultation.consultationType} ({new_status})",
                            fallback_body=f"Hello {cust_user.fullName}, your consultation for '{consultation.consultationType}' status has been updated to: {new_status}.",
                            email_type="ConsultationStatusChanged",
                            user_id=cust_user.userID
                        )
            except Exception as notif_err:
                print(f"[Warning] Failed to send status update notification/email: {str(notif_err)}")

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

            from app.models.users import AuditLog
            emp_name = employee.user.fullName if (employee_id and employee and employee.user) else "Unassigned"
            AuditLog.log_action(
                action='EDIT',
                table_name='consultation',
                record_id=consultation_id,
                description=f"Assigned consultant '{emp_name}' to consultation #{consultation_id} ('{consultation.consultationType}')"
            )
            db.session.commit()
            
            # Send notifications & emails (wrapped)
            try:
                from app.services.notification_service import NotificationService
                from app.services.email_service import EmailService
                
                cust_user = consultation.customer.user if (consultation.customer and consultation.customer.user) else None
                date_str = consultation.scheduledDate.strftime('%B %d, %Y') if consultation.scheduledDate else "To Be Scheduled"
                time_str = consultation.scheduledTime.strftime('%I:%M %p') if consultation.scheduledTime else "To Be Coordinated"
                method_str = consultation.preferredMethod or "Office / Phone"

                # 1. Notify Employee
                if employee_id and employee and employee.user:
                    NotificationService.create_notification(
                        user_id=employee.userID,
                        message=f"You have been assigned to handle the consultation request for '{consultation.consultationType}' (Customer ID: {consultation.customerID}).",
                        action_url="/control-panel"
                    )

                    if employee.user.email:
                        EmailService.send_templated_email(
                            recipient=employee.user.email,
                            feature_key='ConsultationConsultantAssignedEmployee',
                            default_template_key='CONS-AGENT-EMP-V1',
                            placeholders={
                                'EmployeeName': employee.user.fullName,
                                'CustomerName': cust_user.fullName if cust_user else "Customer",
                                'CustomerEmail': cust_user.email if cust_user else "N/A",
                                'CustomerPhone': cust_user.phoneNumber if cust_user else "N/A",
                                'ConsultationType': consultation.consultationType,
                                'ScheduledDate': date_str,
                                'ScheduledTime': time_str,
                                'Notes': consultation.notes or 'No initial notes'
                            },
                            fallback_subject=f"Consultation Assignment: {consultation.consultationType} with {cust_user.fullName if cust_user else 'Client'}",
                            fallback_body=f"Hello {employee.user.fullName}, you have been assigned to lead an advisory consultation for '{consultation.consultationType}'.",
                            email_type="ConsultationConsultantAssignedEmployee",
                            user_id=employee.userID
                        )
                
                # 2. Notify Customer
                if cust_user:
                    NotificationService.create_notification(
                        user_id=cust_user.userID,
                        message=f"A consultant ({emp_name}) has been assigned to your consultation request '{consultation.consultationType}'.",
                        action_url="/dashboard"
                    )

                    if cust_user.email:
                        EmailService.send_templated_email(
                            recipient=cust_user.email,
                            feature_key='ConsultationConsultantAssignedCustomer',
                            default_template_key='CONS-AGENT-CUST-V1',
                            placeholders={
                                'CustomerName': cust_user.fullName,
                                'ConsultantName': emp_name,
                                'ConsultationType': consultation.consultationType,
                                'ScheduledDate': date_str,
                                'ScheduledTime': time_str,
                                'PreferredMethod': method_str
                            },
                            fallback_subject=f"Advisor Assigned for your Consultation: {consultation.consultationType}",
                            fallback_body=f"Hello {cust_user.fullName}, {emp_name} has been assigned as your advisor for '{consultation.consultationType}'.",
                            email_type="ConsultationConsultantAssignedCustomer",
                            user_id=cust_user.userID
                        )
            except Exception as notif_err:
                print(f"[Warning] Failed to send consultant assignment notifications/emails: {str(notif_err)}")

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

            from app.models.users import AuditLog
            AuditLog.log_action(
                action='EDIT',
                table_name='consultation',
                record_id=consultation_id,
                description=f"Updated schedule for consultation #{consultation_id} ('{consultation.consultationType}') to {consultation.scheduledDate} {consultation.scheduledTime}"
            )
            db.session.commit()
            
            # Send notifications & emails (wrapped)
            try:
                from app.services.notification_service import NotificationService
                from app.services.email_service import EmailService
                cust_user = consultation.customer.user if (consultation.customer and consultation.customer.user) else None
                if cust_user and consultation.scheduledDate:
                    time_display = consultation.scheduledTime.strftime('%I:%M %p') if consultation.scheduledTime else ""
                    date_display = consultation.scheduledDate.strftime('%B %d, %Y')
                    
                    NotificationService.create_notification(
                        user_id=cust_user.userID,
                        message=f"Your consultation request '{consultation.consultationType}' has been scheduled for {date_display} at {time_display}.",
                        action_url="/dashboard"
                    )

                    if cust_user.email:
                        EmailService.send_templated_email(
                            recipient=cust_user.email,
                            feature_key='ConsultationStatusChanged',
                            default_template_key='CONS-STATUS-V1',
                            placeholders={
                                'CustomerName': cust_user.fullName,
                                'ConsultationType': consultation.consultationType,
                                'Status': consultation.status,
                                'ScheduledDate': date_display,
                                'ScheduledTime': time_display
                            },
                            fallback_subject=f"Consultation Scheduled: {consultation.consultationType}",
                            fallback_body=f"Hello {cust_user.fullName}, your consultation session for '{consultation.consultationType}' has been scheduled for {date_display} at {time_display}.",
                            email_type="ConsultationStatusChanged",
                            user_id=cust_user.userID
                        )
            except Exception as notif_err:
                print(f"[Warning] Failed to send schedule update notification/email: {str(notif_err)}")

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

            from app.models.users import AuditLog
            AuditLog.log_action(
                action='EDIT',
                table_name='consultation',
                record_id=consultation_id,
                description=f"Updated consultant notes for consultation #{consultation_id} ('{consultation.consultationType}')"
            )
            db.session.commit()
            return {'success': True, 'message': 'Notes updated successfully'}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'Failed to update notes: {str(e)}', 'code': 500}
