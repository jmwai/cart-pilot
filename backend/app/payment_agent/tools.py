from __future__ import annotations
from typing import Any, Dict, List
import uuid
from datetime import datetime
import json

from app.common.db import get_db_session
from app.common.models import Order, Mandate, Payment


def create_payment_mandate(order_id: str, payment_method: str) -> Dict[str, Any]:
    """
    Create AP2 payment mandate.

    Args:
        order_id: Order identifier.
        payment_method: Payment method (e.g., 'credit_card', 'paypal')

    Returns:
        Mandate details with status
    """
    with get_db_session() as db:
        # Get order details
        order = db.query(Order).filter(Order.order_id == order_id).first()
        if not order:
            raise ValueError(f"Order {order_id} not found")

        # Create mandate
        mandate_id = str(uuid.uuid4())
        mandate_data = {
            "order_id": order_id,
            "amount": order.total_amount,
            "payment_method": payment_method,
            "timestamp": datetime.now().isoformat(),
        }

        mandate = Mandate(
            mandate_id=mandate_id,
            mandate_type="payment",
            session_id=order.session_id,
            mandate_data=json.dumps(mandate_data),
            status="pending"
        )
        db.add(mandate)
        # commit() happens automatically in context manager

        return {
            "mandate_id": mandate_id,
            "order_id": order_id,
            "amount": order.total_amount,
            "payment_method": payment_method,
            "status": "pending",
            "message": "Payment mandate created",
        }


def process_payment(order_id: str, payment_method: str) -> Dict[str, Any]:
    """
    Process payment with AP2 compliance.

    Args:
        order_id: Order identifier
        payment_method: Payment method

    Returns:
        Payment details with transaction ID
    """
    with get_db_session() as db:
        # Get order
        order = db.query(Order).filter(Order.order_id == order_id).first()
        if not order:
            raise ValueError(f"Order {order_id} not found")

        # Create payment mandate first
        mandate_result = create_payment_mandate(order_id, payment_method)
        mandate_id = mandate_result["mandate_id"]

        # Create payment record
        payment_id = str(uuid.uuid4())
        transaction_id = f"txn_{uuid.uuid4().hex[:16]}"

        payment = Payment(
            payment_id=payment_id,
            order_id=order_id,
            amount=order.total_amount,
            payment_method=payment_method,
            payment_mandate_id=mandate_id,
            transaction_id=transaction_id,
            status="completed"
        )
        db.add(payment)

        # Update order status
        order.status = "completed"

        # Update mandate status
        mandate = db.query(Mandate).filter(
            Mandate.mandate_id == mandate_id).first()
        if mandate:
            mandate.status = "approved"

        # commit() happens automatically in context manager

        return {
            "payment_id": payment_id,
            "order_id": order_id,
            "amount": order.total_amount,
            "payment_method": payment_method,
            "status": "completed",
            "transaction_id": transaction_id,
            "payment_mandate_id": mandate_id,
            "message": "Payment processed successfully",
        }


def get_payment_status(payment_id: str) -> Dict[str, Any]:
    """
    Check payment status.

    Args:
        payment_id: Payment identifier

    Returns:
        Payment status details
    """
    with get_db_session() as db:
        payment = db.query(Payment).filter(
            Payment.payment_id == payment_id).first()

        if not payment:
            raise ValueError(f"Payment {payment_id} not found")

        return {
            "payment_id": payment.payment_id,
            "order_id": payment.order_id,
            "amount": payment.amount,
            "payment_method": payment.payment_method,
            "status": payment.status,
            "transaction_id": payment.transaction_id,
            "payment_mandate_id": payment.payment_mandate_id,
            "processed_at": payment.created_at.isoformat() if payment.created_at else "",
            "message": f"Payment status: {payment.status}",
        }


def refund_payment(payment_id: str, reason: str) -> Dict[str, Any]:
    """
    Initiate refund.

    Args:
        payment_id: Payment identifier
        reason: Reason for refund

    Returns:
        Refund details
    """
    with get_db_session() as db:
        # Get payment
        payment = db.query(Payment).filter(
            Payment.payment_id == payment_id).first()
        if not payment:
            raise ValueError(f"Payment {payment_id} not found")

        # Update payment status
        payment.status = "refunded"

        # Update order status
        order = db.query(Order).filter(
            Order.order_id == payment.order_id).first()
        if order:
            order.status = "refunded"

        # commit() happens automatically in context manager

        return {
            "refund_id": str(uuid.uuid4()),
            "payment_id": payment_id,
            "amount": payment.amount,
            "reason": reason,
            "status": "refunded",
            "message": "Refund processed successfully",
        }


def get_payment_history(session_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve payment history.

    Args:
        session_id: Session identifier

    Returns:
        List of payment records
    """
    with get_db_session() as db:
        # Query payments via order relationship
        payments = db.query(Payment).join(Order).filter(
            Order.session_id == session_id
        ).order_by(Payment.created_at.desc()).all()

        result = []
        for payment in payments:
            result.append({
                "payment_id": payment.payment_id,
                "order_id": payment.order_id,
                "amount": payment.amount,
                "payment_method": payment.payment_method,
                "status": payment.status,
                "date": payment.created_at.isoformat() if payment.created_at else "",
            })

        return result
