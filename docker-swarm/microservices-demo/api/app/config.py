import os

DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASS = os.environ.get('DB_PASS', 'admin123xyz')

OTEL_EXPORTER_OTLP_TRACES_ENDPOINT = os.environ.get('OTEL_EXPORTER_OTLP_TRACES_ENDPOINT', 'http://localhost:4317')