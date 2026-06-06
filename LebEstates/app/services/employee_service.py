from app.models.hr import Employee, Salary
from app.models.users import Users, Role
from app.models.base import db
from datetime import datetime
import bcrypt

def get_all_employees():
    """Retrieve all employees with their associated user and latest salary data."""
    employees = db.session.query(Employee, Users).join(Users, Employee.userID == Users.userID).all()
    
    result = []
    for employee, user in employees:
        # Resolve their most recent salary entry if one exists
        latest_salary = db.session.query(Salary).filter_by(employeeID=employee.employeeID).order_by(Salary.salaryMonth.desc()).first()
        base_salary = float(latest_salary.baseSalary) if latest_salary else 0.0
        
        result.append({
            'employee_id': f"#EMP-{employee.employeeID}",
            'full_name': user.fullName,
            'email': user.email,
            'phone': user.phoneNumber,
            'position': employee.position,
            'status': employee.status, # Active, OnLeave, Terminated
            'user_status': user.status, # Active, Inactive, Blacklisted
            'base_salary': base_salary,
            'hire_date': employee.hireDate.strftime("%b %d, %Y") if employee.hireDate else "N/A",
            'avatar_url': f"https://ui-avatars.com/api/?name={user.fullName.replace(' ', '+')}&background=random",
            'raw_employee': employee,
            'raw_user': user
        })
    return result

def add_employee(data):
    """Add a new employee and their associated user and initial salary records."""
    email = data.get('email', '').strip()
    full_name = data.get('full_name', '').strip()
    phone = data.get('phone', '').strip()
    password = data.get('password', '')
    position = data.get('position', 'Agent').strip()
    base_salary = data.get('base_salary', 0.0)
    
    # Check unique constraints
    existing = Users.query.filter_by(email=email).first()
    if existing:
        return {"success": False, "error": "This email address is already registered.", "code": 400}
        
    # Resolve role: 'Employee'
    employee_role = Role.query.filter_by(roleName='Employee').first()
    if not employee_role:
        try:
            employee_role = Role(roleName='Employee')
            db.session.add(employee_role)
            db.session.commit()
        except Exception as role_err:
            db.session.rollback()
            print(f"Role creation failed: {role_err}")
            return {"success": False, "error": "Database error: Employee role could not be seeded.", "code": 500}
            
    # Hash password with bcrypt
    hashed_pwd = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    try:
        # Create core user profile
        new_user = Users(
            fullName=full_name,
            email=email,
            phoneNumber=phone if phone else None,
            passwordHash=hashed_pwd,
            roleID=employee_role.roleID,
            status='Active'
        )
        db.session.add(new_user)
        db.session.flush()
        
        # Create Employee profile
        new_employee = Employee(
            userID=new_user.userID,
            position=position,
            hireDate=datetime.utcnow().date(),
            status='Active'
        )
        db.session.add(new_employee)
        db.session.flush()
        
        # Add initial salary sheet if base_salary is provided
        if base_salary and float(base_salary) > 0:
            salary_month = datetime.utcnow().strftime("%Y-%m")
            new_salary = Salary(
                employeeID=new_employee.employeeID,
                baseSalary=float(base_salary),
                bonus=0.0,
                deduction=0.0,
                totalSalary=float(base_salary),
                salaryMonth=salary_month,
                paymentStatus='Pending'
            )
            db.session.add(new_salary)
            
        db.session.commit()
        return {"success": True}
    except Exception as e:
        db.session.rollback()
        print(f"Add employee service error: {e}")
        return {"success": False, "error": "An internal error occurred while adding the employee.", "code": 500}

