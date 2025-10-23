from __future__ import annotations
from typing import Any, Dict, List
import uuid
from datetime import datetime

from app.common.db import get_conn, put_conn


def create_payment_mandate(order_id: str, payment_method: str) -> Dict[str, Any]:
    """
    Create AP2 payment mandate.

    Args:
        order_id: Order identifier
        payment_method: Payment method (e.g., 'credit_card', 'paypal')

    Returns:
        Mandate details with status
    """
    conn = get_conn()
    try:
        cur = conn.cursor()

        # Get order details
        cur.execute(
            "SELECT total_amount, session_id FROM orders WHERE order_id = %s",
            (order_id,)
        )

        order = cur.fetchone()
        if not order:
            raise ValueError(f"Order {order_id} not found")

        # Create mandate
        mandate_id = str(uuid.uuid4())
        mandate_data = {
            "order_id": order_id,
            "amount": float(order[0]),
            "payment_method": payment_method,
            "timestamp": datetime.now().isoformat(),
        }

        # Insert mandate (signature to be implemented)
        cur.execute(
            """INSERT INTO mandates (mandate_id, mandate_type, session_id, mandate_data, status, created_at)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (mandate_id, "payment", order[1], str(
                mandate_data), "pending", datetime.now())
        )
        conn.commit()

        return {
            "mandate_id": mandate_id,
            "order_id": order_id,
            "amount": float(order[0]),
            "payment_method": payment_method,
            "status": "pending",
            "message": "Payment mandate created",
        }
    finally:
        put_conn(conn)


def process_payment(order_id: str, payment_method: str) -> Dict[str, Any]:
    """
    Process payment with AP2 compliance.

    Args:
        order_id: Order identifier
        payment_method: Payment method

    Returns:
        Payment details with transaction ID
    """
    conn = get_conn()
    try:
        cur = conn.cursor()

        # Get order
        cur.execute(
            "SELECT total_amount, session_id FROM orders WHERE order_id = %s",
            (order_id,)
        )

        order = cur.fetchone()
        if not order:
            raise ValueError(f"Order {order_id} not found")

        # Create payment mandate first
        mandate_result = create_payment_mandate(order_id, payment_method)
        mandate_id = mandate_result["mandate_id"]

        # Create payment record
        payment_id = str(uuid.uuid4())
        transaction_id = f"txn_{uuid.uuid4().hex[:16]}"

        cur.execute(
            """INSERT INTO payments (payment_id, order_id, amount, payment_method, 
                                     payment_mandate_id, transaction_id, status, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (payment_id, order_id, order[0], payment_method, mandate_id,
             transaction_id, "completed", datetime.now())
        )

        # Update order status
        cur.execute(
            "UPDATE orders SET status = 'completed' WHERE order_id = %s",
            (order_id,)
        )

        # Update mandate status
        cur.execute(
            "UPDATE mandates SET status = 'approved' WHERE mandate_id = %s",
            (mandate_id,)
        )

        conn.commit()

        return {
            "payment_id": payment_id,
            "order_id": order_id,
            "amount": float(order[0]),
            "payment_method": payment_method,
            "status": "completed",
            "transaction_id": transaction_id,
            "payment_mandate_id": mandate_id,
            "message": "Payment processed successfully",
        }
    finally:
        put_conn(conn)


def get_payment_status(payment_id: str) -> Dict[str, Any]:
    """
    Check payment status.

    Args:
        payment_id: Payment identifier

    Returns:
        Payment status details
    """
    conn = get_conn()
    try:
        cur = conn.cursor()

        cur.execute(
            """SELECT payment_id, order_id, amount, payment_method, status, 
                      transaction_id, payment_mandate_id, created_at
               FROM payments WHERE payment_id = %s""",
            (payment_id,)
        )

        payment = cur.fetchone()

        if not payment:
            raise ValueError(f"Payment {payment_id} not found")

        return {
            "payment_id": payment[0],
            "order_id": payment[1],
            "amount": float(payment[2]),
            "payment_method": payment[3],
            "status": payment[4],
            "transaction_id": payment[5],
            "payment_mandate_id": payment[6],
            "processed_at": payment[7].isoformat() if payment[7] else "",
            "message": f"Payment status: {payment[4]}",
        }
    finally:
        put_conn(conn)


def refund_payment(payment_id: str, reason: str) -> Dict[str, Any]:
    """
    Initiate refund.

    Args:
        payment_id: Payment identifier
        reason: Reason for refund

    Returns:
        Refund details
    """
    conn = get_conn()
    try:
        cur = conn.cursor()

        # Get payment
        cur.execute(
            "SELECT amount, order_id FROM payments WHERE payment_id = %s",
            (payment_id,)
        )

        payment = cur.fetchone()
        if not payment:
            raise ValueError(f"Payment {payment_id} not found")

        # Update payment status
        cur.execute(
            "UPDATE payments SET status = 'refunded' WHERE payment_id = %s",
            (payment_id,)
        )

        # Update order status
        cur.execute(
            "UPDATE orders SET status = 'refunded' WHERE order_id = %s",
            (payment[1],)
        )

        conn.commit()

        return {
            "refund_id": str(uuid.uuid4()),
            "payment_id": payment_id,
            "amount": float(payment[0]),
            "reason": reason,
            "status": "refunded",
            "message": "Refund processed successfully",
        }
    finally:
        put_conn(conn)


def get_payment_history(session_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve payment history.

    Args:
        session_id: Session identifier

    Returns:
        List of payment records
    """
    conn = get_conn()
    try:
        cur = conn.cursor()

        cur.execute(
            """SELECT p.payment_id, p.order_id, p.amount, p.payment_method, 
                      p.status, p.created_at
               FROM payments p
               JOIN orders o ON p.order_id = o.order_id
               WHERE o.session_id = %s
               ORDER BY p.created_at DESC""",
            (session_id,)
        )

        payments = []
        for row in cur.fetchall():
            payments.append({
                "payment_id": row[0],
                "order_id": row[1],
                "amount": float(row[2]),
                "payment_method": row[3],
                "status": row[4],
                "date": row[5].isoformat() if row[5] else "",
            })

        return payments
    finally:
        put_conn(conn)
