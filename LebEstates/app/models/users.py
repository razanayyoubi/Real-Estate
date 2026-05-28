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
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Blacklist(db.Model):
    __tablename__ = 'blacklist'
    blacklistID = db.Column(db.Integer, primary_key=True)
    userID = db.Column(db.Integer, db.ForeignKey('users.userID'), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    blacklistedBy = db.Column(db.Integer, db.ForeignKey('users.userID'), nullable=False)
    blacklistedAt = db.Column(db.DateTime, default=datetime.utcnow)
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
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('Users', foreign_keys=[userID])
