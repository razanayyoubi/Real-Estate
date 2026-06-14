from app.models.base import db
from app.models.customer import Customer
from app.models.operations import Consultation

def request_consultation(user_id, data):
    """
    Handle requesting a consultation by a user.
    """
    customer = Customer.query.filter_by(userID=user_id).first()
    if not customer:
        return {'success': False, 'message': 'Only registered customers can request consultations.', 'code': 403}

    consult_type = data.get('consult_type')
    contact_method = data.get('contact_method')
    message = data.get('message')
    pref_date_str = data.get('pref_date')
    pref_time_str = data.get('pref_time')

    if not consult_type:
        return {'success': False, 'message': 'Consultation type is required.', 'code': 400}

    try:
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
        return {'success': True, 'message': 'Request Received!', 'code': 201}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'An error occurred while saving your request: {str(e)}', 'code': 500}
