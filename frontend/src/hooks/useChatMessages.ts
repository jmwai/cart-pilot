/**
 * Hook for managing chat messages state
 */
import { useState, useRef, useEffect, useCallback } from 'react';
import { MessageWithArtifacts } from '@/types/chat';
import { Product, CartItem, Order, OrderSummary, PaymentMethod } from '@/types';
import { createMessage, ensureAssistantMessageIndex, updateMessageWithArtifacts } from '@/lib/utils/messageUtils';
import { StreamingState } from '@/types/chat';

export function useChatMessages() {
  const [messages, setMessages] = useState<MessageWithArtifacts[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const assistantMessageIndexRef = useRef<number>(-1);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const addMessage = useCallback((
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
  ) => {
    const message = createMessage(role, content, artifacts);
    setMessages(prev => [...prev, message]);
  }, []);

  const updateMessage = useCallback((
    index: number,
    updates: {
      content?: string;
      products?: Product[];
      cart?: CartItem[];
      order?: Order;
      orderSummary?: OrderSummary;
      paymentMethods?: PaymentMethod[];
      selectedPaymentMethod?: PaymentMethod;
    }
  ) => {
    setMessages(prev => {
      const updated = [...prev];
      if (index >= 0 && index < updated.length) {
        updated[index] = updateMessageWithArtifacts(updated[index], updates);
      }
      return updated;
    });
  }, []);

  const ensureAssistantMessage = useCallback((
    messagesArray: MessageWithArtifacts[],
    streamingState: StreamingState
  ): number => {
    return ensureAssistantMessageIndex(messagesArray, assistantMessageIndexRef, streamingState);
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    assistantMessageIndexRef.current = -1;
  }, []);

  const resetAssistantMessageIndex = useCallback(() => {
    assistantMessageIndexRef.current = -1;
  }, []);

  return {
    messages,
    setMessages,
    messagesEndRef: messagesEndRef as React.RefObject<HTMLDivElement | null>,
    assistantMessageIndexRef,
    addMessage,
    updateMessage,
    ensureAssistantMessage,
    clearMessages,
    resetAssistantMessageIndex,
  };
}

