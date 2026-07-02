import json
import urllib.request
import urllib.error
import base64
import logging
from datetime import datetime
from flask import current_app
from app.models.base import db
from app.models.email_hub import EmailTemplate, SenderIdentity, EmailFeatureConfig, EmailLog

logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    def send_email(to_email, recipient_name, subject, html_content, text_content=None, from_email=None, from_name=None):
        """
        Sends a single email using the Mailjet Send API v3.1.
        
        :param to_email: Email address of the recipient.
        :param recipient_name: Name of the recipient.
        :param subject: Email subject line.
        :param html_content: HTML body of the email.
        :param text_content: Optional text body of the email.
        :param from_email: Override default sender email.
        :param from_name: Override default sender display name.
        :return: dict with 'success' boolean and optional error message / details.
        """
        api_key = current_app.config.get('MAILJET_API_KEY')
        secret_key = current_app.config.get('MAILJET_SECRET_KEY')
        
        if not from_email:
            try:
                default_identity = SenderIdentity.query.filter_by(isDefault=True, isActive=True).first()
                if default_identity:
                    from_email = default_identity.fromEmail
                    from_name = from_name or default_identity.displayName
            except Exception as e:
                logger.error(f"Error querying database for default SenderIdentity: {e}")

        sender_email = from_email or current_app.config.get('MAILJET_SENDER_EMAIL')
        sender_name = from_name or current_app.config.get('MAILJET_SENDER_NAME')

        if not api_key or not secret_key:
            logger.error("Mailjet API credentials are not configured in app config.")
            return {'success': False, 'error': 'Mailjet API credentials are not configured.'}
        if not sender_email:
            logger.error("Mailjet sender email is not configured in app config.")
            return {'success': False, 'error': 'Mailjet sender email is not configured.'}

        # Prepare payload according to Mailjet Send API v3.1
        payload = {
            "Messages": [
                {
                    "From": {
                        "Email": sender_email,
                        "Name": sender_name or "LebEstates"
                    },
                    "To": [
                        {
                            "Email": to_email,
                            "Name": recipient_name or ""
                        }
                    ],
                    "Subject": subject,
                    "HTMLPart": html_content
                }
            ]
        }
        
        if text_content:
            payload["Messages"][0]["TextPart"] = text_content

        # Setup request
        url = "https://api.mailjet.com/v3.1/send"
        req_data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=req_data, method='POST')
        
        # Add headers
        req.add_header('Content-Type', 'application/json')
        
        # Setup basic authentication
        auth_str = f"{api_key}:{secret_key}"
        auth_bytes = auth_str.encode('utf-8')
        auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
        req.add_header('Authorization', f"Basic {auth_b64}")

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                res_body = response.read().decode('utf-8')
                res_json = json.loads(res_body)
                
                messages = res_json.get('Messages', [])
                if messages and messages[0].get('Status') == 'success':
                    logger.info(f"Email sent successfully to {to_email}. Subject: {subject}")
                    return {'success': True, 'message_id': messages[0].get('To', [{}])[0].get('MessageID')}
                else:
                    status = messages[0].get('Status') if messages else 'No status'
                    logger.warning(f"Mailjet Send API returned failure status ({status}) for {to_email}: {res_json}")
                    return {'success': False, 'error': f"Mailjet returned status: {status}", 'details': res_json}
        except urllib.error.HTTPError as e:
            try:
                err_body = e.read().decode('utf-8')
                err_json = json.loads(err_body)
            except Exception:
                err_json = e.reason
            logger.error(f"Mailjet send failed with HTTP Error {e.code}: {e.reason}. Response: {err_json}")
            return {'success': False, 'error': f"HTTP Error {e.code}: {e.reason}", 'details': err_json}
        except urllib.error.URLError as e:
            logger.error(f"Mailjet send failed with URL Error: {e.reason}")
            return {'success': False, 'error': f"URL Error: {str(e.reason)}"}
        except Exception as e:
            logger.error(f"Unexpected error sending email with Mailjet: {str(e)}")
            return {'success': False, 'error': f"Unexpected error: {str(e)}"}

    @staticmethod
    def send_email_safe(recipient, subject, message, email_type, user_id=None, template_key=None, from_email=None, from_name=None):
        """
        Sends an email and logs the details to the database EmailLog table.
        """
        if not recipient or not recipient.strip():
            return False

        # Create log record as Pending
        log_entry = EmailLog(
            recipientsRaw=recipient,
            subject=subject or "",
            body=message or "",
            emailType=email_type,
            status='Pending',
            attempts=1,
            templateKey=template_key,
            createdByUserID=user_id
        )

        try:
            db.session.add(log_entry)
            db.session.commit()
        except Exception as db_err:
            db.session.rollback()
            logger.error(f"Failed to create EmailLog database record: {db_err}")
            # Continue trying to send anyway

        # Call send_email API
        result = EmailService.send_email(
            to_email=recipient,
            recipient_name=None,
            subject=subject,
            html_content=message,
            from_email=from_email,
            from_name=from_name
        )

        if result.get('success'):
            log_entry.status = 'Sent'
            log_entry.sentAt = datetime.utcnow()
        else:
            log_entry.status = 'Failed'
            log_entry.lastError = str(result.get('error', 'Unknown send error'))

        try:
            db.session.commit()
        except Exception as db_err:
            db.session.rollback()
            logger.error(f"Failed to update EmailLog database record status: {db_err}")

        return log_entry.status == 'Sent'

    @staticmethod
    def send_templated_email(recipient, feature_key, default_template_key, placeholders=None, fallback_subject="Notification", fallback_body="", email_type="Notification", user_id=None):
        """
        Orchestrated template sender modeled after RentACar.
        Resolves template configurations, processes placeholders, and logs delivery output.
        """
        if not recipient or not recipient.strip():
            return False

        subject = fallback_subject
        body = fallback_body
        template_used = default_template_key
        from_email = None
        from_name = None

        if placeholders is None:
            placeholders = {}

        try:
            # 1. Fetch feature config from Database
            feature_config = EmailFeatureConfig.query.filter_by(featureKey=feature_key).first()
            if feature_config:
                if not feature_config.enabled:
                    logger.info(f"Skipping email send. Feature '{feature_key}' is disabled in configuration.")
                    return False

                if feature_config.templateKey:
                    template_used = feature_config.templateKey

                if feature_config.sender_identity and feature_config.sender_identity.isActive:
                    from_email = feature_config.sender_identity.fromEmail
                    from_name = feature_config.sender_identity.displayName

                if feature_config.replyToOverride:
                    # Can be passed to headers, but standard Mailjet sender works with basic From
                    pass

            # 2. Fetch template
            if template_used:
                template = EmailTemplate.query.filter_by(templateKey=template_used, isActive=True).first()
                if template:
                    subject = template.subject
                    body = template.body

                    # 3. Substitute placeholders
                    for key, val in placeholders.items():
                        placeholder = "{{" + key + "}}"
                        if placeholder in subject:
                            subject = subject.replace(placeholder, str(val))
                        if placeholder in body:
                            body = body.replace(placeholder, str(val))
        except Exception as ex:
            logger.error(f"Error resolving template configurations for feature '{feature_key}': {ex}")

        # Send safely
        return EmailService.send_email_safe(
            recipient=recipient,
            subject=subject,
            message=body,
            email_type=email_type,
            user_id=user_id,
            template_key=template_used,
            from_email=from_email,
            from_name=from_name
        )

    @staticmethod
    def send_raw_email_batch(recipients, subject, body, user_id=None):
        """
        Sends raw HTML emails to multiple recipients in a batch.
        """
        success_count = 0
        for email in recipients:
            email_clean = email.strip()
            if email_clean:
                if EmailService.send_email_safe(email_clean, subject, body, 'AdHoc Campaign', user_id=user_id):
                    success_count += 1
        return success_count
