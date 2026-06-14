from app.models.base import db
from datetime import datetime

class Role(db.Model):
    __tablename__ = 'role'
    roleID = db.Column(db.Integer, primary_key=True)
    roleName = db.Column(db.String(50), nullable=False, unique=True)
    
    users = db.relationship('Users', backref='role', lazy=True)

class Users(db.Model):
    __tablename__ = 'users'
    userID = db.Column(db.Integer, primary_key=True)
    fullName = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phoneNumber = db.Column(db.String(20))
    passwordHash = db.Column(db.String(255), nullable=False)
    roleID = db.Column(db.Integer, db.ForeignKey('role.roleID'), nullable=False)
    status = db.Column(db.Enum('Active', 'Inactive', 'Blacklisted', name='user_status'), default='Active')
    avatar = db.Column(db.LargeBinary(length=2**24), nullable=True)
    twoFactorEnabled = db.Column(db.Boolean, default=False)
    twoFactorSecret = db.Column(db.String(100), nullable=True)
    createdAt = db.Column(db.DateTime, default=datetime.now)
    updatedAt = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    @property
    def avatar_url(self):
        if self.avatar:
            return f"/profile/avatar/{self.userID}"
        return f"https://ui-avatars.com/api/?name={self.fullName.replace(' ', '+')}&background=random"

class Blacklist(db.Model):
    __tablename__ = 'blacklist'
    blacklistID = db.Column(db.Integer, primary_key=True)
    userID = db.Column(db.Integer, db.ForeignKey('users.userID'), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    blacklistedBy = db.Column(db.Integer, db.ForeignKey('users.userID'), nullable=False)
    blacklistedAt = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(50)) # e.g. Active, Resolved

    user = db.relationship('Users', foreign_keys=[userID])
    admin = db.relationship('Users', foreign_keys=[blacklistedBy])

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    logID = db.Column(db.Integer, primary_key=True)
    userID = db.Column(db.Integer, db.ForeignKey('users.userID'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    tableName = db.Column(db.String(100), nullable=False)
    recordID = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    ipAddress = db.Column(db.String(45), nullable=True)
    changes = db.Column(db.Text, nullable=True)
    createdAt = db.Column(db.DateTime, default=datetime.now)

    user = db.relationship('Users', foreign_keys=[userID])

    @staticmethod
    def log_action(action, table_name, record_id, description, user_id=None, changes=None):
        from flask import session, request
        from app.models.base import db
        import json
        
        # If user_id is not explicitly passed, try to get it from Flask session
        if not user_id:
            try:
                user_id = session.get('user_id')
            except Exception:
                pass
                
        # Resolve client IP address automatically
        ip_addr = None
        try:
            ip_addr = request.remote_addr
        except Exception:
            pass
            
        # Serialize changes to JSON if passed as a dictionary
        changes_str = None
        if changes is not None:
            if isinstance(changes, dict):
                try:
                    changes_str = json.dumps(changes)
                except Exception:
                    changes_str = str(changes)
            else:
                changes_str = str(changes)
        
        log = AuditLog(
            userID=user_id,
            action=action,
            tableName=table_name,
            recordID=record_id,
            description=description,
            ipAddress=ip_addr,
            changes=changes_str,
            createdAt=datetime.now()
        )
        db.session.add(log)

class UserSession(db.Model):
    __tablename__ = 'user_sessions'
    sessionID = db.Column(db.Integer, primary_key=True)
    userID = db.Column(db.Integer, db.ForeignKey('users.userID'), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)
    ipAddress = db.Column(db.String(45))
    userAgent = db.Column(db.String(255))
    lastActive = db.Column(db.DateTime, default=datetime.now)

    user = db.relationship('Users', backref=db.backref('sessions', lazy=True, cascade="all, delete-orphan"), foreign_keys=[userID])

class LoginLog(db.Model):
    __tablename__ = 'login_logs'
    logID = db.Column(db.Integer, primary_key=True)
    userID = db.Column(db.Integer, db.ForeignKey('users.userID'), nullable=False)
    ipAddress = db.Column(db.String(45))
    userAgent = db.Column(db.String(255))
    loginAt = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(50)) # e.g. Success, Failed

    user = db.relationship('Users', backref=db.backref('login_logs', lazy=True), foreign_keys=[userID])

