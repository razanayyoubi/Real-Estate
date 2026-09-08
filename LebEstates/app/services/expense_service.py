from app.models.base import db
from app.models.expenses import OfficeExpense
from app.models.users import AuditLog
from datetime import datetime

class ExpenseService:
    @staticmethod
    def get_all_expenses(filters=None):
        query = OfficeExpense.query

        if filters:
            q = filters.get('server_q', '').strip()
            if q:
                from sqlalchemy import or_
                query = query.filter(or_(
                    OfficeExpense.title.ilike(f'%{q}%'),
                    OfficeExpense.category.ilike(f'%{q}%'),
                    OfficeExpense.notes.ilike(f'%{q}%')
                ))

            status = filters.get('status', 'All').strip()
            if status and status.lower() != 'all':
                query = query.filter(OfficeExpense.status.ilike(status))

            category = filters.get('category', 'All').strip()
            if category and category.lower() != 'all':
                query = query.filter(OfficeExpense.category.ilike(category))

        expenses = query.order_by(OfficeExpense.expenseDate.desc()).all()
        
        all_unfiltered = OfficeExpense.query.all()
        total_amount = sum(e.amount for e in all_unfiltered)
        paid_amount = sum(e.amount for e in all_unfiltered if e.status == 'Paid')
        pending_amount = sum(e.amount for e in all_unfiltered if e.status != 'Paid')
        
        categories = ['Office Rent', 'Utilities', 'Marketing', 'Software Subscriptions', 'Legal & Professional', 'Maintenance', 'Miscellaneous']
        category_totals = {c: sum(e.amount for e in all_unfiltered if e.category == c) for c in categories}
        
        return {
            'expenses': expenses,
            'total_amount': total_amount,
            'paid_amount': paid_amount,
            'pending_amount': pending_amount,
            'categories': categories,
            'category_totals': category_totals
        }

    @staticmethod
    def create_expense(data, user_id):
        title = data.get('title', '').strip()
        category = data.get('category', '').strip()
        amount_str = data.get('amount')
        expense_date_str = data.get('expense_date')
        status = data.get('status', 'Paid')
        notes = data.get('notes', '').strip()

        if not title or not category or not amount_str:
            return {'success': False, 'error': 'Title, category, and amount are required.', 'code': 400}

        try:
            amount = float(amount_str)
            if amount <= 0:
                return {'success': False, 'error': 'Amount must be greater than zero.', 'code': 400}
        except ValueError:
            return {'success': False, 'error': 'Invalid amount format.', 'code': 400}

        expense_date = datetime.now().date()
        if expense_date_str:
            try:
                expense_date = datetime.strptime(expense_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        is_recurring = bool(data.get('is_recurring'))
        recurrence_type = data.get('recurrence_type', 'Monthly')

        try:
            new_expense = OfficeExpense(
                title=title,
                category=category,
                amount=amount,
                expenseDate=expense_date,
                status=status,
                isRecurring=is_recurring,
                recurrenceType=recurrence_type,
                notes=notes,
                createdByID=user_id
            )
            db.session.add(new_expense)
            db.session.flush()

            AuditLog.log_action(
                action='ADD',
                table_name='office_expenses',
                record_id=new_expense.expenseID,
                description=f"Created office expense '{title}' (${amount:,.2f})",
                user_id=user_id
            )

            db.session.commit()
            return {'success': True, 'message': 'Office expense recorded successfully!'}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'Database error: {str(e)}', 'code': 500}

    @staticmethod
    def update_expense(expense_id, data, user_id):
        expense = OfficeExpense.query.get(expense_id)
        if not expense:
            return {'success': False, 'error': 'Expense record not found.', 'code': 404}

        title = data.get('title', '').strip()
        category = data.get('category', '').strip()
        amount_str = data.get('amount')
        expense_date_str = data.get('expense_date')
        status = data.get('status')
        notes = data.get('notes', '').strip()

        if title: expense.title = title
        if category: expense.category = category
        if amount_str:
            try:
                expense.amount = float(amount_str)
            except ValueError:
                pass
        if expense_date_str:
            try:
                expense.expenseDate = datetime.strptime(expense_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        if status: expense.status = status
        expense.notes = notes
        expense.updatedAt = datetime.now()

        try:
            AuditLog.log_action(
                action='EDIT',
                table_name='office_expenses',
                record_id=expense_id,
                description=f"Updated office expense #{expense_id} '{expense.title}'",
                user_id=user_id
            )
            db.session.commit()
            return {'success': True, 'message': 'Expense updated successfully!'}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'Database error: {str(e)}', 'code': 500}

    @staticmethod
    def delete_expense(expense_id, user_id):
        expense = OfficeExpense.query.get(expense_id)
        if not expense:
            return {'success': False, 'error': 'Expense record not found.', 'code': 404}

        try:
            AuditLog.log_action(
                action='DELETE',
                table_name='office_expenses',
                record_id=expense_id,
                description=f"Deleted office expense #{expense_id} '{expense.title}'",
                user_id=user_id
            )
            db.session.delete(expense)
            db.session.commit()
            return {'success': True, 'message': 'Expense record deleted.'}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'Database error: {str(e)}', 'code': 500}
