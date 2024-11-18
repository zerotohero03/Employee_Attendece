from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app, jsonify
import pandas as pd
from werkzeug.utils import secure_filename
from io import BytesIO
import pdfkit
from zipfile import ZipFile
import os
from services.db_service import get_db_connection, create_tables_if_not_exist
import threading
import time

payroll_blueprint = Blueprint('payroll', __name__, template_folder='templates')

@payroll_blueprint.before_app_request
def initialize():
    conn = get_db_connection()
    create_tables_if_not_exist(conn)
    conn.close()

@payroll_blueprint.route('/define_salary_structure', methods=['GET', 'POST'])
def define_salary_structure():
    from forms.payroll_form import DefineSalaryStructureForm
    form = DefineSalaryStructureForm()

    if form.validate_on_submit():
        print("Form submitted successfully")
        print("Form data:", form.data)  # Check form data
        
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                sql_query = '''
                INSERT INTO Payroll (Employee_Code, Month, Year, WDAY, LOPD, ACTDAYS, ARRDAYS, Days_Payable, Basic, HRA, Special_Allowance, LTA, Retention_Bonus, Mobile_Internet_Allowance, Professional_Development_Allowance, Office_Attire, Other_Allowance, Additional_Payments, Additional_Payment_Bonus, PF, VPF, LWF, PT, LWF_Arrears_Deduction, Other_Deductions, TDS)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                '''
                print("SQL Query:", sql_query)  # Check SQL query
                
                cursor.execute(sql_query, (
                    form.employee_search.data,
                    form.month.data,
                    form.year.data,
                    form.wday.data,
                    form.lopd.data,
                    form.actdays.data,
                    form.arrdays.data,
                    form.days_payable.data,
                    form.basic_salary.data,
                    form.hra.data,
                    form.special_allowance.data,
                    form.lta.data,
                    form.retention_bonus.data,
                    form.mobile_internet.data,
                    form.professional_development.data,
                    form.office_attire.data,
                    form.other_allowance.data,
                    form.additional_payment.data,
                    form.additional_bonus.data,
                    form.pf.data,
                    form.vpf.data,
                    form.lwf.data,
                    form.pt.data,
                    form.lwf_arrears.data,
                    form.other_deductions.data,
                    form.tds.data
                ))
                conn.commit()
                flash('Salary structure defined successfully.', 'success')
        finally:
            conn.close()
        return redirect(url_for('payroll.define_salary_structure'))
    
    return render_template('define_salary_structure.html', form=form)

@payroll_blueprint.route('/generate_payslip/<employee_code>/<int:month>/<int:year>')
def generate_payslip(employee_code, month, year):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('''
            SELECT * FROM Payroll WHERE Employee_Code = %s AND Month = %s AND Year = %s
            ''', (employee_code, month, year))
            payroll_data = cursor.fetchone()
            
            if not payroll_data:
                flash('No payroll data found for the given employee and period.', 'error')
                return redirect(url_for('payroll.define_salary_structure'))

            payroll = dict(zip(cursor.column_names, payroll_data))

            cursor.execute('SELECT * FROM Employees WHERE Employee_Code = %s', (employee_code,))
            employee_data = cursor.fetchone()
            if not employee_data:
                flash('Employee not found. Please check the Employee Code and try again.', 'error')
                return redirect(url_for('payroll.define_salary_structure'))

            employee = dict(zip(cursor.column_names, employee_data))
    finally:
        conn.close()

    return render_template('payslip.html', payroll=payroll, employee=employee)

