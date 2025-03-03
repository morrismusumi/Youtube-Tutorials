from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import psycopg2
from config import DB_HOST, DB_PORT, DB_USER, DB_PASS, OTEL_EXPORTER_OTLP_TRACES_ENDPOINT
# OTEL Instrumentation
import opentelemetry.trace as trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Set up Tracer Provider with a Service Name
resource = Resource.create({"service.name": "api-service"})
tracer_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(tracer_provider)

# Configure Exporters
console_exporter = ConsoleSpanExporter()
otlp_exporter = OTLPSpanExporter(endpoint=OTEL_EXPORTER_OTLP_TRACES_ENDPOINT, insecure=True)

# Add Span Processors
tracer_provider.add_span_processor(BatchSpanProcessor(console_exporter))
tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))


app = FastAPI()

# OTEL Instrumentation
FastAPIInstrumentor.instrument_app(app)

# Instrument PostgreSQL (psycopg2)
Psycopg2Instrumentor().instrument()


# Set Tracer
tracer = trace.get_tracer(__name__)

class Order(BaseModel):
    order_no: str

# Function to establish a connection to PostgreSQL
def connect_to_postgres():
    # Connection parameters - update these with your details
    conn_params = {
        'dbname': 'postgres',
        'user': DB_USER,
        'password': DB_PASS,
        'host': DB_HOST,
        'port': DB_PORT
    }
    # Establishing the connection
    conn = psycopg2.connect(**conn_params)
    
    # Creating a cursor object using the connection
    cursor = conn.cursor()
    
    # SQL statement for creating the database and table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            order_no TEXT NOT NULL
        );
    """)
    
    # Committing the SQL command
    conn.commit()
    
    return conn, cursor

def save_order_to_db(order_no):
    with tracer.start_as_current_span("insert_into_db"):
        try:
            conn, cursor = connect_to_postgres()
            insert_sql = "INSERT INTO orders (order_no) VALUES (%s);"
            cursor.execute(insert_sql, (order_no,))
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"INFO:     Order: {order_no} saved successfully!")
            return True
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error: {error}")
            return False


# Define your POST endpoint to receive plain text
@app.get("/")
async def home():
    return "Welcome to the microserivces-demo API!!"

# Define your POST endpoint to receive plain text
@app.post("/orders")
async def receive_text(order: Order):
    if save_order_to_db(order.order_no):
        return JSONResponse(content={"status": "success", "message": f"Order: {order.order_no} created!"}, status_code=status.HTTP_200_OK)
    else:
        return JSONResponse(content={"status": "failed", "message": f"Failed to Create Order: {order.order_no}"}, status_code=status.HTTP_200_OK)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)