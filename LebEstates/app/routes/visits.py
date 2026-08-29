from datetime import datetime
from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from app.services.auth_service import AuthService
from app.services.visit_service import VisitService

visits_bp = Blueprint('visits', __name__)

@visits_bp.route('/control-panel/visits', methods=['GET'])
def visits_list():
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return redirect(url_for('auth.login_page'))
        
    user = AuthService.get_user_by_id(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.login_page'))

    filters = {
        'server_q': request.args.get('server_q', ''),
        'status': request.args.get('status', 'All'),
        'consultant_id': request.args.get('consultant_id', 'All')
    }

    data = VisitService.get_visits_list_data(filters)

    return render_template(
        'visits_mgmt.html',
        user=user,
        visits=data['visits'],
        total_requests=data['total_requests'],
        pending_today=data['pending_today'],
        confirmed_visits=data['confirmed_visits'],
        completion_rate=data['completion_rate'],
        employees=data['employees'],
        recent_notes=data['recent_notes'],
        filters=filters,
        now=datetime.now()
    )

@visits_bp.route('/control-panel/visits/<int:visit_id>/update_status', methods=['POST'])
def update_visit_status(visit_id):
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({'error': 'Status is required'}), 400

    res = VisitService.update_status(visit_id, data['status'])
    if res.get('success'):
        return jsonify({'success': True, 'message': res.get('message')})
    else:
        return jsonify({'error': res.get('error')}), res.get('code', 500)

@visits_bp.route('/control-panel/visits/<int:visit_id>/update_consultant', methods=['POST'])
def update_visit_consultant(visit_id):
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    if not data or 'employee_id' not in data:
        return jsonify({'error': 'Consultant is required'}), 400

    res = VisitService.update_consultant(visit_id, data['employee_id'])
    if res.get('success'):
        return jsonify({'success': True, 'message': res.get('message')})
    else:
        return jsonify({'error': res.get('error')}), res.get('code', 500)


@visits_bp.route('/control-panel/visits/api/search-users', methods=['GET'])
def search_users():
    role = request.args.get('role', 'customer')
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
    
    from sqlalchemy import or_
    from app.models.base import db
    from app.models.users import Users
    from app.models.customer import Customer
    from app.models.hr import Employee

    if role == 'employee':
        results = db.session.query(Employee, Users).join(Users, Employee.userID == Users.userID).filter(
            Employee.status == 'Active',
            or_(
                Users.fullName.ilike(f'%{q}%'),
                Users.email.ilike(f'%{q}%'),
                Users.phoneNumber.ilike(f'%{q}%')
            )
        ).limit(20).all()
        
        return jsonify([
            {
                'id': emp.employeeID,
                'fullName': user.fullName,
                'email': user.email,
                'phone': user.phoneNumber or 'N/A'
            } for emp, user in results
        ])
    else: # customer
        results = db.session.query(Customer, Users).join(Users, Customer.userID == Users.userID).filter(
            or_(
                Users.fullName.ilike(f'%{q}%'),
                Users.email.ilike(f'%{q}%'),
                Users.phoneNumber.ilike(f'%{q}%')
            )
        ).limit(20).all()
        
        return jsonify([
            {
                'id': cust.customerID,
                'fullName': user.fullName,
                'email': user.email,
                'phone': user.phoneNumber or 'N/A'
            } for cust, user in results
        ])


@visits_bp.route('/control-panel/visits/api/search-properties', methods=['GET'])
def search_properties():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
    
    from sqlalchemy import or_
    from app.models.property import Property
    results = Property.query.filter(
        Property.status != 'Draft',
        or_(
            Property.title.ilike(f'%{q}%'),
            Property.location.ilike(f'%{q}%'),
            Property.address.ilike(f'%{q}%')
        )
    ).limit(20).all()
    
    return jsonify([
        {
            'id': prop.propertyID,
            'title': prop.title,
            'location': prop.location,
            'price': float(prop.price)
        } for prop in results
    ])


@visits_bp.route('/control-panel/visits/api/employees/availability', methods=['GET'])
def check_employee_availability():
    date_str = request.args.get('date', '').strip()
    time_str = request.args.get('time', '').strip()
    exclude_visit_id = request.args.get('exclude_visit_id')
    exclude_consultation_id = request.args.get('exclude_consultation_id')
    
    if not date_str or not time_str:
        return jsonify({'error': 'Date and time are required'}), 400
    
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        target_time = datetime.strptime(time_str, '%H:%M').time()
    except ValueError:
        return jsonify({'error': 'Invalid date or time format'}), 400
    
    from app.models.hr import Employee
    from app.models.users import Users, db
    from app.models.operations import Visit, Consultation
    
    employees = db.session.query(Employee, Users).join(Users, Employee.userID == Users.userID).filter(Employee.status == 'Active').all()
    
    def time_to_minutes(t):
        return t.hour * 60 + t.minute
    
    target_mins = time_to_minutes(target_time)
    
    results = []
    for emp, user in employees:
        conflict_reason = None
        
        # Check scheduled visits (within 60 mins conflict)
        v_query = Visit.query.filter(
            Visit.employeeID == emp.employeeID,
            Visit.visitDate == target_date,
            Visit.status == 'Scheduled'
        )
        if exclude_visit_id:
            v_query = v_query.filter(Visit.visitID != int(exclude_visit_id))
        
        for v in v_query.all():
            v_mins = time_to_minutes(v.visitTime)
            if abs(v_mins - target_mins) < 60:
                conflict_reason = f"Has visit scheduled at {v.visitTime.strftime('%I:%M %p')} for Property '{v.property_obj.title}'"
                break
        
        if not conflict_reason:
            # Check scheduled consultations (within 60 mins conflict)
            c_query = Consultation.query.filter(
                Consultation.assignedEmployeeID == emp.employeeID,
                Consultation.scheduledDate == target_date,
                Consultation.status == 'Scheduled'
            )
            if exclude_consultation_id:
                c_query = c_query.filter(Consultation.consultationID != int(exclude_consultation_id))
                
            for c in c_query.all():
                c_mins = time_to_minutes(c.scheduledTime) if c.scheduledTime else None
                if c_mins is not None and abs(c_mins - target_mins) < 60:
                    conflict_reason = f"Has consultation scheduled at {c.scheduledTime.strftime('%I:%M %p')}"
                    break
                    
        results.append({
            'id': emp.employeeID,
            'fullName': user.fullName,
            'has_conflict': conflict_reason is not None,
            'conflict_reason': conflict_reason
        })
        
    return jsonify(results)


@visits_bp.route('/control-panel/visits/create', methods=['POST'])
def create_visit():
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.get_json() or {}
    property_id = data.get('property_id')
    customer_id = data.get('customer_id')
    employee_id = data.get('employee_id') # Can be null or 'All'/'Unassigned'
    visit_date_str = data.get('visit_date')
    visit_time_str = data.get('visit_time')
    notes = data.get('notes', '')
    status = data.get('status', 'Pending')
    
    if not property_id or not customer_id or not visit_date_str or not visit_time_str:
        return jsonify({'error': 'Property, Customer, Date, and Time are required'}), 400
        
    try:
        visit_date = datetime.strptime(visit_date_str, '%Y-%m-%d').date()
        visit_time = datetime.strptime(visit_time_str, '%H:%M').time()
    except ValueError:
        return jsonify({'error': 'Invalid date or time format'}), 400
        
    if employee_id == '' or employee_id == 'Unassigned' or employee_id is None or str(employee_id).lower() == 'all':
        emp_val = None
    else:
        emp_val = int(employee_id)
        
    from app.models.operations import Visit
    from app.models.users import AuditLog, db
    
    try:
        visit = Visit(
            propertyID=int(property_id),
            customerID=int(customer_id),
            employeeID=emp_val,
            visitDate=visit_date,
            visitTime=visit_time,
            status=status,
            notes=notes
        )
        db.session.add(visit)
        db.session.commit()
        
        AuditLog.log_action(
            action='ADD',
            table_name='visit',
            record_id=visit.visitID,
            description=f"Scheduled visit for Property ID {property_id} and Customer ID {customer_id} on {visit_date} at {visit_time}.",
            user_id=session['user_id']
        )
        db.session.commit()
        return jsonify({'success': True, 'message': 'Visit scheduled successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to schedule visit: {str(e)}'}), 500


@visits_bp.route('/control-panel/visits/<int:visit_id>/edit', methods=['POST'])
def edit_visit(visit_id):
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return jsonify({'error': 'Unauthorized'}), 403
        
    from app.models.operations import Visit
    visit = Visit.query.get_or_404(visit_id)
    
    data = request.get_json() or {}
    property_id = data.get('property_id')
    customer_id = data.get('customer_id')
    employee_id = data.get('employee_id')
    visit_date_str = data.get('visit_date')
    visit_time_str = data.get('visit_time')
    status = data.get('status')
    notes = data.get('notes')
    
    if not property_id or not customer_id or not visit_date_str or not visit_time_str:
        return jsonify({'error': 'Property, Customer, Date, and Time are required'}), 400
        
    try:
        visit_date = datetime.strptime(visit_date_str, '%Y-%m-%d').date()
        visit_time = datetime.strptime(visit_time_str, '%H:%M').time()
    except ValueError:
        return jsonify({'error': 'Invalid date or time format'}), 400
        
    if employee_id == '' or employee_id == 'Unassigned' or employee_id is None or str(employee_id).lower() == 'all':
        emp_val = None
    else:
        emp_val = int(employee_id)
        
    from app.models.users import AuditLog, db
    
    try:
        visit.propertyID = int(property_id)
        visit.customerID = int(customer_id)
        visit.employeeID = emp_val
        visit.visitDate = visit_date
        visit.visitTime = visit_time
        if status:
            visit.status = status
        if notes is not None:
            visit.notes = notes
            
        db.session.commit()
        
        AuditLog.log_action(
            action='UPDATE',
            table_name='visit',
            record_id=visit.visitID,
            description=f"Updated visit details for Visit ID {visit.visitID}.",
            user_id=session['user_id']
        )
        db.session.commit()
        return jsonify({'success': True, 'message': 'Visit updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update visit: {str(e)}'}), 500



