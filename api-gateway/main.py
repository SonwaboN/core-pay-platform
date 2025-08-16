from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict
import uuid
import datetime
import os
from kafka import KafkaProducer
import json

# --- Pydantic Models for Data Validation ---

class Transaction(BaseModel):
    customer_id: str = Field(..., description="The unique identifier for the customer.")
    amount: float = Field(..., gt=0, description="The transaction amount.")
    currency: str = Field(..., min_length=3, max_length=3, description="ISO currency code.")
    merchant_id: str = Field(..., description="The unique identifier for the merchant.")
    device_type: str = Field(..., description="Type of device used for the transaction (e.g., 'mobile', 'desktop').")

class TransactionResponse(BaseModel):
    transaction_id: str = Field(..., description="The unique identifier for the processed transaction.")
    status: str = Field(..., description="The status of the transaction processing.")
    received_at: datetime.datetime = Field(..., description="Timestamp when the transaction was received.")

class TransactionDetails(Transaction):
    transaction_id: str
    status: str
    risk_score: float
    live_outcome: Dict
    simulation_outcome: Dict
    divergence_detected: bool

class CustomerAnalytics(BaseModel):
    customer_id: str
    total_spend_30d: float
    transaction_count_30d: int
    average_risk_score: float
    denial_rate_30d: float

class DivergenceReport(BaseModel):
    transaction_id: str
    diverged_at: datetime.datetime
    live_decision: str
    sim_decision: str

class SimulationResponse(BaseModel):
    simulation_id: str
    predicted_decision: str
    risk_score: float
    reasoning: List[str]


# --- FastAPI Application ---

app = FastAPI(
    title="CorePay API",
    description="API for processing transactions and accessing analytics and simulation services.",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the CorePay API"}

# --- API Endpoints ---

@app.post("/v1/transactions", response_model=TransactionResponse, status_code=202)
async def process_transaction(transaction: Transaction):
    """
    Receives a new transaction, assigns a unique ID, and submits it for processing.
    This is an asynchronous operation.
    """
    producer = KafkaProducer(
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092"),
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    producer.send('raw_transactions', value=transaction.dict())
    producer.flush()
    print(f"Received transaction: {transaction.dict()}")
    
    response = TransactionResponse(
        transaction_id=str(uuid.uuid4()),
        status="Transaction received and is being processed.",
        received_at=datetime.datetime.now()
    )
    return response

@app.get("/v1/transactions/{transaction_id}", response_model=TransactionDetails)
async def get_transaction_details(transaction_id: str):
    """
    Retrieves the detailed status and outcomes of a specific transaction.
    (STUBBED RESPONSE)
    """
    # This is a mock response. In a real implementation, this would query
    # a database (e.g., Couchbase) to get the real data.
    return TransactionDetails(
        transaction_id=transaction_id,
        status="Completed",
        risk_score=0.12,
        live_outcome={"decision": "APPROVE", "reason": "Within normal parameters"},
        simulation_outcome={"decision": "APPROVE", "reason": "Matches historical spending"},
        divergence_detected=False,
        customer_id="cust_123",
        amount=100.50,
        currency="ZAR",
        merchant_id="merch_456",
        device_type="mobile"
    )

@app.get("/v1/customers/{customer_id}/analytics", response_model=CustomerAnalytics)
async def get_customer_analytics(customer_id: str):
    """
    Provides aggregated analytics for a specific customer.
    (STUBBED RESPONSE)
    """
    # Mock response. This would be calculated by the digital-twin-service.
    return CustomerAnalytics(
        customer_id=customer_id,
        total_spend_30d=5430.21,
        transaction_count_30d=45,
        average_risk_score=0.08,
        denial_rate_30d=0.02
    )

@app.get("/v1/reports/divergence", response_model=List[DivergenceReport])
async def get_divergence_report(start_date: datetime.date, end_date: datetime.date):
    """
    Gets a report of all detected divergences over a time period.
    (STUBBED RESPONSE)
    """
    # Mock response. This would query a persistent store of alerts.
    return [
        DivergenceReport(
            transaction_id=str(uuid.uuid4()),
            diverged_at=datetime.datetime.now() - datetime.timedelta(days=1),
            live_decision="DENY",
            sim_decision="APPROVE"
        )
    ]

@app.post("/v1/simulations", response_model=SimulationResponse)
async def run_what_if_simulation(transaction: Transaction):
    """
    Runs a "what-if" simulation for a given transaction without processing it live.
    (STUBBED RESPONSE)
    """
    # Mock response. This would trigger the simulation path in the ai-engine.
    return SimulationResponse(
        simulation_id=str(uuid.uuid4()),
        predicted_decision="APPROVE",
        risk_score=0.05,
        reasoning=["Amount is typical for this customer", "Merchant is trusted"]
    )
