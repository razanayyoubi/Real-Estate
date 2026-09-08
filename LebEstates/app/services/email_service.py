import io
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
    def send_email(to_email, recipient_name, subject, html_content, text_content=None, from_email=None, from_name=None, cc_email=None, attachments=None):
        """
        Sends a single email using the Mailjet Send API v3.1.
        
        :param to_email: Email address of the recipient.
        :param recipient_name: Name of the recipient.
        :param subject: Email subject line.
        :param html_content: HTML body of the email.
        :param text_content: Optional text body of the email.
        :param from_email: Override default sender email.
        :param from_name: Override default sender display name.
        :param cc_email: Optional CC email address (str or list).
        :param attachments: Optional list of dicts: [{'ContentType': 'application/pdf', 'Filename': '...', 'Base64Content': '...'}]
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

        # Prepare message object
        message_obj = {
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

        if text_content:
            message_obj["TextPart"] = text_content

        # Handle CC recipients
        if cc_email:
            cc_recipients = []
            if isinstance(cc_email, str):
                for c in cc_email.split(','):
                    if c.strip():
                        cc_recipients.append({"Email": c.strip()})
            elif isinstance(cc_email, list):
                for c in cc_email:
                    if isinstance(c, str) and c.strip():
                        cc_recipients.append({"Email": c.strip()})
                    elif isinstance(c, dict) and c.get('Email'):
                        cc_recipients.append(c)
            if cc_recipients:
                message_obj["Cc"] = cc_recipients

        # Handle Attachments
        if attachments and isinstance(attachments, list):
            valid_attachments = []
            for att in attachments:
                if isinstance(att, dict) and att.get('Base64Content') and att.get('Filename'):
                    valid_attachments.append({
                        "ContentType": att.get('ContentType', 'application/pdf'),
                        "Filename": att.get('Filename'),
                        "Base64Content": att.get('Base64Content')
                    })
            if valid_attachments:
                message_obj["Attachments"] = valid_attachments

        # Prepare payload according to Mailjet Send API v3.1
        payload = {
            "Messages": [message_obj]
        }

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
    def send_email_safe(recipient, subject, message, email_type, user_id=None, template_key=None, from_email=None, from_name=None, cc_email=None, attachments=None, log_token=None):
        """
        Sends an email and logs the details to the database EmailLog table.
        """
        if not recipient or not recipient.strip():
            return False

        # Idempotency check if log_token is provided
        if log_token:
            existing_sent = EmailLog.query.filter_by(templateKey=log_token, status='Sent').first()
            if existing_sent:
                logger.info(f"Skipping email with log_token '{log_token}' as it was already sent.")
                return True

        # Create log record as Pending
        saved_key = log_token if log_token else template_key
        recipients_log = recipient
        if cc_email:
            recipients_log += f" (CC: {cc_email})"

        log_entry = EmailLog(
            recipientsRaw=recipients_log,
            subject=subject or "",
            body=message or "",
            emailType=email_type,
            status='Pending',
            attempts=1,
            templateKey=saved_key,
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
            from_name=from_name,
            cc_email=cc_email,
            attachments=attachments
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
    def send_templated_email(recipient, feature_key, default_template_key, placeholders=None, fallback_subject="Notification", fallback_body="", email_type="Notification", user_id=None, cc_email=None, attachments=None, log_token=None):
        """
        Orchestrated template sender modeled after RentACar.
        Resolves template configurations, processes placeholders, and logs delivery output.
        """
        if not recipient or not recipient.strip():
            return False

        # Idempotency check if log_token is provided
        if log_token:
            existing_sent = EmailLog.query.filter_by(templateKey=log_token, status='Sent').first()
            if existing_sent:
                logger.info(f"Skipping templated email with log_token '{log_token}' as it was already sent.")
                return True

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
            from_name=from_name,
            cc_email=cc_email,
            attachments=attachments,
            log_token=log_token
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

    @staticmethod
    def generate_receipt_pdf(transaction):
        """
        Generates a sleek, professional PDF document for a transaction receipt.
        Returns bytes of the generated PDF file.
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch

            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=36,
                leftMargin=36,
                topMargin=36,
                bottomMargin=36
            )
            story = []

            styles = getSampleStyleSheet()
            brand_style = ParagraphStyle(
                'BrandStyle',
                parent=styles['Normal'],
                fontName='Helvetica-Bold',
                fontSize=22,
                leading=26,
                textColor=colors.HexColor('#00081e')
            )
            title_style = ParagraphStyle(
                'TitleStyle',
                parent=styles['Normal'],
                fontName='Helvetica-Bold',
                fontSize=14,
                leading=18,
                textColor=colors.HexColor('#735c00'),
                alignment=2 # Right
            )
            subtitle_style = ParagraphStyle(
                'SubtitleStyle',
                parent=styles['Normal'],
                fontName='Helvetica',
                fontSize=10,
                leading=14,
                textColor=colors.HexColor('#666666'),
                alignment=2
            )
            label_style = ParagraphStyle(
                'LabelStyle',
                parent=styles['Normal'],
                fontName='Helvetica-Bold',
                fontSize=9,
                leading=12,
                textColor=colors.HexColor('#888888')
            )
            val_style = ParagraphStyle(
                'ValStyle',
                parent=styles['Normal'],
                fontName='Helvetica-Bold',
                fontSize=10,
                leading=14,
                textColor=colors.HexColor('#1a1a1a')
            )
            normal_val_style = ParagraphStyle(
                'NormalValStyle',
                parent=styles['Normal'],
                fontName='Helvetica',
                fontSize=10,
                leading=14,
                textColor=colors.HexColor('#333333')
            )

            # Header Table
            trans_date_str = transaction.transactionDate.strftime('%B %d, %Y') if transaction.transactionDate else datetime.now().strftime('%B %d, %Y')
            header_data = [
                [
                    Paragraph("<font color='#00081e'>LEB</font><font color='#d4af37'>ESTATES</font>", brand_style),
                    Paragraph(f"OFFICIAL RECEIPT<br/><font color='#666666' size='9'>#TRX-{transaction.transactionID:05d}</font><br/><font color='#666666' size='8'>Date: {trans_date_str}</font>", title_style)
                ]
            ]
            header_table = Table(header_data, colWidths=[3.5*inch, 3.5*inch])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ]))
            story.append(header_table)
            story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#00081e'), spaceBefore=4, spaceAfter=15))

            # Customer & Property Parties Table
            cust_name = transaction.customer.user.fullName if (transaction.customer and transaction.customer.user) else "Customer"
            cust_email = transaction.customer.user.email if (transaction.customer and transaction.customer.user) else "N/A"
            cust_phone = transaction.customer.user.phoneNumber if (transaction.customer and transaction.customer.user) else "N/A"
            
            owner_name = transaction.owner.user.fullName if (transaction.owner and transaction.owner.user) else "Property Owner"
            owner_email = transaction.owner.user.email if (transaction.owner and transaction.owner.user) else "N/A"
            
            agent_name = transaction.employee.user.fullName if (transaction.employee and transaction.employee.user) else "LebEstates Agent"

            parties_data = [
                [
                    Paragraph("BILLED TO / CLIENT", label_style),
                    Paragraph("PROPERTY OWNER / LANDLORD", label_style)
                ],
                [
                    Paragraph(f"<b>{cust_name}</b><br/>{cust_email}<br/>{cust_phone}", normal_val_style),
                    Paragraph(f"<b>{owner_name}</b><br/>{owner_email}", normal_val_style)
                ]
            ]
            parties_table = Table(parties_data, colWidths=[3.5*inch, 3.5*inch])
            parties_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8f9fa')),
                ('PADDING', (0,0), (-1,-1), 8),
            ]))
            story.append(parties_table)
            story.append(Spacer(1, 15))

            # Property & Deal Information
            prop_title = transaction.property_obj.title if transaction.property_obj else f"Property #{transaction.propertyID}"
            prop_loc = transaction.property_obj.location if transaction.property_obj else "Lebanon"
            prop_addr = transaction.property_obj.address if transaction.property_obj else ""

            prop_data = [
                [Paragraph("PROPERTY DETAILS", label_style), Paragraph("DEAL PARTICULARS", label_style)],
                [
                    Paragraph(f"<b>{prop_title}</b><br/>Location: {prop_loc}<br/>Address: {prop_addr}", normal_val_style),
                    Paragraph(f"Type: <b>{transaction.transactionType}</b><br/>Facilitating Agent: <b>{agent_name}</b><br/>Payment Method: <b>{transaction.paymentMethod or 'Wire Transfer'}</b>", normal_val_style)
                ]
            ]
            prop_table = Table(prop_data, colWidths=[3.5*inch, 3.5*inch])
            prop_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('PADDING', (0,0), (-1,-1), 8),
            ]))
            story.append(prop_table)
            story.append(Spacer(1, 15))

            # Breakdown Table
            final_price = float(transaction.finalPrice)
            amount_paid = float(transaction.amountPaid) if transaction.amountPaid is not None else final_price
            status_display = "Closed / Paid in Full" if transaction.paymentStatus == 'Closed' else (transaction.paymentStatus or 'Pending')

            items_data = [
                [
                    Paragraph("<b>Description</b>", ParagraphStyle('H1', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#ffffff'))),
                    Paragraph("<b>Type</b>", ParagraphStyle('H2', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#ffffff'))),
                    Paragraph("<b>Status</b>", ParagraphStyle('H3', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#ffffff'))),
                    Paragraph("<b>Amount</b>", ParagraphStyle('H4', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, alignment=2, textColor=colors.HexColor('#ffffff')))
                ],
                [
                    Paragraph(f"Real Estate {transaction.transactionType} Agreement - {prop_title}", normal_val_style),
                    Paragraph(transaction.paymentType or "Full Payment", normal_val_style),
                    Paragraph(status_display, normal_val_style),
                    Paragraph(f"${final_price:,.2f}", ParagraphStyle('P1', parent=styles['Normal'], alignment=2, fontName='Helvetica-Bold'))
                ],
                [
                    "",
                    "",
                    Paragraph("<b>Total Amount Paid:</b>", ParagraphStyle('TP', parent=styles['Normal'], alignment=2, fontName='Helvetica-Bold', fontSize=11, textColor=colors.HexColor('#00081e'))),
                    Paragraph(f"<b>${amount_paid:,.2f}</b>", ParagraphStyle('TP2', parent=styles['Normal'], alignment=2, fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor('#27ae60')))
                ]
            ]

            items_table = Table(items_data, colWidths=[3.0*inch, 1.4*inch, 1.4*inch, 1.2*inch])
            items_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#00081e')),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('PADDING', (0,0), (-1,-1), 8),
                ('GRID', (0,0), (-1,1), 0.5, colors.HexColor('#e0e0e0')),
                ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#fcfbfa')),
                ('LINEABOVE', (0,-1), (-1,-1), 1.5, colors.HexColor('#00081e')),
            ]))
            story.append(items_table)
            story.append(Spacer(1, 25))

            # Footer / Notice
            footer_text = (
                "<b>Important Notice:</b> This official transaction receipt confirms the execution status recorded by LebEstates. "
                "For inquiries, legal escrow verification, or deed transfers, please contact LebEstates Billing & Escrow at billing@lebestates.com."
            )
            story.append(Paragraph(footer_text, ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, leading=11, textColor=colors.HexColor('#777777'))))

            doc.build(story)
            pdf_bytes = buffer.getvalue()
            buffer.close()
            return pdf_bytes
        except Exception as e:
            logger.error(f"Failed to generate receipt PDF with reportlab: {e}")
            # Minimal fallback raw PDF generator
            fallback_content = f"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>/Contents 4 0 R>>endobj 4 0 obj<</Length 110>>stream\nBT /F1 16 Tf 50 720 Td (LebEstates Official Receipt #TRX-{transaction.transactionID}) Tj ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000214 00000 n \ntrailer<</Size 5/Root 1 0 R>>\nstartxref\n375\n%%EOF".encode('utf-8')
            return fallback_content

    @staticmethod
    def send_transaction_receipt(transaction, recipient_email=None, user_id=None):
        """
        Builds the receipt PDF for a transaction, attaches it to the email,
        and dispatches it to the customer via EmailService.
        """
        cust = transaction.customer
        if not recipient_email and cust and cust.user:
            recipient_email = cust.user.email

        if not recipient_email:
            logger.error(f"Cannot send transaction receipt for transaction #{transaction.transactionID}: No recipient email found.")
            return False

        cust_name = cust.user.fullName if (cust and cust.user) else "Valued Customer"
        prop_title = transaction.property_obj.title if transaction.property_obj else f"Property #{transaction.propertyID}"
        final_price = float(transaction.finalPrice)
        amount_paid = float(transaction.amountPaid) if transaction.amountPaid is not None else final_price
        date_str = transaction.transactionDate.strftime('%B %d, %Y') if transaction.transactionDate else datetime.now().strftime('%B %d, %Y')

        # Generate PDF bytes and encode base64
        pdf_bytes = EmailService.generate_receipt_pdf(transaction)
        pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')
        filename = f"LebEstates-Receipt-TRX-{transaction.transactionID:05d}.pdf"

        attachments = [
            {
                "ContentType": "application/pdf",
                "Filename": filename,
                "Base64Content": pdf_b64
            }
        ]

        placeholders = {
            'CustomerName': cust_name,
            'PropertyTitle': prop_title,
            'TransactionID': f"{transaction.transactionID:05d}",
            'TransactionType': transaction.transactionType,
            'FinalPrice': f"${final_price:,.2f}",
            'AmountPaid': f"${amount_paid:,.2f}",
            'PaymentMethod': transaction.paymentMethod or "Bank Transfer",
            'PaymentStatus': transaction.paymentStatus,
            'Date': date_str
        }

        return EmailService.send_templated_email(
            recipient=recipient_email,
            feature_key='TransactionReceipt',
            default_template_key='TRANS-RECEIPT-V1',
            placeholders=placeholders,
            fallback_subject=f"Receipt for Transaction #{transaction.transactionID:05d} - LebEstates",
            fallback_body=f"Hello {cust_name}, please find attached your official transaction receipt for {prop_title}.",
            email_type="TransactionReceipt",
            user_id=user_id,
            attachments=attachments
        )

