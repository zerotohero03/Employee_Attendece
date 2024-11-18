from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory, abort, jsonify
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import logging
import urllib.parse
from datetime import datetime
from blueprints.view_attendance_blueprint import view_attendance_blueprint
from blueprints.payroll import payroll_blueprint
from config import Config

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['DATABASE'] = 'database/employees.db'
app.config.from_object(Config)

# Initialize logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

# Register the blueprint
app.register_blueprint(view_attendance_blueprint, url_prefix='/view_attendance')
app.register_blueprint(payroll_blueprint, url_prefix='/payroll')

# Ensure the upload folder exists with proper permissions
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    logging.debug(f"Created upload folder: {app.config['UPLOAD_FOLDER']}")

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
        logging.info("Database initialized successfully.")
    except sqlite3.Error as e:
        logging.error(f"SQLite error: {e}")
    finally:
        if conn:
            conn.close()

# Save file with logging and error handling
def save_file(file, employee_folder):
    try:
        filename = secure_filename(file.filename)
        file_path = os.path.join(employee_folder, filename)
        logging.debug(f"Saving file to: {file_path}")

        file.save(file_path)
        logging.info(f"File saved: {file_path}")

        # Return the file path relative to the "static/uploads" directory
        relative_path = os.path.relpath(file_path, app.config['UPLOAD_FOLDER']).replace("\\", "/")
        logging.debug(f"File saved with relative path: {relative_path}")
        return relative_path
    except Exception as e:
        logging.error(f"Failed to save file: {e}")
        raise

@app.route('/')
def index():
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM employees LIMIT 1')
    employee_data = cursor.fetchone()
    conn.close()

    if employee_data:
        employee = {
            'id': employee_data[0],
            'name': employee_data[1],
            'dob': employee_data[2],
        }
        return render_template('index.html', employee=employee)
    else:
        flash('No employee data found.', 'error')
        return redirect(url_for('login'))

