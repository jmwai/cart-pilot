'use client';

import { OrderSummary, OrderItem } from '@/types';

interface OrderSummaryDisplayProps {
  orderSummary: OrderSummary;
}

export default function OrderSummaryDisplay({ orderSummary }: OrderSummaryDisplayProps) {
  return (
    <div className="order-summary-display bg-white border-2 border-blue-200 rounded-lg p-4 shadow-sm">
      {/* Review Header */}
      <div className="mb-4 pb-4 border-b border-blue-100">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center flex-shrink-0">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900">Review Your Order</h3>
        </div>
        <p className="text-sm text-gray-600">
          Please review your order details below. Shipping address is from your profile.
        </p>
      </div>

      {/* Order Items - Vertical Layout with Small Thumbnails */}
      <div className="mb-4">
        <h4 className="text-sm font-semibold text-gray-700 mb-3">Order Items:</h4>
        <div className="space-y-3">
          {orderSummary.items.map((item: OrderItem, index: number) => (
            <div key={`${item.product_id}-${index}`} className="flex items-start gap-3 pb-3 border-b border-gray-100 last:border-0">
              {/* Small Thumbnail */}
              <div className="w-12 h-12 flex-shrink-0 bg-gray-100 rounded border border-gray-200 overflow-hidden">
                {item.picture ? (
                  <img 
                    src={item.picture} 
                    alt={item.name}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = 'none';
                    }}
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-gray-400 text-xs">
                    <span>No Image</span>
                  </div>
                )}
              </div>
              
              {/* Item Details */}
              <div className="flex-1 min-w-0">
                <h5 className="text-sm font-medium text-gray-900 mb-1">{item.name}</h5>
                <div className="flex items-center gap-4 text-xs text-gray-600">
                  <span>Qty: {item.quantity}</span>
                  <span>${item.price.toFixed(2)} each</span>
                  {item.subtotal !== undefined && (
                    <span className="font-medium text-gray-900">Subtotal: ${item.subtotal.toFixed(2)}</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Order Summary */}
      <div className="mb-4 pt-4 border-t border-gray-200">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-semibold text-gray-700">Total Amount:</span>
          <span className="text-lg font-bold text-gray-900">${orderSummary.total_amount.toFixed(2)}</span>
        </div>
      </div>

      {/* Shipping Address */}
      {orderSummary.shipping_address && (
        <div className="pt-4 border-t border-gray-200">
          <h4 className="text-sm font-semibold text-gray-700 mb-2">Shipping Address:</h4>
          <p className="text-sm text-gray-600 bg-gray-50 p-2 rounded border border-gray-200">
            {orderSummary.shipping_address}
          </p>
        </div>
      )}

      {/* Confirmation Prompt */}
      <div className="mt-4 pt-4 border-t border-blue-100">
        <p className="text-sm text-gray-700 font-medium">
          Please review your order above. Would you like to confirm and place this order?
        </p>
        <p className="text-xs text-gray-500 mt-1">
          Type "yes", "confirm", or "place order" to proceed, or "no" to cancel.
        </p>
      </div>
    </div>
  );
}

