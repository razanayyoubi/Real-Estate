from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from app.services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET'])
def register_page():
    return render_template('signup.html')

@auth_bp.route('/register', methods=['POST'])
def register_submit():
    # Supports both AJAX JSON payloads and standard form payloads
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip()
    phone_number = data.get('phone_number', '').strip()
    password = data.get('password', '')
    address = data.get('address', '').strip()

    # 1. Server-side required validation
    if not full_name:
        return jsonify({'error': 'Full Name is required.'}), 400
    if not email:
        return jsonify({'error': 'Email address is required.'}), 400
    if not password or len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters long.'}), 400

    # 2. Delegate registration logic to AuthService
    result = AuthService.register_customer(full_name, email, phone_number, password, address)
    if result["success"]:
        return jsonify({'message': 'Registration successful!'}), 201
    else:
        return jsonify({'error': result["error"]}), result["code"]

@auth_bp.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

@auth_bp.route('/login', methods=['POST'])
def login_submit():
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and Password are required.'}), 400

    # Delegate verification logic to AuthService
    result = AuthService.verify_credentials(email, password)
    if result["success"]:
        session['user_id'] = result['user_id']
        session['role_id'] = result['role_id']
        session['full_name'] = result['full_name']
        session['role_name'] = result['role_name']
        
        return jsonify({
            'message': 'Login successful',
            'redirect_url': '/' 
        }), 200
    else:
        return jsonify({'error': result['error']}), result['code']

@auth_bp.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect(url_for('auth.login_page'))

