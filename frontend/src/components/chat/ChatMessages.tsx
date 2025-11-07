/**
 * Chat messages component for displaying the messages list
 */
import { RefObject } from 'react';
import { MessageWithArtifacts } from '@/types/chat';
import MessageBubble from './MessageBubble';
import MessageArtifacts from './MessageArtifacts';
import LoadingIndicator from './LoadingIndicator';
import DiscoveryPrompts from './DiscoveryPrompts';

interface ChatMessagesProps {
  messages: MessageWithArtifacts[];
  isLoading: boolean;
  loadingMessage: string;
  discoveryPrompts: string[];
  onPromptClick: (prompt: string) => void;
  onAddToCart: (productId: string, quantity?: number) => void;
  onUpdateQuantity: (cartItemId: string, quantity: number) => void;
  onRemoveFromCart: (cartItemId: string) => void;
  onSelectPaymentMethod: (paymentMethodId: string) => void;
  messagesEndRef: RefObject<HTMLDivElement | null>;
}

export default function ChatMessages({
  messages,
  isLoading,
  loadingMessage,
  discoveryPrompts,
  onPromptClick,
  onAddToCart,
  onUpdateQuantity,
  onRemoveFromCart,
  onSelectPaymentMethod,
  messagesEndRef,
}: ChatMessagesProps) {
  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50 custom-scrollbar">
      {messages.map((msg) => (
        <div key={msg.id} className="space-y-2">
          {/* Message bubble */}
          <MessageBubble message={msg} />

          {/* Message artifacts */}
          <MessageArtifacts
            message={msg}
            onAddToCart={onAddToCart}
            onUpdateQuantity={onUpdateQuantity}
            onRemoveFromCart={onRemoveFromCart}
            onSelectPaymentMethod={onSelectPaymentMethod}
          />
        </div>
      ))}

      {/* Show discovery prompts when there are no messages or only welcome message */}
      {messages.length <= 1 && (
        <DiscoveryPrompts
          prompts={discoveryPrompts}
          onPromptClick={onPromptClick}
          isLoading={isLoading}
        />
      )}

      {/* Loading indicator */}
      {isLoading && <LoadingIndicator message={loadingMessage} />}

      <div ref={messagesEndRef} />
    </div>
  );
}