@payroll_blueprint.route('/generate_payslips', methods=['GET', 'POST'])
def generate_payslips():
    if request.method == 'POST':
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                employee_code = request.form['employee_search']
                cursor.execute('SELECT * FROM Employees WHERE Employee_Code = %s', (employee_code,))
                employee_data = cursor.fetchone()

                if employee_data:
                    employee = dict(zip(cursor.column_names, employee_data))
                    
                    cursor.execute('SELECT * FROM Payroll WHERE Employee_Code = %s', (employee_code,))
                    payroll_data = cursor.fetchone()

                    if payroll_data:
                        payroll = dict(zip(cursor.column_names, payroll_data))
                        print("Employee:", employee)  # Debugging statement
                        print("Payroll:", payroll)    # Debugging statement
                        return render_template('payslip.html', payroll=payroll, employee=employee)
                    else:
                        flash('Payroll data not found for the employee. Please define the salary structure first.', 'error')
                else:
                    flash('Employee not found. Please check the Employee Code and try again.', 'error')
        finally:
            conn.close()

    return render_template('generate_payslips.html')

@payroll_blueprint.route('/upload_payslips', methods=['POST'])
def upload_payslips():
    if 'payslip_files' not in request.files:
        flash('No files part', 'error')
        return redirect(request.url)

    files = request.files.getlist('payslip_files')
    if not files:
        flash('No selected files', 'error')
        return redirect(request.url)

    conn = get_db_connection()
    try:
        for file in files:
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            payroll_data = pd.read_excel(file_path)
            with conn.cursor() as cursor:
                for _, row in payroll_data.iterrows():
                    cursor.execute('''
                    INSERT INTO Payroll (Employee_Code, Month, Year, WDAY, LOPD, ACTDAYS, ARRDAYS, Days_Payable, Basic, HRA, Special_Allowance, LTA, Retention_Bonus, Mobile_Internet_Allowance, Professional_Development_Allowance, Office_Attire, Other_Allowance, Additional_Payments, Additional_Payment_Bonus, PF, VPF, LWF, PT, LWF_Arrears_Deduction, Other_Deductions, TDS)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ''', tuple(row))
        conn.commit()
        flash('Payslips uploaded and processed successfully.', 'success')
    finally:
        conn.close()

    return redirect(url_for('payroll.define_salary_structure'))

@payroll_blueprint.route('/download_payslips')
def download_payslips():
    conn = get_db_connection()
    zip_buffer = BytesIO()

    try:
        with ZipFile(zip_buffer, 'w') as zip_file:
            with conn.cursor() as cursor:
                cursor.execute('SELECT DISTINCT Employee_Code, Month, Year FROM Payroll')
                records = cursor.fetchall()

                for record in records:
                    employee_code, month, year = record
                    cursor.execute('''
                    SELECT * FROM Payroll WHERE Employee_Code = %s AND Month = %s AND Year = %s
                    ''', (employee_code, month, year))
                    payroll_data = cursor.fetchone()

                    if payroll_data:
                        payslip_data = dict(zip(cursor.column_names, payroll_data))
                        payslip_html = render_template('payslip.html', payslip_data=payslip_data)
                        payslip_pdf = pdfkit.from_string(payslip_html, False)

                        payslip_filename = f'payslip_{employee_code}_{month}_{year}.pdf'
                        zip_file.writestr(payslip_filename, payslip_pdf)

    finally:
        conn.close()

    zip_buffer.seek(0)
    return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name='payslips.zip')

@payroll_blueprint.route('/download_excel')
def download_excel():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM Employees')
            employees = cursor.fetchall()

            employee_df = pd.DataFrame(employees, columns=[desc[0] for desc in cursor.description])
            payroll_columns = ['Employee ID', 'Month', 'Year', 'Working Days', 'Leave Without Pay Days', 'Actual Days Worked', 'Arrear Days', 'Days Payable', 
                               'Basic Salary', 'HRA', 'Special Allowance', 'LTA', 'Retention Bonus', 'Mobile & Internet Allowance', 
                               'Professional Development Allowance', 'Office Attire Allowance', 'Other Allowance', 'Additional Payments', 
                               'Additional Bonus', 'PF', 'VPF', 'LWF', 'PT', 'LWF Arrears', 'Other Deductions', 'TDS']
            payroll_df = pd.DataFrame(columns=payroll_columns)
            
            combined_df = pd.concat([employee_df, payroll_df], axis=1)

            output = BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter')
            combined_df.to_excel(writer, index=False, sheet_name='Payroll_Template')
            writer.book.close()
            output.seek(0)
            
            return send_file(output, download_name='payroll_template.xlsx', as_attachment=True)
    finally:
        conn.close()