@app.route('/employee_dashboard')
def employee_dashboard():
    if 'username' not in session or session['role'] != 'employee':
        return redirect(url_for('login'))

    name = session['username']

    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM employees WHERE name = ?', (name,))
    employee = cursor.fetchone()
    conn.close()

    if employee:
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
        flash(f'Welcome, {name}!', 'success')
        return render_template('employee_dashboard.html', employee=employee_dict)
    else:
        flash('Employee details not found. Please check your credentials or contact the administrator.', 'error')
        return redirect(url_for('logout'))

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'username' not in session or session['role'] != 'employee':
        return redirect(url_for('login'))

    name = session['username']
    full_name = request.form['full_name']
    email = request.form['email']
    phone = request.form['phone']
    profile_picture = request.files.get('profile_picture')

    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    cursor.execute('SELECT id, profile_photo_path FROM employees WHERE name = ?', (name,))
    employee = cursor.fetchone()
    conn.close()

    if not employee:
        flash('Employee not found!', 'error')
        return redirect(url_for('employee_dashboard'))

    employee_id = employee[0]
    current_profile_photo_path = employee[1]

    employee_folder = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(full_name))
    if not os.path.exists(employee_folder):
        os.makedirs(employee_folder, exist_ok=True)
        logging.debug(f"Created folder for employee: {employee_folder}")

    profile_photo_path = current_profile_photo_path
    if profile_picture:
        try:
            profile_photo_path = save_file(profile_picture, employee_folder)
            profile_photo_path = profile_photo_path.replace("static/uploads/", "")
        except Exception as e:
            flash('Failed to save profile picture!', 'error')
            logging.error(f"Error saving profile picture: {e}")
            return redirect(url_for('employee_dashboard'))

    try:
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE employees
            SET name = ?, email = ?, phone = ?, profile_photo_path = ?
            WHERE id = ?
        ''', (full_name, email, phone, profile_photo_path, employee_id))
        conn.commit()
        flash('Profile updated successfully!')
        logging.info(f"Profile updated for employee ID: {employee_id}")
    except sqlite3.Error as e:
        logging.error(f"SQLite error: {e}")
        flash('An error occurred while updating the profile!', 'error')
    finally:
        if conn:
            conn.close()

    return redirect(url_for('employee_dashboard'))

@app.route('/add_employee', methods=['GET', 'POST'])
def add_employee():
    if request.method == 'POST':
        name = request.form['name']
        dob = request.form['dob']
        gender = request.form['gender']
        address = request.form['address']
        state = request.form['state']
        pincode = request.form['pincode']
        phone = request.form['phone']
        alt_phone = request.form.get('alt_phone')
        email = request.form['email']
        pan = request.form.get('pan')
        aadhar = request.form.get('aadhar')
        employee_code = request.form['employee_code']

        employee_folder = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(name))
        if not os.path.exists(employee_folder):
            os.makedirs(employee_folder, exist_ok=True)
            logging.debug(f"Created folder for new employee: {employee_folder}")

        aadhar_path = None
        pan_path = None
        bank_passbook_path = None
        profile_photo_path = None
        for file_key in request.files:
            file = request.files[file_key]
            if file:
                try:
                    file_path = save_file(file, employee_folder)
                    if file_key == 'aadhar_upload':
                        aadhar_path = file_path
                    elif file_key == 'pan_upload':
                        pan_path = file_path
                    elif file_key == 'bank_passbook_upload':
                        bank_passbook_path = file_path
                    elif file_key == 'profile_photo_upload':
                        profile_photo_path = file_path
                except Exception as e:
                    flash('Failed to save uploaded files!', 'error')
                    logging.error(f"Error saving {file_key}: {e}")
                    return redirect(url_for('add_employee'))

        bank_name = request.form['bank_name']
        bank = request.form['bank']
        account = request.form['account']
        ifsc = request.form['ifsc']
        uan = request.form['uan']
        experience = request.form['experience']
        company_name = request.form.get('company_name')
        designation = request.form.get('designation')
        function_performed = request.form.get('function')
        period_of_work = request.form.get('period')
        reason_for_leaving = request.form.get('reason')

        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO employees (
                    name, dob, gender, address, state, pincode, phone, alt_phone, email, pan, aadhar, 
                    employee_code, aadhar_path, pan_path, bank_passbook_path, profile_photo_path,
                    bank_name, bank, account, ifsc, uan, experience, company_name, designation, 
                    function_performed, period_of_work, reason_for_leaving
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                name, dob, gender, address, state, pincode, phone, alt_phone, email, pan, aadhar, 
                employee_code, aadhar_path, pan_path, bank_passbook_path, profile_photo_path,
                bank_name, bank, account, ifsc, uan, experience, company_name, designation, 
                function_performed, period_of_work, reason_for_leaving
            ))
            conn.commit()
            flash('Employee added successfully!')
            logging.info(f"Employee {name} added successfully.")
        except sqlite3.IntegrityError as e:
            logging.error(f"SQLite Integrity error: {e}")
            flash('An employee with this name or employee code already exists!', 'error')
        except sqlite3.Error as e:
            logging.error(f"SQLite error: {e}")
            flash('An error occurred while adding employee!', 'error')
        finally:
            if conn:
                conn.close()

        return redirect(url_for('index'))

    return render_template('add_employee.html')

@app.route('/edit_employee', methods=['GET', 'POST'])
@app.route('/edit_employee/<int:employee_id>', methods=['GET', 'POST'])
def edit_employee(employee_id=None):
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    cursor.execute('SELECT id, name FROM employees')
    employees = cursor.fetchall()
    if employee_id:
        cursor.execute('SELECT * FROM employees WHERE id = ?', (employee_id,))
        employee = cursor.fetchone()
    conn.close()

    if employee_id and not employee:
        flash('Employee not found!', 'error')
        return redirect(url_for('edit_employee'))

    if request.method == 'POST' and employee:
        name = request.form['name']
        dob = request.form['dob']
        gender = request.form['gender']
        address = request.form['address']
        state = request.form['state']
        pincode = request.form['pincode']
        phone = request.form['phone']
        alt_phone = request.form['alt_phone']
        email = request.form['email']
        pan = request.form['pan']
        aadhar = request.form['aadhar']
        employee_code = request.form['employee_code']
        aadhar_file = request.files.get('aadhar_file')
        pan_file = request.files.get('pan_file')
        bank_passbook_file = request.files.get('bank_passbook_file')
        profile_photo_file = request.files.get('profile_photo_file')
        bank_name = request.form['bank_name']
        bank = request.form['bank']
        account = request.form['account']
        ifsc = request.form['ifsc']
        uan = request.form['uan']
        experience = request.form['experience']
        company_name = request.form['company_name']
        designation = request.form['designation']
        function_performed = request.form['function_performed']
        period_of_work = request.form['period_of_work']
        reason_for_leaving = request.form['reason_for_leaving']

        employee_folder = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(name))
        if not os.path.exists(employee_folder):
            os.makedirs(employee_folder, exist_ok=True)
            logging.debug(f"Created folder for employee {employee_id}: {employee_folder}")

        aadhar_path = employee[13]
        if aadhar_file:
            try:
                aadhar_path = save_file(aadhar_file, employee_folder)
            except Exception as e:
                flash('Failed to save Aadhar file!', 'error')
                logging.error(f"Error saving Aadhar file: {e}")

        pan_path = employee[14]
        if pan_file:
            try:
                pan_path = save_file(pan_file, employee_folder)
            except Exception as e:
                flash('Failed to save PAN file!', 'error')
                logging.error(f"Error saving PAN file: {e}")

        bank_passbook_path = employee[15]
        if bank_passbook_file:
            try:
                bank_passbook_path = save_file(bank_passbook_file, employee_folder)
            except Exception as e:
                flash('Failed to save Bank Passbook file!', 'error')
                logging.error(f"Error saving Bank Passbook file: {e}")

        profile_photo_path = employee[16]
        if profile_photo_file:
            try:
                profile_photo_path = save_file(profile_photo_file, employee_folder)
            except Exception as e:
                flash('Failed to save Profile Photo file!', 'error')
                logging.error(f"Error saving Profile Photo file: {e}")

        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE employees
                SET name = ?, dob = ?, gender = ?, address = ?, state = ?, pincode = ?, phone = ?, alt_phone = ?, email = ?, pan = ?, aadhar = ?, employee_code = ?, aadhar_path = ?, pan_path = ?, bank_passbook_path = ?, profile_photo_path = ?, bank_name = ?, bank = ?, account = ?, ifsc = ?, uan = ?, experience = ?, company_name = ?, designation = ?, function_performed = ?, period_of_work = ?, reason_for_leaving = ?
                WHERE id = ?
            ''', (
                name, dob, gender, address, state, pincode, phone, alt_phone, email, pan, aadhar, 
                employee_code, aadhar_path, pan_path, bank_passbook_path, profile_photo_path, 
                bank_name, bank, account, ifsc, uan, experience, company_name, designation, 
                function_performed, period_of_work, reason_for_leaving, employee_id
            ))
            conn.commit()
            flash('Employee updated successfully!')
            logging.info(f"Employee {employee_id} updated successfully.")
        except sqlite3.Error as e:
            logging.error(f"SQLite error: {e}")
            flash('An error occurred while updating the employee!', 'error')
        finally:
            if conn:
                conn.close()

        return redirect(url_for('edit_employee', employee_id=employee_id))

    employee_dict = None
    if employee:
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

    return render_template('edit_employee.html', employee=employee_dict, employees=employees, employee_id=employee_id)

@app.route('/uploads/<employee_name>/<path:filename>')
def uploaded_file(employee_name, filename):
    decoded_filename = urllib.parse.unquote(filename)
    decoded_filename = decoded_filename.replace("\\", "/")
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(employee_name), decoded_filename)
    if os.path.exists(file_path):
        logging.info(f"Serving file: {file_path}")
        return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(employee_name)), os.path.basename(decoded_filename))
    else:
        logging.warning(f"File not found: {file_path}")
        abort(404)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
