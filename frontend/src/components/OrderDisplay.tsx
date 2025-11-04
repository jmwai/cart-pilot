'use client';

import { Order } from '@/types';

interface OrderDisplayProps {
  order: Order;
}

export default function OrderDisplay({ order }: OrderDisplayProps) {
  const formatDate = (dateString?: string) => {
    if (!dateString) return '';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateString;
    }
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'cancelled':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  return (
    <div className="order-display bg-white border-2 border-green-200 rounded-lg p-4 shadow-sm">
      {/* Success Header */}
      <div className="mb-4 pb-4 border-b border-green-100">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900">Order Confirmed!</h3>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-medium text-gray-700">Order ID:</span>
          <span className="text-sm font-mono font-semibold text-gray-900 bg-gray-50 px-2 py-1 rounded">
            {order.order_id}
          </span>
          <span className={`text-xs font-medium px-2 py-1 rounded border ${getStatusBadgeColor(order.status)}`}>
            {order.status.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Order Items - Vertical Layout with Small Thumbnails */}
      <div className="mb-4">
        <h4 className="text-sm font-semibold text-gray-700 mb-3">Order Items:</h4>
        <div className="space-y-3">
          {order.items.map((item, index) => (
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
          <span className="text-lg font-bold text-gray-900">${order.total_amount.toFixed(2)}</span>
        </div>
        {order.created_at && (
          <div className="text-xs text-gray-500">
            Order Date: {formatDate(order.created_at)}
          </div>
        )}
      </div>

      {/* Shipping Address */}
      {order.shipping_address && (
        <div className="pt-4 border-t border-gray-200">
          <h4 className="text-sm font-semibold text-gray-700 mb-2">Shipping Address:</h4>
          <p className="text-sm text-gray-600 bg-gray-50 p-2 rounded border border-gray-200">
            {order.shipping_address}
          </p>
        </div>
      )}
    </div>
  );
}