@payroll_blueprint.route('/upload_excel', methods=['GET', 'POST'])
def upload_excel():
    if request.method == 'POST':
        file = request.files['excel_file']
        if file and file.filename.endswith('.xlsx'):
            conn = get_db_connection()
            try:
                with conn.cursor() as cursor:
                    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
                    file.save(filepath)
                    df = pd.read_excel(filepath)

                    for _, row in df.iterrows():
                        cursor.execute('''
                        INSERT INTO Payroll (Employee_Code, Month, Year, WDAY, LOPD, ACTDAYS, ARRDAYS, Days_Payable, Basic, HRA, 
                                             Special_Allowance, LTA, Retention_Bonus, Mobile_Internet_Allowance, 
                                             Professional_Development_Allowance, Office_Attire, Other_Allowance, Additional_Payments, 
                                             Additional_Payment_Bonus, PF, VPF, LWF, PT, LWF_Arrears_Deduction, Other_Deductions, TDS)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ''', (
                            row['Employee_Code'], row['Month'], row['Year'], row['WDAY'], row['LOPD'], row['ACTDAYS'],
                            row['ARRDAYS'], row['Days_Payable'], row['Basic'], row['HRA'], row['Special_Allowance'], row['LTA'],
                            row['Retention_Bonus'], row['Mobile_Internet_Allowance'], row['Professional_Development_Allowance'], 
                            row['Office_Attire'], row['Other_Allowance'], row['Additional_Payments'], row['Additional_Payment_Bonus'], 
                            row['PF'], row['VPF'], row['LWF'], row['PT'], row['LWF_Arrears_Deduction'], row['Other_Deductions'], row['TDS']
                        ))
                    conn.commit()
                    flash('Excel file uploaded and processed successfully.', 'success')
            finally:
                conn.close()
            return redirect(url_for('payroll.generate_payslips'))
        else:
            flash('Invalid file format. Please upload an Excel file.', 'error')

    return render_template('upload_excel.html')

def generate_payslip_pdf(employee_code, month, year):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('''
            SELECT * FROM Payroll WHERE Employee_Code = %s AND Month = %s AND Year = %s
            ''', (employee_code, month, year))
            payroll_data = cursor.fetchone()
            payroll = dict(zip(cursor.column_names, payroll_data))

            cursor.execute('SELECT * FROM Employees WHERE Employee_Code = %s', (employee_code,))
            employee_data = cursor.fetchone()
            employee = dict(zip(cursor.column_names, employee_data))

        payslip_html = render_template('payslip.html', payroll=payroll, employee=employee)
        return pdfkit.from_string(payslip_html, False)
    finally:
        conn.close()

def create_payslip_zip():
    conn = get_db_connection()
    zip_buffer = BytesIO()
    try:
        with ZipFile(zip_buffer, 'w') as zip_file:
            with conn.cursor() as cursor:
                cursor.execute('SELECT DISTINCT Employee_Code, Month, Year FROM Payroll')
                records = cursor.fetchall()

                for record in records:
                    employee_code, month, year = record
                    payslip_pdf = generate_payslip_pdf(employee_code, month, year)
                    payslip_filename = f'payslip_{employee_code}_{month}_{year}.pdf'
                    zip_file.writestr(payslip_filename, payslip_pdf)
    finally:
        conn.close()
    zip_buffer.seek(0)
    return zip_buffer

@payroll_blueprint.route('/generate_payslips_progress')
def generate_payslips_progress():
    # Simulated progress endpoint for demonstration purposes
    progress = 0
    while progress < 100:
        time.sleep(1)  # Simulating processing time
        progress += 10
        yield f"data:{progress}\n\n"



@payroll_blueprint.route('/payroll_management')
def payroll_management():
    return render_template('payroll_management.html')

