from app.models.base import db
from datetime import datetime

class OfficeExpense(db.Model):
    __tablename__ = 'office_expenses'
    
    expenseID = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50), nullable=False) # Office Rent, Utilities, Marketing, Software, Legal, Maintenance, Miscellaneous
    amount = db.Column(db.Float, nullable=False)
    expenseDate = db.Column(db.Date, nullable=False, default=datetime.now)
    status = db.Column(db.String(50), default='Paid') # Paid, Pending, Overdue
    isRecurring = db.Column(db.Boolean, default=False)
    recurrenceType = db.Column(db.String(50), default='Monthly') # Monthly, Yearly
    notes = db.Column(db.Text, nullable=True)
    createdByID = db.Column(db.Integer, db.ForeignKey('users.userID'), nullable=True)
    createdAt = db.Column(db.DateTime, default=datetime.now)
    updatedAt = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    createdBy = db.relationship('Users', foreign_keys=[createdByID])
