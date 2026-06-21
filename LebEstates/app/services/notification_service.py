from app.models.base import db
from app.models.notification import Notification
from app.models.users import Users
from app.services.email_service import EmailService

class NotificationService:
    @staticmethod
    def create_notification(user_id, message, action_url=None):
        """
        Creates a new notification record in the database for the given user,
        and triggers a parallel email notification to their email address.
        """
        user = Users.query.get(user_id)
        if not user:
            return {'success': False, 'error': 'User not found.'}

        try:
            # Create Notification DB entry
            new_notif = Notification(
                userID=user_id,
                message=message,
                actionURL=action_url,
                isRead=False
            )
            db.session.add(new_notif)
            db.session.commit()

            # Format email body
            email_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #dddddd; border-radius: 8px;">
                        <h2 style="color: #0d1b2a;">LebEstates Notification</h2>
                        <p>Hello {user.fullName},</p>
                        <p>{message}</p>
                        {f'<p><a href="http://localhost:5000{action_url}" style="display: inline-block; background-color: #ffd65b; color: #0d1b2a; padding: 10px 20px; text-decoration: none; font-weight: bold; border-radius: 5px;">View Action</a></p>' if action_url else ''}
                        <hr style="border: 0; border-top: 1px solid #eeeeee; margin: 20px 0;">
                        <p style="font-size: 12px; color: #777777;">This is an automated email from LebEstates. Please do not reply directly to this message.</p>
                    </div>
                </body>
            </html>
            """
            
            # Send Email
            EmailService.send_email(
                to_email=user.email,
                subject="New Notification | LebEstates",
                body_html=email_body
            )

            return {'success': True, 'notification_id': new_notif.notificationID}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'Database error: {str(e)}'}

    @staticmethod
    def get_unread_notifications(user_id):
        """Returns unread notifications for a user, ordered by creation date descending."""
        return Notification.query.filter_by(userID=user_id, isRead=False).order_by(Notification.createdAt.desc()).all()

    @staticmethod
    def get_all_notifications(user_id, limit=20):
        """Returns all notifications for a user, ordered by creation date descending."""
        return Notification.query.filter_by(userID=user_id).order_by(Notification.createdAt.desc()).limit(limit).all()

    @staticmethod
    def mark_as_read(notification_id, user_id):
        """Marks a single notification as read."""
        notif = Notification.query.filter_by(notificationID=notification_id, userID=user_id).first()
        if notif:
            try:
                notif.isRead = True
                db.session.commit()
                return {'success': True}
            except Exception as e:
                db.session.rollback()
                return {'success': False, 'error': str(e)}
        return {'success': False, 'error': 'Notification not found.'}

    @staticmethod
    def mark_all_as_read(user_id):
        """Marks all unread notifications for a user as read."""
        unread = Notification.query.filter_by(userID=user_id, isRead=False).all()
        try:
            for notif in unread:
                notif.isRead = True
            db.session.commit()
            return {'success': True, 'count': len(unread)}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
