from app.models.base import db
from datetime import datetime

class Visit(db.Model):
    __tablename__ = 'visit'
    visitID = db.Column(db.Integer, primary_key=True)
    propertyID = db.Column(db.Integer, db.ForeignKey('property.propertyID'), nullable=False)
    customerID = db.Column(db.Integer, db.ForeignKey('customer.customerID'), nullable=False)
    employeeID = db.Column(db.Integer, db.ForeignKey('employee.employeeID'), nullable=False)
    visitDate = db.Column(db.Date, nullable=False)
    visitTime = db.Column(db.Time, nullable=False)
    status = db.Column(db.Enum('Scheduled', 'Completed', 'Cancelled', name='visit_status'), default='Scheduled')
    notes = db.Column(db.Text)
    createdAt = db.Column(db.DateTime, default=datetime.now)
    updatedAt = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    property_obj = db.relationship('Property', foreign_keys=[propertyID])
    customer = db.relationship('Customer', foreign_keys=[customerID])
    employee = db.relationship('Employee', foreign_keys=[employeeID])

class Consultation(db.Model):
    __tablename__ = 'consultation'
    consultationID = db.Column(db.Integer, primary_key=True)
    customerID = db.Column(db.Integer, db.ForeignKey('customer.customerID'), nullable=False)
    assignedEmployeeID = db.Column(db.Integer, db.ForeignKey('employee.employeeID'))
    consultationType = db.Column(db.String(100), nullable=False)
    preferredMethod = db.Column(db.String(50)) # e.g. Phone, Office, Video Call
    message = db.Column(db.Text)
    status = db.Column(db.Enum('Pending', 'Scheduled', 'Completed', 'Cancelled', name='cons_status'), default='Pending')
    scheduledDate = db.Column(db.Date)
    scheduledTime = db.Column(db.Time)
    notes = db.Column(db.Text)
    createdAt = db.Column(db.DateTime, default=datetime.now)
    updatedAt = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    customer = db.relationship('Customer', foreign_keys=[customerID])
    employee = db.relationship('Employee', foreign_keys=[assignedEmployeeID])

class Transaction(db.Model):
    __tablename__ = 'transaction'
    transactionID = db.Column(db.Integer, primary_key=True)
    propertyID = db.Column(db.Integer, db.ForeignKey('property.propertyID'), nullable=False)
    customerID = db.Column(db.Integer, db.ForeignKey('customer.customerID'), nullable=False)
    ownerID = db.Column(db.Integer, db.ForeignKey('customer.customerID'), nullable=False)
    employeeID = db.Column(db.Integer, db.ForeignKey('employee.employeeID'), nullable=False)
    transactionType = db.Column(db.String(50), nullable=False) # Sell, Rent
    finalPrice = db.Column(db.Numeric(15, 2), nullable=False)
    commissionRate = db.Column(db.Numeric(5, 2), nullable=False)
    commissionAmount = db.Column(db.Numeric(15, 2), nullable=False)
    paymentStatus = db.Column(db.Enum('Pending', 'Completed', 'Failed', name='trans_pay_status'), default='Pending')
    transactionDate = db.Column(db.DateTime, default=datetime.now)
    createdAt = db.Column(db.DateTime, default=datetime.now)

    property_obj = db.relationship('Property', foreign_keys=[propertyID])
    customer = db.relationship('Customer', foreign_keys=[customerID])
    owner = db.relationship('Customer', foreign_keys=[ownerID])
    employee = db.relationship('Employee', foreign_keys=[employeeID])
