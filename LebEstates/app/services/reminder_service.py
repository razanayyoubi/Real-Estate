import logging
from datetime import datetime, timedelta, date, time
from app.models.base import db
from app.models.operations import Visit, Consultation, Transaction
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)

class ReminderService:
    @staticmethod
    def process_all_reminders(app=None):
        """
        Executes all automated background reminder checks across:
        1. Property Visits (24h before, 1h before, 2h post-visit feedback)
        2. Consultations (1h before, 1d post-consultation CSAT survey)
        3. Payment Schedules (7d before due, 3d before due, 1d overdue, 7d overdue escalation)
        """
        results = {
            'visits_24h': 0,
            'visits_1h': 0,
            'visits_feedback_2h': 0,
            'consultations_1h': 0,
            'consultations_survey_1d': 0,
            'payments_7d': 0,
            'payments_3d': 0,
            'payments_overdue_1d': 0,
            'payments_overdue_7d': 0
        }

        try:
            results['visits_24h'] = ReminderService.process_visit_reminders_24h()
            results['visits_1h'] = ReminderService.process_visit_reminders_1h()
            results['visits_feedback_2h'] = ReminderService.process_visit_feedback_2h()
            results['consultations_1h'] = ReminderService.process_consultation_reminders_1h()
            results['consultations_survey_1d'] = ReminderService.process_consultation_survey_1d()
            results['payments_7d'] = ReminderService.process_payment_reminders_7d()
            results['payments_3d'] = ReminderService.process_payment_reminders_3d()
            results['payments_overdue_1d'] = ReminderService.process_payment_overdue_1d()
            results['payments_overdue_7d'] = ReminderService.process_payment_overdue_7d()
            logger.info(f"Completed reminder check cycle: {results}")
        except Exception as e:
            logger.error(f"Error executing ReminderService.process_all_reminders: {e}")

        return results

    # ---------------------------------------------------------
    # 1. PROPERTY VISIT REMINDERS
    # ---------------------------------------------------------
    @staticmethod
    def process_visit_reminders_24h():
        """
        Visits scheduled ~24 hours from now (status='Scheduled').
        Sent to Customer and Assigned Employee.
        """
        count = 0
        now = datetime.now()
        target_date = (now + timedelta(days=1)).date()
        
        # Look for scheduled visits on target date
        visits = Visit.query.filter(
            Visit.status == 'Scheduled',
            Visit.visitDate == target_date
        ).all()

        for visit in visits:
            log_token = f"VISIT_REMIND_24H_V{visit.visitID}_{visit.visitDate}"
            prop_title = visit.property_obj.title if visit.property_obj else f"Property #{visit.propertyID}"
            prop_loc = visit.property_obj.location if visit.property_obj else "Lebanon"
            prop_addr = visit.property_obj.address if visit.property_obj else prop_loc
            time_str = visit.visitTime.strftime('%I:%M %p') if visit.visitTime else "Scheduled Time"
            date_str = visit.visitDate.strftime('%B %d, %Y')

            cust_user = visit.customer.user if (visit.customer and visit.customer.user) else None
            emp_user = visit.employee.user if (visit.employee and visit.employee.user) else None

            # 1. Email Customer
            if cust_user and cust_user.email:
                cust_placeholders = {
                    'RecipientName': cust_user.fullName,
                    'CustomerName': cust_user.fullName,
                    'PropertyTitle': prop_title,
                    'VisitDate': date_str,
                    'VisitTime': time_str,
                    'Address': prop_addr,
                    'ConsultantName': emp_user.fullName if emp_user else "LebEstates Agent",
                    'OtherPartyName': emp_user.fullName if emp_user else "LebEstates Agent",
                    'Role': 'Customer'
                }
                sent = EmailService.send_templated_email(
                    recipient=cust_user.email,
                    feature_key='VisitReminder24h',
                    default_template_key='VISIT-REMIND-24H',
                    placeholders=cust_placeholders,
                    fallback_subject=f"Reminder: Property Visit for {prop_title} Tomorrow at {time_str}",
                    fallback_body=f"Hello {cust_user.fullName}, this is a reminder for your upcoming visit tomorrow ({date_str} at {time_str}) for {prop_title}.",
                    email_type="VisitReminder24h",
                    log_token=f"{log_token}_CUST"
                )
                if sent:
                    count += 1

            # 2. Email Assigned Employee
            if emp_user and emp_user.email:
                emp_placeholders = {
                    'RecipientName': emp_user.fullName,
                    'EmployeeName': emp_user.fullName,
                    'PropertyTitle': prop_title,
                    'VisitDate': date_str,
                    'VisitTime': time_str,
                    'Address': prop_addr,
                    'CustomerName': cust_user.fullName if cust_user else "Customer",
                    'OtherPartyName': cust_user.fullName if cust_user else "Customer",
                    'Role': 'Consultant / Agent'
                }
                EmailService.send_templated_email(
                    recipient=emp_user.email,
                    feature_key='VisitReminder24h',
                    default_template_key='VISIT-REMIND-24H',
                    placeholders=emp_placeholders,
                    fallback_subject=f"Staff Reminder: Scheduled Viewing for {prop_title} Tomorrow at {time_str}",
                    fallback_body=f"Hello {emp_user.fullName}, you have a scheduled viewing tomorrow ({date_str} at {time_str}) for {prop_title}.",
                    email_type="VisitReminder24h",
                    log_token=f"{log_token}_EMP"
                )

        return count

    @staticmethod
    def process_visit_reminders_1h():
        """
        Visits scheduled ~1 hour from now (status='Scheduled', same day, within 45 to 75 minutes).
        Sent to Customer and Assigned Employee.
        """
        count = 0
        now = datetime.now()
        today = now.date()
        visits = Visit.query.filter(
            Visit.status == 'Scheduled',
            Visit.visitDate == today
        ).all()

        for visit in visits:
            if not visit.visitTime:
                continue
            visit_dt = datetime.combine(visit.visitDate, visit.visitTime)
            diff_mins = (visit_dt - now).total_seconds() / 60.0

            # Window: between 20 minutes and 90 minutes ahead
            if 20 <= diff_mins <= 90:
                log_token = f"VISIT_REMIND_1H_V{visit.visitID}_{visit.visitDate}_{visit.visitTime.strftime('%H%M')}"
                prop_title = visit.property_obj.title if visit.property_obj else f"Property #{visit.propertyID}"
                prop_loc = visit.property_obj.location if visit.property_obj else "Lebanon"
                prop_addr = visit.property_obj.address if visit.property_obj else prop_loc
                time_str = visit.visitTime.strftime('%I:%M %p')
                date_str = visit.visitDate.strftime('%B %d, %Y')

                cust_user = visit.customer.user if (visit.customer and visit.customer.user) else None
                emp_user = visit.employee.user if (visit.employee and visit.employee.user) else None

                # Email Customer
                if cust_user and cust_user.email:
                    cust_placeholders = {
                        'RecipientName': cust_user.fullName,
                        'CustomerName': cust_user.fullName,
                        'PropertyTitle': prop_title,
                        'VisitDate': date_str,
                        'VisitTime': time_str,
                        'Address': prop_addr,
                        'ConsultantName': emp_user.fullName if emp_user else "LebEstates Agent",
                        'OtherPartyName': emp_user.fullName if emp_user else "LebEstates Agent"
                    }
                    sent = EmailService.send_templated_email(
                        recipient=cust_user.email,
                        feature_key='VisitReminder1h',
                        default_template_key='VISIT-REMIND-1H',
                        placeholders=cust_placeholders,
                        fallback_subject=f"1-Hour Reminder: Visit for {prop_title} today at {time_str}",
                        fallback_body=f"Hello {cust_user.fullName}, your visit for {prop_title} starts in 1 hour at {time_str}.",
                        email_type="VisitReminder1h",
                        log_token=f"{log_token}_CUST"
                    )
                    if sent:
                        count += 1

                # Email Employee
                if emp_user and emp_user.email:
                    emp_placeholders = {
                        'RecipientName': emp_user.fullName,
                        'EmployeeName': emp_user.fullName,
                        'PropertyTitle': prop_title,
                        'VisitDate': date_str,
                        'VisitTime': time_str,
                        'Address': prop_addr,
                        'CustomerName': cust_user.fullName if cust_user else "Customer",
                        'OtherPartyName': cust_user.fullName if cust_user else "Customer"
                    }
                    EmailService.send_templated_email(
                        recipient=emp_user.email,
                        feature_key='VisitReminder1h',
                        default_template_key='VISIT-REMIND-1H',
                        placeholders=emp_placeholders,
                        fallback_subject=f"1-Hour Reminder: Assigned Viewing for {prop_title} today at {time_str}",
                        fallback_body=f"Hello {emp_user.fullName}, your assigned viewing for {prop_title} starts in 1 hour.",
                        email_type="VisitReminder1h",
                        log_token=f"{log_token}_EMP"
                    )

        return count

    @staticmethod
    def process_visit_feedback_2h():
        """
        Sent to customer 2 hours after visit completion (status='Completed') to gather feedback.
        """
        count = 0
        now = datetime.now()
        two_hours_ago = now - timedelta(hours=2)
        
        # Check visits completed today or recently
        visits = Visit.query.filter(
            Visit.status == 'Completed'
        ).all()

        for visit in visits:
            # Estimate completion timestamp from updatedAt or visitDate + visitTime + 1 hour
            completion_dt = visit.updatedAt or datetime.combine(visit.visitDate, visit.visitTime or time(12, 0)) + timedelta(hours=1)
            time_since_completed = (now - completion_dt).total_seconds() / 3600.0

            # Window: completed between 1.5 and 48 hours ago
            if 1.5 <= time_since_completed <= 48.0:
                log_token = f"VISIT_FEEDBACK_2H_V{visit.visitID}"
                cust_user = visit.customer.user if (visit.customer and visit.customer.user) else None
                if cust_user and cust_user.email:
                    prop_title = visit.property_obj.title if visit.property_obj else f"Property #{visit.propertyID}"
                    feedback_url = "http://127.0.0.1:5000/dashboard"
                    placeholders = {
                        'CustomerName': cust_user.fullName,
                        'PropertyTitle': prop_title,
                        'FeedbackUrl': feedback_url
                    }
                    sent = EmailService.send_templated_email(
                        recipient=cust_user.email,
                        feature_key='VisitFeedback2h',
                        default_template_key='VISIT-FEEDBACK-2H',
                        placeholders=placeholders,
                        fallback_subject=f"How was your visit to {prop_title}? We'd love your feedback",
                        fallback_body=f"Hello {cust_user.fullName}, thank you for touring {prop_title}. We value your experience! Visit your dashboard to share feedback.",
                        email_type="VisitFeedback2h",
                        log_token=log_token
                    )
                    if sent:
                        count += 1

        return count

    # ---------------------------------------------------------
    # 2. CONSULTATION REMINDERS
    # ---------------------------------------------------------
    @staticmethod
    def process_consultation_reminders_1h():
        """
        1 hour before scheduled consultation time: Sent to customer and consultant.
        """
        count = 0
        now = datetime.now()
        today = now.date()
        consultations = Consultation.query.filter(
            Consultation.status == 'Scheduled',
            Consultation.scheduledDate == today
        ).all()

        for cons in consultations:
            if not cons.scheduledTime:
                continue
            cons_dt = datetime.combine(cons.scheduledDate, cons.scheduledTime)
            diff_mins = (cons_dt - now).total_seconds() / 60.0

            if 20 <= diff_mins <= 90:
                log_token = f"CONS_REMIND_1H_C{cons.consultationID}_{cons.scheduledDate}_{cons.scheduledTime.strftime('%H%M')}"
                cust_user = cons.customer.user if (cons.customer and cons.customer.user) else None
                emp_user = cons.employee.user if (cons.employee and cons.employee.user) else None
                time_str = cons.scheduledTime.strftime('%I:%M %p')
                date_str = cons.scheduledDate.strftime('%B %d, %Y')
                method_str = cons.preferredMethod or "Office Meeting"

                # Email Customer
                if cust_user and cust_user.email:
                    cust_placeholders = {
                        'RecipientName': cust_user.fullName,
                        'CustomerName': cust_user.fullName,
                        'ConsultationType': cons.consultationType,
                        'ScheduledDate': date_str,
                        'ScheduledTime': time_str,
                        'PreferredMethod': method_str,
                        'ConsultantName': emp_user.fullName if emp_user else "LebEstates Consultant",
                        'OtherPartyName': emp_user.fullName if emp_user else "LebEstates Consultant"
                    }
                    sent = EmailService.send_templated_email(
                        recipient=cust_user.email,
                        feature_key='ConsultationReminder1h',
                        default_template_key='CONS-REMIND-1H',
                        placeholders=cust_placeholders,
                        fallback_subject=f"1-Hour Reminder: Consultation '{cons.consultationType}' at {time_str}",
                        fallback_body=f"Hello {cust_user.fullName}, your consultation session for '{cons.consultationType}' begins in 1 hour at {time_str}.",
                        email_type="ConsultationReminder1h",
                        log_token=f"{log_token}_CUST"
                    )
                    if sent:
                        count += 1

                # Email Consultant
                if emp_user and emp_user.email:
                    emp_placeholders = {
                        'RecipientName': emp_user.fullName,
                        'EmployeeName': emp_user.fullName,
                        'ConsultationType': cons.consultationType,
                        'ScheduledDate': date_str,
                        'ScheduledTime': time_str,
                        'PreferredMethod': method_str,
                        'CustomerName': cust_user.fullName if cust_user else "Customer",
                        'OtherPartyName': cust_user.fullName if cust_user else "Customer"
                    }
                    EmailService.send_templated_email(
                        recipient=emp_user.email,
                        feature_key='ConsultationReminder1h',
                        default_template_key='CONS-REMIND-1H',
                        placeholders=emp_placeholders,
                        fallback_subject=f"1-Hour Reminder: Client Consultation '{cons.consultationType}' at {time_str}",
                        fallback_body=f"Hello {emp_user.fullName}, you have a scheduled consultation '{cons.consultationType}' starting in 1 hour.",
                        email_type="ConsultationReminder1h",
                        log_token=f"{log_token}_EMP"
                    )

        return count

    @staticmethod
    def process_consultation_survey_1d():
        """
        1 day after scheduled consultation: Sent to customer (Thank you note, CSAT survey).
        """
        count = 0
        now = datetime.now()
        yesterday = (now - timedelta(days=1)).date()

        consultations = Consultation.query.filter(
            Consultation.status.in_(['Completed', 'Scheduled']),
            Consultation.scheduledDate == yesterday
        ).all()

        for cons in consultations:
            log_token = f"CONS_SURVEY_1D_C{cons.consultationID}_{cons.scheduledDate}"
            cust_user = cons.customer.user if (cons.customer and cons.customer.user) else None
            emp_user = cons.employee.user if (cons.employee and cons.employee.user) else None

            if cust_user and cust_user.email:
                survey_url = "http://127.0.0.1:5000/dashboard"
                placeholders = {
                    'CustomerName': cust_user.fullName,
                    'ConsultationType': cons.consultationType,
                    'ConsultantName': emp_user.fullName if emp_user else "LebEstates Advisory Team",
                    'SurveyUrl': survey_url
                }
                sent = EmailService.send_templated_email(
                    recipient=cust_user.email,
                    feature_key='ConsultationSurvey1d',
                    default_template_key='CONS-SURVEY-1D',
                    placeholders=placeholders,
                    fallback_subject=f"Thank You: How was your LebEstates Consultation?",
                    fallback_body=f"Hello {cust_user.fullName}, thank you for meeting with our consultation team yesterday. Please take 1 minute to share your feedback.",
                    email_type="ConsultationSurvey1d",
                    log_token=log_token
                )
                if sent:
                    count += 1

        return count

    # ---------------------------------------------------------
    # 3. RENT / INSTALLMENT PAYMENT REMINDERS
    # ---------------------------------------------------------
    @staticmethod
    def process_payment_reminders_7d():
        """
        7 days before nextDueDate of transaction (sent to Tenant / Buyer).
        """
        count = 0
        now = datetime.now().date()
        target_due_date = now + timedelta(days=7)

        transactions = Transaction.query.filter(
            Transaction.nextDueDate == target_due_date,
            Transaction.paymentStatus.notin_(['Closed', 'Cancelled'])
        ).all()

        for trans in transactions:
            log_token = f"PAY_REMIND_7D_T{trans.transactionID}_{trans.nextDueDate}"
            cust_user = trans.customer.user if (trans.customer and trans.customer.user) else None
            if cust_user and cust_user.email:
                prop_title = trans.property_obj.title if trans.property_obj else f"Property #{trans.propertyID}"
                final_price = float(trans.finalPrice)
                due_date_str = trans.nextDueDate.strftime('%B %d, %Y')

                placeholders = {
                    'CustomerName': cust_user.fullName,
                    'PropertyTitle': prop_title,
                    'DueDate': due_date_str,
                    'AmountDue': f"${final_price:,.2f}",
                    'PaymentMethod': trans.paymentMethod or "Bank Transfer",
                    'TransactionID': f"{trans.transactionID:05d}"
                }
                sent = EmailService.send_templated_email(
                    recipient=cust_user.email,
                    feature_key='PaymentReminder7d',
                    default_template_key='PAY-REMIND-7D',
                    placeholders=placeholders,
                    fallback_subject=f"Upcoming Payment Reminder: {prop_title} Due on {due_date_str}",
                    fallback_body=f"Hello {cust_user.fullName}, this is a gentle reminder that your scheduled installment/payment of ${final_price:,.2f} for {prop_title} is due in 7 days ({due_date_str}).",
                    email_type="PaymentReminder7d",
                    log_token=log_token
                )
                if sent:
                    count += 1

        return count

    @staticmethod
    def process_payment_reminders_3d():
        """
        3 days before nextDueDate of transaction (sent to Tenant / Buyer).
        """
        count = 0
        now = datetime.now().date()
        target_due_date = now + timedelta(days=3)

        transactions = Transaction.query.filter(
            Transaction.nextDueDate == target_due_date,
            Transaction.paymentStatus.notin_(['Closed', 'Cancelled'])
        ).all()

        for trans in transactions:
            log_token = f"PAY_REMIND_3D_T{trans.transactionID}_{trans.nextDueDate}"
            cust_user = trans.customer.user if (trans.customer and trans.customer.user) else None
            if cust_user and cust_user.email:
                prop_title = trans.property_obj.title if trans.property_obj else f"Property #{trans.propertyID}"
                final_price = float(trans.finalPrice)
                due_date_str = trans.nextDueDate.strftime('%B %d, %Y')

                placeholders = {
                    'CustomerName': cust_user.fullName,
                    'PropertyTitle': prop_title,
                    'DueDate': due_date_str,
                    'AmountDue': f"${final_price:,.2f}",
                    'PaymentMethod': trans.paymentMethod or "Bank Transfer",
                    'TransactionID': f"{trans.transactionID:05d}"
                }
                sent = EmailService.send_templated_email(
                    recipient=cust_user.email,
                    feature_key='PaymentReminder3d',
                    default_template_key='PAY-REMIND-3D',
                    placeholders=placeholders,
                    fallback_subject=f"Action Required: Payment Due in 3 Days - {prop_title}",
                    fallback_body=f"Hello {cust_user.fullName}, your payment for {prop_title} of ${final_price:,.2f} is due in 3 days on {due_date_str}.",
                    email_type="PaymentReminder3d",
                    log_token=log_token
                )
                if sent:
                    count += 1

        return count

    @staticmethod
    def process_payment_overdue_1d():
        """
        1 day after nextDueDate (if unpaid) (sent to Tenant / Buyer).
        """
        count = 0
        now = datetime.now().date()
        target_due_date = now - timedelta(days=1)

        transactions = Transaction.query.filter(
            Transaction.nextDueDate == target_due_date,
            Transaction.paymentStatus.notin_(['Closed', 'Cancelled'])
        ).all()

        for trans in transactions:
            log_token = f"PAY_OVERDUE_1D_T{trans.transactionID}_{trans.nextDueDate}"
            cust_user = trans.customer.user if (trans.customer and trans.customer.user) else None
            if cust_user and cust_user.email:
                prop_title = trans.property_obj.title if trans.property_obj else f"Property #{trans.propertyID}"
                final_price = float(trans.finalPrice)
                due_date_str = trans.nextDueDate.strftime('%B %d, %Y')

                placeholders = {
                    'CustomerName': cust_user.fullName,
                    'PropertyTitle': prop_title,
                    'DueDate': due_date_str,
                    'AmountDue': f"${final_price:,.2f}",
                    'TransactionID': f"{trans.transactionID:05d}"
                }
                sent = EmailService.send_templated_email(
                    recipient=cust_user.email,
                    feature_key='PaymentOverdue1d',
                    default_template_key='PAY-OVERDUE-1D',
                    placeholders=placeholders,
                    fallback_subject=f"Notice: Missed Payment for {prop_title} (Due {due_date_str})",
                    fallback_body=f"Hello {cust_user.fullName}, our system notes that the scheduled payment of ${final_price:,.2f} for {prop_title} was due yesterday ({due_date_str}) and remains outstanding. Please arrange payment to avoid late fees.",
                    email_type="PaymentOverdue1d",
                    log_token=log_token
                )
                if sent:
                    count += 1

        return count

    @staticmethod
    def process_payment_overdue_7d():
        """
        7 days after nextDueDate (if unpaid) (Sent to Tenant / Buyer, CC: Landlord / Agent).
        Includes gentle warning of missed payment and late fee escalation.
        """
        count = 0
        now = datetime.now().date()
        target_due_date = now - timedelta(days=7)

        transactions = Transaction.query.filter(
            Transaction.nextDueDate <= target_due_date,
            Transaction.paymentStatus.notin_(['Closed', 'Cancelled'])
        ).all()

        for trans in transactions:
            log_token = f"PAY_OVERDUE_7D_T{trans.transactionID}_{trans.nextDueDate}"
            cust_user = trans.customer.user if (trans.customer and trans.customer.user) else None
            owner_user = trans.owner.user if (trans.owner and trans.owner.user) else None
            agent_user = trans.employee.user if (trans.employee and trans.employee.user) else None

            if cust_user and cust_user.email:
                prop_title = trans.property_obj.title if trans.property_obj else f"Property #{trans.propertyID}"
                final_price = float(trans.finalPrice)
                due_date_str = trans.nextDueDate.strftime('%B %d, %Y') if trans.nextDueDate else "Past Due"

                # Prepare CC list
                cc_emails = []
                if owner_user and owner_user.email:
                    cc_emails.append(owner_user.email)
                if agent_user and agent_user.email:
                    cc_emails.append(agent_user.email)
                cc_str = ", ".join(cc_emails) if cc_emails else None

                late_fee_notice = "According to your agreement terms, late penalties and legal escrow proceedings may apply for overdue balances exceeding 7 days."

                placeholders = {
                    'CustomerName': cust_user.fullName,
                    'PropertyTitle': prop_title,
                    'DueDate': due_date_str,
                    'AmountDue': f"${final_price:,.2f}",
                    'LateFeeNotice': late_fee_notice,
                    'TransactionID': f"{trans.transactionID:05d}",
                    'LandlordName': owner_user.fullName if owner_user else "Property Owner",
                    'AgentName': agent_user.fullName if agent_user else "LebEstates Agent"
                }

                sent = EmailService.send_templated_email(
                    recipient=cust_user.email,
                    feature_key='PaymentOverdue7d',
                    default_template_key='PAY-OVERDUE-7D',
                    placeholders=placeholders,
                    fallback_subject=f"Urgent: Overdue Payment Warning for {prop_title} (Late Fee Notice)",
                    fallback_body=f"Hello {cust_user.fullName}, your payment for {prop_title} is more than 7 days overdue ({due_date_str}). Please settle this payment immediately to prevent further escalation.",
                    email_type="PaymentOverdue7d",
                    cc_email=cc_str,
                    log_token=log_token
                )
                if sent:
                    count += 1

        return count
