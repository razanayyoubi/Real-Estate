from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, abort, Response
from app.models.base import db
from app.models.users import Users
from app.models.property import Property, PropertyImage
from app.services.customer_service import get_all_customers
from app.services.property_service import PropertyService

properties_bp = Blueprint('properties', __name__)

@properties_bp.route('/sell-rent', methods=['GET'])
def sell_rent_page():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
        
    user = Users.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.login_page'))
        
    role = session.get('role_name', 'Customer').lower()
    is_employee = role in ['admin', 'employee']
    
    active_customers = []
    if is_employee:
        customers_data = get_all_customers()
        active_customers = [c for c in customers_data if c['status'].lower() == 'active']
        
    return render_template('property_add.html', 
                           user=user, 
                           is_employee=is_employee, 
                           active_customers=active_customers)

@properties_bp.route('/sell-rent', methods=['POST'])
def sell_rent_submit():
    if 'user_id' not in session:
        return jsonify({'error': 'You must be logged in to perform this action.'}), 401
        
    user = Users.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found.'}), 404
        
    role = session.get('role_name', 'Customer').lower()
    is_employee = role in ['admin', 'employee']
    
    photos = request.files.getlist('photos')
    
    res = PropertyService.create_property(request.form, photos, user, is_employee)
    if res.get('success'):
        return jsonify({'success': True, 'message': res.get('message')}), 201
    else:
        return jsonify({'error': res.get('error')}), res.get('code', 400)

@properties_bp.route('/properties/image/<int:image_id>', methods=['GET'])
def get_property_image(image_id):
    img = PropertyImage.query.get_or_404(image_id)
    if not img.fileData:
        return abort(404)
    return Response(img.fileData, mimetype=img.fileType or 'image/jpeg')

@properties_bp.route('/properties', methods=['GET'])
def properties_browse():
    properties = Property.query.filter_by(status='Published').order_by(Property.createdAt.desc()).all()
    return render_template('properties_browse.html', properties=properties)

@properties_bp.route('/control-panel/properties', methods=['GET'])
def properties_list():
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return redirect(url_for('auth.login_page'))
        
    user = Users.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.login_page'))

    data = PropertyService.get_all_properties_and_stats()

    return render_template(
        'properties_mgmt.html',
        user=user,
        properties=data['properties'],
        total_count=data['total_count'],
        active_count=data['active_count'],
        pending_count=data['pending_count'],
        portfolio_valuation=data['portfolio_valuation'],
        pending_queue=data['pending_queue'],
        image_count=data['image_count']
    )

@properties_bp.route('/properties/<int:prop_id>/approve', methods=['POST'])
def approve_property(prop_id):
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return jsonify({'error': 'Unauthorized'}), 403
        
    res = PropertyService.approve_property(prop_id, session['user_id'])
    if res.get('success'):
        return jsonify({'success': True, 'message': res.get('message')})
    else:
        return jsonify({'error': res.get('error')}), res.get('code', 400)

@properties_bp.route('/properties/<int:prop_id>/reject', methods=['POST'])
def reject_property(prop_id):
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return jsonify({'error': 'Unauthorized'}), 403
        
    res = PropertyService.reject_property(prop_id)
    if res.get('success'):
        return jsonify({'success': True, 'message': res.get('message')})
    else:
        return jsonify({'error': res.get('error')}), res.get('code', 400)

@properties_bp.route('/properties/<int:prop_id>/update_status', methods=['POST'])
def update_property_status(prop_id):
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({'error': 'Status is required'}), 400
        
    res = PropertyService.update_property_status(prop_id, data['status'], session['user_id'])
    if res.get('success'):
        return jsonify({'success': True, 'message': res.get('message'), 'new_status': res.get('new_status')})
    else:
        return jsonify({'error': res.get('error')}), res.get('code', 400)

@properties_bp.route('/properties/<int:prop_id>/delete', methods=['POST'])
def delete_property(prop_id):
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return jsonify({'error': 'Unauthorized'}), 403
        
    res = PropertyService.delete_property(prop_id)
    if res.get('success'):
        return jsonify({'success': True, 'message': res.get('message')})
    else:
        return jsonify({'error': res.get('error')}), res.get('code', 400)

@properties_bp.route('/properties/<int:prop_id>/edit', methods=['POST'])
def edit_property(prop_id):
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return jsonify({'error': 'Unauthorized'}), 403
        
    new_photos = request.files.getlist('new_photos')
    res = PropertyService.update_property_details(prop_id, request.form, new_photos)
    if res.get('success'):
        return jsonify({
            'success': True,
            'message': res.get('message'),
            'image_urls': res.get('image_urls')
        })
    else:
        return jsonify({'error': res.get('error')}), res.get('code', 400)