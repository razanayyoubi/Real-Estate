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

    data = VisitService.get_visits_list_data()

    return render_template(
        'visits_mgmt.html',
        user=user,
        visits=data['visits'],
        total_requests=data['total_requests'],
        pending_today=data['pending_today'],
        confirmed_visits=data['confirmed_visits'],
        completion_rate=data['completion_rate'],
        employees=data['employees'],
        recent_notes=data['recent_notes']
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


