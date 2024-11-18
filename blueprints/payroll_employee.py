from flask import Blueprint, render_template, session, redirect, url_for, current_app
import sqlite3

payroll_employee_blueprint = Blueprint('payroll_employee', __name__)

@payroll_employee_blueprint.route('/payroll_employee')
def payroll():
    if 'username' not in session or session['role'] != 'employee':
        return redirect(url_for('login'))
    
    conn = sqlite3.connect(current_app.config['DATABASE'])
    cursor = conn.cursor()
    username = session['username']

    cursor.execute('''
        SELECT p.* FROM payroll p
        JOIN employees e ON p.employee_id = e.id
        WHERE e.name = ?
    ''', (username,))
    records = cursor.fetchall()
    conn.close()

    return render_template('payroll_employee.html', records=records)
