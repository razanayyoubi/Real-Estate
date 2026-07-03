import re
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash, session, abort
from functools import wraps
from app.models.base import db
from app.models.users import Users, SupportSession, SupportMessage

support_bp = Blueprint('support', __name__, url_prefix='/support')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login_page'))
        return f(*args, **kwargs)
    return decorated_function

def employee_or_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login_page'))
        role = session.get('role_name', '').lower()
        if role not in ['admin', 'employee']:
            flash("You do not have permission to access this page.", "danger")
            return redirect(url_for('main.homepage'))
        return f(*args, **kwargs)
    return decorated_function


# --- CUSTOMER VIEWS ---

@support_bp.route('/')
@login_required
def customer_sessions():
    user_id = session['user_id']
    # Check if the user is a customer (employees should go to their control-panel hub)
    role = session.get('role_name', '').lower()
    if role in ['admin', 'employee']:
        return redirect(url_for('support.employee_hub'))

    sessions = SupportSession.query.filter_by(customerID=user_id).order_by(SupportSession.createdAt.desc()).all()
    return render_template('support/support_list.html', sessions=sessions)

@support_bp.route('/create', methods=['POST'])
@login_required
def create_session():
    user_id = session['user_id']
    subject = request.form.get('subject', '').strip()
    if not subject:
        flash('Subject is required to start a support request.', 'danger')
        return redirect(url_for('support.customer_sessions'))

    try:
        new_session = SupportSession(
            customerID=user_id,
            subject=subject,
            status='Open'
        )
        db.session.add(new_session)
        db.session.commit()
        flash('Support request created successfully! An agent will join shortly.', 'success')
        return redirect(url_for('support.customer_chat', session_id=new_session.sessionID))
    except Exception as e:
        db.session.rollback()
        flash(f'Error starting support session: {str(e)}', 'danger')
        return redirect(url_for('support.customer_sessions'))

@support_bp.route('/chat/<int:session_id>')
@login_required
def customer_chat(session_id):
    user_id = session['user_id']
    chat_session = SupportSession.query.get_or_404(session_id)

    # Check if this chat belongs to the logged-in customer
    if chat_session.customerID != user_id:
        abort(403)

    return render_template('support/chat_room.html', chat_session=chat_session, is_employee=False)


# --- EMPLOYEE / ADMIN VIEWS ---

@support_bp.route('/control-panel')
@employee_or_admin_required
def employee_hub():
    user_id = session['user_id']
    role = session.get('role_name', '').lower()

    if role == 'admin':
        # Admin sees all requests
        unassigned_chats = SupportSession.query.filter_by(employeeID=None, status='Open').order_by(SupportSession.createdAt.asc()).all()
        my_chats = SupportSession.query.filter(SupportSession.employeeID != None, SupportSession.status != 'Closed').order_by(SupportSession.createdAt.desc()).all()
        closed_chats = SupportSession.query.filter_by(status='Closed').order_by(SupportSession.closedAt.desc()).all()
    else:
        # Employee sees only unassigned and their own chats
        unassigned_chats = SupportSession.query.filter_by(employeeID=None, status='Open').order_by(SupportSession.createdAt.asc()).all()
        my_chats = SupportSession.query.filter_by(employeeID=user_id, status='Active').order_by(SupportSession.createdAt.desc()).all()
        closed_chats = SupportSession.query.filter_by(employeeID=user_id, status='Closed').order_by(SupportSession.closedAt.desc()).all()

    return render_template('support/admin_hub.html', 
                           unassigned_chats=unassigned_chats, 
                           my_chats=my_chats, 
                           closed_chats=closed_chats,
                           is_admin=(role == 'admin'))

