from __future__ import annotations
from typing import Any, Dict, List, Optional
import uuid
from datetime import datetime

from app.common.db import get_db_session
from app.common.models import CustomerInquiry, Order


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

    with get_db_session() as db:
        inquiry_id = str(uuid.uuid4())

        inquiry = CustomerInquiry(
            inquiry_id=inquiry_id,
            session_id=session_id,
            inquiry_type=inquiry_type,
            message=message,
            related_order_id=order_id,
            status="open"
        )
        db.add(inquiry)
        # commit() happens automatically in context manager

        return {
            "inquiry_id": inquiry_id,
            "inquiry_type": inquiry_type,
            "message": message,
            "status": "open",
            "order_id": order_id,
            "created_at": inquiry.created_at.isoformat(),
            "response": "Your inquiry has been submitted and will be reviewed.",
        }


def get_inquiry_status(inquiry_id: str) -> Dict[str, Any]:
    """
    Check inquiry status.

    Args:
        inquiry_id: Inquiry identifier

    Returns:
        Inquiry status details
    """
    with get_db_session() as db:
        inquiry = db.query(CustomerInquiry).filter(
            CustomerInquiry.inquiry_id == inquiry_id).first()

        if not inquiry:
            raise ValueError(f"Inquiry {inquiry_id} not found")

        return {
            "inquiry_id": inquiry.inquiry_id,
            "inquiry_type": inquiry.inquiry_type,
            "message": inquiry.message,
            "status": inquiry.status,
            "order_id": inquiry.related_order_id,
            "created_at": inquiry.created_at.isoformat() if inquiry.created_at else "",
            "response": f"Inquiry status: {inquiry.status}",
        }


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
    with get_db_session() as db:
        # Get order
        order = db.query(Order).filter(Order.order_id == order_id).first()

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


def get_order_inquiries(order_id: str) -> List[Dict[str, Any]]:
    """
    Get all inquiries for an order.

    Args:
        order_id: Order identifier

    Returns:
        List of inquiries related to the order
    """
    with get_db_session() as db:
        inquiries = db.query(CustomerInquiry).filter(
            CustomerInquiry.related_order_id == order_id
        ).order_by(CustomerInquiry.created_at.desc()).all()

        result = []
        for inquiry in inquiries:
            result.append({
                "inquiry_id": inquiry.inquiry_id,
                "inquiry_type": inquiry.inquiry_type,
                "status": inquiry.status,
                "created_at": inquiry.created_at.isoformat() if inquiry.created_at else "",
            })

        return result
