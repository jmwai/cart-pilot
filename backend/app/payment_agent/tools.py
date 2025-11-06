from __future__ import annotations
from typing import Any, Dict, List, Optional
import uuid
from datetime import datetime
import json

from google.adk.tools import ToolContext

from app.common.db import get_db_session
from app.common.models import Order, Mandate, Payment, CartItem

# Dummy payment methods for demo purposes
DUMMY_PAYMENT_METHODS = [
    {
        "id": "pm_visa_1234",
        "type": "credit_card",
        "display_name": "Visa •••• 1234",
        "last_four": "1234",
        "expiry_month": 12,
        "expiry_year": 2025,
        "cardholder_name": "John Doe",
        "brand": "Visa"
    },
    {
        "id": "pm_mastercard_5678",
        "type": "credit_card",
        "display_name": "Mastercard •••• 5678",
        "last_four": "5678",
        "expiry_month": 6,
        "expiry_year": 2026,
        "cardholder_name": "John Doe",
        "brand": "Mastercard"
    },
    {
        "id": "pm_amex_9012",
        "type": "credit_card",
        "display_name": "American Express •••• 9012",
        "last_four": "9012",
        "expiry_month": 3,
        "expiry_year": 2027,
        "cardholder_name": "John Doe",
        "brand": "American Express"
    }
]


