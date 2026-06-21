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

    data = ConsultationService.get_consultations_list_data()

    return render_template(
        'consultations_mgmt.html',
        user=user,
        consultations=data['consultations'],
        total_requests=data['total_requests'],
        pending_today=data['pending_today'],
        scheduled_consultations=data['scheduled_consultations'],
        completion_rate=data['completion_rate'],
        employees=data['employees'],
        recent_notes=data['recent_notes']
    )

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
