from __future__ import annotations
from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field
from typing import Optional

from .tools import (
    create_payment_mandate,
    process_payment,
    get_payment_status,
    refund_payment,
    get_payment_history,
)

GEMINI_MODEL = "gemini-2.5-flash"


class PaymentOutput(BaseModel):
    payment_id: str = Field(description="Payment ID")
    order_id: str = Field(description="Order ID")
    amount: float = Field(description="Payment amount")
    payment_method: str = Field(description="Payment method")
    status: str = Field(description="Payment status")
    transaction_id: Optional[str] = Field(
        description="Transaction ID", default="")
    payment_mandate_id: Optional[str] = Field(
        description="AP2 mandate ID", default="")
    message: Optional[str] = Field(description="Status message", default="")


root_agent = LlmAgent(
    name="payment_agent",
    instruction="""You are a payment processing assistant. Your role is to process payments securely with AP2 compliance.
    You can create payment mandates, process payments, check payment status, issue refunds, and retrieve payment history.
    Always ensure AP2 mandates are created for audit and compliance.
    """,
    description="Processes payments using AP2 protocol with cryptographic mandates",
    model=GEMINI_MODEL,
    tools=[
        create_payment_mandate,
        process_payment,
        get_payment_status,
        refund_payment,
        get_payment_history,
    ],
    output_schema=PaymentOutput,
    output_key="payment",
)
