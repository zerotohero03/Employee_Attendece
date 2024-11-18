from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
import sqlite3
from werkzeug.utils import secure_filename
import os

profile_blueprint = Blueprint('profile', __name__)

@profile_blueprint.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'username' not in session or session['role'] != 'employee':
        return redirect(url_for('login'))
    
    conn = sqlite3.connect(current_app.config['DATABASE'])
    cursor = conn.cursor()
    username = session['username']

    if request.method == 'POST':
        name = request.form['name']
        department = request.form['department']
        job_title = request.form['job_title']
        
        profile_photo = request.files['profile_photo']
        profile_photo_filename = secure_filename(profile_photo.filename)
        profile_photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], profile_photo_filename)
        profile_photo.save(profile_photo_path)
        
        cursor.execute('''
            UPDATE employees
            SET name=?, department=?, job_title=?, profile_photo_path=?
            WHERE name=?
        ''', (name, department, job_title, profile_photo_filename, username))
        conn.commit()
        flash('Profile updated successfully!')
        return redirect(url_for('profile.profile'))

    cursor.execute('SELECT * FROM employees WHERE name = ?', (username,))
    employee = cursor.fetchone()
    conn.close()

    return render_template('profile.html', employee=employee)
