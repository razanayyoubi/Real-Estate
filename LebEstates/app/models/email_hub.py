from app.models.base import db
from datetime import datetime

class EmailTemplate(db.Model):
    __tablename__ = 'email_templates'
    templateID = db.Column(db.Integer, primary_key=True)
    templateKey = db.Column(db.String(100), nullable=False, unique=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), default='System') # e.g. Customer, Employee, System
    subject = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    isActive = db.Column(db.Boolean, default=True)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updatedByUserID = db.Column(db.Integer, db.ForeignKey('users.userID'), nullable=True)

    updater = db.relationship('Users', foreign_keys=[updatedByUserID])

class SenderIdentity(db.Model):
    __tablename__ = 'sender_identity'
    senderIdentityID = db.Column(db.Integer, primary_key=True)
    displayName = db.Column(db.String(100), nullable=False)
    fromEmail = db.Column(db.String(100), nullable=False, unique=True)
    replyToEmail = db.Column(db.String(100), nullable=True)
    isActive = db.Column(db.Boolean, default=True)
    isDefault = db.Column(db.Boolean, default=False)
    verifiedStatus = db.Column(db.String(50), default='Verified') # Verified, Pending, Unknown
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)

class EmailFeatureConfig(db.Model):
    __tablename__ = 'email_feature_configs'
    featureConfigID = db.Column(db.Integer, primary_key=True)
    featureKey = db.Column(db.String(100), nullable=False, unique=True) # e.g. "ForgotPassword", "Otp2FA"
    featureName = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), default='System')
    enabled = db.Column(db.Boolean, default=True)
    senderIdentityID = db.Column(db.Integer, db.ForeignKey('sender_identity.senderIdentityID'), nullable=True)
    templateKey = db.Column(db.String(100), nullable=True) # loosely coupled templateKey
    replyToOverride = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updatedByUserID = db.Column(db.Integer, db.ForeignKey('users.userID'), nullable=True)

    sender_identity = db.relationship('SenderIdentity', foreign_keys=[senderIdentityID])
    updater = db.relationship('Users', foreign_keys=[updatedByUserID])

class DistributionList(db.Model):
    __tablename__ = 'distribution_list'
    distributionListID = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    isActive = db.Column(db.Boolean, default=True)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)

    members = db.relationship('DistributionListMember', backref='distribution_list', cascade="all, delete-orphan", lazy=True)
    rules = db.relationship('DistributionListRule', backref='distribution_list', cascade="all, delete-orphan", lazy=True)

class DistributionListMember(db.Model):
    __tablename__ = 'distribution_list_member'
    memberID = db.Column(db.Integer, primary_key=True)
    distributionListID = db.Column(db.Integer, db.ForeignKey('distribution_list.distributionListID'), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    label = db.Column(db.String(100), nullable=True)
    memberType = db.Column(db.String(50), default='Other') # Employee, Admin, Customer, Other
    isActive = db.Column(db.Boolean, default=True)
    addedAt = db.Column(db.DateTime, default=datetime.utcnow)

class DistributionListRule(db.Model):
    __tablename__ = 'distribution_list_rule'
    ruleID = db.Column(db.Integer, primary_key=True)
    distributionListID = db.Column(db.Integer, db.ForeignKey('distribution_list.distributionListID'), nullable=False)
    includeEmployees = db.Column(db.Boolean, default=False)
    includeAdmins = db.Column(db.Boolean, default=False)
    includeCustomers = db.Column(db.Boolean, default=False)
    onlyActiveUsers = db.Column(db.Boolean, default=True)
    excludeBlacklistedCustomers = db.Column(db.Boolean, default=True)
    manualEmailsRaw = db.Column(db.Text, nullable=True)

class EmailLog(db.Model):
    __tablename__ = 'email_logs'
    emailLogID = db.Column(db.Integer, primary_key=True)
    recipientsRaw = db.Column(db.Text, nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    emailType = db.Column(db.String(100), nullable=False) # e.g. Auth, Visit, Campaign
    status = db.Column(db.String(50), default='Pending') # Pending, Sent, Failed
    sentAt = db.Column(db.DateTime, nullable=True)
    attempts = db.Column(db.Integer, default=1)
    lastError = db.Column(db.Text, nullable=True)
    templateKey = db.Column(db.String(100), nullable=True)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    createdByUserID = db.Column(db.Integer, db.ForeignKey('users.userID'), nullable=True)

    creator = db.relationship('Users', foreign_keys=[createdByUserID])

class EmailDraft(db.Model):
    __tablename__ = 'email_drafts'
    draftID = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(255), nullable=True)
    body = db.Column(db.Text, nullable=True)
    recipientsRaw = db.Column(db.Text, nullable=True)
    selectedDistributionListIDsRaw = db.Column(db.Text, nullable=True)
    lastUpdated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    createdByUserID = db.Column(db.Integer, db.ForeignKey('users.userID'), nullable=False)

    creator = db.relationship('Users', foreign_keys=[createdByUserID])
