from app.models.base import db
from datetime import datetime

class Notification(db.Model):
    __tablename__ = 'notification'
    notificationID = db.Column(db.Integer, primary_key=True)
    userID = db.Column(db.Integer, db.ForeignKey('users.userID'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    isRead = db.Column(db.Boolean, default=False, nullable=False)
    actionURL = db.Column(db.String(255), nullable=True)
    createdAt = db.Column(db.DateTime, default=datetime.now)

    user = db.relationship('Users', backref=db.backref('notifications', lazy=True, cascade="all, delete-orphan"))
