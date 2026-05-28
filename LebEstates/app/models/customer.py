from app.models.base import db
from datetime import datetime

class Customer(db.Model):
    __tablename__ = 'customer'
    customerID = db.Column(db.Integer, primary_key=True)
    userID = db.Column(db.Integer, db.ForeignKey('users.userID'), nullable=False, unique=True)
    nationalID = db.Column(db.String(50), nullable=False, unique=True)
    address = db.Column(db.String(255))
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('Users', backref=db.backref('customer_profile', uselist=False))
    documents = db.relationship('CustomerDocument', backref='customer', lazy=True)

class CustomerDocument(db.Model):
    __tablename__ = 'customer_document'
    documentID = db.Column(db.Integer, primary_key=True)
    customerID = db.Column(db.Integer, db.ForeignKey('customer.customerID'), nullable=False)
    documentType = db.Column(db.String(50), nullable=False)
    documentSide = db.Column(db.String(50)) # e.g., Front, Back
    fileName = db.Column(db.String(255), nullable=False)
    fileType = db.Column(db.String(50))
    fileData = db.Column(db.LargeBinary) # BLOB
    status = db.Column(db.Enum('Pending', 'Verified', 'Rejected', name='doc_status'), default='Pending')
    rejectionReason = db.Column(db.Text)
    uploadedAt = db.Column(db.DateTime, default=datetime.utcnow)
    verifiedBy = db.Column(db.Integer, db.ForeignKey('employee.employeeID'))
    verifiedAt = db.Column(db.DateTime)

    verifier = db.relationship('Employee', foreign_keys=[verifiedBy])
