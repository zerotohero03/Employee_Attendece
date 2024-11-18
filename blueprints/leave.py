from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
import sqlite3

leave_blueprint = Blueprint('leave', __name__)

@leave_blueprint.route('/leave', methods=['GET', 'POST'])
def leave():
    if 'username' not in session or session['role'] != 'employee':
        return redirect(url_for('login'))
    
    conn = sqlite3.connect(current_app.config['DATABASE'])
    cursor = conn.cursor()
    username = session['username']

    if request.method == 'POST':
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        reason = request.form['reason']

        cursor.execute('SELECT id FROM employees WHERE name = ?', (username,))
        employee_id = cursor.fetchone()[0]

        cursor.execute('''
            INSERT INTO leave_requests (employee_id, start_date, end_date, reason)
            VALUES (?, ?, ?, ?)
        ''', (employee_id, start_date, end_date, reason))
        conn.commit()
        flash('Leave request submitted successfully!')
        return redirect(url_for('leave.leave'))

    cursor.execute('SELECT * FROM leave_requests WHERE employee_id = (SELECT id FROM employees WHERE name = ?)', (username,))
    records = cursor.fetchall()
    conn.close()

    return render_template('leave.html', records=records)
