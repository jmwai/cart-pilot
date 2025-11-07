/**
 * Streaming utility functions for processing A2A events
 */
import { StreamingEvent } from '@/lib/a2a-parser';
import { StreamingState } from '@/types/chat';
import { Product, CartItem, Order, OrderSummary, PaymentMethod } from '@/types';
import { extractStatusMessage } from './statusMessageUtils';

/**
 * Process a streaming event and update the streaming state
 */
export function processStreamingEvent(
  event: StreamingEvent,
  currentState: StreamingState
): { updatedState: StreamingState; statusMessage?: string } {
  const updatedState = { ...currentState };
  let statusMessage: string | undefined = undefined;

  switch (event.type) {
    case 'text':
      // Accumulate text incrementally
      const textChunk =
        typeof event.data?.text === 'string'
          ? event.data.text
          : String(event.data?.text || '');
      updatedState.text += textChunk;
      // Ensure text is always a string
      updatedState.text =
        typeof updatedState.text === 'string'
          ? updatedState.text
          : String(updatedState.text || '');
      break;

    case 'products':
      updatedState.products = event.data.products as Product[];
      break;

    case 'cart':
      updatedState.cart = event.data.items as CartItem[];
      break;

    case 'order':
      updatedState.order = event.data.order as Order;
      break;

    case 'order_summary':
      updatedState.orderSummary = event.data.orderSummary as OrderSummary;
      break;

    case 'payment_methods':
      updatedState.paymentMethods = event.data.paymentMethods as PaymentMethod[];
      break;

    case 'payment_method_selection':
      updatedState.paymentMethods = event.data.paymentMethods as PaymentMethod[];
      updatedState.selectedPaymentMethod = event.data
        .selectedPaymentMethod as PaymentMethod;
      break;

    case 'status':
      // Extract status message safely
      const extractedStatus = extractStatusMessage(event.data);
      if (extractedStatus && typeof extractedStatus === 'string') {
        statusMessage = extractedStatus;
      } else {
        statusMessage = String(extractedStatus || '');
      }
      break;

    case 'complete':
      // Finalize state - no changes needed, just mark as complete
      break;

    default:
      // Unknown event type, ignore
      break;
  }

  return { updatedState, statusMessage };
}

/**
 * Safely extract text from event data
 */
export function extractTextFromEvent(data: any): string {
  if (typeof data?.text === 'string') {
    return data.text;
  }
  return String(data?.text || '');
}

/**
 * Validate streaming state
 */
export function validateStreamingState(state: StreamingState): boolean {
  // Ensure text is always a string
  if (state.text !== undefined && typeof state.text !== 'string') {
    return false;
  }
  return true;
}

/**
 * Merge streaming state into message update params
 */
export function streamingStateToMessageParams(
  state: StreamingState
): {
  content: string;
  products?: Product[];
  cart?: CartItem[];
  order?: Order;
  orderSummary?: OrderSummary;
  paymentMethods?: PaymentMethod[];
  selectedPaymentMethod?: PaymentMethod;
} {
  return {
    content: state.text || 'I received your message.',
    products: state.products,
    cart: state.cart,
    order: state.order,
    orderSummary: state.orderSummary,
    paymentMethods: state.paymentMethods,
    selectedPaymentMethod: state.selectedPaymentMethod,
  };
}

