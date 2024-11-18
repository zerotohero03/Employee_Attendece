from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
import sqlite3
from datetime import datetime

attendance_blueprint = Blueprint('attendance', __name__)

@attendance_blueprint.route('/attendance', methods=['GET', 'POST'])
def attendance():
    if 'username' not in session or session['role'] != 'employee':
        return redirect(url_for('login'))
    
    conn = sqlite3.connect(current_app.config['DATABASE'])
    cursor = conn.cursor()
    username = session['username']

    if request.method == 'POST':
        date = request.form['date']
        status = request.form['status']
        time = datetime.now().strftime('%H:%M:%S')
        reason = request.form.get('reason')

        cursor.execute('SELECT id FROM employees WHERE name = ?', (username,))
        employee_id = cursor.fetchone()[0]

        cursor.execute('''
            INSERT INTO attendance (employee_id, date, time, status, reason_for_absence_halfday)
            VALUES (?, ?, ?, ?, ?)
        ''', (employee_id, date, time, status, reason))
        conn.commit()
        flash('Attendance marked successfully!')
        return redirect(url_for('attendance.attendance'))

    cursor.execute('SELECT * FROM attendance WHERE employee_id = (SELECT id FROM employees WHERE name = ?)', (username,))
    records = cursor.fetchall()
    conn.close()

    return render_template('attendance.html', records=records)
