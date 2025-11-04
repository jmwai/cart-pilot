"""
SQLAlchemy ORM models for the Cart Pilot application.
All models consolidated in this single file.
"""
from __future__ import annotations

from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship, declarative_base
from pgvector.sqlalchemy import Vector
from typing import Optional
import uuid

# Base class for all models
Base = declarative_base()


# ============================================================================
# BASE MIXINS
# ============================================================================

class TimestampMixin:
    """Mixin for created_at timestamp field"""
    created_at = Column(DateTime(timezone=True),
                        server_default=func.now(), nullable=False)


# ============================================================================
# CATALOG MODELS
# ============================================================================

class CatalogItem(Base, TimestampMixin):
    """Product catalog items with pgvector embeddings for semantic search"""
    __tablename__ = 'catalog_items'

    id = Column(String(255), primary_key=True)
    name = Column(String(500), nullable=False)
    description = Column(Text)
    picture = Column(String(1000))
    product_image_url = Column(String(1000))
    price_usd_units = Column(Integer)  # Price in dollars (e.g., 1999 = $19.99)

    # pgvector embeddings for semantic search
    product_embedding = Column(Vector(1408))      # Text embedding
    product_image_embedding = Column(Vector(1408))  # Image embedding

    # Relationships
    cart_items = relationship("CartItem", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")


# ============================================================================
# CART MODELS
# ============================================================================

class CartItem(Base, TimestampMixin):
    """Shopping cart items"""
    __tablename__ = 'cart_items'

    cart_item_id = Column(String(255), primary_key=True)
    session_id = Column(String(255), nullable=False, index=True)
    product_id = Column(String(255), ForeignKey(
        'catalog_items.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    product = relationship("CatalogItem", back_populates="cart_items")


# ============================================================================
# ORDER MODELS
# ============================================================================

class Order(Base, TimestampMixin):
    """Customer orders"""
    __tablename__ = 'orders'

    order_id = Column(String(255), primary_key=True)
    session_id = Column(String(255), nullable=False, index=True)
    total_amount = Column(Float, nullable=False)
    status = Column(String(50), nullable=False, default='pending')
    shipping_address = Column(Text)

    # Relationships
    items = relationship("OrderItem", back_populates="order",
                         cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="order")
    inquiries = relationship("CustomerInquiry", back_populates="order")


class OrderItem(Base):
    """Individual items within an order"""
    __tablename__ = 'order_items'

    order_item_id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(255), ForeignKey(
        'orders.order_id'), nullable=False)
    product_id = Column(String(255), ForeignKey(
        'catalog_items.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("CatalogItem", back_populates="order_items")


# ============================================================================
# PAYMENT MODELS
# ============================================================================

class Mandate(Base, TimestampMixin):
    """AP2 mandates for cryptographic proof of user intent"""
    __tablename__ = 'mandates'

    mandate_id = Column(String(255), primary_key=True)
    mandate_type = Column(String(50), nullable=False)
    session_id = Column(String(255), nullable=False, index=True)
    mandate_data = Column(Text)  # Stores JSON data
    signature = Column(String(512))
    status = Column(String(50), nullable=False, default='pending')

    # Relationships
    payments = relationship("Payment", back_populates="mandate")


class Payment(Base, TimestampMixin):
    """Payment transactions with AP2 compliance"""
    __tablename__ = 'payments'

    payment_id = Column(String(255), primary_key=True)
    order_id = Column(String(255), ForeignKey(
        'orders.order_id'), nullable=False)
    amount = Column(Float, nullable=False)
    payment_method = Column(String(50), nullable=False)
    payment_mandate_id = Column(String(255), ForeignKey('mandates.mandate_id'))
    transaction_id = Column(String(255))
    status = Column(String(50), nullable=False)

    # Relationships
    order = relationship("Order", back_populates="payments")
    mandate = relationship("Mandate", back_populates="payments")


# ============================================================================
# CUSTOMER SERVICE MODELS
# ============================================================================

class CustomerInquiry(Base, TimestampMixin):
    """Customer support inquiries"""
    __tablename__ = 'customer_inquiries'

    inquiry_id = Column(String(255), primary_key=True)
    session_id = Column(String(255), nullable=False, index=True)
    inquiry_type = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    related_order_id = Column(String(255), ForeignKey('orders.order_id'))
    status = Column(String(50), nullable=False, default='open')

    # Relationships
    order = relationship("Order", back_populates="inquiries")
