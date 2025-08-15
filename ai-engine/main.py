from kafka import KafkaConsumer
import json
import time

print("AI Engine starting...")

# Add a delay before trying to connect to Kafka
time.sleep(15)

consumer = KafkaConsumer(
    'raw_transactions',
    bootstrap_servers=['kafka:29092'],
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='ai-engine-group',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

print("AI Engine is listening for messages...")
for message in consumer:
    transaction = message.value
    print(f"AI Engine received: {transaction}")
    # TODO: Add AI model processing here
