from flask import Blueprint, render_template, request, jsonify, redirect, url_for, send_file
import sqlite3
from datetime import datetime
import pandas as pd

view_attendance_blueprint = Blueprint('view_attendance', __name__, template_folder='templates')

def get_db_connection():
    conn = sqlite3.connect('database/employees.db')
    conn.row_factory = sqlite3.Row
    return conn

# Add a new column 'time' to the attendance table
def add_time_column():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("ALTER TABLE attendance ADD COLUMN time TEXT")
        conn.commit()

# Ensure the time column exists
try:
    add_time_column()
except sqlite3.OperationalError:
    # The column already exists
    pass

def row_to_dict(row):
    return {k: row[k] for k in row.keys()}

@view_attendance_blueprint.route('/view_attendance', methods=['GET', 'POST'])
def view_attendance():
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Fetch filters from request
        employee_name = request.form.get('employee_name')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        # Default to current date if not provided
        if not start_date:
            start_date = datetime.now().strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        # Check if "Clear Filters" button was clicked
        if request.form.get('clear_filters'):
            # Redirect to the same page to reset filters
            return redirect(url_for('view_attendance.view_attendance'))

        # Prepare the base query
        query = '''
            SELECT employees.name, attendance.date, attendance.status, attendance.time 
            FROM attendance 
            JOIN employees ON attendance.employee_id = employees.id
            WHERE attendance.date BETWEEN ? AND ?
        '''
        params = [start_date, end_date]

        if employee_name:
            query += ' AND employees.name = ?'
            params.append(employee_name)

        cursor.execute(query, params)
        attendance_records = [row_to_dict(row) for row in cursor.fetchall()]

        # Fetch employee names for the dropdown
        cursor.execute('SELECT name FROM employees')
        employee_names = cursor.fetchall()

        # Prepare statistics data
        stats = {}
        for record in attendance_records:
            name, status, _date, time = record['name'], record['status'], record['date'], record['time']
            if name not in stats:
                stats[name] = []
            stats[name].append({'status': status, 'date': _date, 'time': time})

    return render_template('view_attendance.html', 
                           records=attendance_records, 
                           employee_names=employee_names, 
                           stats=stats or {},
                           selected_employee=employee_name,
                           start_date=start_date,
                           end_date=end_date)

@view_attendance_blueprint.route('/export_attendance', methods=['POST'])
def export_attendance():
    start_date = request.form.get('export_start_date')
    end_date = request.form.get('export_end_date')

    if not start_date or not end_date:
        return redirect(url_for('view_attendance.view_attendance'))

    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = '''
            SELECT employees.name, attendance.date, attendance.status, attendance.time 
            FROM attendance 
            JOIN employees ON attendance.employee_id = employees.id
            WHERE attendance.date BETWEEN ? AND ?
        '''
        params = [start_date, end_date]
        cursor.execute(query, params)
        attendance_records = [row_to_dict(row) for row in cursor.fetchall()]

    df = pd.DataFrame(attendance_records)
    filename = 'attendance_records.xlsx'
    df.to_excel(filename, index=False)
    return send_file(filename, as_attachment=True)
