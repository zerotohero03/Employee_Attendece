import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your_secret_key')
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/path/to/upload/folder')
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'Aakash@312003')
    DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')
    DB_NAME = os.environ.get('DB_NAME', 'payroll_db')
    DB_POOL_SIZE = int(os.environ.get('DB_POOL_SIZE', 20))   # specify number of connections that can be made a time to the database. currently it is set to 20 and upper limit is 32.
    #employee dashboard related
    DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database/employees.db')
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')