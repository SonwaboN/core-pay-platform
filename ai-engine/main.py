from kafka import KafkaConsumer, KafkaProducer
import json
import time
import joblib
import pandas as pd
import requests
import os

print("AI Engine starting...")

MOCK_GATEWAY_URL = os.getenv("MOCK_GATEWAY_URL", "http://mock-payment-gateway:5000/process")

# Add a delay before trying to connect to Kafka
time.sleep(15)

# Load the trained model
try:
    model = joblib.load('fraud_detection_model.joblib')
    print("Fraud detection model loaded successfully.")
except FileNotFoundError:
    print("Error: fraud_detection_model.joblib not found. Please run train_model.py first.")
    exit(1)

# Define the features and expected columns for the model
# These must match the features used during training
features = ['amount', 'transactions_per_hour', 'device_type_mobile']
device_type_columns = ['device_type_mobile', 'device_type_desktop'] # All possible one-hot encoded columns

consumer = KafkaConsumer(
    'raw_transactions',
    bootstrap_servers=[os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")],
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='ai-engine-group',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

producer = KafkaProducer(
    bootstrap_servers=[os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def call_mock_gateway(transaction_data):
    try:
        response = requests.post(MOCK_GATEWAY_URL, json=transaction_data, timeout=5)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling mock payment gateway: {e}")
        return {"status": "FAILED", "message": str(e)}

print("AI Engine is listening for messages...")
for message in consumer:
    transaction = message.value
    print(f"AI Engine received: {transaction}")

    # --- Simulation Path (ML Model) ---
    # Prepare data for the model
    df = pd.DataFrame([transaction])
    df = pd.get_dummies(df, columns=['device_type'], prefix='device_type')
    for col in features:
        if col not in df.columns:
            df[col] = 0 # Ensure all expected features are present
    
    X_predict = df[features]

    # Make prediction
    is_fraud_prediction = model.predict(X_predict)[0]
    fraud_probability = model.predict_proba(X_predict)[0][1] # Probability of being fraud

    # Determine decision based on prediction
    sim_decision = "DENY" if is_fraud_prediction == 1 else "APPROVE"

    # Enrich the transaction with AI results for simulation
    simulated_transaction = transaction.copy()
    simulated_transaction['risk_score'] = round(float(fraud_probability), 4)
    simulated_transaction['decision'] = sim_decision
    simulated_transaction['ai_model_version'] = "1.0" # Example versioning
    simulated_transaction['path'] = "simulation"

    # --- Live Path (Mock Gateway) ---
    live_transaction = transaction.copy()
    gateway_response = call_mock_gateway(live_transaction)
    live_decision = "APPROVE" if gateway_response.get("status") == "SUCCESS" else "DENY"
    live_transaction['gateway_status'] = gateway_response.get("status")
    live_transaction['gateway_message'] = gateway_response.get("message")
    live_transaction['decision'] = live_decision
    live_transaction['path'] = "live"

    print(f"AI Engine processed simulation path: {simulated_transaction}")
    print(f"AI Engine processed live path: {live_transaction}")

    # Produce to live_outcome topic
    producer.send('live_outcome', value=live_transaction)
    producer.flush()
    print(f"Produced enriched transaction to live_outcome topic.")

    # Produce to simulation_outcome topic
    producer.send('simulation_outcome', value=simulated_transaction)
    producer.flush()
    print(f"Produced enriched transaction to simulation_outcome topic.")
