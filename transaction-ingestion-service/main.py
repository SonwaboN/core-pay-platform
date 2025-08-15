from flask import Flask, request, jsonify
from kafka import KafkaProducer
import json

app = Flask(__name__)
producer = KafkaProducer(
    bootstrap_servers=['kafka:29092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

@app.route('/transaction', methods=['POST'])
def handle_transaction():
    print(f"Incoming headers: {request.headers}")
    transaction_data = request.get_json()
    # TODO: Add validation
    producer.send('raw_transactions', value=transaction_data)
    producer.flush()
    return jsonify({"status": "Transaction received"}), 202

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
