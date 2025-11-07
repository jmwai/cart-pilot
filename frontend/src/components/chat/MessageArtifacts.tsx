/**
 * Message artifacts component for displaying products, cart, orders, etc.
 */
import { MessageWithArtifacts } from '@/types/chat';
import ProductList from '../ProductList';
import CartDisplay from '../CartDisplay';
import OrderDisplay from '../OrderDisplay';
import OrderSummaryDisplay from '../OrderSummaryDisplay';
import PaymentMethodSelection from '../PaymentMethodSelection';

interface MessageArtifactsProps {
  message: MessageWithArtifacts;
  onAddToCart: (productId: string, quantity?: number) => void;
  onUpdateQuantity: (cartItemId: string, quantity: number) => void;
  onRemoveFromCart: (cartItemId: string) => void;
  onSelectPaymentMethod: (paymentMethodId: string) => void;
}

export default function MessageArtifacts({
  message,
  onAddToCart,
  onUpdateQuantity,
  onRemoveFromCart,
  onSelectPaymentMethod,
}: MessageArtifactsProps) {
  return (
    <>
      {/* Render products if available */}
      {message.products && message.products.length > 0 && (
        <div className="w-full">
          <ProductList
            products={message.products}
            onAddToCart={onAddToCart}
            onViewDetails={(productId) => {
              // TODO: Navigate to product details page
              console.log('View details:', productId);
            }}
          />
        </div>
      )}

      {/* Render cart if available */}
      {message.cart && message.cart.length > 0 && (
        <div className="w-full">
          <CartDisplay
            items={message.cart}
            onUpdateQuantity={onUpdateQuantity}
            onRemove={onRemoveFromCart}
          />
        </div>
      )}

      {/* Render order summary if available */}
      {message.orderSummary && (
        <div className="w-full">
          <OrderSummaryDisplay orderSummary={message.orderSummary} />
        </div>
      )}

      {/* Render payment methods if available */}
      {message.paymentMethods && message.paymentMethods.length > 0 && (
        <div className="w-full">
          <PaymentMethodSelection
            paymentMethods={message.paymentMethods}
            selectedPaymentMethodId={message.selectedPaymentMethod?.id}
            onSelect={onSelectPaymentMethod}
          />
        </div>
      )}

      {/* Render order if available */}
      {message.order && (
        <div className="w-full">
          <OrderDisplay order={message.order} />
        </div>
      )}
    </>
  );
}

