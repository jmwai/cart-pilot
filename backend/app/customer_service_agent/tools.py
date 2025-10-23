from __future__ import annotations
from typing import Any, Dict, List, Optional
import uuid
from datetime import datetime

from app.common.db import get_conn, put_conn


def create_inquiry(inquiry_type: str, message: str, session_id: str, order_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Create customer inquiry.

    Args:
        inquiry_type: Type of inquiry ('return', 'refund', 'question', 'complaint', 'product_issue')
        message: Inquiry message
        session_id: Session identifier
        order_id: Related order ID (optional)

    Returns:
        Inquiry details with status
    """
    valid_types = ['return', 'refund',
                   'question', 'complaint', 'product_issue']
    if inquiry_type not in valid_types:
        raise ValueError(f"Inquiry type must be one of: {valid_types}")

    conn = get_conn()
    try:
        cur = conn.cursor()

        inquiry_id = str(uuid.uuid4())

        cur.execute(
            """INSERT INTO customer_inquiries (inquiry_id, session_id, inquiry_type, message, 
                                                related_order_id, status, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (inquiry_id, session_id, inquiry_type,
             message, order_id, "open", datetime.now())
        )
        conn.commit()

        return {
            "inquiry_id": inquiry_id,
            "inquiry_type": inquiry_type,
            "message": message,
            "status": "open",
            "order_id": order_id,
            "created_at": datetime.now().isoformat(),
            "response": "Your inquiry has been submitted and will be reviewed.",
        }
    finally:
        put_conn(conn)


def get_inquiry_status(inquiry_id: str) -> Dict[str, Any]:
    """
    Check inquiry status.

    Args:
        inquiry_id: Inquiry identifier

    Returns:
        Inquiry status details
    """
    conn = get_conn()
    try:
        cur = conn.cursor()

        cur.execute(
            """SELECT inquiry_id, inquiry_type, message, status, related_order_id, created_at
               FROM customer_inquiries WHERE inquiry_id = %s""",
            (inquiry_id,)
        )

        inquiry = cur.fetchone()

        if not inquiry:
            raise ValueError(f"Inquiry {inquiry_id} not found")

        return {
            "inquiry_id": inquiry[0],
            "inquiry_type": inquiry[1],
            "message": inquiry[2],
            "status": inquiry[3],
            "order_id": inquiry[4],
            "created_at": inquiry[5].isoformat() if inquiry[5] else "",
            "response": f"Inquiry status: {inquiry[3]}",
        }
    finally:
        put_conn(conn)


def search_faq(query: str) -> List[Dict[str, Any]]:
    """
    Search FAQ knowledge base.

    Args:
        query: Search query

    Returns:
        List of FAQ entries matching the query
    """
    # TODO: Implement vector search over FAQ knowledge base
    # For now, return mock results

    faq_data = [
        {
            "question": "How do I return an item?",
            "answer": "You can initiate a return by contacting customer service with your order ID.",
            "relevance_score": 0.9,
        },
        {
            "question": "What is your refund policy?",
            "answer": "We offer full refunds within 30 days of purchase.",
            "relevance_score": 0.8,
        },
        {
            "question": "How long does shipping take?",
            "answer": "Standard shipping takes 5-7 business days.",
            "relevance_score": 0.7,
        },
    ]

    # Simple keyword matching (replace with vector search)
    results = []
    query_lower = query.lower()

    for faq in faq_data:
        if query_lower in faq["question"].lower() or query_lower in faq["answer"].lower():
            results.append(faq)

    return results if results else faq_data[:2]


def initiate_return(order_id: str, reason: str, session_id: str) -> Dict[str, Any]:
    """
    Initiate return process.

    Args:
        order_id: Order identifier
        reason: Reason for return
        session_id: Session identifier

    Returns:
        Return details with instructions
    """
    conn = get_conn()
    try:
        cur = conn.cursor()

        # Get order
        cur.execute(
            "SELECT status FROM orders WHERE order_id = %s", (order_id,))
        order = cur.fetchone()

        if not order:
            raise ValueError(f"Order {order_id} not found")

        # Create return inquiry
        inquiry_result = create_inquiry("return", reason, session_id, order_id)

        return {
            "return_id": str(uuid.uuid4()),
            "order_id": order_id,
            "status": "initiated",
            "reason": reason,
            "instructions": "Please package the item securely and schedule a pickup.",
            "inquiry_id": inquiry_result["inquiry_id"],
        }
    finally:
        put_conn(conn)


def get_order_inquiries(order_id: str) -> List[Dict[str, Any]]:
    """
    Get all inquiries for an order.

    Args:
        order_id: Order identifier

    Returns:
        List of inquiries related to the order
    """
    conn = get_conn()
    try:
        cur = conn.cursor()

        cur.execute(
            """SELECT inquiry_id, inquiry_type, status, created_at
               FROM customer_inquiries WHERE related_order_id = %s
               ORDER BY created_at DESC""",
            (order_id,)
        )

        inquiries = []
        for row in cur.fetchall():
            inquiries.append({
                "inquiry_id": row[0],
                "inquiry_type": row[1],
                "status": row[2],
                "created_at": row[3].isoformat() if row[3] else "",
            })

        return inquiries
    finally:
        put_conn(conn)
