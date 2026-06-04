from app.models.base import db
from datetime import datetime

class Property(db.Model):
    __tablename__ = 'property'
    propertyID = db.Column(db.Integer, primary_key=True)
    ownerID = db.Column(db.Integer, db.ForeignKey('customer.customerID'), nullable=False)
    createdBy = db.Column(db.Integer, db.ForeignKey('users.userID'), nullable=False)
    approvedBy = db.Column(db.Integer, db.ForeignKey('users.userID'))
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    propertyType = db.Column(db.String(100), nullable=False) # e.g., Apartment, Villa
    listingType = db.Column(db.String(50), nullable=False) # e.g., Sell, Rent
    location = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Numeric(15, 2), nullable=False)
    area = db.Column(db.Numeric(10, 2), nullable=False) # In sqm
    rooms = db.Column(db.Integer)
    bathrooms = db.Column(db.Integer)
    floorNumber = db.Column(db.Integer)
    parkingAvailable = db.Column(db.Boolean, default=False)
    status = db.Column(db.Enum('Pending', 'Published', 'Sold', 'Rented', 'Rejected', name='prop_status'), default='Pending')
    latitude = db.Column(db.Numeric(10, 8), nullable=True)
    longitude = db.Column(db.Numeric(11, 8), nullable=True)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = db.relationship('Customer', foreign_keys=[ownerID])
    creator = db.relationship('Users', foreign_keys=[createdBy])
    approver = db.relationship('Users', foreign_keys=[approvedBy])
    images = db.relationship('PropertyImage', backref='property', lazy=True, cascade="all, delete-orphan")

class PropertyImage(db.Model):
    __tablename__ = 'property_image'
    imageID = db.Column(db.Integer, primary_key=True)
    propertyID = db.Column(db.Integer, db.ForeignKey('property.propertyID'), nullable=False)
    imageURL = db.Column(db.String(255), nullable=True)
    fileData = db.Column(db.LargeBinary)
    fileType = db.Column(db.String(50))
    isMainImage = db.Column(db.Boolean, default=False)
    uploadedAt = db.Column(db.DateTime, default=datetime.utcnow)



class Favorite(db.Model):
    __tablename__ = 'favorite'
    favoriteID = db.Column(db.Integer, primary_key=True)
    customerID = db.Column(db.Integer, db.ForeignKey('customer.customerID'), nullable=False)
    propertyID = db.Column(db.Integer, db.ForeignKey('property.propertyID'), nullable=False)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship('Customer', foreign_keys=[customerID])
    property_obj = db.relationship('Property', foreign_keys=[propertyID])
