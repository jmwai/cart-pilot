'use client';

import { CartItem } from '@/types';
import { useState } from 'react';

interface CartDisplayProps {
  items: CartItem[];
  onUpdateQuantity?: (cartItemId: string, quantity: number) => void;
  onRemove?: (cartItemId: string) => void;
}

export default function CartDisplay({ items, onUpdateQuantity, onRemove }: CartDisplayProps) {
  const [updating, setUpdating] = useState<string | null>(null);
  
  if (items.length === 0) {
    return (
      <div className="cart-empty">
        <p className="text-gray-500 text-sm">Your cart is empty</p>
      </div>
    );
  }
  
  const total = items.reduce((sum, item) => sum + item.subtotal, 0);
  
  const handleQuantityChange = async (cartItemId: string, newQuantity: number) => {
    if (newQuantity < 1) {
      if (onRemove) {
        onRemove(cartItemId);
      }
      return;
    }
    
    setUpdating(cartItemId);
    try {
      if (onUpdateQuantity) {
        await onUpdateQuantity(cartItemId, newQuantity);
      }
    } finally {
      setUpdating(null);
    }
  };
  
  return (
    <div className="cart-display">
      <div className="cart-header">
        <h3 className="cart-title">Shopping Cart ({items.length} {items.length === 1 ? 'item' : 'items'})</h3>
      </div>
      
      <div className="cart-items">
        {items.map((item) => (
          <div key={item.cart_item_id} className="cart-item">
            <div className="cart-item-image-container">
              {item.picture ? (
                <img 
                  src={item.picture} 
                  alt={item.name}
                  className="cart-item-image"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = 'none';
                  }}
                />
              ) : (
                <div className="cart-item-image-placeholder">
                  <span>No Image</span>
                </div>
              )}
            </div>
            
            <div className="cart-item-details">
              <h4 className="cart-item-name">{item.name}</h4>
              <div className="cart-item-info">
                <span className="cart-item-price">${item.price.toFixed(2)}</span>
                <span className="cart-item-quantity-label">Qty:</span>
                <div className="cart-item-quantity-controls">
                  <button
                    className="quantity-btn"
                    onClick={() => handleQuantityChange(item.cart_item_id, item.quantity - 1)}
                    disabled={updating === item.cart_item_id}
                  >
                    −
                  </button>
                  <span className="quantity-value">{item.quantity}</span>
                  <button
                    className="quantity-btn"
                    onClick={() => handleQuantityChange(item.cart_item_id, item.quantity + 1)}
                    disabled={updating === item.cart_item_id}
                  >
                    +
                  </button>
                </div>
              </div>
              <div className="cart-item-subtotal">
                Subtotal: <strong>${item.subtotal.toFixed(2)}</strong>
              </div>
            </div>
            
            {onRemove && (
              <button
                className="cart-item-remove"
                onClick={() => onRemove(item.cart_item_id)}
                aria-label="Remove item"
              >
                ×
              </button>
            )}
          </div>
        ))}
      </div>
      
      <div className="cart-footer">
        <div className="cart-total">
          <span className="cart-total-label">Total:</span>
          <span className="cart-total-amount">${total.toFixed(2)}</span>
        </div>
      </div>
    </div>
  );
}

