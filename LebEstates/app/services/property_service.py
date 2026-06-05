import os
from app.models.base import db
from app.models.property import Property, PropertyImage
from app.models.customer import Customer
from app.models.users import Users
from datetime import datetime

class PropertyService:

    @staticmethod
    def create_property(form_data, files, user, is_employee):
        """
        Validates form inputs, resolves the property owner, creates a new property,
        and saves any uploaded images as BLOBs in the database.
        """
        title = form_data.get('title', '').strip()
        listing_type = form_data.get('listing_type', '').strip() # Sell or Rent
        price = form_data.get('price', '').strip()
        property_type = form_data.get('property_type', '').strip()
        area = form_data.get('area', '').strip()
        rooms = form_data.get('rooms', '').strip()
        bathrooms = form_data.get('bathrooms', '').strip()
        floor_number = form_data.get('floor_number', '').strip()
        parking_spots = form_data.get('parking_spots', '').strip()
        description = form_data.get('description', '').strip()
        region = form_data.get('region', '').strip()
        address = form_data.get('address', '').strip()
        latitude = form_data.get('latitude', '').strip()
        longitude = form_data.get('longitude', '').strip()

        # Required validation
        if not title:
            return {'success': False, 'error': 'Title is required.', 'code': 400}
        if not listing_type:
            return {'success': False, 'error': 'Listing type is required.', 'code': 400}
        if not price:
            return {'success': False, 'error': 'Price is required.', 'code': 400}
        if not property_type:
            return {'success': False, 'error': 'Property type is required.', 'code': 400}
        if not area:
            return {'success': False, 'error': 'Area is required.', 'code': 400}
        if not region:
            return {'success': False, 'error': 'Region is required.', 'code': 400}
        if not address:
            return {'success': False, 'error': 'Address is required.', 'code': 400}

        # Determine Owner ID
        if is_employee:
            owner_id = form_data.get('owner_id')
            if not owner_id:
                return {'success': False, 'error': 'Please select a property owner.', 'code': 400}
            cust = Customer.query.get(owner_id)
            if not cust:
                return {'success': False, 'error': 'Selected owner customer profile does not exist.', 'code': 404}
        else:
            cust = Customer.query.filter_by(userID=user.userID).first()
            if not cust:
                cust = Customer(userID=user.userID, address=address)
                db.session.add(cust)
                db.session.commit()
            owner_id = cust.customerID

        # Determine approval and status
        if is_employee:
            status = 'Published'
            approved_by = user.userID
        else:
            status = 'Pending'
            approved_by = None

        try:
            price_val = float(price)
            area_val = float(area)
            rooms_val = int(rooms) if rooms else None
            bathrooms_val = int(bathrooms) if bathrooms else None
            floor_val = int(floor_number) if floor_number else None
            parking_spots_val = int(parking_spots) if parking_spots else 0
            parking_avail = parking_spots_val > 0
            lat_val = float(latitude) if latitude else None
            lng_val = float(longitude) if longitude else None
        except ValueError:
            return {'success': False, 'error': 'Invalid numeric values provided for specs.', 'code': 400}

        # Create Property record
        new_prop = Property(
            ownerID=owner_id,
            createdBy=user.userID,
            approvedBy=approved_by,
            title=title,
            description=description,
            propertyType=property_type,
            listingType=listing_type,
            location=region,
            address=address,
            price=price_val,
            area=area_val,
            rooms=rooms_val,
            bathrooms=bathrooms_val,
            floorNumber=floor_val,
            parkingAvailable=parking_avail,
            status=status,
            latitude=lat_val,
            longitude=lng_val
        )
        db.session.add(new_prop)

        try:
            db.session.flush() # Populate new_prop.propertyID

            # Handle photos upload
            allowed_extensions = {'.png', '.jpg', '.jpeg', '.webp', '.gif'}
            first_image = True

            for f in files:
                if f and f.filename != '':
                    _, ext = os.path.splitext(f.filename.lower())
                    if ext not in allowed_extensions:
                        return {
                            'success': False,
                            'error': f'Invalid file type: {f.filename}. Allowed formats: PNG, JPG, JPEG, WEBP, GIF.',
                            'code': 400
                        }

                    # Read binary content
                    file_data = f.read()
                    file_type = getattr(f, 'content_type', 'image/jpeg') or 'image/jpeg'

                    # Save Image as BLOB in DB
                    new_img = PropertyImage(
                        propertyID=new_prop.propertyID,
                        fileData=file_data,
                        fileType=file_type,
                        isMainImage=first_image
                    )
                    db.session.add(new_img)
                    db.session.flush()

                    new_img.imageURL = f"/properties/image/{new_img.imageID}"
                    first_image = False

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'Database error: {str(e)}', 'code': 500}

        msg = 'Property listing published directly!' if is_employee else 'Property submitted successfully! Pending approval from an employee.'
        return {'success': True, 'message': msg, 'property_id': new_prop.propertyID}

    @staticmethod
    def get_all_properties_and_stats():
        """
        Queries all properties ordered by creation date, computes active/pending counts,
        valuation sums, and formats valuation for the template context.
        """
        all_properties = Property.query.order_by(Property.createdAt.desc()).all()

        total_properties = len(all_properties)
        active_properties = sum(1 for p in all_properties if p.status == 'Published')
        pending_properties = sum(1 for p in all_properties if p.status == 'Pending')

        valuation_sum = sum(p.price for p in all_properties if p.status == 'Published')
        if valuation_sum >= 1_000_000_000:
            formatted_valuation = f"${valuation_sum / 1_000_000_000:.1f}B"
        elif valuation_sum >= 1_000_000:
            formatted_valuation = f"${valuation_sum / 1_000_000:.1f}M"
        else:
            formatted_valuation = f"${valuation_sum:,.2f}"

        pending_queue = [p for p in all_properties if p.status == 'Pending']
        image_count = PropertyImage.query.count()

        return {
            'properties': all_properties,
            'total_count': total_properties,
            'active_count': active_properties,
            'pending_count': pending_properties,
            'portfolio_valuation': formatted_valuation,
            'pending_queue': pending_queue,
            'image_count': image_count
        }

    @staticmethod
    def update_property_status(prop_id, new_status, user_id=None):
        prop = Property.query.get(prop_id)
        if not prop:
            return {'success': False, 'error': 'Property not found', 'code': 404}

        valid_statuses = ['Published', 'Pending', 'Sold', 'Rented', 'Rejected']
        if new_status not in valid_statuses:
            return {'success': False, 'error': 'Invalid status', 'code': 400}

        prop.status = new_status
        if new_status == 'Published' and user_id:
            prop.approvedBy = user_id
            
        db.session.commit()
        return {'success': True, 'message': 'Property status updated.', 'new_status': new_status}

    @staticmethod
    def approve_property(prop_id, user_id):
        """
        Approves a pending property.
        """
        prop = Property.query.get(prop_id)
        if not prop:
            return {'success': False, 'error': 'Property not found', 'code': 404}

        prop.status = 'Published'
        prop.approvedBy = user_id
        db.session.commit()
        return {'success': True, 'message': 'Property approved successfully.'}

    @staticmethod
    def reject_property(prop_id):
        """
        Rejects a property.
        """
        prop = Property.query.get(prop_id)
        if not prop:
            return {'success': False, 'error': 'Property not found', 'code': 404}

        prop.status = 'Rejected'
        db.session.commit()
        return {'success': True, 'message': 'Property rejected successfully.'}

    @staticmethod
    def delete_property(prop_id):
        """
        Permanently deletes a property listing. Cascading deletes linked images.
        """
        prop = Property.query.get(prop_id)
        if not prop:
            return {'success': False, 'error': 'Property not found', 'code': 404}

        db.session.delete(prop)
        db.session.commit()
        return {'success': True, 'message': 'Property deleted successfully.'}

    @staticmethod
    def update_property_details(prop_id, form_data, new_photos=None):
        """
        Updates the details and associated photos (adds/deletes) of an existing property record.
        """
        prop = Property.query.get(prop_id)
        if not prop:
            return {'success': False, 'error': 'Property not found', 'code': 404}

        title = form_data.get('title', '').strip()
        listing_type = form_data.get('listing_type', '').strip()
        price = form_data.get('price', '').strip()
        property_type = form_data.get('property_type', '').strip()
        area = form_data.get('area', '').strip()
        rooms = form_data.get('rooms', '').strip()
        bathrooms = form_data.get('bathrooms', '').strip()
        floor_number = form_data.get('floor_number', '').strip()
        parking_spots = form_data.get('parking_spots', '').strip()
        description = form_data.get('description', '').strip()
        region = form_data.get('region', '').strip()
        address = form_data.get('address', '').strip()
        latitude = form_data.get('latitude', '').strip()
        longitude = form_data.get('longitude', '').strip()

        # Required validation
        if not title:
            return {'success': False, 'error': 'Title is required.', 'code': 400}
        if not listing_type:
            return {'success': False, 'error': 'Listing type is required.', 'code': 400}
        if not price:
            return {'success': False, 'error': 'Price is required.', 'code': 400}
        if not property_type:
            return {'success': False, 'error': 'Property type is required.', 'code': 400}
        if not area:
            return {'success': False, 'error': 'Area is required.', 'code': 400}
        if not region:
            return {'success': False, 'error': 'Region is required.', 'code': 400}
        if not address:
            return {'success': False, 'error': 'Address is required.', 'code': 400}

        try:
            price_val = float(price)
            area_val = float(area)
            rooms_val = int(rooms) if rooms else None
            bathrooms_val = int(bathrooms) if bathrooms else None
            floor_val = int(floor_number) if floor_number else None
            parking_spots_val = int(parking_spots) if parking_spots else 0
            parking_avail = parking_spots_val > 0
            lat_val = float(latitude) if latitude else None
            lng_val = float(longitude) if longitude else None
        except ValueError:
            return {'success': False, 'error': 'Invalid numeric values provided for specs.', 'code': 400}

        # Update fields
        prop.title = title
        prop.listingType = listing_type
        prop.price = price_val
        prop.propertyType = property_type
        prop.area = area_val
        prop.rooms = rooms_val
        prop.bathrooms = bathrooms_val
        prop.floorNumber = floor_val
        prop.parkingAvailable = parking_avail
        prop.description = description
        prop.location = region
        prop.address = address
        prop.latitude = lat_val
        prop.longitude = lng_val

        try:
            # 1. Handle deleted images
            deleted_ids_str = form_data.get('deleted_image_ids', '')
            if deleted_ids_str:
                deleted_ids = [int(x) for x in deleted_ids_str.split(',') if x.strip().isdigit()]
                for img_id in deleted_ids:
                    img_rec = PropertyImage.query.filter_by(propertyID=prop.propertyID, imageID=img_id).first()
                    if img_rec:
                        db.session.delete(img_rec)
                db.session.flush()

            # 2. Handle new photos
            if new_photos:
                allowed_extensions = {'.png', '.jpg', '.jpeg', '.webp', '.gif'}
                
                # Check if there is currently a main image
                has_main = PropertyImage.query.filter_by(propertyID=prop.propertyID, isMainImage=True).first() is not None
                first_image = not has_main

                for f in new_photos:
                    if f and f.filename != '':
                        _, ext = os.path.splitext(f.filename.lower())
                        if ext not in allowed_extensions:
                            return {
                                'success': False,
                                'error': f'Invalid file type: {f.filename}. Allowed formats: PNG, JPG, JPEG, WEBP, GIF.',
                                'code': 400
                            }

                        file_data = f.read()
                        file_type = getattr(f, 'content_type', 'image/jpeg') or 'image/jpeg'

                        new_img = PropertyImage(
                            propertyID=prop.propertyID,
                            fileData=file_data,
                            fileType=file_type,
                            isMainImage=first_image
                        )
                        db.session.add(new_img)
                        db.session.flush()

                        new_img.imageURL = f"/properties/image/{new_img.imageID}"
                        first_image = False

            db.session.commit()

            # Gather updated image URLs
            updated_imgs = PropertyImage.query.filter_by(propertyID=prop.propertyID).all()
            image_urls_list = [img.imageURL for img in updated_imgs]
            image_urls_str = ",".join(image_urls_list)

            return {
                'success': True,
                'message': 'Property details updated successfully.',
                'image_urls': image_urls_str
            }
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'Database error: {str(e)}', 'code': 500}

