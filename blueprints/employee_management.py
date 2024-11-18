from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_from_directory, abort
from werkzeug.utils import secure_filename
import os
import sqlite3
import urllib.parse

# Create a blueprint for employee management
employee_management_blueprint = Blueprint('employee_management', __name__, template_folder='templates', static_folder='static')

# Load the configurations for UPLOAD_FOLDER and DATABASE
UPLOAD_FOLDER = os.path.join('static', 'uploads')
DATABASE = 'database/employees.db'

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def save_file(file, employee_folder):
    """Save an uploaded file to the employee's folder."""
    filename = secure_filename(file.filename)
    file_path = os.path.join(employee_folder, filename)
    file.save(file_path)
    return os.path.relpath(file_path, UPLOAD_FOLDER).replace("\\", "/")

def save_file_if_uploaded(file, folder, default_path):
    """Save the file if uploaded, otherwise return the default path."""
    if file:
        return save_file(file, folder)
    return default_path  # Return existing path if no new file is uploaded

def get_employee_by_id(employee_id):
    """Retrieve an employee's details by their ID."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM employees WHERE id = ?', (employee_id,))
        return cursor.fetchone()

def update_employee(employee_id, form_data, files):
    """Update an employee's details in the database."""
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()

            employee_folder = os.path.join(UPLOAD_FOLDER, secure_filename(form_data['name']))
            if not os.path.exists(employee_folder):
                os.makedirs(employee_folder)

            aadhar_path = save_file_if_uploaded(files.get('aadhar_file'), employee_folder, form_data.get('aadhar_path'))
            pan_path = save_file_if_uploaded(files.get('pan_file'), employee_folder, form_data.get('pan_path'))
            bank_passbook_path = save_file_if_uploaded(files.get('bank_passbook_file'), employee_folder, form_data.get('bank_passbook_path'))
            profile_photo_path = save_file_if_uploaded(files.get('profile_photo_file'), employee_folder, form_data.get('profile_photo_path'))

            cursor.execute('''
                UPDATE employees
                SET name = ?, dob = ?, gender = ?, address = ?, state = ?, pincode = ?, phone = ?, alt_phone = ?, email = ?, pan = ?, aadhar = ?, employee_code = ?, 
                    aadhar_path = ?, pan_path = ?, bank_passbook_path = ?, profile_photo_path = ?, bank_name = ?, bank = ?, account = ?, ifsc = ?, uan = ?, experience = ?, 
                    company_name = ?, designation = ?, function_performed = ?, period_of_work = ?, reason_for_leaving = ?
                WHERE id = ?
            ''', (
                form_data['name'], form_data['dob'], form_data['gender'], form_data['address'], form_data['state'], form_data['pincode'],
                form_data['phone'], form_data['alt_phone'], form_data['email'], form_data['pan'], form_data['aadhar'], 
                form_data['employee_code'], aadhar_path, pan_path, bank_passbook_path, profile_photo_path, 
                form_data['bank_name'], form_data['bank'], form_data['account'], form_data['ifsc'], form_data['uan'], form_data['experience'], 
                form_data['company_name'], form_data['designation'], form_data['function_performed'], form_data['period_of_work'], form_data['reason_for_leaving'], 
                employee_id
            ))
            conn.commit()
            flash('Employee updated successfully!', 'success')
    except sqlite3.Error as e:
        print("SQLite error:", e)
        flash('An error occurred while updating the employee!', 'error')

