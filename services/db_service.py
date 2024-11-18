import mysql.connector
from mysql.connector import pooling, errorcode
from flask import current_app
from contextlib import closing

def get_db_connection():
    print("Getting DB connection...")
    dbconfig = {
        'user': current_app.config['DB_USER'],
        'password': current_app.config['DB_PASSWORD'],
        'host': current_app.config['DB_HOST'],
        'database': current_app.config['DB_NAME']
    }

    try:
        pool = pooling.MySQLConnectionPool(pool_name="mypool", pool_size=current_app.config['DB_POOL_SIZE'], **dbconfig)
        print("Connection successful")
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_BAD_DB_ERROR:
            create_database()
            pool = pooling.MySQLConnectionPool(pool_name="mypool", pool_size=current_app.config['DB_POOL_SIZE'], **dbconfig)
        else:
            raise

    return pool.get_connection()

def create_database():
    dbconfig = {
        'user': current_app.config['DB_USER'],
        'password': current_app.config['DB_PASSWORD'],
        'host': current_app.config['DB_HOST']
    }

    connection = mysql.connector.connect(**dbconfig)
    cursor = connection.cursor()

    try:
        cursor.execute(f"CREATE DATABASE {current_app.config['DB_NAME']}")
    except mysql.connector.Error as err:
        print(f"Failed to create database: {err}")
        exit(1)
    finally:
        cursor.close()
        connection.close()

def create_tables_if_not_exist(conn):
    with closing(conn.cursor()) as cursor:
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Employees (
            id INT PRIMARY KEY AUTO_INCREMENT,
            Employee_Code VARCHAR(50) UNIQUE,
            Employee_Name VARCHAR(100),
            Designation VARCHAR(100),
            Department VARCHAR(100),
            D_O_J DATE,
            Company_Name VARCHAR(100),
            D_O_L DATE,
            D_O_B DATE,
            Gender VARCHAR(10),
            State VARCHAR(50),
            Contact VARCHAR(20),
            E_Mail VARCHAR(100),
            Name_as_per_Bank VARCHAR(100),
            Bank_Name VARCHAR(100),
            Location VARCHAR(100),
            PAN VARCHAR(20),
            AADHAR VARCHAR(20),
            Bank_Account VARCHAR(20),
            IFSC VARCHAR(20),
            UAN_Number VARCHAR(20),
            ESI_Number VARCHAR(20)
        )''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Payroll (
            id INT PRIMARY KEY AUTO_INCREMENT,
            Employee_Code VARCHAR(50),
            Month INT,
            Year INT,
            WDAY INT,
            LOPD INT,
            ACTDAYS INT,
            ARRDAYS INT,
            Days_Payable INT,
            Basic DECIMAL(10, 2),
            HRA DECIMAL(10, 2),
            Special_Allowance DECIMAL(10, 2),
            LTA DECIMAL(10, 2),
            Retention_Bonus DECIMAL(10, 2),
            Mobile_Internet_Allowance DECIMAL(10, 2),
            Professional_Development_Allowance DECIMAL(10, 2),
            Office_Attire DECIMAL(10, 2),
            Other_Allowance DECIMAL(10, 2),
            Additional_Payments DECIMAL(10, 2),
            Additional_Payment_Bonus DECIMAL(10, 2),
            GROSS_EARNING DECIMAL(10, 2) GENERATED ALWAYS AS 
                (Basic + HRA + Special_Allowance + LTA + Retention_Bonus + Mobile_Internet_Allowance + 
                 Professional_Development_Allowance + Office_Attire + Other_Allowance + 
                 Additional_Payments + Additional_Payment_Bonus) STORED,
            PF DECIMAL(10, 2),
            VPF DECIMAL(10, 2),
            LWF DECIMAL(10, 2),
            PT DECIMAL(10, 2),
            LWF_Arrears_Deduction DECIMAL(10, 2),
            Other_Deductions DECIMAL(10, 2),
            TDS DECIMAL(10, 2),
            GROSS_DEDUCTION DECIMAL(10, 2) GENERATED ALWAYS AS 
                (PF + VPF + LWF + PT + LWF_Arrears_Deduction + Other_Deductions + TDS) STORED,
            Net_Pay DECIMAL(10, 2) GENERATED ALWAYS AS 
                (GROSS_EARNING - GROSS_DEDUCTION) STORED,
            FOREIGN KEY (Employee_Code) REFERENCES Employees(Employee_Code)
        )''')

    conn.commit()
