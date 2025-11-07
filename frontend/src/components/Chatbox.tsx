'use client';

import { useState, useRef, useEffect } from 'react';
import { shoppingAPI } from '@/lib/shopping-api';
import { parseStreamingEvent } from '@/lib/a2a-parser';
import { useMobileDetection } from '@/hooks/useMobileDetection';
import { useChatInitialization } from '@/hooks/useChatInitialization';
import { useImageUpload } from '@/hooks/useImageUpload';
import { useChatMessages } from '@/hooks/useChatMessages';
import { useStreamingMessage } from '@/hooks/useStreamingMessage';
import ChatToggleButton from './chat/ChatToggleButton';
import ChatHeader from './chat/ChatHeader';
import ChatMessages from './chat/ChatMessages';
import ChatInput from './chat/ChatInput';

// Shoe discovery prompts
const DISCOVERY_PROMPTS = [
  'Find running shoes',
  'Show me casual sneakers',
  'I need basketball shoes',
  'Show me dress shoes',
  'Find hiking boots',
  'Show me athletic shoes',
];

export default function Chatbox() {
  // Hooks
  const { isMobile, mounted } = useMobileDetection();
  const { isInitialized } = useChatInitialization();
  const {
    selectedImage,
    imageUrl,
    handleImageSelect,
    clearImage,
    createImageUrl,
    fileInputRef,
  } = useImageUpload();
  const {
    messages,
    setMessages,
    messagesEndRef,
    addMessage,
    ensureAssistantMessage,
    resetAssistantMessageIndex,
  } = useChatMessages();
  const { sendMessage, isLoading, loadingMessage } = useStreamingMessage({
    messages,
    setMessages,
    ensureAssistantMessage,
    resetAssistantMessageIndex,
  });

  // Local state
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  // Initialize welcome message
  useEffect(() => {
    if (isInitialized && messages.length === 0) {
      addMessage('assistant', "Hello! I'm your shopping assistant. How can I help you today?");
    }
  }, [isInitialized, messages.length, addMessage]);

  // Auto-focus input when chat opens
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  // Set initial open state based on mobile detection
  useEffect(() => {
    if (mounted) {
      setIsOpen(!isMobile);
    }
  }, [mounted, isMobile]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();

    // Allow sending if there's text OR an image selected
    if ((!input.trim() && !selectedImage) || isLoading || !isInitialized) return;

    const userMessage = input.trim();
    const imageToSend = selectedImage;

    // Create image URL for display
    const displayImageUrl = imageToSend ? createImageUrl(imageToSend) : undefined;

    // Add user message with image if present
    addMessage('user', userMessage || (imageToSend ? 'Image search' : ''), {
      imageUrl: displayImageUrl,
    });

    // Clear inputs
    setInput('');
    clearImage();

    // Send message via streaming hook
    await sendMessage(userMessage || undefined, imageToSend || undefined);
  };

  const handlePromptClick = async (prompt: string) => {
    if (isLoading || !isInitialized) return;

    // Add user message
    addMessage('user', prompt);

    // Send message via streaming hook
    await sendMessage(prompt);
  };

  const handleAddToCart = (productId: string, quantity: number = 1) => {
    // Find product from the most recent message with products
    const productMessage = [...messages].reverse().find((msg) => msg.products?.length);
    const product = productMessage?.products?.find((p) => p.id === productId);
    if (product) {
      // Always include quantity explicitly, default to 1
      setInput(`Add ${quantity} ${product.name} to my cart`);
    }
  };

  const handleUpdateQuantity = async (cartItemId: string, quantity: number) => {
    // Send message to update cart quantity
    setInput(`Update quantity of cart item ${cartItemId} to ${quantity}`);
  };

  const handleRemoveFromCart = (cartItemId: string) => {
    // Send message to remove item
    setInput(`Remove cart item ${cartItemId}`);
  };

  const handleSelectPaymentMethod = async (paymentMethodId: string) => {
    if (isLoading || !isInitialized) return;

    const userMessage = `Select payment method ${paymentMethodId}`;

    // Add user message
    addMessage('user', userMessage);

    // Send message via streaming hook
    await sendMessage(userMessage);
  };

  // Don't render until mounted to prevent hydration mismatch
  if (!mounted) {
    return null;
  }

  return (
    <>
      {/* Floating Chat Button - Only on mobile/tablet */}
      {isMobile && !isOpen && <ChatToggleButton onClick={() => setIsOpen(true)} />}

      {/* Backdrop for mobile/tablet */}
      {isMobile && isOpen && (
        <div
          className="chatbox-backdrop fixed inset-0 bg-black bg-opacity-50 z-[45]"
          onClick={() => setIsOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Chat Window - Sticky right panel */}
      {isOpen && (
        <div className={`chatbox-panel ${isMobile ? 'chatbox-slide-in' : ''}`}>
          {/* Header */}
          <ChatHeader onClose={() => setIsOpen(false)} showCloseButton={isMobile} />

          {/* Messages */}
          <ChatMessages
            messages={messages}
            isLoading={isLoading}
            loadingMessage={loadingMessage}
            discoveryPrompts={DISCOVERY_PROMPTS}
            onPromptClick={handlePromptClick}
            onAddToCart={handleAddToCart}
            onUpdateQuantity={handleUpdateQuantity}
            onRemoveFromCart={handleRemoveFromCart}
            onSelectPaymentMethod={handleSelectPaymentMethod}
            messagesEndRef={messagesEndRef}
          />

          {/* Input Form */}
          <ChatInput
            input={input}
            setInput={setInput}
            selectedImage={selectedImage}
            onImageSelect={handleImageSelect}
            onSubmit={handleSend}
            isLoading={isLoading}
            isInitialized={isInitialized}
            inputRef={inputRef}
            fileInputRef={fileInputRef}
          />
        </div>
      )}
    </>
  );
}
