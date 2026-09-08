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

        is_draft = form_data.get('is_draft') in ['true', '1', True]

        # Required validation
        if not title:
            return {'success': False, 'error': 'Title is required to save property.', 'code': 400}

        if not is_draft:
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

        if not listing_type:
            listing_type = 'Sell'
        if not property_type:
            property_type = 'Apartment'
        if not region:
            region = 'Beirut'
        if not address:
            address = 'Draft Address'

        # Determine Owner ID
        if is_employee:
            owner_id = form_data.get('owner_id')
            if not owner_id and not is_draft:
                return {'success': False, 'error': 'Please select a property owner.', 'code': 400}
            cust = Customer.query.get(owner_id) if owner_id else None
            if not cust:
                cust = Customer.query.filter_by(userID=user.userID).first()
                if not cust:
                    cust = Customer(userID=user.userID, address=address)
                    db.session.add(cust)
                    db.session.commit()
            owner_id = cust.customerID
        else:
            cust = Customer.query.filter_by(userID=user.userID).first()
            if not cust:
                cust = Customer(userID=user.userID, address=address)
                db.session.add(cust)
                db.session.commit()
            owner_id = cust.customerID

        # Determine approval and status
        if is_draft:
            status = 'Draft'
            approved_by = None
        elif is_employee:
            status = 'Published'
            approved_by = user.userID
        else:
            status = 'Pending'
            approved_by = None

        try:
            price_val = float(price) if price else 0.0
            area_val = float(area) if area else 0.0
            rooms_val = int(rooms) if rooms else None
            bathrooms_val = int(bathrooms) if bathrooms else None
            floor_val = int(floor_number) if floor_number else None
            parking_spots_val = int(parking_spots) if parking_spots else 0
            parking_avail = parking_spots_val > 0
            lat_val = float(latitude) if latitude else None
            lng_val = float(longitude) if longitude else None
        except ValueError:
            return {'success': False, 'error': 'Invalid numeric values provided for specs.', 'code': 400}

        # Check if updating an existing draft for this user
        draft_id = form_data.get('draft_id')
        existing_prop = None
        if draft_id:
            existing_prop = Property.query.filter_by(propertyID=draft_id, createdBy=user.userID).first()
        if not existing_prop and is_draft:
            existing_prop = Property.query.filter_by(createdBy=user.userID, status='Draft').first()

        if existing_prop:
            new_prop = existing_prop
            new_prop.ownerID = owner_id
            new_prop.approvedBy = approved_by
            new_prop.title = title
            new_prop.description = description
            new_prop.propertyType = property_type
            new_prop.listingType = listing_type
            new_prop.location = region
            new_prop.address = address
            new_prop.price = price_val
            new_prop.area = area_val
            new_prop.rooms = rooms_val
            new_prop.bathrooms = bathrooms_val
            new_prop.floorNumber = floor_val
            new_prop.parkingAvailable = parking_avail
            new_prop.status = status
            new_prop.latitude = lat_val
            new_prop.longitude = lng_val
            new_prop.updatedAt = datetime.now()
        else:
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

            from app.models.users import AuditLog
            AuditLog.log_action(
                action='ADD',
                table_name='property',
                record_id=new_prop.propertyID,
                description=f"Created property listing '{title}' (Type: '{property_type}', Listing: '{listing_type}', Price: ${price_val:,.2f})",
                user_id=user.userID
            )
            db.session.commit()
            
            # Send notifications & emails (wrapped to prevent SMTP/DB errors from failing listing submission)
            try:
                from app.services.notification_service import NotificationService
                from app.services.email_service import EmailService
                from app.models.users import Users, Role
                
                # 1. Notify creator
                NotificationService.create_notification(
                    user_id=user.userID,
                    message=f"Your property listing '{title}' has been successfully submitted! Status: {'Published' if is_employee else 'Pending'}.",
                    action_url="/control-panel/properties" if is_employee else "/dashboard"
                )

                # Send Property Listing Submitted email if submitted by customer
                if not is_employee and not is_draft and user.email:
                    EmailService.send_templated_email(
                        recipient=user.email,
                        feature_key='PropertySubmitted',
                        default_template_key='PROP-SUBMITTED-V1',
                        placeholders={
                            'CustomerName': user.fullName,
                            'PropertyTitle': title,
                            'PropertyType': property_type,
                            'Location': region,
                            'Price': f"${price_val:,.2f}",
                            'Status': 'Pending Approval'
                        },
                        fallback_subject=f"Property Listing Submitted: {title}",
                        fallback_body=f"Hello {user.fullName}, your property listing for '{title}' has been submitted and is pending review.",
                        email_type="PropertySubmitted",
                        user_id=user.userID
                    )
                
                # 2. Notify admin/employee staff if listing is pending
                if not is_employee:
                    staff_users = Users.query.join(Role).filter(Role.roleName.in_(['admin', 'employee', 'Admin', 'Employee'])).all()
                    for staff in staff_users:
                        NotificationService.create_notification(
                            user_id=staff.userID,
                            message=f"New property listing '{title}' submitted by customer {user.fullName} requires your approval.",
                            action_url="/control-panel/properties"
                        )
            except Exception as notif_err:
                print(f"[Warning] Failed to send property submission notifications: {str(notif_err)}")
                
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'Database error: {str(e)}', 'code': 500}

        if is_draft:
            msg = 'Draft property listing saved successfully!'
        elif is_employee:
            msg = 'Property listing published directly!'
        else:
            msg = 'Property submitted successfully! Pending approval from an employee.'
        return {'success': True, 'message': msg, 'property_id': new_prop.propertyID}

    @staticmethod
    def get_user_draft(user_id):
        draft = Property.query.filter_by(createdBy=user_id, status='Draft').order_by(Property.createdAt.desc()).first()
        if not draft:
            return None
        return {
            'propertyID': draft.propertyID,
            'title': draft.title,
            'description': draft.description or '',
            'propertyType': draft.propertyType,
            'listingType': draft.listingType,
            'location': draft.location,
            'address': draft.address or '',
            'price': float(draft.price or 0.0),
            'area': float(draft.area or 0.0),
            'rooms': draft.rooms or 0,
            'bathrooms': draft.bathrooms or 0,
            'floorNumber': draft.floorNumber or 0,
            'parkingAvailable': bool(draft.parkingAvailable),
            'latitude': float(draft.latitude) if draft.latitude else None,
            'longitude': float(draft.longitude) if draft.longitude else None,
            'ownerID': draft.ownerID
        }

    @staticmethod
    def discard_user_draft(user_id):
        drafts = Property.query.filter_by(createdBy=user_id, status='Draft').all()
        for d in drafts:
            db.session.delete(d)
        db.session.commit()
        return {'success': True, 'message': 'Draft discarded successfully.'}

    @staticmethod
    def get_all_properties_and_stats(filters=None):
        """
        Queries all properties ordered by creation date, applying optional server-side filters,
        computes active/pending counts, valuation sums, and formats valuation for template context.
        """
        query = Property.query.filter(Property.status != 'Draft')

        if filters:
            q = filters.get('server_q', '').strip()
            if q:
                from sqlalchemy import or_
                query = query.filter(or_(
                    Property.title.ilike(f'%{q}%'),
                    Property.description.ilike(f'%{q}%'),
                    Property.location.ilike(f'%{q}%'),
                    Property.address.ilike(f'%{q}%')
                ))

            status = filters.get('status', 'All').strip()
            if status and status.lower() != 'all':
                query = query.filter(Property.status.ilike(status))

            listing_type = filters.get('listing_type', 'All').strip()
            if listing_type and listing_type.lower() != 'all':
                query = query.filter(Property.listingType.ilike(listing_type))

            property_type = filters.get('property_type', 'All').strip()
            if property_type and property_type.lower() != 'all':
                query = query.filter(Property.propertyType.ilike(property_type))

            location = filters.get('location', 'All').strip()
            if location and location.lower() != 'all':
                query = query.filter(Property.location.ilike(location))

        all_properties = query.order_by(Property.createdAt.desc()).all()

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

        # Count properties by type dynamically
        type_counts = {}
        for p in all_properties:
            t = p.propertyType or 'Other'
            type_counts[t] = type_counts.get(t, 0) + 1

        return {
            'properties': all_properties,
            'total_count': total_properties,
            'active_count': active_properties,
            'pending_count': pending_properties,
            'portfolio_valuation': formatted_valuation,
            'pending_queue': pending_queue,
            'image_count': image_count,
            'type_counts': type_counts
        }

    @staticmethod
    def update_property_status(prop_id, new_status, user_id=None):
        prop = Property.query.get(prop_id)
        if not prop:
            return {'success': False, 'error': 'Property not found', 'code': 404}

        valid_statuses = ['Published', 'Pending', 'Draft', 'Sold', 'Rejected', 'Cancelled', 'Refused']
        if new_status not in valid_statuses:
            return {'success': False, 'error': 'Invalid status', 'code': 400}

        old_status = prop.status
        if old_status == new_status:
            return {'success': True, 'message': 'Status is already set to this value.', 'new_status': new_status}

        prop.status = new_status
        if new_status == 'Published' and user_id:
            prop.approvedBy = user_id

        from app.models.users import AuditLog
        AuditLog.log_action(
            action='EDIT',
            table_name='property',
            record_id=prop_id,
            description=f"Updated status of property '{prop.title}' to '{new_status}'",
            user_id=user_id
        )

        # If property is sold or rented, automatically create a placeholder transaction
        if new_status in ['Sold', 'Rented']:
            from app.models.operations import Transaction
            from app.models.hr import Employee

            employee = None
            if user_id:
                employee = Employee.query.filter_by(userID=user_id).first()
            if not employee:
                employee = Employee.query.first()
            employee_id = employee.employeeID if employee else 1

            trans_type = 'Sell' if new_status == 'Sold' else 'Rent'

            if trans_type == 'Sell':
                commission_rate = 5.0
                commission_amount = float(prop.price) * 0.05
            else: # Rent
                commission_rate = 100.0
                commission_amount = float(prop.price)

            placeholder_trans = Transaction(
                propertyID=prop.propertyID,
                customerID=prop.ownerID, # Placeholder client (buyer/tenant) same as owner
                ownerID=prop.ownerID,
                employeeID=employee_id,
                transactionType=trans_type,
                finalPrice=prop.price,
                commissionRate=commission_rate,
                commissionAmount=commission_amount,
                paymentStatus='Escrow', # Default (Pending)
                transactionDate=datetime.now(),
                createdAt=datetime.now()
            )
            db.session.add(placeholder_trans)
            db.session.flush()

            AuditLog.log_action(
                action='INSERT',
                table_name='transaction',
                record_id=placeholder_trans.transactionID,
                description=f"Auto-created placeholder transaction #{placeholder_trans.transactionID} due to property '{prop.title}' status changed to '{new_status}'",
                user_id=user_id
            )

        db.session.commit()

        msg = f"Property status updated to {new_status}."
        if new_status in ['Sold', 'Rented']:
            msg += "\n\n[NOTICE]: A placeholder transaction has been automatically added to the ledger. Please visit the All Transactions page to edit and finalize the stakeholder details, final price, and agent commission splits."

        return {'success': True, 'message': msg, 'new_status': new_status}

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
        from app.models.users import AuditLog
        AuditLog.log_action(
            action='EDIT',
            table_name='property',
            record_id=prop_id,
            description=f"Approved property listing '{prop.title}'",
            user_id=user_id
        )
        db.session.commit()
        
        # Notify the submitter
        try:
            from app.services.notification_service import NotificationService
            from app.services.email_service import EmailService
            from app.models.users import Users
            
            NotificationService.create_notification(
                user_id=prop.createdBy,
                message=f"Your property listing '{prop.title}' has been approved by our staff and is now published!",
                action_url="/properties"
            )

            creator_user = Users.query.get(prop.createdBy)
            if creator_user and creator_user.email:
                prop_url = "http://127.0.0.1:5000/properties"
                EmailService.send_templated_email(
                    recipient=creator_user.email,
                    feature_key='PropertyApproved',
                    default_template_key='PROP-APPROVED-V1',
                    placeholders={
                        'CustomerName': creator_user.fullName,
                        'PropertyTitle': prop.title,
                        'Price': f"${float(prop.price):,.2f}",
                        'Location': prop.location or 'Lebanon',
                        'PropertyUrl': prop_url
                    },
                    fallback_subject=f"Your Property Listing is Now Live: {prop.title}",
                    fallback_body=f"Hello {creator_user.fullName}, your listing for '{prop.title}' is now published and live on LebEstates.",
                    email_type="PropertyApproved",
                    user_id=prop.createdBy
                )
        except Exception as notif_err:
            print(f"[Warning] Failed to send approval notification/email: {str(notif_err)}")

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
        from app.models.users import AuditLog
        AuditLog.log_action(
            action='EDIT',
            table_name='property',
            record_id=prop_id,
            description=f"Rejected property listing '{prop.title}'"
        )
        db.session.commit()
        
        # Notify the submitter
        try:
            from app.services.notification_service import NotificationService
            from app.services.email_service import EmailService
            from app.models.users import Users

            NotificationService.create_notification(
                user_id=prop.createdBy,
                message=f"Your property listing '{prop.title}' has been rejected by our staff.",
                action_url="/dashboard"
            )

            creator_user = Users.query.get(prop.createdBy)
            if creator_user and creator_user.email:
                support_url = "http://127.0.0.1:5000/support"
                EmailService.send_templated_email(
                    recipient=creator_user.email,
                    feature_key='PropertyRejected',
                    default_template_key='PROP-REJECTED-V1',
                    placeholders={
                        'CustomerName': creator_user.fullName,
                        'PropertyTitle': prop.title,
                        'Reason': 'Listing did not meet quality verification or documentation standards.',
                        'SupportUrl': support_url
                    },
                    fallback_subject=f"Update regarding your listing: {prop.title}",
                    fallback_body=f"Hello {creator_user.fullName}, your listing for '{prop.title}' was reviewed and could not be approved at this time.",
                    email_type="PropertyRejected",
                    user_id=prop.createdBy
                )
        except Exception as notif_err:
            print(f"[Warning] Failed to send rejection notification/email: {str(notif_err)}")

        return {'success': True, 'message': 'Property rejected successfully.'}

    @staticmethod
    def delete_property(prop_id):
        """
        Permanently deletes a property listing. Cascading deletes linked images.
        """
        prop = Property.query.get(prop_id)
        if not prop:
            return {'success': False, 'error': 'Property not found', 'code': 404}

        from app.models.users import AuditLog
        AuditLog.log_action(
            action='DELETE',
            table_name='property',
            record_id=prop_id,
            description=f"Deleted property listing '{prop.title}' (Price: ${prop.price:,.2f})"
        )
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

            from app.models.users import AuditLog
            AuditLog.log_action(
                action='EDIT',
                table_name='property',
                record_id=prop_id,
                description=f"Updated details for property listing '{prop.title}' (Price: ${prop.price:,.2f})"
            )
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

    @staticmethod
    def get_property_image(image_id):
        img = PropertyImage.query.get(image_id)
        if not img or not img.fileData:
            return None, None
        return img.fileData, img.fileType or 'image/jpeg'

    @staticmethod
    def query_properties(filters):
        from sqlalchemy import or_
        query = Property.query.filter_by(status='Published')
        
        # Text search
        q = filters.get('q', '').strip()
        if q:
            query = query.filter(or_(
                Property.title.ilike(f'%{q}%'),
                Property.description.ilike(f'%{q}%'),
                Property.location.ilike(f'%{q}%'),
                Property.address.ilike(f'%{q}%')
            ))
            
        # Listing Type
        listing_type = filters.get('listing_type', 'All').strip()
        if listing_type and listing_type.lower() != 'all':
            query = query.filter(Property.listingType.ilike(listing_type))
            
        # Location
        location = filters.get('location', 'All').strip()
        if location and location.lower() != 'all':
            query = query.filter(Property.location.ilike(location))
            
        # Property Types
        property_types = filters.get('property_types', [])
        if isinstance(property_types, str):
            if ',' in property_types:
                property_types = [t.strip() for t in property_types.split(',') if t.strip()]
            elif property_types.strip():
                property_types = [property_types.strip()]
            else:
                property_types = []
        if property_types:
            query = query.filter(Property.propertyType.in_(property_types))
            
        # Price range
        price_min = filters.get('price_min')
        if price_min is not None and price_min != '':
            try:
                query = query.filter(Property.price >= float(price_min))
            except (ValueError, TypeError):
                pass
                
        price_max = filters.get('price_max')
        if price_max is not None and price_max != '':
            try:
                query = query.filter(Property.price <= float(price_max))
            except (ValueError, TypeError):
                pass
                
        # Area range
        area_min = filters.get('area_min')
        if area_min is not None and area_min != '':
            try:
                query = query.filter(Property.area >= float(area_min))
            except (ValueError, TypeError):
                pass
                
        area_max = filters.get('area_max')
        if area_max is not None and area_max != '':
            try:
                query = query.filter(Property.area <= float(area_max))
            except (ValueError, TypeError):
                pass
                
        # Rooms
        rooms = filters.get('rooms')
        if rooms is not None and rooms != '':
            try:
                query = query.filter(Property.rooms >= int(rooms))
            except (ValueError, TypeError):
                pass
                
        # Bathrooms
        bathrooms = filters.get('bathrooms')
        if bathrooms is not None and bathrooms != '':
            try:
                query = query.filter(Property.bathrooms >= int(bathrooms))
            except (ValueError, TypeError):
                pass
                
        # Floor
        floor = filters.get('floor')
        if floor is not None and floor != '':
            try:
                query = query.filter(Property.floorNumber == int(floor))
            except (ValueError, TypeError):
                pass
                
        # Parking
        parking = filters.get('parking', 'Any').strip()
        if parking and parking.lower() == 'available':
            query = query.filter(Property.parkingAvailable == True)
            
        # Sorting
        sort_order = filters.get('sort', 'newest').strip()
        if sort_order == 'price-desc':
            query = query.order_by(Property.price.desc(), Property.propertyID.desc())
        elif sort_order == 'price-asc':
            query = query.order_by(Property.price.asc(), Property.propertyID.desc())
        elif sort_order == 'area-desc':
            query = query.order_by(Property.area.desc(), Property.propertyID.desc())
        else: # newest
            query = query.order_by(Property.createdAt.desc(), Property.propertyID.desc())
            
        return query

    @staticmethod
    def browse_properties(user_id, filters, limit=6):
        from app.models.property import Favorite
        query = PropertyService.query_properties(filters)
        total_count = query.count()
        properties = query.limit(limit).all()
        
        favorite_ids = []
        if user_id:
            customer = Customer.query.filter_by(userID=user_id).first()
            if customer:
                favorites = Favorite.query.filter_by(customerID=customer.customerID).all()
                favorite_ids = [f.propertyID for f in favorites]
                
        return properties, favorite_ids, total_count

    @staticmethod
    def get_properties_api(user_id, data):
        from app.models.property import Favorite
        try:
            offset = int(data.get('offset', 0))
        except (ValueError, TypeError):
            offset = 0
            
        try:
            limit = int(data.get('limit', 6))
        except (ValueError, TypeError):
            limit = 6
            
        query = PropertyService.query_properties(data)
        total_count = query.count()
        properties = query.offset(offset).limit(limit).all()
        
        favorite_ids = []
        if user_id:
            customer = Customer.query.filter_by(userID=user_id).first()
            if customer:
                favorites = Favorite.query.filter_by(customerID=customer.customerID).all()
                favorite_ids = [f.propertyID for f in favorites]
                
        properties_data = []
        for prop in properties:
            images_data = []
            for img in prop.images:
                images_data.append({
                    'imageID': img.imageID,
                    'imageURL': img.imageURL,
                    'isMainImage': img.isMainImage
                })
            properties_data.append({
                'propertyID': prop.propertyID,
                'ownerID': prop.ownerID,
                'createdBy': prop.createdBy,
                'title': prop.title,
                'description': prop.description or '',
                'propertyType': prop.propertyType,
                'listingType': prop.listingType,
                'location': prop.location,
                'address': prop.address or '',
                'price': float(prop.price),
                'area': float(prop.area),
                'rooms': prop.rooms or 0,
                'bathrooms': prop.bathrooms or 0,
                'floorNumber': prop.floorNumber or 0,
                'parkingAvailable': bool(prop.parkingAvailable),
                'latitude': float(prop.latitude) if prop.latitude else None,
                'longitude': float(prop.longitude) if prop.longitude else None,
                'createdAt': prop.createdAt.isoformat() if prop.createdAt else None,
                'is_favorited': prop.propertyID in favorite_ids,
                'images': images_data
            })
            
        return {
            'success': True,
            'properties': properties_data,
            'total_count': total_count
        }

    @staticmethod
    def toggle_favorite(user_id, property_id):
        from app.models.property import Favorite
        prop = Property.query.get(property_id)
        if not prop:
            return {'success': False, 'error': 'Property not found.', 'code': 404}
            
        customer = Customer.query.filter_by(userID=user_id).first()
        if not customer:
            customer = Customer(userID=user_id)
            db.session.add(customer)
            db.session.commit()
            
        favorite = Favorite.query.filter_by(customerID=customer.customerID, propertyID=property_id).first()
        if favorite:
            db.session.delete(favorite)
            action = 'removed'
        else:
            favorite = Favorite(customerID=customer.customerID, propertyID=property_id)
            db.session.add(favorite)
            action = 'added'
            
        try:
            db.session.commit()
            return {'success': True, 'action': action}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'Failed to update favorite: {str(e)}', 'code': 500}

    @staticmethod
    def get_favorite_properties(user_id):
        from app.models.property import Favorite
        customer = Customer.query.filter_by(userID=user_id).first()
        favorite_properties = []
        if customer:
            favorites = Favorite.query.filter_by(customerID=customer.customerID).all()
            favorite_properties = [f.property_obj for f in favorites if f.property_obj and f.property_obj.status == 'Published']
        return favorite_properties

    @staticmethod
    def get_homepage_stats():
        """
        Query total sold properties (using Transactions and a base) to showcase dynamic activity.
        """
        from app.models.operations import Transaction
        sold_count = Transaction.query.filter(
            Transaction.transactionType == 'Sell',
            Transaction.paymentStatus != 'Cancelled'
        ).count()
        total_sold = 2450 + sold_count
        if total_sold >= 1000:
            formatted_sold = f"{total_sold/1000:.1f}k+"
        else:
            formatted_sold = f"{total_sold}+"
        return {
            'properties_sold': formatted_sold
        }



