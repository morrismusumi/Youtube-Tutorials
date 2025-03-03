import urllib.request
import urllib.parse
import json
import time
import random
from config import API_BASE_URL, OTEL_EXPORTER_OTLP_TRACES_ENDPOINT
# OTEL Instrumentation
import opentelemetry.trace as trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.urllib import URLLibInstrumentor
from opentelemetry.propagate import inject

# Define a resource with a service name
resource = Resource.create({"service.name": "worker"})

# Set up Tracer Provider
tracer_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(tracer_provider)

# Configure Span Exporters
console_exporter = ConsoleSpanExporter()
otlp_exporter = OTLPSpanExporter(endpoint=OTEL_EXPORTER_OTLP_TRACES_ENDPOINT, insecure=True)

# Add Span Processors
tracer_provider.add_span_processor(SimpleSpanProcessor(console_exporter))
tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

# Instrument urllib
URLLibInstrumentor().instrument()

# Set Tracer
tracer = trace.get_tracer(__name__)

def post_order(order_no):
    url = f"{API_BASE_URL}/orders"
    headers = {
        'Content-Type': 'application/json',
    }
    data = json.dumps({"order_no": order_no}).encode('utf-8')
    
    # OTEL Instrumentation
    inject(headers)
    with tracer.start_as_current_span("post_order"):
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        with urllib.request.urlopen(req) as response:
            response_body = response.read()
            print(f"Order {order_no} posted successfully: {response_body}")

def schedule_random_post_order():
    while True:
        # Generate a random order number
        order_no = str(random.randint(10000000, 99999999))
        try:
            post_order(order_no)
        except urllib.error.HTTPError as e:
            print(f"HTTPError for order {order_no}: {e.code} - {e.reason}")
        except urllib.error.URLError as e:
            print(f"URLError for order {order_no}: {e.reason}")
        time.sleep(5)

if __name__ == "__main__":
    print("Starting worker...")
    schedule_random_post_order()





