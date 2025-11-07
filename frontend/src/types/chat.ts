/**
 * Chat-specific types and interfaces
 */
import { ChatMessage, Product, CartItem, Order, OrderSummary, PaymentMethod } from '@/types';

/**
 * Extended chat message with artifacts (products, cart, orders, etc.)
 */
export interface MessageWithArtifacts extends ChatMessage {
  products?: Product[];
  cart?: CartItem[];
  order?: Order;
  orderSummary?: OrderSummary;
  paymentMethods?: PaymentMethod[];
  selectedPaymentMethod?: PaymentMethod;
}

/**
 * Streaming state for message updates
 */
export interface StreamingState {
  text: string;
  products?: Product[];
  cart?: CartItem[];
  order?: Order;
  orderSummary?: OrderSummary;
  paymentMethods?: PaymentMethod[];
  selectedPaymentMethod?: PaymentMethod;
}

/**
 * Message update parameters
 */
export interface MessageUpdateParams {
  content?: string;
  products?: Product[];
  cart?: CartItem[];
  order?: Order;
  orderSummary?: OrderSummary;
  paymentMethods?: PaymentMethod[];
  selectedPaymentMethod?: PaymentMethod;
}

