from flask import Flask, request, jsonify
import random

app = Flask(__name__)

@app.route('/process', methods=['POST'])
def process_payment():
    data = request.get_json()
    print(f"Mock Payment Gateway received request: {data}")

    # Simulate a success for now. Can add random failures later.
    response = {
        "status": "SUCCESS",
        "gateway_reference": str(random.randint(100000, 999999)),
        "message": "Payment processed successfully by mock gateway."
    }
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
