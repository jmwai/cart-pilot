/**
 * Message utility functions for chat operations
 */
import { v4 as uuidv4 } from 'uuid';
import { MessageWithArtifacts, StreamingState, MessageUpdateParams } from '@/types/chat';
import { Product, CartItem, Order, OrderSummary, PaymentMethod } from '@/types';

/**
 * Create a new message with artifacts
 */
export function createMessage(
  role: 'user' | 'assistant',
  content: string,
  artifacts?: {
    products?: Product[];
    cart?: CartItem[];
    order?: Order;
    orderSummary?: OrderSummary;
    imageUrl?: string;
    paymentMethods?: PaymentMethod[];
    selectedPaymentMethod?: PaymentMethod;
  }
): MessageWithArtifacts {
  return {
    id: uuidv4(),
    role,
    content,
    timestamp: new Date(),
    products: artifacts?.products,
    cart: artifacts?.cart,
    order: artifacts?.order,
    orderSummary: artifacts?.orderSummary,
    imageUrl: artifacts?.imageUrl,
    paymentMethods: artifacts?.paymentMethods,
    selectedPaymentMethod: artifacts?.selectedPaymentMethod,
  };
}

/**
 * Ensure an assistant message exists in the messages array and return its index.
 * This prevents duplicate assistant messages during streaming.
 */
export function ensureAssistantMessageIndex(
  messages: MessageWithArtifacts[],
  assistantMessageIndexRef: React.MutableRefObject<number>,
  streamingState: StreamingState
): number {
  // Check if we already have an assistant message for this request
  if (
    assistantMessageIndexRef.current >= 0 &&
    assistantMessageIndexRef.current < messages.length &&
    messages[assistantMessageIndexRef.current]?.role === 'assistant'
  ) {
    return assistantMessageIndexRef.current;
  }

  // Check if there's already an assistant message at the end
  if (messages.length > 0) {
    const lastMessage = messages[messages.length - 1];
    if (lastMessage.role === 'assistant') {
      assistantMessageIndexRef.current = messages.length - 1;
      return assistantMessageIndexRef.current;
    }
  }

  // Create new assistant message index
  const newIndex = messages.length;
  assistantMessageIndexRef.current = newIndex;
  return newIndex;
}

/**
 * Update a message with new content and artifacts
 */
export function updateMessageWithArtifacts(
  message: MessageWithArtifacts,
  updates: MessageUpdateParams
): MessageWithArtifacts {
  return {
    ...message,
    content: updates.content ?? message.content,
    products: updates.products ?? message.products,
    cart: updates.cart ?? message.cart,
    order: updates.order ?? message.order,
    orderSummary: updates.orderSummary ?? message.orderSummary,
    paymentMethods: updates.paymentMethods ?? message.paymentMethods,
    selectedPaymentMethod: updates.selectedPaymentMethod ?? message.selectedPaymentMethod,
  };
}

/**
 * Create a message from streaming state
 */
export function createMessageFromStreamingState(
  streamingState: StreamingState,
  role: 'user' | 'assistant' = 'assistant'
): MessageWithArtifacts {
  return createMessage(
    role,
    streamingState.text || 'I received your message.',
    {
      products: streamingState.products,
      cart: streamingState.cart,
      order: streamingState.order,
      orderSummary: streamingState.orderSummary,
      paymentMethods: streamingState.paymentMethods,
      selectedPaymentMethod: streamingState.selectedPaymentMethod,
    }
  );
}

/**
 * Initialize empty streaming state
 */
export function createEmptyStreamingState(): StreamingState {
  return {
    text: '',
    products: undefined,
    cart: undefined,
    order: undefined,
    orderSummary: undefined,
    paymentMethods: undefined,
    selectedPaymentMethod: undefined,
  };
}