@support_bp.route('/control-panel/assign/<int:session_id>', methods=['POST'])
@employee_or_admin_required
def assign_session(session_id):
    user_id = session['user_id']
    chat_session = SupportSession.query.get_or_404(session_id)

    if chat_session.employeeID is not None:
        flash('This chat session has already been claimed by another agent.', 'warning')
        return redirect(url_for('support.employee_hub'))

    try:
        chat_session.employeeID = user_id
        chat_session.status = 'Active'
        db.session.commit()
        
        # Add automated system join message
        sys_msg = SupportMessage(
            sessionID=chat_session.sessionID,
            senderID=user_id,
            messageText="Hello! I have joined this chat support session. How can I help you today?"
        )
        db.session.add(sys_msg)
        db.session.commit()
        
        flash('Chat session assigned successfully!', 'success')
        return redirect(url_for('support.employee_chat', session_id=chat_session.sessionID))
    except Exception as e:
        db.session.rollback()
        flash(f'Error claiming session: {str(e)}', 'danger')
        return redirect(url_for('support.employee_hub'))

@support_bp.route('/control-panel/chat/<int:session_id>')
@employee_or_admin_required
def employee_chat(session_id):
    user_id = session['user_id']
    role = session.get('role_name', '').lower()
    chat_session = SupportSession.query.get_or_404(session_id)

    # Admins can see all chats, employees can only see chats assigned to them
    if role != 'admin' and chat_session.employeeID != user_id:
        flash('Access Denied. You are not assigned to this support session.', 'danger')
        return redirect(url_for('support.employee_hub'))

    return render_template('support/chat_room.html', chat_session=chat_session, is_employee=True)


@support_bp.route('/api/control-panel/updates', methods=['GET'])
@employee_or_admin_required
def control_panel_updates():
    user_id = session['user_id']
    role = session.get('role_name', '').lower()

    if role == 'admin':
        unassigned_chats = SupportSession.query.filter_by(employeeID=None, status='Open').order_by(SupportSession.createdAt.asc()).all()
        my_chats = SupportSession.query.filter(SupportSession.employeeID != None, SupportSession.status != 'Closed').order_by(SupportSession.createdAt.desc()).all()
        closed_chats = SupportSession.query.filter_by(status='Closed').order_by(SupportSession.closedAt.desc()).all()
    else:
        unassigned_chats = SupportSession.query.filter_by(employeeID=None, status='Open').order_by(SupportSession.createdAt.asc()).all()
        my_chats = SupportSession.query.filter_by(employeeID=user_id, status='Active').order_by(SupportSession.createdAt.desc()).all()
        closed_chats = SupportSession.query.filter_by(employeeID=user_id, status='Closed').order_by(SupportSession.closedAt.desc()).all()

    unassigned_data = []
    for chat in unassigned_chats:
        unassigned_data.append({
            'sessionID': chat.sessionID,
            'subject': chat.subject,
            'customerName': chat.customer.fullName,
            'customerEmail': chat.customer.email,
            'createdAt': chat.createdAt.strftime('%b %d, %H:%M')
        })

    my_chats_data = []
    for chat in my_chats:
        my_chats_data.append({
            'sessionID': chat.sessionID,
            'subject': chat.subject,
            'customerName': chat.customer.fullName,
            'employeeName': chat.employee.fullName if chat.employee else 'Unassigned',
            'createdAt': chat.createdAt.strftime('%b %d, %H:%M')
        })

    closed_chats_data = []
    for chat in closed_chats:
        closed_chats_data.append({
            'sessionID': chat.sessionID,
            'subject': chat.subject,
            'customerName': chat.customer.fullName,
            'employeeName': chat.employee.fullName if chat.employee else '--',
            'closedAt': chat.closedAt.strftime('%b %d, %Y - %H:%M') if chat.closedAt else '--',
            'closedBy': chat.closedBy.fullName if chat.closedBy else '',
            'rating': chat.rating,
            'ratingFeedback': chat.ratingFeedback or '(No feedback submitted)'
        })

    return jsonify({
        'success': True,
        'unassigned_chats': unassigned_data,
        'my_chats': my_chats_data,
        'closed_chats': closed_chats_data
    })


# --- SHARED CHAT REST API ENDPOINTS ---

