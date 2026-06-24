from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, abort, Response
from app.services.auth_service import AuthService
from app.services.customer_service import get_all_customers
from app.services.property_service import PropertyService

properties_bp = Blueprint('properties', __name__)

@properties_bp.route('/sell-rent', methods=['GET'])
def sell_rent_page():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
        
    user = AuthService.get_user_by_id(session['user_id'])
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
        
    user = AuthService.get_user_by_id(session['user_id'])
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
    file_data, file_type = PropertyService.get_property_image(image_id)
    if not file_data:
        return abort(404)
    return Response(file_data, mimetype=file_type)

@properties_bp.route('/properties', methods=['GET'])
def properties_browse():
    filters = {
        'q': request.args.get('q', ''),
        'location': request.args.get('location', 'All'),
        'listing_type': request.args.get('listing_type', 'All'),
        'property_types': request.args.get('property_types', ''),
        'price_min': request.args.get('price_min', ''),
        'price_max': request.args.get('price_max', ''),
        'area_min': request.args.get('area_min', ''),
        'area_max': request.args.get('area_max', ''),
        'rooms': request.args.get('rooms', ''),
        'bathrooms': request.args.get('bathrooms', ''),
        'floor': request.args.get('floor', ''),
        'parking': request.args.get('parking', 'Any'),
        'sort': request.args.get('sort', 'newest')
    }
    
    user_id = session.get('user_id')
    properties, favorite_ids, total_count = PropertyService.browse_properties(user_id, filters, limit=6)
            
    return render_template(
        'properties_browse.html', 
        properties=properties, 
        favorite_ids=favorite_ids, 
        total_count=total_count,
        initial_filters=filters
    )

@properties_bp.route('/properties/api/list', methods=['POST'])
def properties_api_list():
    data = request.get_json() or {}
    user_id = session.get('user_id')
    
    res = PropertyService.get_properties_api(user_id, data)
    return jsonify(res)

@properties_bp.route('/control-panel/properties', methods=['GET'])
def properties_list():
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return redirect(url_for('auth.login_page'))
        
    user = AuthService.get_user_by_id(session['user_id'])
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
        image_count=data['image_count'],
        type_counts=data['type_counts']
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

@properties_bp.route('/properties/favorite/toggle', methods=['POST'])
def toggle_favorite():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'You must be logged in to favorite properties.', 'redirect': url_for('auth.login_page')}), 401
        
    data = request.get_json() or {}
    property_id = data.get('property_id')
    if not property_id:
        return jsonify({'success': False, 'error': 'Property ID is required.'}), 400
        
    res = PropertyService.toggle_favorite(session['user_id'], property_id)
    if res.get('success'):
        return jsonify({'success': True, 'action': res.get('action')})
    else:
        return jsonify({'success': False, 'error': res.get('error')}), res.get('code', 500)

@properties_bp.route('/favorites', methods=['GET'])
def favorites_page():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
        
    user = AuthService.get_user_by_id(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.login_page'))

    favorite_properties = PropertyService.get_favorite_properties(user.userID)
    return render_template('favorites.html', user=user, properties=favorite_properties)