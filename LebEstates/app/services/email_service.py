import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app

class EmailService:
    @staticmethod
    def send_email(to_email, subject, body_html):
        """
        Sends an email. If SMTP settings are missing or if it fails,
        logs the email details to a file for local verification.
        """
        # Determine log file path in the workspace
        workspace_dir = r"c:\Users\Fatima\OneDrive\Desktop\Real-Estate"
        log_file_path = os.path.join(workspace_dir, "sent_emails.log")

        log_content = (
            f"==================================================\n"
            f"DATE/TIME: {os.popen('date /t').read().strip()} {os.popen('time /t').read().strip()}\n"
            f"TO: {to_email}\n"
            f"SUBJECT: {subject}\n"
            f"BODY:\n{body_html}\n"
            f"==================================================\n\n"
        )

        # Write to log file
        try:
            with open(log_file_path, "a", encoding="utf-8") as f:
                f.write(log_content)
            print(f"[Email Service] Email details written to log: {log_file_path}")
        except Exception as e:
            print(f"[Email Service] Failed to write to email log file: {str(e)}")

        # Check SMTP config in current app context
        try:
            smtp_server = current_app.config.get('MAIL_SERVER')
            smtp_port = current_app.config.get('MAIL_PORT', 587)
            smtp_user = current_app.config.get('MAIL_USERNAME')
            smtp_pwd = current_app.config.get('MAIL_PASSWORD')
            sender = current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@lebestates.com')

            if smtp_server and smtp_user and smtp_pwd:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = sender
                msg["To"] = to_email

                part1 = MIMEText(body_html, "html")
                msg.attach(part1)

                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_pwd)
                    server.sendmail(sender, to_email, msg.as_string())
                print(f"[Email Service] Successfully sent real SMTP email to {to_email}")
                return True
        except Exception as smtp_err:
            print(f"[Email Service] Real SMTP delivery failed: {str(smtp_err)}. Log fallback succeeded.")

        return False
