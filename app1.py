from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory, abort, jsonify
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import urllib.parse
import datetime
from datetime import datetime
from blueprints.view_attendance_blueprint import view_attendance_blueprint
from blueprints.payroll import payroll_blueprint
from blueprints.employee_management import employee_management_blueprint 
from config import Config
from blueprints.profile import profile_blueprint
from blueprints.attendance import attendance_blueprint
from blueprints.leave import leave_blueprint
from blueprints.payroll_employee import payroll_employee_blueprint


app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['DATABASE'] = 'database/employees.db'
app.config.from_object(Config)

# Register the blueprint
app.register_blueprint(view_attendance_blueprint, url_prefix='/view_attendance')
app.register_blueprint(payroll_blueprint, url_prefix='/payroll')
app.register_blueprint(employee_management_blueprint, url_prefix='/employee_management')
app.register_blueprint(profile_blueprint)
app.register_blueprint(attendance_blueprint)
app.register_blueprint(leave_blueprint)
app.register_blueprint(payroll_employee_blueprint)

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
    
# Database creation if not exist
def init_db():
    conn = None
    try:
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                dob TEXT NOT NULL,
                gender TEXT NOT NULL,
                address TEXT NOT NULL,
                state TEXT NOT NULL,
                pincode TEXT NOT NULL,
                phone TEXT NOT NULL,
                alt_phone TEXT,
                email TEXT NOT NULL UNIQUE,
                pan TEXT,
                aadhar TEXT,
                employee_code TEXT NOT NULL UNIQUE,
                aadhar_path TEXT,
                pan_path TEXT,
                bank_passbook_path TEXT,
                profile_photo_path TEXT NOT NULL,
                bank_name TEXT NOT NULL,
                bank TEXT NOT NULL,
                account TEXT NOT NULL,
                ifsc TEXT NOT NULL,
                uan TEXT NOT NULL,
                experience TEXT NOT NULL,
                company_name TEXT,
                designation TEXT,
                function_performed TEXT,
                period_of_work TEXT,
                reason_for_leaving TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                time TEXT,
                status TEXT NOT NULL,
                reason_for_absence_halfday TEXT,
                FOREIGN KEY(employee_id) REFERENCES employees(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leave_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                reason TEXT NOT NULL,
                status TEXT DEFAULT 'Pending',
                FOREIGN KEY(employee_id) REFERENCES employees(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employee_login (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_login (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payroll (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                basic_salary REAL NOT NULL,
                hra REAL NOT NULL,
                special_allowance REAL NOT NULL,
                lta REAL NOT NULL,
                retention_bonus REAL,
                mobile_internet REAL,
                professional_development REAL,
                office_attire REAL,
                other_allowance REAL,
                additional_payment REAL,
                additional_bonus REAL,
                pf REAL NOT NULL,
                vpf REAL,
                lwf REAL,
                pt REAL NOT NULL,
                lwf_arrears REAL,
                other_deductions REAL,
                tds REAL NOT NULL,
                net_pay REAL NOT NULL,
                FOREIGN KEY(employee_id) REFERENCES employees(id)
            )
        ''')
        conn.commit()
    except sqlite3.Error as e:
        print("SQLite error:", e)
    finally:
        if conn:
            conn.close()


import datetime  # this is for below route (essential) Ensure this line is at the top of your app1.py script

@app.route('/')
def index():
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    try:
        # Connect to the database
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()

        # Fetch the count of employees
        cursor.execute('SELECT COUNT(*) FROM employees')
        employees_count = cursor.fetchone()[0]

        if employees_count == 0:
            # No employees found
            return render_template('index.html', error="No employees found in the database.")
        
        # Fetch all employees from the database
        cursor.execute('SELECT * FROM employees')
        employees_data = cursor.fetchall()  # Fetches all rows
        
        if not employees_data:
            # No employees found
            return render_template('index.html', error="No employees found in the database.")
        
        employees = []
        for employee_data in employees_data:
            # Convert the fetched data into a dictionary
            employee = {
                'id': employee_data[0],
                'name': employee_data[1],
                'dob': employee_data[2],
                # Add other fields as needed
            }
            employees.append(employee)
        
        # Fetch leave requests summary for all employees
        cursor.execute('SELECT COUNT(*) FROM leave_requests')
        leave_requests_count = cursor.fetchone()[0]
        
        # Fetch leave requests by status
        cursor.execute('SELECT COUNT(*) FROM leave_requests WHERE status = ?', ('Pending',))
        pending_requests_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM leave_requests WHERE status = ?', ('Approved',))
        approved_requests_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM leave_requests WHERE status = ?', ('Rejected',))
        rejected_requests_count = cursor.fetchone()[0]
        
        # Fetch attendance summary for all employees for today
        today_date = datetime.date.today().strftime('%Y-%m-%d')
        
        cursor.execute('SELECT COUNT(*) FROM attendance WHERE date = ? AND status = ?', (today_date, 'Present'))
        present_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM attendance WHERE date = ? AND status = ?', (today_date, 'Absent'))
        absent_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM attendance WHERE date = ? AND status = ?', (today_date, 'Half Day'))
        Half_Day_count = cursor.fetchone()[0]
        
    except sqlite3.Error as e:
        # Handle database connection errors
        return render_template('index.html', error=f"Database error: {e}")
    
    finally:
        # Close the database connection
        if conn:
            conn.close()
    
    # Pass the employee data and summaries to the template context
    return render_template('index.html', employees=employees,
                           employees_count=employees_count, 
                           leave_requests_count=leave_requests_count,
                           pending_requests_count=pending_requests_count,
                           approved_requests_count=approved_requests_count,
                           rejected_requests_count=rejected_requests_count,
                           present_count=present_count,
                           absent_count=absent_count,
                           Half_Day_count=Half_Day_count)

# Update the employee_dashboard Route to Include the Current Employee's Data:
# Modify the employee_dashboard route to pass the current employee's data to the template.

@app.route('/employee_dashboard')
def employee_dashboard():
    if 'username' not in session or session['role'] != 'employee':
        return redirect(url_for('login'))

    name = session['username']  # Assuming the employee's name is stored in the session as 'username'

    conn = None
    employee = None
    try:
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM employees WHERE name = ?', (name,))
        employee = cursor.fetchone()
    except sqlite3.Error as e:
        print("SQLite error:", e)
        flash('An error occurred while retrieving employee data!', 'error')
    finally:
        if conn:
            conn.close()

    if not employee:
        flash('Employee details not found. Please check your credentials or contact the administrator.', 'error')
        return redirect(url_for('logout'))

    # Convert employee data to a dictionary
    employee_dict = {
        'id': employee[0],
        'name': employee[1],
        'dob': employee[2],
        'gender': employee[3],
        'address': employee[4],
        'state': employee[5],
        'pincode': employee[6],
        'phone': employee[7],
        'alt_phone': employee[8],
        'email': employee[9],
        'pan': employee[10],
        'aadhar': employee[11],
        'employee_code': employee[12],
        'aadhar_path': employee[13],
        'pan_path': employee[14],
        'bank_passbook_path': employee[15],
        'profile_photo_path': employee[16],
        'bank_name': employee[17],
        'bank': employee[18],
        'account': employee[19],
        'ifsc': employee[20],
        'uan': employee[21],
        'experience': employee[22],
        'company_name': employee[23],
        'designation': employee[24],
        'function_performed': employee[25],
        'period_of_work': employee[26],
        'reason_for_leaving': employee[27]
    }

    flash('Welcome, {}!'.format(name), 'success')
    return render_template('employee_dashboard.html', employee=employee_dict)

@app.route('/view_employee')
def view_employee():
    conn = None
    try:
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM employees')
        employees = cursor.fetchall()
    except sqlite3.Error as e:
        print("SQLite error:", e)
        flash('An error occurred while retrieving employees!', 'error')
        employees = []
    finally:
        if conn:
            conn.close()

    return render_template('view_employee.html', employees=employees)

@app.route('/get_employee_details/<int:id>')
def get_employee_details(id):
    conn = None
    try:
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM employees WHERE id = ?', (id,))
        employee = cursor.fetchone()
        # print("Employee:", employee)  # Debug statement
        if employee:
            employee_dict = {
                'id': employee[0],
                'name': employee[1],
                'dob': employee[2],
                'gender': employee[3],
                'address': employee[4] if employee[4] else None,
                'state': employee[5] if employee[5] else None,
                'pincode': employee[6] if employee[6] else None,
                'phone': employee[7] if employee[7] else None,
                'alt_phone': employee[8] if employee[8] else None,
                'email': employee[9] if employee[9] else None,
                'pan': employee[10] if employee[10] else None,
                'aadhar': employee[11] if employee[11] else None,
                'employee_code': employee[12] if employee[12] else None,
                'aadhar_doc_path': employee[13] if employee[13] else None,
                'pan_doc_path': employee[14] if employee[14] else None,
                'bank_passbook_doc_path': employee[15] if employee[15] else None,
                'photo_doc_path': employee[16] if employee[16] else None,
                'bank_name': employee[18] if employee[18] else None,
                'bank': employee[19] if employee[19] else None,
                'account': employee[20] if employee[20] else None,
                'ifsc': employee[21] if employee[21] else None,
                'uan': employee[22] if employee[22] else None,
                'experience': employee[23] if employee[23] else None,
                'company_name': employee[24] if employee[24] else None,
                'designation': employee[25] if employee[25] else None,
                'function_performed': employee[26] if employee[26] else None,
                'period_of_work': employee[27] if employee[27] else None,
                'reason_for_leaving': employee[28] if len(employee) > 28 and employee[28] else None
            }
            # print("Employee Dictionary:", employee_dict)  # Debug statement to whether the employees details are getting fetched or not.
            return jsonify({'employee': employee_dict})
        else:
            return jsonify({'error': 'Employee not found'}), 404
    except sqlite3.Error as e:
        print("SQLite error:", e)
        return jsonify({'error': 'An error occurred while retrieving employee details'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/employees')
def list_employees():
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    cursor.execute('SELECT id, name FROM employees')
    employees = cursor.fetchall()
    conn.close()
    return render_template('employees.html', employees=employees)

@app.route('/mark_attendance', methods=['GET', 'POST'])
def mark_attendance():
    conn = None
    try:
        if request.method == 'POST':
            employee_id = request.form['employee_id']
            date = request.form['date']
            status = request.form['status']

            # Get the current time
            current_time = datetime.datetime.now().strftime('%H:%M:%S')

            # Get the reason for absence (if half-day, specify AM/PM)
            reason_for_absence_halfday = request.form.get('reason_for_absence_halfday')

            conn = sqlite3.connect(app.config['DATABASE'])
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO attendance (employee_id, date, time, status, reason_for_absence_halfday)
                VALUES (?, ?, ?, ?, ?)
            ''', (employee_id, date, current_time, status, reason_for_absence_halfday))
            conn.commit()
            flash('Attendance marked successfully!')

            return redirect(url_for('mark_attendance'))

        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        # Retrieve a list of all employees from the employees table, or an empty list if there are no employees
        cursor.execute('SELECT id, name FROM employees')
        employees = cursor.fetchall() or []
    except sqlite3.Error as e:
        print("SQLite error:", e)
        flash('An error occurred while processing the request!', 'error')
        employees = []
    finally:
        if conn:
            conn.close()

    return render_template('mark_attendance.html', employees=employees)

@app.route('/leave_request', methods=['GET', 'POST'])
def leave_request():
    conn = None
    try:
        if request.method == 'POST':
            employee_id = request.form['employee_id']
            start_date = request.form['start_date']
            end_date = request.form['end_date']
            reason = request.form['reason']

            conn = sqlite3.connect(app.config['DATABASE'])
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO leave_requests (employee_id, start_date, end_date, reason)
                VALUES (?, ?, ?, ?)
            ''', (employee_id, start_date, end_date, reason))
            conn.commit()
            flash('Leave request submitted successfully!')

            return redirect(url_for('index'))

        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM employees')
        employees = cursor.fetchall()
    except sqlite3.Error as e:
        print("SQLite error:", e)
        flash('An error occurred while processing the request!', 'error')
        employees = []
    finally:
        if conn:
            conn.close()

    return render_template('leave_request.html', employees=employees)

@app.route('/register_admin', methods=['GET', 'POST'])
def register_admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        try:
            add_admin(username, hashed_password)
            flash('Admin registered successfully!')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists!')
    return render_template('register_admin.html')

@app.route('/register_employee', methods=['GET', 'POST'])
def register_employee():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        try:
            add_employee_login(username, hashed_password)
            flash('Employee registered successfully!')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists!')
    return render_template('register_employee.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        
        if role == 'employee':
            cursor.execute('SELECT * FROM employee_login WHERE username = ?', (username,))
        elif role == 'admin':
            cursor.execute('SELECT * FROM admin_login WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user[2], password):
            session['username'] = username
            session['role'] = role
            if role == 'admin':
                return redirect(url_for('index'))
            elif role == 'employee':
                return redirect(url_for('employee_dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('user_authentication.html')

@app.route('/static/css/images/<path:path>')
def send_static_images(path):
    return send_from_directory('static/css/images', path)

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))

# Helper functions to add admins and employees
def add_admin(username, password):
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    cursor.execute('INSERT INTO admin_login (username, password) VALUES (?, ?)', (username, password))
    conn.commit()
    conn.close()

def add_employee_login(username, password):
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    cursor.execute('INSERT INTO employee_login (username, password) VALUES (?, ?)', (username, password))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
