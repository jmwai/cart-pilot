'use client';

import { PaymentMethod } from '@/types';

interface PaymentMethodSelectionProps {
  paymentMethods: PaymentMethod[];
  onSelect: (paymentMethodId: string) => void;
  selectedPaymentMethodId?: string;
}

export default function PaymentMethodSelection({ 
  paymentMethods, 
  onSelect, 
  selectedPaymentMethodId 
}: PaymentMethodSelectionProps) {
  const getCardIcon = (brand?: string) => {
    switch (brand?.toLowerCase()) {
      case 'visa':
        return (
          <div className="w-8 h-8 bg-blue-600 rounded flex items-center justify-center text-white text-xs font-bold">
            VISA
          </div>
        );
      case 'mastercard':
        return (
          <div className="w-8 h-8 bg-red-600 rounded flex items-center justify-center text-white text-xs font-bold">
            MC
          </div>
        );
      case 'american express':
      case 'amex':
        return (
          <div className="w-8 h-8 bg-blue-500 rounded flex items-center justify-center text-white text-xs font-bold">
            AMEX
          </div>
        );
      default:
        return (
          <div className="w-8 h-8 bg-gray-300 rounded flex items-center justify-center text-gray-600 text-xs">
            CARD
          </div>
        );
    }
  };

  const formatExpiry = (month?: number, year?: number) => {
    if (!month || !year) return '';
    return `${String(month).padStart(2, '0')}/${String(year).slice(-2)}`;
  };

  return (
    <div className="payment-method-selection bg-white border-2 border-purple-200 rounded-lg p-4 shadow-sm">
      {/* Header */}
      <div className="mb-4 pb-4 border-b border-purple-100">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center flex-shrink-0">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900">Select Payment Method</h3>
        </div>
        <p className="text-sm text-gray-600">
          Please choose a payment method to complete your order.
        </p>
      </div>

      {/* Payment Methods List */}
      <div className="space-y-3">
        {paymentMethods.map((method) => {
          const isSelected = selectedPaymentMethodId === method.id;
          return (
            <button
              key={method.id}
              onClick={() => onSelect(method.id)}
              className={`w-full p-4 border-2 rounded-lg transition-all ${
                isSelected
                  ? 'border-purple-500 bg-purple-50'
                  : 'border-gray-200 bg-white hover:border-purple-300 hover:bg-purple-50'
              }`}
            >
              <div className="flex items-center gap-4">
                {/* Card Icon */}
                {getCardIcon(method.brand)}
                
                {/* Card Details */}
                <div className="flex-1 text-left">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-semibold text-gray-900">{method.display_name}</span>
                    {isSelected && (
                      <span className="text-xs bg-purple-500 text-white px-2 py-0.5 rounded">
                        Selected
                      </span>
                    )}
                  </div>
                  {method.cardholder_name && (
                    <p className="text-sm text-gray-600">{method.cardholder_name}</p>
                  )}
                  {(method.expiry_month || method.expiry_year) && (
                    <p className="text-xs text-gray-500">
                      Expires: {formatExpiry(method.expiry_month, method.expiry_year)}
                    </p>
                  )}
                </div>
                
                {/* Select Indicator */}
                {!isSelected && (
                  <div className="w-6 h-6 border-2 border-gray-300 rounded-full flex-shrink-0"></div>
                )}
                {isSelected && (
                  <div className="w-6 h-6 bg-purple-500 rounded-full flex items-center justify-center flex-shrink-0">
                    <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                )}
              </div>
            </button>
          );
        })}
      </div>

      {/* Instructions */}
      <div className="mt-4 pt-4 border-t border-purple-100">
        <p className="text-xs text-gray-500">
          Click on a payment method above to select it, or type the payment method name in the chat.
        </p>
      </div>
    </div>
  );
}

