from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from app.services.auth_service import AuthService
from app.services.consultation_service import request_consultation
from app.services.visit_service import VisitService

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def homepage():
    return render_template('homepage.html')


@main_bp.route('/about')
def about():
    return render_template('about.html')


@main_bp.route('/consultation', methods=['GET', 'POST'])
def consultation():
    if request.method == 'POST':
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'You must be logged in to request a consultation.'}), 401
            
        data = request.get_json() if request.is_json else request.form
        res = request_consultation(session['user_id'], data)
        return jsonify(res), res.get('code', 200)

    return render_template('consultation.html')

@main_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
    user = AuthService.get_user_by_id(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.login_page'))
    return render_template('dashboard.html', user=user)

@main_bp.route('/control-panel')
def control_panel():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
    user = AuthService.get_user_by_id(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.login_page'))
    return render_template('control_panel.html', user=user)

@main_bp.route('/contact')
def contact():
    return render_template('contact.html')


@main_bp.route('/visit', methods=['POST'])
def schedule_visit():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'You must be logged in to schedule a visit.'}), 401
        
    data = request.get_json() if request.is_json else request.form
    res = VisitService.schedule_visit(session['user_id'], data)
    return jsonify(res), res.get('code', 200)

