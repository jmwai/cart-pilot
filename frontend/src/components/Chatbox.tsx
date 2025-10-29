'use client';

import { useState, useRef, useEffect } from 'react';
import { ChatMessage, Product, CartItem } from '@/types';
import { shoppingAPI } from '@/lib/shopping-api';
import { parseA2AResponse, parseStreamingEvent } from '@/lib/a2a-parser';
import ProductGrid from './ProductGrid';
import CartDisplay from './CartDisplay';

interface MessageWithArtifacts extends ChatMessage {
  products?: Product[];
  cart?: CartItem[];
}

export default function Chatbox() {
  // Track if component has mounted (client-side only)
  const [mounted, setMounted] = useState(false);
  
  // On desktop, always open. On mobile/tablet, use toggle state
  // Initialize as false to match server render, then update on mount
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<MessageWithArtifacts[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  
  // Check if we're on mobile/tablet
  const [isMobile, setIsMobile] = useState(false);
  
  // Handle mounting and mobile detection
  useEffect(() => {
    // Mark as mounted
    setMounted(true);
    
    const checkMobile = () => {
      const mobile = window.innerWidth < 1024;
      setIsMobile(mobile);
      // On desktop, always keep open. On mobile, start closed
      if (mobile) {
        setIsOpen(false);
      } else {
        setIsOpen(true);
      }
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  useEffect(() => {
    // Initialize on mount
    const init = async () => {
      try {
        await shoppingAPI.initialize();
        setIsInitialized(true);
        addMessage('assistant', 'Hello! I\'m your shopping assistant. How can I help you today?');
      } catch (error) {
        console.error('Failed to initialize:', error);
        addMessage('assistant', 'Failed to connect to the shopping assistant. Please check your connection.');
      }
    };
    init();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  const addMessage = (
    role: 'user' | 'assistant', 
    content: string, 
    products?: Product[], 
    cart?: CartItem[]
  ) => {
    setMessages(prev => [...prev, {
      role,
      content,
      timestamp: new Date(),
      products,
      cart
    }]);
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!input.trim() || isLoading || !isInitialized) return;

    const userMessage = input.trim();
    setInput('');
    addMessage('user', userMessage);
    setLoadingMessage(getContextualLoadingMessage(userMessage));
    setIsLoading(true);
    
    // Initialize streaming message state
    let streamingText = '';
    let streamingProducts: Product[] | undefined = undefined;
    let streamingCart: CartItem[] | undefined = undefined;
    let assistantMessageIndex = -1;

    // Helper function to safely extract status message
    const extractStatusMessage = (data: any): string => {
      if (!data) return '';
      if (typeof data === 'string') return data;
      if (data && typeof data === 'object') {
        // Try to extract message from object
        if (data.message !== undefined) {
          if (typeof data.message === 'string') return data.message;
          if (typeof data.message === 'object') {
            // If message is an object, try to extract text from it
            return data.message.text || data.message.value || String(data.message || '');
          }
          return String(data.message);
        }
        if (data.state) return String(data.state);
        if (data.text) return String(data.text);
        // If it's just an object with no clear message, return empty string
        return '';
      }
      return String(data || '');
    };

    try {
      // Use streaming method
      for await (const event of shoppingAPI.sendMessageStream(userMessage)) {
        const parsedEvent = parseStreamingEvent(event);
        
        if (!parsedEvent) continue;
        
        try {
          switch (parsedEvent.type) {
            case 'text':
              // Accumulate text incrementally
              // Ensure text is a string
              const textChunk = typeof parsedEvent.data?.text === 'string' 
                ? parsedEvent.data.text 
                : String(parsedEvent.data?.text || '');
              streamingText += textChunk;
              
              // Ensure streamingText is always a string before setting state
              const safeText = typeof streamingText === 'string' ? streamingText : String(streamingText || '');
              
              // Update or create assistant message in real-time
              setMessages(prev => {
                const updated = [...prev];
                if (assistantMessageIndex >= 0 && updated[assistantMessageIndex]) {
                  // Update existing message
                  updated[assistantMessageIndex] = {
                    ...updated[assistantMessageIndex],
                    content: safeText,
                    products: streamingProducts,
                    cart: streamingCart
                  };
                } else {
                  // Create new assistant message
                  assistantMessageIndex = updated.length;
                  updated.push({
                    role: 'assistant',
                    content: safeText,
                    timestamp: new Date(),
                    products: streamingProducts,
                    cart: streamingCart
                  });
                }
                return updated;
              });
              break;
              
            case 'products':
              // Update products immediately
              streamingProducts = parsedEvent.data.products;
              
              setMessages(prev => {
                const updated = [...prev];
                if (assistantMessageIndex >= 0 && updated[assistantMessageIndex]) {
                  updated[assistantMessageIndex] = {
                    ...updated[assistantMessageIndex],
                    products: streamingProducts,
                    cart: streamingCart
                  };
                } else {
                  // Create message if it doesn't exist yet
                  assistantMessageIndex = updated.length;
                  updated.push({
                    role: 'assistant',
                    content: streamingText,
                    timestamp: new Date(),
                    products: streamingProducts,
                    cart: streamingCart
                  });
                }
                return updated;
              });
              break;
              
            case 'cart':
              // Update cart immediately
              streamingCart = parsedEvent.data.items;
              
              setMessages(prev => {
                const updated = [...prev];
                if (assistantMessageIndex >= 0 && updated[assistantMessageIndex]) {
                  updated[assistantMessageIndex] = {
                    ...updated[assistantMessageIndex],
                    cart: streamingCart,
                    products: streamingProducts
                  };
                } else {
                  // Create message if it doesn't exist yet
                  assistantMessageIndex = updated.length;
                  updated.push({
                    role: 'assistant',
                    content: streamingText,
                    timestamp: new Date(),
                    products: streamingProducts,
                    cart: streamingCart
                  });
                }
                return updated;
              });
              break;
              
            case 'status':
              // Update loading message if provided - ensure it's a string
              const statusMsg2 = extractStatusMessage(parsedEvent.data);
              if (statusMsg2 && typeof statusMsg2 === 'string') {
                setLoadingMessage(statusMsg2);
              } else {
                // Fallback: ensure we never set an object
                setLoadingMessage(String(statusMsg2 || ''));
              }
              break;
              
            case 'complete':
              // Finalize message - ensure final state is set
              setIsLoading(false);
              setMessages(prev => {
                const updated = [...prev];
                if (assistantMessageIndex >= 0 && updated[assistantMessageIndex]) {
                  // Ensure final state is correct
                  const finalText = typeof streamingText === 'string' ? streamingText : String(streamingText || '');
                  updated[assistantMessageIndex] = {
                    ...updated[assistantMessageIndex],
                    content: finalText || 'I received your message.',
                    products: streamingProducts,
                    cart: streamingCart
                  };
                } else {
                  // Create final message if somehow missing
                  const finalText = typeof streamingText === 'string' ? streamingText : String(streamingText || '');
                  updated.push({
                    role: 'assistant',
                    content: finalText || 'I received your message.',
                    timestamp: new Date(),
                    products: streamingProducts,
                    cart: streamingCart
                  });
                }
                return updated;
              });
              break;
          }
        } catch (eventError) {
          // Handle individual event processing errors
          console.error('Error processing streaming event:', eventError);
          // Continue processing other events
        }
      }
      
      // Ensure loading is stopped even if no complete event received
      setIsLoading(false);
      
    } catch (error) {
      console.error('Error in streaming:', error);
      // Save partial results if available
      if (streamingText || streamingProducts || streamingCart) {
        addMessage(
          'assistant',
          streamingText || 'I received your message.',
          streamingProducts,
          streamingCart
        );
      } else {
        addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
      }
      setIsLoading(false);
    }
  };

  const handleAddToCart = (productId: string, quantity: number = 1) => {
    // Find product from the most recent message with products
    const productMessage = [...messages].reverse().find(msg => msg.products?.length);
    const product = productMessage?.products?.find(p => p.id === productId);
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

  const handleViewDetails = (productId: string) => {
    // TODO: Navigate to product details page
    console.log('View details:', productId);
  };

  // Generate contextual loading message based on user query
  const getContextualLoadingMessage = (userMessage: string): string => {
    const lowerMessage = userMessage.toLowerCase();
    
    // Shopping cart actions
    if (lowerMessage.includes('add') && lowerMessage.includes('cart')) {
      return 'Adding to cart...';
    }
    if (lowerMessage.includes('remove') || lowerMessage.includes('delete')) {
      return 'Removing from cart...';
    }
    if (lowerMessage.includes('update') && lowerMessage.includes('quantity')) {
      return 'Updating cart...';
    }
    if (lowerMessage.includes('cart') || lowerMessage.includes('basket')) {
      return 'Loading your cart...';
    }
    
    // Search/Discovery actions
    if (lowerMessage.includes('find') || lowerMessage.includes('search') || lowerMessage.includes('show') || lowerMessage.includes('looking')) {
      if (lowerMessage.includes('running') || lowerMessage.includes('jogging')) {
        return 'Finding running shoes...';
      }
      if (lowerMessage.includes('casual') || lowerMessage.includes('sneaker')) {
        return 'Searching for casual shoes...';
      }
      if (lowerMessage.includes('basketball') || lowerMessage.includes('basket')) {
        return 'Finding basketball shoes...';
      }
      if (lowerMessage.includes('dress') || lowerMessage.includes('formal')) {
        return 'Searching for dress shoes...';
      }
      if (lowerMessage.includes('hiking') || lowerMessage.includes('boot')) {
        return 'Finding hiking boots...';
      }
      if (lowerMessage.includes('athletic') || lowerMessage.includes('sport')) {
        return 'Searching for athletic shoes...';
      }
      return 'Searching for shoes...';
    }
    
    // Checkout/Payment actions
    if (lowerMessage.includes('checkout') || lowerMessage.includes('place order') || lowerMessage.includes('buy')) {
      return 'Preparing checkout...';
    }
    if (lowerMessage.includes('pay') || lowerMessage.includes('payment')) {
      return 'Processing payment...';
    }
    
    // Default
    return 'Thinking...';
  };

  const handlePromptClick = async (prompt: string) => {
    if (isLoading || !isInitialized) return;
    
    // Set input and send immediately using streaming
    setInput(prompt);
    
    // Add user message
    addMessage('user', prompt);
    setLoadingMessage(getContextualLoadingMessage(prompt));
    setIsLoading(true);
    
    // Initialize streaming message state
    let streamingText = '';
    let streamingProducts: Product[] | undefined = undefined;
    let streamingCart: CartItem[] | undefined = undefined;
    let assistantMessageIndex = -1;

    // Helper function to safely extract status message
    const extractStatusMessage = (data: any): string => {
      if (!data) return '';
      if (typeof data === 'string') return data;
      if (data && typeof data === 'object') {
        // Try to extract message from object
        if (data.message !== undefined) {
          if (typeof data.message === 'string') return data.message;
          if (typeof data.message === 'object') {
            // If message is an object, try to extract text from it
            return data.message.text || data.message.value || String(data.message || '');
          }
          return String(data.message);
        }
        if (data.state) return String(data.state);
        if (data.text) return String(data.text);
        // If it's just an object with no clear message, return empty string
        return '';
      }
      return String(data || '');
    };

    try {
      // Use streaming method (same as handleSend)
      for await (const event of shoppingAPI.sendMessageStream(prompt)) {
        const parsedEvent = parseStreamingEvent(event);
        
        if (!parsedEvent) continue;
        
        try {
          switch (parsedEvent.type) {
            case 'text':
              // Ensure text is always a string
              const promptTextChunk = typeof parsedEvent.data?.text === 'string' 
                ? parsedEvent.data.text 
                : String(parsedEvent.data?.text || '');
              streamingText += promptTextChunk;
              
              // Ensure streamingText is always a string before setting state
              const promptSafeText = typeof streamingText === 'string' ? streamingText : String(streamingText || '');
              
              setMessages(prev => {
                const updated = [...prev];
                if (assistantMessageIndex >= 0 && updated[assistantMessageIndex]) {
                  updated[assistantMessageIndex] = {
                    ...updated[assistantMessageIndex],
                    content: promptSafeText,
                    products: streamingProducts,
                    cart: streamingCart
                  };
                } else {
                  assistantMessageIndex = updated.length;
                  updated.push({
                    role: 'assistant',
                    content: promptSafeText,
                    timestamp: new Date(),
                    products: streamingProducts,
                    cart: streamingCart
                  });
                }
                return updated;
              });
              break;
              
            case 'products':
              streamingProducts = parsedEvent.data.products;
              setMessages(prev => {
                const updated = [...prev];
                if (assistantMessageIndex >= 0 && updated[assistantMessageIndex]) {
                  updated[assistantMessageIndex] = {
                    ...updated[assistantMessageIndex],
                    products: streamingProducts,
                    cart: streamingCart
                  };
                } else {
                  assistantMessageIndex = updated.length;
                  updated.push({
                    role: 'assistant',
                    content: streamingText,
                    timestamp: new Date(),
                    products: streamingProducts,
                    cart: streamingCart
                  });
                }
                return updated;
              });
              break;
              
            case 'cart':
              streamingCart = parsedEvent.data.items;
              setMessages(prev => {
                const updated = [...prev];
                if (assistantMessageIndex >= 0 && updated[assistantMessageIndex]) {
                  updated[assistantMessageIndex] = {
                    ...updated[assistantMessageIndex],
                    cart: streamingCart,
                    products: streamingProducts
                  };
                } else {
                  assistantMessageIndex = updated.length;
                  updated.push({
                    role: 'assistant',
                    content: streamingText,
                    timestamp: new Date(),
                    products: streamingProducts,
                    cart: streamingCart
                  });
                }
                return updated;
              });
              break;
              
            case 'status':
              // Update loading message if provided - ensure it's a string
              const statusMsg = extractStatusMessage(parsedEvent.data);
              if (statusMsg && typeof statusMsg === 'string') {
                setLoadingMessage(statusMsg);
              } else {
                // Fallback: ensure we never set an object
                setLoadingMessage(String(statusMsg || ''));
              }
              break;
              setMessages(prev => {
                const updated = [...prev];
                if (assistantMessageIndex >= 0 && updated[assistantMessageIndex]) {
                  const promptFinalText = typeof streamingText === 'string' ? streamingText : String(streamingText || '');
                  updated[assistantMessageIndex] = {
                    ...updated[assistantMessageIndex],
                    content: promptFinalText || 'I received your message.',
                    products: streamingProducts,
                    cart: streamingCart
                  };
                } else {
                  const promptFinalText = typeof streamingText === 'string' ? streamingText : String(streamingText || '');
                  updated.push({
                    role: 'assistant',
                    content: promptFinalText || 'I received your message.',
                    timestamp: new Date(),
                    products: streamingProducts,
                    cart: streamingCart
                  });
                }
                return updated;
              });
              break;
          }
        } catch (eventError) {
          console.error('Error processing streaming event:', eventError);
        }
      }
      
      setIsLoading(false);
      setInput(''); // Clear input after sending
      
    } catch (error) {
      console.error('Error in streaming:', error);
      if (streamingText || streamingProducts || streamingCart) {
        addMessage(
          'assistant',
          streamingText || 'I received your message.',
          streamingProducts,
          streamingCart
        );
      } else {
      addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
      }
      setIsLoading(false);
      setInput(''); // Clear input after error
    }
  };

  // Shoe discovery prompts
  const discoveryPrompts = [
    'Find running shoes',
    'Show me casual sneakers',
    'I need basketball shoes',
    'Show me dress shoes',
    'Find hiking boots',
    'Show me athletic shoes',
  ];

  // Don't render until mounted to prevent hydration mismatch
  if (!mounted) {
    return null;
  }

  return (
    <>
      {/* Floating Chat Button - Only on mobile/tablet */}
      {isMobile && !isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 w-14 h-14 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg flex items-center justify-center transition-all hover:scale-110 z-50"
          aria-label="Open chat"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        </button>
      )}

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
          <div className="bg-blue-600 text-white px-4 py-4 flex items-center justify-between border-b border-blue-700 h-16 flex-shrink-0">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
                </svg>
              </div>
              <span className="font-semibold">Shopping Assistant</span>
            </div>
            {isMobile && (
            <button
              onClick={() => setIsOpen(false)}
              className="hover:bg-blue-700 rounded p-1 transition-colors"
              aria-label="Close chat"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            )}
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50 custom-scrollbar">
            {messages.map((msg, idx) => (
              <div key={idx} className="space-y-2">
                {/* Message bubble */}
              <div
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] px-4 py-2 rounded-lg ${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white text-gray-800 border border-gray-200'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">
                    {typeof msg.content === 'string' ? msg.content : String(msg.content || '')}
                  </p>
                  <p className="text-xs mt-1 opacity-70">
                    {msg.timestamp.toLocaleTimeString()}
                  </p>
                </div>
                </div>
                
                {/* Render products if available */}
                {msg.products && msg.products.length > 0 && (
                  <div className="w-full">
                    <ProductGrid
                      products={msg.products}
                      onAddToCart={handleAddToCart}
                      onViewDetails={handleViewDetails}
                    />
                  </div>
                )}
                
                {/* Render cart if available */}
                {msg.cart && msg.cart.length > 0 && (
                  <div className="w-full">
                    <CartDisplay
                      items={msg.cart}
                      onUpdateQuantity={handleUpdateQuantity}
                      onRemove={handleRemoveFromCart}
                    />
                  </div>
                )}
              </div>
            ))}
            
            {/* Show discovery prompts when there are no messages or only welcome message */}
            {messages.length <= 1 && !isLoading && (
              <div className="space-y-3">
                <p className="text-sm text-gray-600 font-medium">Try asking:</p>
                <div className="flex flex-wrap gap-2">
                  {discoveryPrompts.map((prompt, idx) => (
                    <button
                      key={idx}
                      onClick={() => handlePromptClick(prompt)}
                      className="px-3 py-2 text-sm bg-white border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-blue-300 transition-colors text-gray-700"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            )}
            
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-white text-gray-800 px-4 py-3 rounded-lg border border-gray-200 flex items-center gap-2">
                  {/* Typing animation */}
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full typing-dot"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full typing-dot"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full typing-dot"></div>
                  </div>
                  <p className="text-sm">
                    {(() => {
                      // Extra defensive check to ensure we never render an object
                      if (typeof loadingMessage === 'string') {
                        return loadingMessage;
                      }
                      const msgObj = loadingMessage as any;
                      if (msgObj && typeof msgObj === 'object') {
                        // If it's an object, try to extract a string
                        const extracted = msgObj.message || msgObj.text || msgObj.state || '';
                        return typeof extracted === 'string' ? extracted : String(extracted || '');
                      }
                      return String(loadingMessage || '');
                    })()}
                  </p>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Form */}
          <form onSubmit={handleSend} className="p-4 border-t border-gray-200 bg-white flex-shrink-0">
            <div className="flex gap-2">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type your message..."
                className="flex-1 px-4 py-3 text-base border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={isLoading || !isInitialized}
              />
              <button
                type="submit"
                disabled={isLoading || !input.trim() || !isInitialized}
                className="px-5 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </div>
          </form>
        </div>
      )}
    </>
  );
}