def convert_employee_to_dict(employee):
    """Convert employee tuple to dictionary."""
    if employee:
        return {
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
    return None

@employee_management_blueprint.route('/add_employee', methods=['GET', 'POST'])
def add_employee():
    """Add a new employee to the database."""
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

        employee_folder = os.path.join(UPLOAD_FOLDER, secure_filename(name))
        if not os.path.exists(employee_folder):
            os.makedirs(employee_folder)

        aadhar_path = pan_path = bank_passbook_path = profile_photo_path = None
        for file_key in request.files:
            file = request.files[file_key]
            if file:
                file_path = save_file(file, employee_folder)
                if file_key == 'aadhar_upload':
                    aadhar_path = file_path
                elif file_key == 'pan_upload':
                    pan_path = file_path
                elif file_key == 'bank_passbook_upload':
                    bank_passbook_path = file_path
                elif file_key == 'profile_photo_upload':
                    profile_photo_path = file_path

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

        conn = None
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
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
            flash('Employee added successfully!', 'success')
        except sqlite3.IntegrityError as e:
            print("SQLite Integrity error:", e)
            flash('An employee with this name or employee code already exists!', 'error')
        except sqlite3.Error as e:
            print("SQLite error:", e)
            flash('An error occurred while adding the employee!', 'error')
        finally:
            if conn:
                conn.close()

        # return redirect(url_for('employee_management.index'))

    return render_template('add_employee.html')

@employee_management_blueprint.route('/uploads/<employee_name>/<path:filename>')
def uploaded_file(employee_name, filename):
    """Serve the uploaded file from the server."""
    decoded_filename = urllib.parse.unquote(filename).replace("\\", "/")
    file_path = os.path.join(UPLOAD_FOLDER, secure_filename(employee_name), decoded_filename)
    if os.path.exists(file_path):
        return send_from_directory(os.path.join(UPLOAD_FOLDER, secure_filename(employee_name)), os.path.basename(decoded_filename))
    else:
        abort(404)

@employee_management_blueprint.route('/update_profile', methods=['POST'])
def update_profile():
    """Update the profile of the currently logged-in employee."""
    if 'username' not in session or session['role'] != 'employee':
        return redirect(url_for('login'))

    name = session['username']
    full_name = request.form['full_name']
    email = request.form['email']
    phone = request.form['phone']
    profile_picture = request.files.get('profile_picture')

    conn = None
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT id, profile_photo_path FROM employees WHERE name = ?', (name,))
        employee = cursor.fetchone()
        if not employee:
            flash('Employee not found!', 'error')
            return redirect(url_for('employee_management.employee_dashboard'))

        employee_id = employee[0]
        current_profile_photo_path = employee[1]

        employee_folder = os.path.join(UPLOAD_FOLDER, secure_filename(full_name))
        if not os.path.exists(employee_folder):
            os.makedirs(employee_folder)

        profile_photo_path = current_profile_photo_path
        if profile_picture:
            profile_photo_path = save_file(profile_picture, employee_folder)
            profile_photo_path = profile_photo_path.replace("static/uploads/", "")

        cursor.execute('''
            UPDATE employees
            SET name = ?, email = ?, phone = ?, profile_photo_path = ?
            WHERE id = ?
        ''', (full_name, email, phone, profile_photo_path, employee_id))

        conn.commit()
        flash('Profile updated successfully!', 'success')
    except sqlite3.Error as e:
        print("SQLite error:", e)
        flash('An error occurred while updating the profile!', 'error')
    finally:
        if conn:
            conn.close()

    return redirect(url_for('employee_management.employee_dashboard'))

@employee_management_blueprint.route('/edit_employee', methods=['GET', 'POST'])
@employee_management_blueprint.route('/edit_employee/<int:employee_id>', methods=['GET', 'POST'])
def edit_employee(employee_id=None):
    """Handle editing of employee details."""
    try:
        # Fetch all employees (id and name only) for the sidebar list
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, name FROM employees')
            employees = cursor.fetchall()
            
            employee = None
            if employee_id and employee_id != 0:
                employee = get_employee_by_id(employee_id)
                if not employee:
                    flash('Employee not found!', 'error')
                    return redirect(url_for('employee_management.edit_employee', employee_id=0))

    except sqlite3.Error as e:
        print("SQLite error:", e)
        flash('An error occurred while retrieving employee data!', 'error')
        employees = []

    if request.method == 'POST' and employee_id and employee_id != 0:
        # Update employee details
        form_data = request.form.to_dict()
        files = request.files.to_dict()
        update_employee(employee_id, form_data, files)
        return redirect(url_for('employee_management.edit_employee', employee_id=employee_id))

    employee_dict = convert_employee_to_dict(employee)

    return render_template('edit_employee.html', employee=employee_dict, employees=employees, employee_id=employee_id)

@employee_management_blueprint.route('/employees')
def list_employees():
    """List all employees."""
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, name FROM employees')
            employees = cursor.fetchall()
    except sqlite3.Error as e:
        print("SQLite error:", e)
        flash('An error occurred while retrieving the employee list!', 'error')
        employees = []
    
    return render_template('employees.html', employees=employees)
