from datetime import datetime
from app.models.base import db
from app.models.hr import Employee, Salary
from app.models.operations import Transaction
from app.models.users import Users, AuditLog

class SalaryService:
    @staticmethod
    def get_payroll_data(selected_month=None):
        """
        Dynamically calculates base salaries, commissions, net payouts,
        completion percentages, ledger details, and audit history.
        """
        if not selected_month:
            selected_month = datetime.utcnow().strftime("%Y-%m")

        # 1. Fetch all employees
        employees = db.session.query(Employee, Users).join(Users, Employee.userID == Users.userID).all()

        ledger = []
        total_base = 0.0
        total_commissions = 0.0
        paid_count = 0
        total_count = 0

        for employee, user in employees:
            # Get salary record for selected month
            salary_record = Salary.query.filter_by(employeeID=employee.employeeID, salaryMonth=selected_month).first()
            
            # If no salary record exists, resolve the latest base salary as a fallback
            if salary_record:
                base_salary = float(salary_record.baseSalary)
                bonus = float(salary_record.bonus or 0.0)
                deduction = float(salary_record.deduction or 0.0)
                status = salary_record.paymentStatus
                salary_id = salary_record.salaryID
            else:
                # Find latest salary record for base salary fallback
                latest_salary = Salary.query.filter_by(employeeID=employee.employeeID).order_by(Salary.salaryMonth.desc()).first()
                base_salary = float(latest_salary.baseSalary) if latest_salary else 0.0
                bonus = 0.0
                deduction = 0.0
                status = 'Pending'
                salary_id = None

            # Calculate commissions for this employee in the selected month
            # Filter Closed transactions for this employee
            emp_transactions = Transaction.query.filter_by(employeeID=employee.employeeID).filter(Transaction.paymentStatus == 'Closed').all()
            
            comm_sum = 0.0
            for t in emp_transactions:
                # Match month
                if t.transactionDate and t.transactionDate.strftime("%Y-%m") == selected_month:
                    rate = float(t.agentCommissionRate or 30.0)
                    comm_amt = float(t.commissionAmount)
                    comm_sum += comm_amt * (rate / 100.0)

            net_value = base_salary + comm_sum + bonus - deduction
            
            total_base += base_salary
            total_commissions += comm_sum
            total_count += 1
            if status == 'Paid':
                paid_count += 1

            # Initials
            parts = user.fullName.split()
            initials = "".join([p[0].upper() for p in parts[:2]]) if parts else "EMP"

            ledger.append({
                'employee_id': employee.employeeID,
                'tres_id': f"TRES-88{employee.employeeID:02d}",
                'name': user.fullName,
                'initials': initials,
                'position': employee.position,
                'base_salary': base_salary,
                'commission': comm_sum,
                'net_value': net_value,
                'status': status,
                'salary_id': salary_id
            })

        # Calculate KPIs
        total_disbursement = total_base + total_commissions
        completion_percent = int((paid_count / total_count) * 100) if total_count > 0 else 0

        # Timeline logs
        audit_logs = AuditLog.query.filter(
            AuditLog.tableName.in_(['employee', 'salary', 'commission_setting'])
        ).order_by(AuditLog.logID.desc()).limit(5).all()

        timeline = []
        for log in audit_logs:
            timeline.append({
                'title': log.action,
                'description': log.description,
                'date': log.createdAt.strftime("%b %d, %Y at %I:%M %p") if hasattr(log, 'createdAt') and log.createdAt else "Recent"
            })

        # Mock fallback if timeline is empty
        if not timeline:
            timeline = [
                {'title': 'System Active', 'description': 'Treasury operations active and running.', 'date': 'System'}
            ]

        # Available months for cycle filter (last 3 months)
        # Generate last 3 months
        from datetime import timedelta
        months = []
        now = datetime.utcnow()
        for i in range(3):
            m = now - timedelta(days=30 * i)
            val = m.strftime("%Y-%m")
            label = m.strftime("%b %Y")
            months.append({'value': val, 'label': label})

        return {
            'ledger': ledger,
            'selected_month': selected_month,
            'months': months,
            'stats': {
                'total_disbursement': total_disbursement,
                'completion_percent': completion_percent,
                'paid_count': paid_count,
                'total_count': total_count,
                'commissions_paid': total_commissions
            },
            'timeline': timeline
        }

    @staticmethod
    def approve_payout(employee_id, month):
        """
        Marks an employee's salary record for the given month as 'Paid'.
        Creates the salary record if it doesn't exist yet.
        """
        salary_record = Salary.query.filter_by(employeeID=employee_id, salaryMonth=month).first()
        
        # If it doesn't exist, create it from the latest known base salary
        if not salary_record:
            latest_salary = Salary.query.filter_by(employeeID=employee_id).order_by(Salary.salaryMonth.desc()).first()
            base_salary = float(latest_salary.baseSalary) if latest_salary else 0.0
            
            salary_record = Salary(
                employeeID=employee_id,
                baseSalary=base_salary,
                bonus=0.0,
                deduction=0.0,
                totalSalary=base_salary,
                salaryMonth=month,
                paymentStatus='Paid'
            )
            db.session.add(salary_record)
        else:
            salary_record.paymentStatus = 'Paid'

        db.session.flush()

        # Log audit trail
        from app.models.users import AuditLog
        emp = Employee.query.get(employee_id)
        user = Users.query.get(emp.userID) if emp else None
        emp_name = user.fullName if user else f"ID {employee_id}"
        
        AuditLog.log_action(
            action='EDIT',
            table_name='salary',
            record_id=salary_record.salaryID,
            description=f"Approved payroll payout of ${float(salary_record.totalSalary):,.2f} for '{emp_name}' (Month: {month})"
        )
        db.session.commit()
        return {"success": True, "message": "Payout approved successfully!"}
