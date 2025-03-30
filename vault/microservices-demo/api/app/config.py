import os

DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'postgres')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASS = os.environ.get('DB_PASS', 'admin123xyz')
SSL_ON = os.environ.get('SSL_ON', 'false').lower() == 'true'
SSL_MODE = 'require' if SSL_ON else 'disable'