def get_available_payment_methods(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Get available payment methods for the user.

    For demo purposes, returns hardcoded dummy payment methods.
    In production, this would retrieve payment methods from a Credentials Provider.

    Args:
        tool_context: ADK tool context providing access to session

    Returns:
        Dictionary with available payment methods
    """
    # Store payment methods in state for later use
    tool_context.state["available_payment_methods"] = DUMMY_PAYMENT_METHODS

    return {
        "payment_methods": DUMMY_PAYMENT_METHODS,
        "count": len(DUMMY_PAYMENT_METHODS),
        "message": "Available payment methods retrieved",
    }


def select_payment_method(tool_context: ToolContext, payment_method_id: str) -> Dict[str, Any]:
    """
    Select a payment method for the current transaction.

    Args:
        tool_context: ADK tool context providing access to session
        payment_method_id: ID of the payment method to select

    Returns:
        Dictionary with selected payment method details
    """
    # Get available payment methods from state or use defaults
    available_methods = tool_context.state.get(
        "available_payment_methods") or DUMMY_PAYMENT_METHODS

    # Find the payment method
    selected_method = None
    for method in available_methods:
        if method["id"] == payment_method_id:
            selected_method = method
            break

    if not selected_method:
        raise ValueError(f"Payment method {payment_method_id} not found")

    # Store selected payment method in state
    tool_context.state["selected_payment_method"] = selected_method

    return {
        "payment_method_id": payment_method_id,
        "display_name": selected_method["display_name"],
        "type": selected_method["type"],
        "brand": selected_method.get("brand", ""),
        "last_four": selected_method.get("last_four", ""),
        "message": f"Payment method {selected_method['display_name']} selected",
    }


def create_cart_mandate(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Create AP2 Cart Mandate - verifies user's intent to purchase cart contents.

    This creates a Verifiable Digital Credential (VDC) that captures the cart contents
    before payment method selection, per AP2 specification Section 4.1.1.

    Args:
        tool_context: ADK tool context providing access to session

    Returns:
        Dictionary with cart mandate details
    """
    # Get session_id from context
    session_id = tool_context._invocation_context.session.id

    with get_db_session() as db:
        # Get cart items with product relationship
        cart_items = db.query(CartItem).filter(
            CartItem.session_id == session_id
        ).all()

        if not cart_items:
            raise ValueError("Cart is empty. Cannot create cart mandate.")

        # Calculate total amount and format cart items
        total_amount = 0.0
        cart_items_data = []
        for cart_item in cart_items:
            product = cart_item.product
            price_usd_units = product.price_usd_units or 0
            price = float(price_usd_units)
            subtotal = price * cart_item.quantity
            total_amount += subtotal

            cart_items_data.append({
                "product_id": cart_item.product_id,
                "name": product.name,
                "quantity": cart_item.quantity,
                "price": price,
                "subtotal": subtotal,
            })

        # Create cart mandate
        mandate_id = f"cart_mandate_{uuid.uuid4()}"
        mandate_data = {
            "cart_items": cart_items_data,
            "total_amount": total_amount,
            "item_count": len(cart_items_data),
            "timestamp": datetime.now().isoformat(),
        }

        mandate = Mandate(
            mandate_id=mandate_id,
            mandate_type="cart",
            session_id=session_id,
            mandate_data=json.dumps(mandate_data),
            status="pending"
        )
        db.add(mandate)
        # commit() happens automatically in context manager

        # Store mandate ID in state
        tool_context.state["cart_mandate_id"] = mandate_id

        return {
            "mandate_id": mandate_id,
            "cart_items": cart_items_data,
            "total_amount": total_amount,
            "item_count": len(cart_items_data),
            "status": "pending",
            "message": "Cart mandate created successfully",
        }


def create_payment_mandate(tool_context: ToolContext, cart_mandate_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Create AP2 Payment Mandate - authorizes payment for a specific transaction.

    This creates a Verifiable Digital Credential (VDC) that links payment authorization
    to specific cart contents via Cart Mandate reference, per AP2 specification Section 4.1.3.

    Args:
        tool_context: ADK tool context providing access to session
        cart_mandate_id: Optional cart mandate ID. If not provided, retrieves from state.

    Returns:
        Dictionary with payment mandate details
    """
    # Get session_id from context
    session_id = tool_context._invocation_context.session.id

    # Get cart mandate ID from parameter or state
    if not cart_mandate_id:
        cart_mandate_id = tool_context.state.get("cart_mandate_id")
        if not cart_mandate_id:
            raise ValueError(
                "Cart mandate ID not found. Please create cart mandate first.")

    # Verify cart mandate exists
    with get_db_session() as db:
        cart_mandate = db.query(Mandate).filter(
            Mandate.mandate_id == cart_mandate_id,
            Mandate.mandate_type == "cart"
        ).first()

        if not cart_mandate:
            raise ValueError(f"Cart mandate {cart_mandate_id} not found")

        # Get selected payment method from state
        selected_payment_method = tool_context.state.get(
            "selected_payment_method")
        if not selected_payment_method:
            raise ValueError(
                "No payment method selected. Please select a payment method first.")

        # Get order summary from state (contains amount and items)
        order_summary = tool_context.state.get("pending_order_summary")
        if not order_summary:
            raise ValueError(
                "Order summary not found. Please prepare order summary first.")

        amount = order_summary.get("total_amount", 0.0)

        # Create payment mandate
        mandate_id = f"payment_mandate_{uuid.uuid4()}"
        mandate_data = {
            "payment_method_id": selected_payment_method["id"],
            "payment_method_type": selected_payment_method["type"],
            "payment_method_display_name": selected_payment_method["display_name"],
            "amount": amount,
            "cart_mandate_id": cart_mandate_id,
            "order_summary_reference": {
                "items": order_summary.get("items", []),
                "total_amount": amount,
                "item_count": order_summary.get("item_count", 0),
            },
            "timestamp": datetime.now().isoformat(),
        }

        mandate = Mandate(
            mandate_id=mandate_id,
            mandate_type="payment",
            session_id=session_id,
            mandate_data=json.dumps(mandate_data),
            status="pending"
        )
        db.add(mandate)
        # commit() happens automatically in context manager

        # Store mandate ID in state
        tool_context.state["payment_mandate_id"] = mandate_id

        return {
            "mandate_id": mandate_id,
            "payment_method_id": selected_payment_method["id"],
            "payment_method_display_name": selected_payment_method["display_name"],
            "amount": amount,
            "cart_mandate_id": cart_mandate_id,
            "status": "pending",
            "message": "Payment mandate created successfully",
        }


def process_payment(tool_context: ToolContext, order_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Process payment with AP2 compliance.

    This function processes payment BEFORE order creation. It uses the payment mandate
    created earlier and stores payment details in state for order creation.

    Args:
        tool_context: ADK tool context providing access to session
        order_id: Optional order identifier. If not provided, payment is processed
                  without order (order will be created after payment)

    Returns:
        Payment details with transaction ID
    """
    # Get session_id from context
    session_id = tool_context._invocation_context.session.id

    # Get payment mandate from state
    payment_mandate_id = tool_context.state.get("payment_mandate_id")
    if not payment_mandate_id:
        raise ValueError(
            "Payment mandate not found. Please create payment mandate first.")

    # Get selected payment method from state
    selected_payment_method = tool_context.state.get("selected_payment_method")
    if not selected_payment_method:
        raise ValueError(
            "No payment method selected. Please select a payment method first.")

    # Get order summary from state
    order_summary = tool_context.state.get("pending_order_summary")
    if not order_summary:
        raise ValueError(
            "Order summary not found. Please prepare order summary first.")

    amount = order_summary.get("total_amount", 0.0)
    payment_method_id = selected_payment_method["id"]
    payment_method_display = selected_payment_method["display_name"]

    with get_db_session() as db:
        # Verify payment mandate exists
        mandate = db.query(Mandate).filter(
            Mandate.mandate_id == payment_mandate_id
        ).first()

        if not mandate:
            raise ValueError(f"Payment mandate {payment_mandate_id} not found")

        # Create payment record
        # Note: If order_id is not provided, we store payment details in state
        # and create the Payment record when the order is created
        payment_id = str(uuid.uuid4())
        transaction_id = f"txn_{uuid.uuid4().hex[:16]}"

        # Store payment details in state (will be used to create Payment record when order is created)
        payment_data = {
            "payment_id": payment_id,
            "order_id": order_id,  # May be None
            "amount": amount,
            "payment_method": payment_method_display,
            "payment_method_id": payment_method_id,
            "status": "completed",
            "transaction_id": transaction_id,
            "payment_mandate_id": payment_mandate_id,
        }
        tool_context.state["payment_processed"] = True
        tool_context.state["payment_data"] = payment_data

        # If order_id is provided, create Payment record now
        # Otherwise, Payment record will be created when order is created
        if order_id:
            payment = Payment(
                payment_id=payment_id,
                order_id=order_id,
                amount=amount,
                payment_method=payment_method_display,
                payment_mandate_id=payment_mandate_id,
                transaction_id=transaction_id,
                status="completed"
            )
            db.add(payment)

            # Update order status
            order = db.query(Order).filter(Order.order_id == order_id).first()
            if order:
                order.status = "completed"

        # Update mandate status
        mandate.status = "approved"

        # commit() happens automatically in context manager

        return {
            "payment_id": payment_id,
            "order_id": order_id or "",
            "amount": amount,
            "payment_method": payment_method_display,
            "status": "completed",
            "transaction_id": transaction_id,
            "payment_mandate_id": payment_mandate_id,
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
