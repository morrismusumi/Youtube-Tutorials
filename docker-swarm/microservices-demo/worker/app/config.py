import os

API_BASE_URL = os.environ.get('API_BASE_URL', 'http://microservices-demo-api:8000')
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT = os.environ.get('OTEL_EXPORTER_OTLP_TRACES_ENDPOINT', 'http://localhost:4317')

