from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from app.models.base import db
from app.models.users import Users
from app.models.operations import Visit
from app.models.hr import Employee
from datetime import datetime

visits_bp = Blueprint('visits', __name__)

@visits_bp.route('/control-panel/visits', methods=['GET'])
def visits_list():
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return redirect(url_for('auth.login_page'))
        
    user = Users.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.login_page'))

    # Query all visits, ordered by date and time desc
    visits = Visit.query.order_by(Visit.visitDate.desc(), Visit.visitTime.desc()).all()

    # Dynamic Stats Calculations
    total_requests = len(visits)
    
    today_date = datetime.now().date()
    pending_today = Visit.query.filter(Visit.visitDate == today_date, Visit.status == 'Scheduled').count()
    
    confirmed_visits = Visit.query.filter_by(status='Scheduled').count()
    
    completed_count = Visit.query.filter_by(status='Completed').count()
    completion_rate = (completed_count / total_requests * 100) if total_requests > 0 else 0.0

    # Fetch all active employees to populate the consultant dropdowns
    employees = Employee.query.join(Users).filter(Employee.status == 'Active').order_by(Users.fullName).all()

    # Fetch 3 recent visits with non-empty notes
    recent_notes = Visit.query.filter(Visit.notes != None, Visit.notes != '').order_by(Visit.updatedAt.desc()).limit(3).all()

    return render_template(
        'visits_mgmt.html',
        user=user,
        visits=visits,
        total_requests=total_requests,
        pending_today=pending_today,
        confirmed_visits=confirmed_visits,
        completion_rate=completion_rate,
        employees=employees,
        recent_notes=recent_notes
    )

@visits_bp.route('/control-panel/visits/<int:visit_id>/update_status', methods=['POST'])
def update_visit_status(visit_id):
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return jsonify({'error': 'Unauthorized'}), 403

    visit = Visit.query.get_or_404(visit_id)
    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({'error': 'Status is required'}), 400

    new_status = data['status']
    if new_status not in ['Scheduled', 'Completed', 'Cancelled']:
        return jsonify({'error': 'Invalid status'}), 400

    try:
        visit.status = new_status
        visit.updatedAt = datetime.now()
        db.session.commit()
        return jsonify({'success': True, 'message': 'Visit status updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update status: {str(e)}'}), 500

@visits_bp.route('/control-panel/visits/<int:visit_id>/update_consultant', methods=['POST'])
def update_visit_consultant(visit_id):
    if 'user_id' not in session or session.get('role_name', '').lower() not in ['admin', 'employee']:
        return jsonify({'error': 'Unauthorized'}), 403

    visit = Visit.query.get_or_404(visit_id)
    data = request.get_json()
    if not data or 'employee_id' not in data:
        return jsonify({'error': 'Consultant is required'}), 400

    new_employee_id = data['employee_id']
    employee = Employee.query.get(new_employee_id)
    if not employee:
        return jsonify({'error': 'Employee not found'}), 404

    try:
        visit.employeeID = new_employee_id
        visit.updatedAt = datetime.now()
        db.session.commit()
        return jsonify({'success': True, 'message': 'Consultant assigned successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update consultant: {str(e)}'}), 500

