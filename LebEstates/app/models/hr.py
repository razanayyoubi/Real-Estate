from app.models.base import db
from datetime import datetime

class Employee(db.Model):
    __tablename__ = 'employee'
    employeeID = db.Column(db.Integer, primary_key=True)
    userID = db.Column(db.Integer, db.ForeignKey('users.userID'), nullable=False, unique=True)
    position = db.Column(db.String(100), nullable=False)
    hireDate = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum('Active', 'OnLeave', 'Terminated', name='emp_status'), default='Active')

    user = db.relationship('Users', backref=db.backref('employee_profile', uselist=False))
    salaries = db.relationship('Salary', backref='employee', lazy=True)

class Salary(db.Model):
    __tablename__ = 'salary'
    salaryID = db.Column(db.Integer, primary_key=True)
    employeeID = db.Column(db.Integer, db.ForeignKey('employee.employeeID'), nullable=False)
    baseSalary = db.Column(db.Numeric(10, 2), nullable=False)
    bonus = db.Column(db.Numeric(10, 2), default=0.0)
    deduction = db.Column(db.Numeric(10, 2), default=0.0)
    totalSalary = db.Column(db.Numeric(10, 2), nullable=False)
    salaryMonth = db.Column(db.String(7), nullable=False) # e.g. YYYY-MM
    paymentStatus = db.Column(db.Enum('Pending', 'Paid', name='pay_status'), default='Pending')
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)

class CommissionSetting(db.Model):
    __tablename__ = 'commission_setting'
    commissionID = db.Column(db.Integer, primary_key=True)
    commissionType = db.Column(db.String(50), nullable=False) # e.g. Sell, Rent
    ratePercentage = db.Column(db.Numeric(5, 2), nullable=False)
    updatedBy = db.Column(db.Integer, db.ForeignKey('users.userID'), nullable=False)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    admin = db.relationship('Users', foreign_keys=[updatedBy])