@support_bp.route('/api/messages/<int:session_id>', methods=['GET'])
@login_required
def get_messages(session_id):
    user_id = session['user_id']
    role = session.get('role_name', '').lower()
    chat_session = SupportSession.query.get_or_404(session_id)

    # Access security check
    if role not in ['admin', 'employee'] and chat_session.customerID != user_id:
        return jsonify({'success': False, 'error': 'Access Denied.'}), 403
    if role == 'employee' and chat_session.employeeID != user_id:
        return jsonify({'success': False, 'error': 'Access Denied.'}), 403

    since_id = request.args.get('since_id', 0, type=int)

    query = SupportMessage.query.filter_by(sessionID=session_id)
    if since_id > 0:
        query = query.filter(SupportMessage.messageID > since_id)
    
    messages = query.order_by(SupportMessage.createdAt.asc()).all()

    messages_data = []
    for msg in messages:
        messages_data.append({
            'messageID': msg.messageID,
            'senderID': msg.senderID,
            'senderName': msg.sender.fullName,
            'senderRole': msg.sender.role.roleName,
            'messageText': msg.messageText,
            'createdAt': msg.createdAt.strftime('%H:%M:%S')
        })

    return jsonify({
        'success': True,
        'messages': messages_data,
        'status': chat_session.status,
        'employee_name': chat_session.employee.fullName if chat_session.employee else None,
        'rating': chat_session.rating,
        'ratingFeedback': chat_session.ratingFeedback
    })

@support_bp.route('/api/send/<int:session_id>', methods=['POST'])
@login_required
def send_message(session_id):
    user_id = session['user_id']
    role = session.get('role_name', '').lower()
    chat_session = SupportSession.query.get_or_404(session_id)

    # Access security check
    if role not in ['admin', 'employee'] and chat_session.customerID != user_id:
        return jsonify({'success': False, 'error': 'Access Denied.'}), 403
    if role == 'employee' and chat_session.employeeID != user_id:
        return jsonify({'success': False, 'error': 'Access Denied.'}), 403

    if chat_session.status == 'Closed':
        return jsonify({'success': False, 'error': 'This support session is closed.'}), 400

    data = request.json or {}
    message_text = data.get('messageText', '').strip()
    if not message_text:
        return jsonify({'success': False, 'error': 'Message text is required.'}), 400

    try:
        new_msg = SupportMessage(
            sessionID=session_id,
            senderID=user_id,
            messageText=message_text
        )
        db.session.add(new_msg)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': {
                'messageID': new_msg.messageID,
                'senderID': new_msg.senderID,
                'senderName': new_msg.sender.fullName,
                'messageText': new_msg.messageText,
                'createdAt': new_msg.createdAt.strftime('%H:%M:%S')
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@support_bp.route('/api/close/<int:session_id>', methods=['POST'])
@login_required
def close_session(session_id):
    user_id = session['user_id']
    role = session.get('role_name', '').lower()
    chat_session = SupportSession.query.get_or_404(session_id)

    # Access security check
    if role not in ['admin', 'employee'] and chat_session.customerID != user_id:
        return jsonify({'success': False, 'error': 'Access Denied.'}), 403
    if role == 'employee' and chat_session.employeeID != user_id:
        return jsonify({'success': False, 'error': 'Access Denied.'}), 403

    try:
        chat_session.status = 'Closed'
        chat_session.closedAt = datetime.now()
        chat_session.closedByUserID = user_id
        db.session.commit()
        return jsonify({'success': True, 'message': 'Support session closed successfully.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@support_bp.route('/api/rate/<int:session_id>', methods=['POST'])
@login_required
def rate_session(session_id):
    user_id = session['user_id']
    chat_session = SupportSession.query.get_or_404(session_id)

    # Only the customer of this session can submit a rating
    if chat_session.customerID != user_id:
        return jsonify({'success': False, 'error': 'Access Denied.'}), 403

    if chat_session.status != 'Closed':
        return jsonify({'success': False, 'error': 'Can only rate closed support sessions.'}), 400

    data = request.json or {}
    rating = data.get('rating')
    feedback = data.get('feedback', '').strip()

    if rating is None or not (1 <= int(rating) <= 5):
        return jsonify({'success': False, 'error': 'Rating must be an integer between 1 and 5.'}), 400

    try:
        chat_session.rating = int(rating)
        chat_session.ratingFeedback = feedback
        db.session.commit()
        return jsonify({'success': True, 'message': 'Thank you for your rating!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
