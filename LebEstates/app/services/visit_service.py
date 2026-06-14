from datetime import datetime
from app.models.base import db
from app.models.operations import Visit
from app.models.customer import Customer
from app.models.hr import Employee
from app.models.users import Users

class VisitService:
    @staticmethod
    def schedule_visit(user_id, data):
        """
        Schedule a property visit for a customer.
        """
        customer = Customer.query.filter_by(userID=user_id).first()
        if not customer:
            return {'success': False, 'message': 'Only registered customers can schedule visits.', 'code': 403}

        property_id = data.get('property_id')
        visit_date = data.get('visit_date')
        visit_time = data.get('visit_time')
        notes = data.get('notes', '')

        if not property_id or not visit_date or not visit_time:
            return {'success': False, 'message': 'Property, date, and time are required.', 'code': 400}

        try:
            # Assign to first available employee for now
            employee = Employee.query.first()
            if not employee:
                return {'success': False, 'message': 'No agents available to assign.', 'code': 500}

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
            return {'success': True, 'message': 'Visit Scheduled Successfully!', 'code': 201}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'An error occurred while saving your visit: {str(e)}', 'code': 500}

    @staticmethod
    def get_visits_list_data():
        """
        Fetch all visits, stats, active employees, and recent notes.
        """
        visits = Visit.query.order_by(Visit.visitDate.desc(), Visit.visitTime.desc()).all()

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

        return {
            'visits': visits,
            'total_requests': total_requests,
            'pending_today': pending_today,
            'confirmed_visits': confirmed_visits,
            'completion_rate': completion_rate,
            'employees': employees,
            'recent_notes': recent_notes
        }

    @staticmethod
    def update_status(visit_id, new_status):
        """
        Update visit status.
        """
        visit = Visit.query.get(visit_id)
        if not visit:
            return {'success': False, 'error': 'Visit not found', 'code': 404}

        if new_status not in ['Scheduled', 'Completed', 'Cancelled']:
            return {'success': False, 'error': 'Invalid status', 'code': 400}

        try:
            visit.status = new_status
            visit.updatedAt = datetime.now()
            db.session.commit()
            return {'success': True, 'message': 'Visit status updated successfully'}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'Failed to update status: {str(e)}', 'code': 500}

    @staticmethod
    def update_consultant(visit_id, employee_id):
        """
        Assign a consultant to a visit.
        """
        visit = Visit.query.get(visit_id)
        if not visit:
            return {'success': False, 'error': 'Visit not found', 'code': 404}

        employee = Employee.query.get(employee_id)
        if not employee:
            return {'success': False, 'error': 'Employee not found', 'code': 404}

        try:
            visit.employeeID = employee_id
            visit.updatedAt = datetime.now()
            db.session.commit()
            return {'success': True, 'message': 'Consultant assigned successfully'}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'Failed to update consultant: {str(e)}', 'code': 500}
