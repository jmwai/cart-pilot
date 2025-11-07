/**
 * Hook for handling message streaming from A2A protocol
 */
import { useState, useCallback } from 'react';
import { shoppingAPI } from '@/lib/shopping-api';
import { parseStreamingEvent } from '@/lib/a2a-parser';
import { processStreamingEvent, streamingStateToMessageParams } from '@/lib/utils/streamingUtils';
import { createEmptyStreamingState, createMessageFromStreamingState } from '@/lib/utils/messageUtils';
import { getContextualLoadingMessage } from '@/lib/utils/statusMessageUtils';
import { StreamingState } from '@/types/chat';
import { updateMessageWithArtifacts } from '@/lib/utils/messageUtils';
import { MessageWithArtifacts } from '@/types/chat';

interface UseStreamingMessageParams {
  messages: MessageWithArtifacts[];
  setMessages: React.Dispatch<React.SetStateAction<MessageWithArtifacts[]>>;
  ensureAssistantMessage: (messagesArray: MessageWithArtifacts[], streamingState: StreamingState) => number;
  resetAssistantMessageIndex: () => void;
}

export function useStreamingMessage({
  messages,
  setMessages,
  ensureAssistantMessage,
  resetAssistantMessageIndex,
}: UseStreamingMessageParams) {
  const [isLoading, setIsLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState<string>('');

  const sendMessage = useCallback(async (
    text?: string,
    image?: File | null
  ) => {
    if (isLoading) return;

    const userMessage = text?.trim() || '';
    const imageToSend = image || undefined;

    // Set initial loading message
    setLoadingMessage(
      imageToSend
        ? 'Searching for similar products...'
        : getContextualLoadingMessage(userMessage)
    );
    setIsLoading(true);

    // Reset assistant message index for new request
    resetAssistantMessageIndex();

    // Initialize streaming state
    let streamingState = createEmptyStreamingState();

    try {
      // Add timeout to prevent infinite loading
      const streamTimeout = setTimeout(() => {
        console.warn('Stream timeout - forcing completion');
        setIsLoading(false);
        resetAssistantMessageIndex();
      }, 30000); // 30 second timeout

      try {
        for await (const event of shoppingAPI.sendMessageStream(
          userMessage || undefined,
          imageToSend || undefined
        )) {
          clearTimeout(streamTimeout); // Clear timeout on successful event

          const parsedEvent = parseStreamingEvent(event);
          if (!parsedEvent) continue;

          try {
            // Process streaming event and update state
            const { updatedState, statusMessage } = processStreamingEvent(
              parsedEvent,
              streamingState
            );
            streamingState = updatedState;

            // Update loading message if status message provided
            if (statusMessage) {
              setLoadingMessage(statusMessage);
            }

            // Update messages based on event type
            switch (parsedEvent.type) {
              case 'text':
              case 'products':
              case 'cart':
              case 'order':
              case 'order_summary':
              case 'payment_methods':
              case 'payment_method_selection':
                // Update or create assistant message in real-time
                setMessages(prev => {
                  const updated = [...prev];
                  const index = ensureAssistantMessage(updated, streamingState);
                  const messageParams = streamingStateToMessageParams(streamingState);

                  if (index < updated.length && updated[index]) {
                    // Update existing message
                    updated[index] = updateMessageWithArtifacts(updated[index], messageParams);
                  } else {
                    // Create new message
                    const newMessage = createMessageFromStreamingState(streamingState);
                    updated.push(newMessage);
                  }
                  return updated;
                });
                break;

              case 'status':
                // Status message already handled above
                break;

              case 'complete':
                // Finalize message
                setIsLoading(false);
                setMessages(prev => {
                  const updated = [...prev];
                  const index = ensureAssistantMessage(updated, streamingState);
                  const messageParams = streamingStateToMessageParams(streamingState);

                  if (index < updated.length && updated[index]) {
                    updated[index] = updateMessageWithArtifacts(updated[index], {
                      ...messageParams,
                      content: messageParams.content || 'I received your message.',
                    });
                  } else {
                    const finalMessage = createMessageFromStreamingState(streamingState);
                    finalMessage.content = finalMessage.content || 'I received your message.';
                    updated.push(finalMessage);
                  }
                  return updated;
                });
                resetAssistantMessageIndex();
                break;
            }
          } catch (eventError) {
            // Handle individual event processing errors
            console.error('Error processing streaming event:', eventError);
            // Continue processing other events
          }
        }

        // Clear timeout when stream completes normally
        clearTimeout(streamTimeout);
      } catch (streamError) {
        // Handle stream errors
        console.error('Error in stream:', streamError);
        clearTimeout(streamTimeout);
        setIsLoading(false);
        resetAssistantMessageIndex();

        // Save partial results if available
        if (
          streamingState.text ||
          streamingState.products ||
          streamingState.cart ||
          streamingState.order ||
          streamingState.orderSummary ||
          streamingState.paymentMethods
        ) {
          const errorMessage = createMessageFromStreamingState(streamingState);
          setMessages(prev => [
            ...prev,
            {
              ...errorMessage,
              content: errorMessage.content || 'I received your message.',
            },
          ]);
        } else {
          setMessages(prev => [
            ...prev,
            {
              id: `error-${Date.now()}`,
              role: 'assistant',
              content: 'Sorry, I encountered an error. Please try again.',
              timestamp: new Date(),
            },
          ]);
        }
      }

      // Ensure loading is stopped even if no complete event received
      setIsLoading(false);
      resetAssistantMessageIndex();
    } catch (error) {
      console.error('Error in streaming:', error);
      setIsLoading(false);
      resetAssistantMessageIndex();

      // Save partial results if available
      if (
        streamingState.text ||
        streamingState.products ||
        streamingState.cart ||
        streamingState.order ||
        streamingState.orderSummary ||
        streamingState.paymentMethods
      ) {
        const errorMessage = createMessageFromStreamingState(streamingState);
        setMessages(prev => [
          ...prev,
          {
            ...errorMessage,
            content: errorMessage.content || 'I received your message.',
          },
        ]);
      } else {
        setMessages(prev => [
          ...prev,
          {
            id: `error-${Date.now()}`,
            role: 'assistant',
            content: 'Sorry, I encountered an error. Please try again.',
            timestamp: new Date(),
          },
        ]);
      }
    }
  }, [isLoading, messages, setMessages, ensureAssistantMessage, resetAssistantMessageIndex]);

  return {
    sendMessage,
    isLoading,
    loadingMessage,
    setLoadingMessage,
  };
}