def update_employee(employee_id, data):
    """Update employee details, position, and active base salary."""
    try:
        employee_and_user = db.session.query(Employee, Users).join(Users, Employee.userID == Users.userID).filter(Employee.employeeID == employee_id).first()
        if not employee_and_user:
            return {"success": False, "error": "Employee not found.", "code": 404}
            
        employee, user = employee_and_user
        
        full_name = data.get('full_name')
        email = data.get('email')
        phone = data.get('phone')
        position = data.get('position')
        status = data.get('status')
        base_salary = data.get('base_salary')
        
        if email and email != user.email:
            existing = Users.query.filter_by(email=email).first()
            if existing:
                return {"success": False, "error": "This email address is already in use.", "code": 400}
            user.email = email
            
        if full_name is not None:
            user.fullName = full_name
        if phone is not None:
            user.phoneNumber = phone
        if position is not None:
            employee.position = position
        if status is not None:
            employee.status = status
            
        # Update or create latest salary entry
        if base_salary is not None and float(base_salary) >= 0:
            latest_salary = db.session.query(Salary).filter_by(employeeID=employee_id).order_by(Salary.salaryMonth.desc()).first()
            if latest_salary:
                latest_salary.baseSalary = float(base_salary)
                latest_salary.totalSalary = float(base_salary) + float(latest_salary.bonus) - float(latest_salary.deduction)
            else:
                salary_month = datetime.utcnow().strftime("%Y-%m")
                new_salary = Salary(
                    employeeID=employee_id,
                    baseSalary=float(base_salary),
                    bonus=0.0,
                    deduction=0.0,
                    totalSalary=float(base_salary),
                    salaryMonth=salary_month,
                    paymentStatus='Pending'
                )
                db.session.add(new_salary)
                
        db.session.commit()
        return {"success": True}
    except Exception as e:
        db.session.rollback()
        print(f"Update employee service error: {e}")
        return {"success": False, "error": "An internal error occurred while updating the employee.", "code": 500}

def delete_employee(employee_id):
    """Delete an employee or soft-terminate them if they have database relationships."""
    from app.models.operations import Visit, Consultation, Transaction
    from sqlalchemy.exc import IntegrityError
    
    try:
        employee_and_user = db.session.query(Employee, Users).join(Users, Employee.userID == Users.userID).filter(Employee.employeeID == employee_id).first()
        if not employee_and_user:
            return {"success": False, "error": "Employee not found.", "code": 404}
            
        employee, user = employee_and_user
        
        # Check active operational relationships
        has_visit = db.session.query(Visit).filter_by(employeeID=employee_id).first() is not None
        has_consultation = db.session.query(Consultation).filter_by(assignedEmployeeID=employee_id).first() is not None
        has_transaction = db.session.query(Transaction).filter_by(employeeID=employee_id).first() is not None
        
        has_actions = has_visit or has_consultation or has_transaction
        
        if has_actions:
            # Soft disable: Terminate employee status & Inactive user status
            employee.status = 'Terminated'
            user.status = 'Inactive'
            db.session.commit()
            return {"success": True, "message": "Employee has active operations. Account has been soft-terminated (Terminated) and user deactivated.", "soft_deleted": True}
            
        # Hard delete
        try:
            # Delete related Salaries first
            Salary.query.filter_by(employeeID=employee_id).delete()
            
            db.session.delete(employee)
            db.session.delete(user)
            db.session.commit()
            return {"success": True, "message": "Employee deleted successfully.", "soft_deleted": False}
        except IntegrityError:
            db.session.rollback()
            # Retry soft termination
            employee_and_user = db.session.query(Employee, Users).join(Users, Employee.userID == Users.userID).filter(Employee.employeeID == employee_id).first()
            if employee_and_user:
                employee, user = employee_and_user
                employee.status = 'Terminated'
                user.status = 'Inactive'
                db.session.commit()
                return {"success": True, "message": "Constraint error. Account soft-terminated instead.", "soft_deleted": True}
            return {"success": False, "error": "Failed to delete or terminate employee.", "code": 500}
            
    except Exception as e:
        db.session.rollback()
        print(f"Delete employee error: {e}")
        return {"success": False, "error": "An internal error occurred while deleting the employee.", "code": 500}
