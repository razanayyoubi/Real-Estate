from flask import Blueprint, render_template, session, redirect, url_for
from app.models.users import Users

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def homepage():
    return render_template('homepage.html')


@main_bp.route('/about')
def about():
    return render_template('about.html')

from flask import request, jsonify
from app.models.operations import Consultation, Visit
from app.models.customer import Customer
from app.models.hr import Employee
from app.models.base import db

@main_bp.route('/consultation', methods=['GET', 'POST'])
def consultation():
    if request.method == 'POST':
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'You must be logged in to request a consultation.'}), 401
            
        customer = Customer.query.filter_by(userID=session['user_id']).first()
        if not customer:
            return jsonify({'success': False, 'message': 'Only registered customers can request consultations.'}), 403
            
        data = request.get_json() if request.is_json else request.form
        
        consult_type = data.get('consult_type')
        contact_method = data.get('contact_method')
        message = data.get('message')
        pref_date_str = data.get('pref_date')
        pref_time_str = data.get('pref_time')
        
        if not consult_type:
            return jsonify({'success': False, 'message': 'Consultation type is required.'}), 400
            
        try:
            # We can pass strings for date and time if they are in standard format, SQLAlchemy handles them
            new_consultation = Consultation(
                customerID=customer.customerID,
                consultationType=consult_type,
                preferredMethod=contact_method,
                message=message,
                status='Pending',
                scheduledDate=pref_date_str if pref_date_str else None,
                scheduledTime=pref_time_str if pref_time_str else None
            )
            db.session.add(new_consultation)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Request Received!'}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': 'An error occurred while saving your request.'}), 500

    return render_template('consultation.html')

@main_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
    user = Users.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.login_page'))
    return render_template('dashboard.html', user=user)

@main_bp.route('/control-panel')
def control_panel():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
    user = Users.query.get(session['user_id'])
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
        
    customer = Customer.query.filter_by(userID=session['user_id']).first()
    if not customer:
        return jsonify({'success': False, 'message': 'Only registered customers can schedule visits.'}), 403
        
    data = request.get_json() if request.is_json else request.form
    
    property_id = data.get('property_id')
    visit_date = data.get('visit_date')
    visit_time = data.get('visit_time')
    notes = data.get('notes', '')
    
    if not property_id or not visit_date or not visit_time:
        return jsonify({'success': False, 'message': 'Property, date, and time are required.'}), 400
        
    try:
        # Assign to first available employee for now
        employee = Employee.query.first()
        if not employee:
            return jsonify({'success': False, 'message': 'No agents available to assign.'}), 500
            
        new_visit = Visit(
            propertyID=property_id,
            customerID=customer.customerID,
            employeeID=employee.employeeID,
            visitDate=visit_date,
            visitTime=visit_time,
            status='Scheduled',
            notes=notes
        )
        db.session.add(new_visit)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Visit Scheduled Successfully!'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'An error occurred while saving your visit: {str(e)}'}), 500
