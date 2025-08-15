import requests
import json

url = "http://localhost:8080/transaction"
headers = {'Content-Type': 'application/json'}
data = {"transaction_id": "t123", "amount": 100.0, "currency": "USD"}

try:
    response = requests.post(url, headers=headers, data=json.dumps(data))
    print(f"Status Code: {response.status_code}")
    print(f"Response JSON: {response.json()}")
except requests.exceptions.ConnectionError as e:
    print(f"Connection Error: {e}")
