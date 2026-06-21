from flask import Blueprint, jsonify, session, request
from app.services.notification_service import NotificationService

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/api/notifications', methods=['GET'])
def get_notifications():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    user_id = session['user_id']
    
    if unread_only:
        notifs = NotificationService.get_unread_notifications(user_id)
    else:
        notifs = NotificationService.get_all_notifications(user_id)
        
    data = []
    for n in notifs:
        data.append({
            'notificationID': n.notificationID,
            'message': n.message,
            'isRead': n.isRead,
            'actionURL': n.actionURL or '',
            'createdAt': n.createdAt.strftime('%Y-%m-%d %H:%M:%S')
        })
        
    return jsonify({'success': True, 'notifications': data})

@notifications_bp.route('/api/notifications/unread-count', methods=['GET'])
def get_unread_count():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    unread = NotificationService.get_unread_notifications(user_id)
    return jsonify({'success': True, 'count': len(unread)})

@notifications_bp.route('/api/notifications/<int:notif_id>/read', methods=['POST'])
def mark_read(notif_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        
    res = NotificationService.mark_as_read(notif_id, session['user_id'])
    return jsonify(res)

@notifications_bp.route('/api/notifications/read-all', methods=['POST'])
def mark_all_read():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        
    res = NotificationService.mark_all_as_read(session['user_id'])
    return jsonify(res)
