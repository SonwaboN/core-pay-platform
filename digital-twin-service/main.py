from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from kafka import KafkaConsumer
from couchbase.cluster import Cluster, ClusterOptions
from couchbase.auth import PasswordAuthenticator
import json
import time
import threading
import uvicorn
import os

print("Digital Twin Service starting...")

# --- FastAPI App Setup ---
app = FastAPI(
    title="Digital Twin Service API",
    description="Manages customer digital twins and provides historical data.",
    version="1.0.0"
)

# --- Couchbase Connection Parameters ---
COUCHBASE_HOST = os.getenv("COUCHBASE_HOST", "couchbase")
COUCHBASE_USERNAME = os.getenv("COUCHBASE_USERNAME", "Administrator")
COUCHBASE_PASSWORD = os.getenv("COUCHBASE_PASSWORD", "password")
COUCHBASE_BUCKET = os.getenv("COUCHBASE_BUCKET", "default")

# --- Kafka Connection Parameters ---
KAFKA_BROKERS = [os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")]
KAFKA_TOPIC = 'live_outcome'

# Global variables for Couchbase connection
cluster = None
collection = None

# --- Couchbase Connection Initialization ---
def init_couchbase():
    global cluster, collection
    for i in range(10):
        try:
            print(f"Attempting to connect to Couchbase... (Attempt {i+1}/10)")
            cluster = Cluster(
                f"couchbase://{COUCHBASE_HOST}",
                ClusterOptions(PasswordAuthenticator(COUCHBASE_USERNAME, COUCHBASE_PASSWORD))
            )
            cluster.wait_until_ready(time.timedelta(seconds=10))
            bucket = cluster.bucket(COUCHBASE_BUCKET)
            collection = bucket.default_collection()
            print("Successfully connected to Couchbase.")
            return True
        except Exception as e:
            print(f"Could not connect to Couchbase: {e}, retrying in 5 seconds...")
            time.sleep(5)
    print("Failed to connect to Couchbase after multiple attempts. Exiting.")
    return False

# --- Kafka Consumer Setup ---
def consume_kafka_messages():
    consumer = None
    for i in range(10):
        try:
            print(f"Attempting to connect to Kafka consumer for {KAFKA_TOPIC}... (Attempt {i+1}/10)")
            consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=KAFKA_BROKERS,
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                group_id='digital-twin-group',
                value_deserializer=lambda x: json.loads(x.decode('utf-8'))
            )
            print(f"Successfully connected to Kafka topic: {KAFKA_TOPIC}")
            break
        except Exception as e:
            print(f"Could not connect to Kafka: {e}, retrying in 5 seconds...")
            time.sleep(5)
    else:
        print("Failed to connect to Kafka after multiple attempts. Exiting Kafka consumer thread.")
        return

    print("Digital Twin Service Kafka consumer is listening for messages...")
    for message in consumer:
        transaction = message.value
        customer_id = transaction.get('customer_id')

        if customer_id:
            try:
                # Store the entire transaction object in Couchbase
                # For a real digital twin, you'd merge/update existing data
                # For now, we'll just upsert the latest transaction for the customer_id
                collection.upsert(customer_id, transaction)
                print(f"Stored/Updated digital twin for customer {customer_id} in Couchbase.")
            except Exception as e:
                print(f"Error storing data in Couchbase for customer {customer_id}: {e}")
        else:
            print(f"Received message without customer_id: {transaction}")

# --- Pydantic Models for API ---
class CustomerHistory(BaseModel):
    customer_id: str
    last_transaction: dict
    # In a real scenario, this would be a list of transactions or aggregated data

# --- API Endpoints ---
@app.get("/v1/customers/{customer_id}/history", response_model=CustomerHistory)
async def get_customer_history(customer_id: str):
    """
    Retrieves the historical data for a specific customer from the digital twin.
    """
    if not collection:
        raise HTTPException(status_code=500, detail="Couchbase not initialized.")
    try:
        result = collection.get(customer_id)
        return CustomerHistory(customer_id=customer_id, last_transaction=result.content_as[dict])
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found or error: {e}")

# --- Startup Events ---
@app.on_event("startup")
async def startup_event():
    if not init_couchbase():
        print("Failed to initialize Couchbase on startup. Exiting.")
        exit(1)
    # Start Kafka consumer in a separate thread
    threading.Thread(target=consume_kafka_messages, daemon=True).start()

# --- Main execution ---
if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
