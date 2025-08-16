from kafka import KafkaConsumer, KafkaProducer
import json
import time
import threading
import os

print("Divergence Detector starting...")

KAFKA_BROKERS = [os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")]
LIVE_OUTCOME_TOPIC = 'live_outcome'
SIMULATION_OUTCOME_TOPIC = 'simulation_outcome'
DIVERGENCE_ALERT_TOPIC = 'divergence_alert'

# In-memory store for transaction outcomes. In a real system, this might be Redis or a database.
transaction_outcomes = {}

# --- Kafka Producers and Consumers ---
producer = None
for i in range(10):
    try:
        print(f"Attempting to connect Kafka Producer... (Attempt {i+1}/10)")
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        producer.flush()
        print("Kafka Producer connected successfully.")
        break
    except Exception as e:
        print(f"Could not connect Kafka Producer: {e}, retrying in 5 seconds...")
        time.sleep(5)
else:
    print("Failed to connect Kafka Producer after multiple attempts. Exiting.")
    exit(1)

def create_consumer(topic, group_id):
    consumer = None
    for i in range(10):
        try:
            print(f"Attempting to connect Kafka Consumer for {topic}... (Attempt {i+1}/10)")
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=KAFKA_BROKERS,
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                group_id=group_id,
                value_deserializer=lambda x: json.loads(x.decode('utf-8'))
            )
            print(f"Kafka Consumer for {topic} connected successfully.")
            return consumer
        except Exception as e:
            print(f"Could not connect Kafka Consumer for {topic}: {e}, retrying in 5 seconds...")
            time.sleep(5)
    print(f"Failed to connect Kafka Consumer for {topic} after multiple attempts. Exiting.")
    exit(1)

live_consumer = create_consumer(LIVE_OUTCOME_TOPIC, 'divergence-detector-live-group')
simulation_consumer = create_consumer(SIMULATION_OUTCOME_TOPIC, 'divergence-detector-sim-group')


def process_message(message, source_type):
    transaction = message.value
    transaction_id = transaction.get('transaction_id')

    if not transaction_id:
        print(f"Received message without transaction_id from {source_type}: {transaction}")
        return

    if transaction_id not in transaction_outcomes:
        transaction_outcomes[transaction_id] = {
            'live': None,
            'sim': None,
            'timestamp': time.time(), # To potentially clean up old entries
            'original_transaction': transaction # Store the full transaction for context
        }

    if source_type == 'live':
        transaction_outcomes[transaction_id]['live'] = transaction
    elif source_type == 'sim':
        transaction_outcomes[transaction_id]['sim'] = transaction

    # Check for divergence if both outcomes are present
    if transaction_outcomes[transaction_id]['live'] and transaction_outcomes[transaction_id]['sim']:
        live_data = transaction_outcomes[transaction_id]['live']
        sim_data = transaction_outcomes[transaction_id]['sim']

        live_decision = live_data.get('decision')
        sim_decision = sim_data.get('decision')

        if live_decision != sim_decision:
            print(f"DIVERGENCE DETECTED for transaction_id: {transaction_id}")
            print(f"  Live Decision: {live_decision}")
            print(f"  Sim Decision: {sim_decision}")

            alert_message = {
                'transaction_id': transaction_id,
                'divergence_type': f"Decision Mismatch: Live={live_decision}, Sim={sim_decision}",
                'live_outcome': live_data,
                'simulation_outcome': sim_data,
                'timestamp': datetime.datetime.now().isoformat()
            }
            producer.send(DIVERGENCE_ALERT_TOPIC, value=alert_message)
            producer.flush()
            print(f"Divergence alert sent for transaction_id: {transaction_id}")
        else:
            print(f"No divergence for transaction_id: {transaction_id}. Decisions match: {live_decision}")

        # Clean up after comparison
        del transaction_outcomes[transaction_id]


def consume_live_messages():
    for message in live_consumer:
        process_message(message, 'live')

def consume_sim_messages():
    for message in simulation_consumer:
        process_message(message, 'sim')

# Start consumers in separate threads
live_thread = threading.Thread(target=consume_live_messages)
sim_thread = threading.Thread(target=consume_sim_messages)

live_thread.start()
sim_thread.start()

print("Divergence Detector is running and listening for messages...")

# Keep the main thread alive
while True:
    time.sleep(1)
