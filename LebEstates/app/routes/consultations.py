from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from app.services.auth_service import AuthService
from app.services.consultation_service import ConsultationService

consultations_bp = Blueprint('consultations', __name__)

@consultations_bp.route('/control-panel/consultations', methods=['GET'])
def consultations_list():
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return redirect(url_for('auth.login_page'))
        
    user = AuthService.get_user_by_id(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.login_page'))

    page = request.args.get('page', 1, type=int)

    filters = {
        'server_q': request.args.get('server_q', ''),
        'status': request.args.get('status', 'All'),
        'consultant_id': request.args.get('consultant_id', 'All'),
        'method': request.args.get('method', 'All')
    }

    data = ConsultationService.get_consultations_list_data(filters, page=page, per_page=10)

    return render_template(
        'consultations_mgmt.html',
        user=user,
        consultations=data['consultations'],
        total_requests=data['total_requests'],
        pending_today=data['pending_today'],
        scheduled_consultations=data['scheduled_consultations'],
        completion_rate=data['completion_rate'],
        employees=data['employees'],
        recent_notes=data['recent_notes'],
        filters=filters,
        page=data['page'],
        per_page=data['per_page'],
        total_pages=data['total_pages'],
        total_filtered_count=data['total_filtered_count']
    )

@consultations_bp.route('/control-panel/customers/<int:customer_id>/details', methods=['GET'])
def get_customer_details(customer_id):
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return jsonify({'error': 'Unauthorized'}), 403

    info = ConsultationService.get_customer_details(customer_id)
    if not info:
        return jsonify({'error': 'Customer not found'}), 404
    return jsonify(info)

@consultations_bp.route('/control-panel/consultations/<int:consultation_id>/update_status', methods=['POST'])
def update_consultation_status(consultation_id):
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({'error': 'Status is required'}), 400

    res = ConsultationService.update_status(consultation_id, data['status'])
    if res.get('success'):
        return jsonify({'success': True, 'message': res.get('message')})
    else:
        return jsonify({'error': res.get('error')}), res.get('code', 500)

@consultations_bp.route('/control-panel/consultations/<int:consultation_id>/update_consultant', methods=['POST'])
def update_consultation_consultant(consultation_id):
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    employee_id = data.get('employee_id') if data else None

    res = ConsultationService.update_consultant(consultation_id, employee_id)
    if res.get('success'):
        return jsonify({'success': True, 'message': res.get('message')})
    else:
        return jsonify({'error': res.get('error')}), res.get('code', 500)

@consultations_bp.route('/control-panel/consultations/<int:consultation_id>/update_schedule', methods=['POST'])
def update_consultation_schedule(consultation_id):
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    date_str = data.get('scheduled_date')
    time_str = data.get('scheduled_time')

    res = ConsultationService.update_schedule(consultation_id, date_str, time_str)
    if res.get('success'):
        return jsonify({'success': True, 'message': res.get('message')})
    else:
        return jsonify({'error': res.get('error')}), res.get('code', 500)

@consultations_bp.route('/control-panel/consultations/<int:consultation_id>/update_notes', methods=['POST'])
def update_consultation_notes(consultation_id):
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    if not data or 'notes' not in data:
        return jsonify({'error': 'Notes content is required'}), 400

    res = ConsultationService.update_notes(consultation_id, data['notes'])
    if res.get('success'):
        return jsonify({'success': True, 'message': res.get('message')})
    else:
        return jsonify({'error': res.get('error')}), res.get('code', 500)


@consultations_bp.route('/control-panel/consultations/create', methods=['POST'])
def create_consultation():
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.get_json() or {}
    customer_id = data.get('customer_id')
    assigned_employee_id = data.get('assigned_employee_id') # can be None
    consultation_type = data.get('consultation_type')
    preferred_method = data.get('preferred_method')
    message = data.get('message', '')
    scheduled_date_str = data.get('scheduled_date')
    scheduled_time_str = data.get('scheduled_time')
    status = data.get('status', 'Pending')
    notes = data.get('notes', '')
    
    if not customer_id or not consultation_type or not preferred_method:
        return jsonify({'error': 'Customer, Type, and Preferred Method are required'}), 400
        
    scheduled_date = None
    scheduled_time = None
    
    if scheduled_date_str:
        try:
            scheduled_date = datetime.strptime(scheduled_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
    if scheduled_time_str:
        try:
            scheduled_time = datetime.strptime(scheduled_time_str, '%H:%M').time()
        except ValueError:
            return jsonify({'error': 'Invalid time format'}), 400
            
    if assigned_employee_id == '' or assigned_employee_id == 'Unassigned' or assigned_employee_id is None or str(assigned_employee_id).lower() == 'all':
        emp_val = None
    else:
        emp_val = int(assigned_employee_id)
        
    from app.models.operations import Consultation
    from app.models.users import AuditLog, db
    
    try:
        consultation = Consultation(
            customerID=int(customer_id),
            assignedEmployeeID=emp_val,
            consultationType=consultation_type,
            preferredMethod=preferred_method,
            message=message,
            scheduledDate=scheduled_date,
            scheduledTime=scheduled_time,
            status=status,
            notes=notes
        )
        db.session.add(consultation)
        db.session.commit()
        
        AuditLog.log_action(
            action='ADD',
            table_name='consultation',
            record_id=consultation.consultationID,
            description=f"Created consultation request for Customer ID {customer_id}.",
            user_id=session['user_id']
        )
        db.session.commit()
        return jsonify({'success': True, 'message': 'Consultation created successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create consultation: {str(e)}'}), 500


@consultations_bp.route('/control-panel/consultations/<int:consultation_id>/edit', methods=['POST'])
def edit_consultation(consultation_id):
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return jsonify({'error': 'Unauthorized'}), 403
        
    from app.models.operations import Consultation
    consultation = Consultation.query.get_or_404(consultation_id)
    
    data = request.get_json() or {}
    customer_id = data.get('customer_id')
    assigned_employee_id = data.get('assigned_employee_id')
    consultation_type = data.get('consultation_type')
    preferred_method = data.get('preferred_method')
    message = data.get('message')
    scheduled_date_str = data.get('scheduled_date')
    scheduled_time_str = data.get('scheduled_time')
    status = data.get('status')
    notes = data.get('notes')
    
    if not customer_id or not consultation_type or not preferred_method:
        return jsonify({'error': 'Customer, Type, and Preferred Method are required'}), 400
        
    scheduled_date = None
    scheduled_time = None
    
    if scheduled_date_str:
        try:
            scheduled_date = datetime.strptime(scheduled_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
    if scheduled_time_str:
        try:
            scheduled_time = datetime.strptime(scheduled_time_str, '%H:%M').time()
        except ValueError:
            return jsonify({'error': 'Invalid time format'}), 400
            
    if assigned_employee_id == '' or assigned_employee_id == 'Unassigned' or assigned_employee_id is None or str(assigned_employee_id).lower() == 'all':
        emp_val = None
    else:
        emp_val = int(assigned_employee_id)
        
    from app.models.users import AuditLog, db
    
    try:
        consultation.customerID = int(customer_id)
        consultation.assignedEmployeeID = emp_val
        consultation.consultationType = consultation_type
        consultation.preferredMethod = preferred_method
        if message is not None:
            consultation.message = message
        consultation.scheduledDate = scheduled_date
        consultation.scheduledTime = scheduled_time
        if status:
            consultation.status = status
        if notes is not None:
            consultation.notes = notes
            
        db.session.commit()
        
        AuditLog.log_action(
            action='UPDATE',
            table_name='consultation',
            record_id=consultation.consultationID,
            description=f"Updated consultation details for Consultation ID {consultation.consultationID}.",
            user_id=session['user_id']
        )
        db.session.commit()
        return jsonify({'success': True, 'message': 'Consultation updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update consultation: {str(e)}'}), 500
