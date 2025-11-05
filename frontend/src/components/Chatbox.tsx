'use client';

import { useState, useRef, useEffect } from 'react';
import { ChatMessage, Product, CartItem, Order } from '@/types';
import { shoppingAPI } from '@/lib/shopping-api';
import { parseA2AResponse, parseStreamingEvent } from '@/lib/a2a-parser';
import ProductList from './ProductList';
import CartDisplay from './CartDisplay';
import OrderDisplay from './OrderDisplay';
import { v4 as uuidv4 } from 'uuid';

interface MessageWithArtifacts extends ChatMessage {
  products?: Product[];
  cart?: CartItem[];
  order?: Order;
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
  const fileInputRef = useRef<HTMLInputElement>(null);
  // Ref to track the current assistant message index for streaming updates
  const assistantMessageIndexRef = useRef<number>(-1);
  
  // Image upload state
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  
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
    cart?: CartItem[],
    order?: Order,
    imageUrl?: string
  ) => {
    setMessages(prev => [...prev, {
      id: uuidv4(),
      role,
      content,
      timestamp: new Date(),
      products,
      cart,
      order,
      imageUrl
    }]);
  };

  // Helper function to ensure assistant message exists and return its index
  // This function ensures only ONE assistant message is created per request
  const ensureAssistantMessage = (
    messages: MessageWithArtifacts[],
    content: string,
    products?: Product[],
    cart?: CartItem[],
    order?: Order
  ): number => {
    // Check if we already have an assistant message for this request
    if (assistantMessageIndexRef.current >= 0 && 
        assistantMessageIndexRef.current < messages.length &&
        messages[assistantMessageIndexRef.current]?.role === 'assistant') {
      return assistantMessageIndexRef.current;
    }
    
    // Check if there's already an assistant message at the end (from a previous event in same request)
    // This handles race conditions where multiple events arrive before ref is set
    if (messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      if (lastMessage.role === 'assistant') {
        // Reuse the last assistant message
        assistantMessageIndexRef.current = messages.length - 1;
        return assistantMessageIndexRef.current;
      }
    }
    
    // Create new assistant message index
    // Set ref immediately to prevent other events from creating duplicates
    const newIndex = messages.length;
    assistantMessageIndexRef.current = newIndex;
    return newIndex;
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Allow sending if there's text OR an image selected
    if ((!input.trim() && !selectedImage) || isLoading || !isInitialized) return;

    const userMessage = input.trim();
    const imageToSend = selectedImage;
    
    // Clear inputs
    setInput('');
    setSelectedImage(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    
    // Create image URL for display (only after sending, per requirement)
    let imageUrl: string | undefined = undefined;
    if (imageToSend) {
      imageUrl = URL.createObjectURL(imageToSend);
    }
    
    // Add user message with image if present
    addMessage('user', userMessage || (imageToSend ? 'Image search' : ''), undefined, undefined, undefined, imageUrl);
    setLoadingMessage(imageToSend ? 'Searching for similar products...' : getContextualLoadingMessage(userMessage));
    setIsLoading(true);
    
    // Reset assistant message index for new request
    assistantMessageIndexRef.current = -1;
    
    // Initialize streaming message state
    let streamingText = '';
    let streamingProducts: Product[] | undefined = undefined;
    let streamingCart: CartItem[] | undefined = undefined;
    let streamingOrder: Order | undefined = undefined;

    // Helper function to safely extract status message
    const extractStatusMessage = (data: any): string => {
      if (!data) return '';
      if (typeof data === 'string') {
        // Make sure it's not [object Object]
        return data !== '[object Object]' ? data : '';
      }
      if (data && typeof data === 'object') {
        // Try to extract message from object
        if (data.message !== undefined) {
          if (typeof data.message === 'string') return data.message;
          if (typeof data.message === 'object') {
            // If message is an object, try to extract text from it
            const msgObj = data.message;
            const extracted = msgObj.text || 
                            msgObj.value || 
                            msgObj.content ||
                            (msgObj.parts && Array.isArray(msgObj.parts) 
                              ? msgObj.parts
                                  .map((p: any) => p.text || p.value || '')
                                  .filter((t: string) => t)
                                  .join(' ')
                              : '');
            // Return extracted string or empty, never [object Object]
            return extracted && extracted !== '[object Object]' ? extracted : '';
          }
          // If String() conversion would give [object Object], return empty
          const str = String(data.message);
          return str !== '[object Object]' ? str : '';
        }
        if (data.state) {
          const stateStr = String(data.state);
          return stateStr !== '[object Object]' ? stateStr : '';
        }
        if (data.text) {
          const textStr = String(data.text);
          return textStr !== '[object Object]' ? textStr : '';
        }
        // If it's just an object with no clear message, return empty string
        return '';
      }
      const str = String(data || '');
      return str !== '[object Object]' ? str : '';
    };

    try {
      // Use streaming method - pass text and/or image
      for await (const event of shoppingAPI.sendMessageStream(userMessage || undefined, imageToSend || undefined)) {
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
              
              // Update or create assistant message in real-time using functional setState
              setMessages(prev => {
                const updated = [...prev];
                const index = ensureAssistantMessage(updated, safeText, streamingProducts, streamingCart, streamingOrder);
                
                if (index < updated.length && updated[index]) {
                  // Update existing message
                  updated[index] = {
                    ...updated[index],
                    content: safeText,
                    products: streamingProducts,
                    cart: streamingCart,
                    order: streamingOrder
                  };
                } else {
                  // Create new message (shouldn't happen due to ensureAssistantMessage, but safety check)
                  updated.push({
                    id: uuidv4(),
                    role: 'assistant',
                    content: safeText,
                    timestamp: new Date(),
                    products: streamingProducts,
                    cart: streamingCart,
                    order: streamingOrder
                  });
                  assistantMessageIndexRef.current = updated.length - 1;
                }
                return updated;
              });
              break;
              
            case 'products':
              // Update products immediately
              streamingProducts = parsedEvent.data.products;
              
              setMessages(prev => {
                const updated = [...prev];
                const index = ensureAssistantMessage(updated, streamingText, streamingProducts, streamingCart, streamingOrder);
                
                if (index < updated.length && updated[index]) {
                  updated[index] = {
                    ...updated[index],
                    products: streamingProducts,
                    cart: streamingCart,
                    order: streamingOrder
                  };
                } else {
                  updated.push({
                    id: uuidv4(),
                    role: 'assistant',
                    content: streamingText,
                    timestamp: new Date(),
                    products: streamingProducts,
                    cart: streamingCart,
                    order: streamingOrder
                  });
                  assistantMessageIndexRef.current = updated.length - 1;
                }
                return updated;
              });
              break;
              
            case 'cart':
              // Update cart immediately
              streamingCart = parsedEvent.data.items;
              
              setMessages(prev => {
                const updated = [...prev];
                const index = ensureAssistantMessage(updated, streamingText, streamingProducts, streamingCart, streamingOrder);
                
                if (index < updated.length && updated[index]) {
                  updated[index] = {
                    ...updated[index],
                    cart: streamingCart,
                    products: streamingProducts,
                    order: streamingOrder
                  };
                } else {
                  updated.push({
                    id: uuidv4(),
                    role: 'assistant',
                    content: streamingText,
                    timestamp: new Date(),
                    products: streamingProducts,
                    cart: streamingCart,
                    order: streamingOrder
                  });
                  assistantMessageIndexRef.current = updated.length - 1;
                }
                return updated;
              });
              break;
              
            case 'order':
              // Update order immediately
              streamingOrder = parsedEvent.data.order;
              
              setMessages(prev => {
                const updated = [...prev];
                const index = ensureAssistantMessage(updated, streamingText, streamingProducts, streamingCart, streamingOrder);
                
                if (index < updated.length && updated[index]) {
                  updated[index] = {
                    ...updated[index],
                    order: streamingOrder,
                    products: streamingProducts,
                    cart: streamingCart
                  };
                } else {
                  updated.push({
                    id: uuidv4(),
                    role: 'assistant',
                    content: streamingText,
                    timestamp: new Date(),
                    products: streamingProducts,
                    cart: streamingCart,
                    order: streamingOrder
                  });
                  assistantMessageIndexRef.current = updated.length - 1;
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
                const finalText = typeof streamingText === 'string' ? streamingText : String(streamingText || '');
                const index = ensureAssistantMessage(updated, finalText, streamingProducts, streamingCart, streamingOrder);
                
                if (index < updated.length && updated[index]) {
                  updated[index] = {
                    ...updated[index],
                    content: finalText || 'I received your message.',
                    products: streamingProducts,
                    cart: streamingCart,
                    order: streamingOrder
                  };
                } else {
                  updated.push({
                    id: uuidv4(),
                    role: 'assistant',
                    content: finalText || 'I received your message.',
                    timestamp: new Date(),
                    products: streamingProducts,
                    cart: streamingCart,
                    order: streamingOrder
                  });
                  assistantMessageIndexRef.current = updated.length - 1;
                }
                return updated;
              });
              // Reset index after completion
              assistantMessageIndexRef.current = -1;
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
      // Reset index after stream completes
      assistantMessageIndexRef.current = -1;
      
    } catch (error) {
      console.error('Error in streaming:', error);
      // Save partial results if available
      if (streamingText || streamingProducts || streamingCart || streamingOrder) {
        addMessage(
          'assistant',
          streamingText || 'I received your message.',
          streamingProducts,
          streamingCart,
          streamingOrder
        );
      } else {
        addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
      }
      setIsLoading(false);
      // Reset index after error
      assistantMessageIndexRef.current = -1;
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

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      alert('Please select a valid image file (JPEG, PNG, or WebP)');
      e.target.value = ''; // Reset input
      return;
    }

    // Validate file size (max 10MB)
    const maxSize = 10 * 1024 * 1024; // 10MB in bytes
    if (file.size > maxSize) {
      alert('Image size must be less than 10MB');
      e.target.value = ''; // Reset input
      return;
    }

    // Store selected image
    setSelectedImage(file);
    // Clear text input when image is selected (separate queries)
    setInput('');
  };

  const handlePlaceOrder = () => {
    // Send message to place order
    const userMessage = 'Place the order';
    setInput('');
    addMessage('user', userMessage);
    setLoadingMessage('Processing your order...');
    setIsLoading(true);
    
    // Reset assistant message index for new request
    assistantMessageIndexRef.current = -1;
    
    // Initialize streaming message state
    let streamingText = '';
    let streamingProducts: Product[] | undefined = undefined;
    let streamingCart: CartItem[] | undefined = undefined;
    let streamingOrder: Order | undefined = undefined;

    // Helper function to safely extract status message
    const extractStatusMessage = (data: any): string => {
      if (!data) return '';
      if (typeof data === 'string') {
        return data !== '[object Object]' ? data : '';
      }
      if (data && typeof data === 'object') {
        if (data.message !== undefined) {
          if (typeof data.message === 'string') return data.message;
          if (typeof data.message === 'object') {
            const msgObj = data.message;
            const extracted = msgObj.text || 
                            msgObj.value || 
                            msgObj.content ||
                            (msgObj.parts && Array.isArray(msgObj.parts) 
                              ? msgObj.parts
                                  .map((p: any) => p.text || p.value || '')
                                  .filter((t: string) => t)
                                  .join(' ')
                              : '');
            return extracted && extracted !== '[object Object]' ? extracted : '';
          }
          const str = String(data.message);
          return str !== '[object Object]' ? str : '';
        }
        if (data.state) {
          const stateStr = String(data.state);
          return stateStr !== '[object Object]' ? stateStr : '';
        }
        if (data.text) {
          const textStr = String(data.text);
          return textStr !== '[object Object]' ? textStr : '';
        }
        return '';
      }
      const str = String(data || '');
      return str !== '[object Object]' ? str : '';
    };

    // Use the same streaming logic as handleSend
    (async () => {
      try {
        for await (const event of shoppingAPI.sendMessageStream(userMessage)) {
          const parsedEvent = parseStreamingEvent(event);
          
          if (!parsedEvent) continue;
          
          try {
            switch (parsedEvent.type) {
              case 'text':
                const textChunk = typeof parsedEvent.data?.text === 'string' 
                  ? parsedEvent.data.text 
                  : String(parsedEvent.data?.text || '');
                streamingText += textChunk;
                
                const safeText = typeof streamingText === 'string' ? streamingText : String(streamingText || '');
                
                setMessages(prev => {
                  const updated = [...prev];
                  const index = ensureAssistantMessage(updated, safeText, streamingProducts, streamingCart, streamingOrder);
                  
                  if (index < updated.length && updated[index]) {
                    updated[index] = {
                      ...updated[index],
                      content: safeText,
                      products: streamingProducts,
                      cart: streamingCart,
                      order: streamingOrder
                    };
                  } else {
                    updated.push({
                      id: uuidv4(),
                      role: 'assistant',
                      content: safeText,
                      timestamp: new Date(),
                      products: streamingProducts,
                      cart: streamingCart,
                      order: streamingOrder
                    });
                    assistantMessageIndexRef.current = updated.length - 1;
                  }
                  return updated;
                });
                break;
                
              case 'products':
                streamingProducts = parsedEvent.data.products;
                
                setMessages(prev => {
                  const updated = [...prev];
                  const index = ensureAssistantMessage(updated, streamingText, streamingProducts, streamingCart, streamingOrder);
                  
                  if (index < updated.length && updated[index]) {
                    updated[index] = {
                      ...updated[index],
                      products: streamingProducts,
                      cart: streamingCart,
                      order: streamingOrder
                    };
                  } else {
                    updated.push({
                      id: uuidv4(),
                      role: 'assistant',
                      content: streamingText,
                      timestamp: new Date(),
                      products: streamingProducts,
                      cart: streamingCart,
                      order: streamingOrder
                    });
                    assistantMessageIndexRef.current = updated.length - 1;
                  }
                  return updated;
                });
                break;
                
              case 'cart':
                streamingCart = parsedEvent.data.items;
                
                setMessages(prev => {
                  const updated = [...prev];
                  const index = ensureAssistantMessage(updated, streamingText, streamingProducts, streamingCart, streamingOrder);
                  
                  if (index < updated.length && updated[index]) {
                    updated[index] = {
                      ...updated[index],
                      cart: streamingCart,
                      products: streamingProducts,
                      order: streamingOrder
                    };
                  } else {
                    updated.push({
                      id: uuidv4(),
                      role: 'assistant',
                      content: streamingText,
                      timestamp: new Date(),
                      products: streamingProducts,
                      cart: streamingCart,
                      order: streamingOrder
                    });
                    assistantMessageIndexRef.current = updated.length - 1;
                  }
                  return updated;
                });
                break;
                
              case 'order':
                streamingOrder = parsedEvent.data.order;
                
                setMessages(prev => {
                  const updated = [...prev];
                  const index = ensureAssistantMessage(updated, streamingText, streamingProducts, streamingCart, streamingOrder);
                  
                  if (index < updated.length && updated[index]) {
                    updated[index] = {
                      ...updated[index],
                      order: streamingOrder,
                      products: streamingProducts,
                      cart: streamingCart
                    };
                  } else {
                    updated.push({
                      id: uuidv4(),
                      role: 'assistant',
                      content: streamingText,
                      timestamp: new Date(),
                      products: streamingProducts,
                      cart: streamingCart,
                      order: streamingOrder
                    });
                    assistantMessageIndexRef.current = updated.length - 1;
                  }
                  return updated;
                });
                break;
                
              case 'status':
                const statusMsg = extractStatusMessage(parsedEvent.data);
                if (statusMsg && typeof statusMsg === 'string') {
                  setLoadingMessage(statusMsg);
                } else {
                  setLoadingMessage(String(statusMsg || ''));
                }
                break;
                
              case 'complete':
                setIsLoading(false);
                setMessages(prev => {
                  const updated = [...prev];
                  const finalText = typeof streamingText === 'string' ? streamingText : String(streamingText || '');
                  const index = ensureAssistantMessage(updated, finalText, streamingProducts, streamingCart, streamingOrder);
                  
                  if (index < updated.length && updated[index]) {
                    updated[index] = {
                      ...updated[index],
                      content: finalText || 'I received your message.',
                      products: streamingProducts,
                      cart: streamingCart,
                      order: streamingOrder
                    };
                  } else {
                    updated.push({
                      id: uuidv4(),
                      role: 'assistant',
                      content: finalText || 'I received your message.',
                      timestamp: new Date(),
                      products: streamingProducts,
                      cart: streamingCart,
                      order: streamingOrder
                    });
                    assistantMessageIndexRef.current = updated.length - 1;
                  }
                  return updated;
                });
                assistantMessageIndexRef.current = -1;
                break;
            }
          } catch (eventError) {
            console.error('Error processing event:', eventError);
          }
        }
      } catch (error) {
        console.error('Error in streaming:', error);
        if (streamingText || streamingProducts || streamingCart || streamingOrder) {
          addMessage(
            'assistant',
            streamingText || 'I received your message.',
            streamingProducts,
            streamingCart,
            streamingOrder
          );
        } else {
          addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
        }
        setIsLoading(false);
        assistantMessageIndexRef.current = -1;
      }
    })();
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
    if (lowerMessage.includes('checkout') || lowerMessage.includes('place order') || lowerMessage.includes('buy') || lowerMessage.includes('yes') && lowerMessage.includes('checkout')) {
      return 'Creating your order...';
    }
    if (lowerMessage.includes('order')) {
      return 'Processing your order...';
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
    
    // Reset assistant message index for new request
    assistantMessageIndexRef.current = -1;
    
    // Initialize streaming message state
    let streamingText = '';
    let streamingProducts: Product[] | undefined = undefined;
    let streamingCart: CartItem[] | undefined = undefined;
    let streamingOrder: Order | undefined = undefined;

    // Helper function to safely extract status message
    const extractStatusMessage = (data: any): string => {
      if (!data) return '';
      if (typeof data === 'string') {
        // Make sure it's not [object Object]
        return data !== '[object Object]' ? data : '';
      }
      if (data && typeof data === 'object') {
        // Try to extract message from object
        if (data.message !== undefined) {
          if (typeof data.message === 'string') return data.message;
          if (typeof data.message === 'object') {
            // If message is an object, try to extract text from it
            const msgObj = data.message;
            const extracted = msgObj.text || 
                            msgObj.value || 
                            msgObj.content ||
                            (msgObj.parts && Array.isArray(msgObj.parts) 
                              ? msgObj.parts
                                  .map((p: any) => p.text || p.value || '')
                                  .filter((t: string) => t)
                                  .join(' ')
                              : '');
            // Return extracted string or empty, never [object Object]
            return extracted && extracted !== '[object Object]' ? extracted : '';
          }
          // If String() conversion would give [object Object], return empty
          const str = String(data.message);
          return str !== '[object Object]' ? str : '';
        }
        if (data.state) {
          const stateStr = String(data.state);
          return stateStr !== '[object Object]' ? stateStr : '';
        }
        if (data.text) {
          const textStr = String(data.text);
          return textStr !== '[object Object]' ? textStr : '';
        }
        // If it's just an object with no clear message, return empty string
        return '';
      }
      const str = String(data || '');
      return str !== '[object Object]' ? str : '';
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
                const index = ensureAssistantMessage(updated, promptSafeText, streamingProducts, streamingCart, streamingOrder);
                
                if (index < updated.length && updated[index]) {
                  updated[index] = {
                    ...updated[index],
                    content: promptSafeText,
                    products: streamingProducts,
                    cart: streamingCart,
                    order: streamingOrder
                  };
                } else {
                  updated.push({
                    id: uuidv4(),
                    role: 'assistant',
                    content: promptSafeText,
                    timestamp: new Date(),
                    products: streamingProducts,
                    cart: streamingCart,
                    order: streamingOrder
                  });
                  assistantMessageIndexRef.current = updated.length - 1;
                }
                return updated;
              });
              break;
              
            case 'products':
              streamingProducts = parsedEvent.data.products;
              setMessages(prev => {
                const updated = [...prev];
                const index = ensureAssistantMessage(updated, streamingText, streamingProducts, streamingCart, streamingOrder);
                
                if (index < updated.length && updated[index]) {
                  updated[index] = {
                    ...updated[index],
                    products: streamingProducts,
                    cart: streamingCart,
                    order: streamingOrder
                  };
                } else {
                  updated.push({
                    id: uuidv4(),
                    role: 'assistant',
                    content: streamingText,
                    timestamp: new Date(),
                    products: streamingProducts,
                    cart: streamingCart,
                    order: streamingOrder
                  });
                  assistantMessageIndexRef.current = updated.length - 1;
                }
                return updated;
              });
              break;
              
            case 'cart':
              streamingCart = parsedEvent.data.items;
              setMessages(prev => {
                const updated = [...prev];
                const index = ensureAssistantMessage(updated, streamingText, streamingProducts, streamingCart, streamingOrder);
                
                if (index < updated.length && updated[index]) {
                  updated[index] = {
                    ...updated[index],
                    cart: streamingCart,
                    products: streamingProducts,
                    order: streamingOrder
                  };
                } else {
                  updated.push({
                    id: uuidv4(),
                    role: 'assistant',
                    content: streamingText,
                    timestamp: new Date(),
                    products: streamingProducts,
                    cart: streamingCart,
                    order: streamingOrder
                  });
                  assistantMessageIndexRef.current = updated.length - 1;
                }
                return updated;
              });
              break;
              
            case 'order':
              streamingOrder = parsedEvent.data.order;
              setMessages(prev => {
                const updated = [...prev];
                const index = ensureAssistantMessage(updated, streamingText, streamingProducts, streamingCart, streamingOrder);
                
                if (index < updated.length && updated[index]) {
                  updated[index] = {
                    ...updated[index],
                    order: streamingOrder,
                    products: streamingProducts,
                    cart: streamingCart
                  };
                } else {
                  updated.push({
                    id: uuidv4(),
                    role: 'assistant',
                    content: streamingText,
                    timestamp: new Date(),
                    products: streamingProducts,
                    cart: streamingCart,
                    order: streamingOrder
                  });
                  assistantMessageIndexRef.current = updated.length - 1;
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
              
            case 'complete':
              setIsLoading(false);
              setMessages(prev => {
                const updated = [...prev];
                const promptFinalText = typeof streamingText === 'string' ? streamingText : String(streamingText || '');
                const index = ensureAssistantMessage(updated, promptFinalText, streamingProducts, streamingCart, streamingOrder);
                
                if (index < updated.length && updated[index]) {
                  updated[index] = {
                    ...updated[index],
                    content: promptFinalText || 'I received your message.',
                    products: streamingProducts,
                    cart: streamingCart,
                    order: streamingOrder
                  };
                } else {
                  updated.push({
                    id: uuidv4(),
                    role: 'assistant',
                    content: promptFinalText || 'I received your message.',
                    timestamp: new Date(),
                    products: streamingProducts,
                    cart: streamingCart,
                    order: streamingOrder
                  });
                  assistantMessageIndexRef.current = updated.length - 1;
                }
                return updated;
              });
              // Reset index after completion
              assistantMessageIndexRef.current = -1;
              break;
          }
        } catch (eventError) {
          console.error('Error processing streaming event:', eventError);
        }
      }
      
      setIsLoading(false);
      setInput(''); // Clear input after sending
      // Reset index after stream completes
      assistantMessageIndexRef.current = -1;
      
    } catch (error) {
      console.error('Error in streaming:', error);
      if (streamingText || streamingProducts || streamingCart || streamingOrder) {
        addMessage(
          'assistant',
          streamingText || 'I received your message.',
          streamingProducts,
          streamingCart,
          streamingOrder
        );
      } else {
      addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
      }
      setIsLoading(false);
      setInput(''); // Clear input after error
      // Reset index after error
      assistantMessageIndexRef.current = -1;
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
            {messages.map((msg) => (
              <div key={msg.id} className="space-y-2">
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
                  {/* Display image if present */}
                  {msg.imageUrl && (
                    <div className="mb-2">
                      <img 
                        src={msg.imageUrl} 
                        alt="Uploaded" 
                        className="max-w-full h-auto rounded-lg max-h-64 object-contain"
                      />
                    </div>
                  )}
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
                    <ProductList
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
                      onPlaceOrder={handlePlaceOrder}
                    />
                  </div>
                )}
                
                {/* Render order if available */}
                {msg.order && (
                  <div className="w-full">
                    <OrderDisplay order={msg.order} />
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
                        // Make sure it's not [object Object]
                        return loadingMessage !== '[object Object]' ? loadingMessage : '';
                      }
                      const msgObj = loadingMessage as any;
                      if (msgObj && typeof msgObj === 'object') {
                        // If it's an object, try to extract a string
                        const extracted = msgObj.message || 
                                        msgObj.text || 
                                        msgObj.value ||
                                        msgObj.content ||
                                        msgObj.state || 
                                        '';
                        const str = typeof extracted === 'string' ? extracted : String(extracted || '');
                        return str !== '[object Object]' ? str : '';
                      }
                      const str = String(loadingMessage || '');
                      return str !== '[object Object]' ? str : '';
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
              {/* Hidden file input */}
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                onChange={handleImageSelect}
                className="hidden"
              />
              
              {/* Camera icon button */}
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={isLoading || !isInitialized}
                className="px-3 py-3 text-gray-500 hover:text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
                aria-label="Upload image"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </button>
              
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={selectedImage ? "Add optional text..." : "Type your message..."}
                className="flex-1 px-4 py-3 text-base border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={isLoading || !isInitialized}
              />
              <button
                type="submit"
                disabled={isLoading || (!input.trim() && !selectedImage) || !isInitialized}
                className="px-5 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </div>
            {/* Show selected image preview */}
            {selectedImage && (
              <div className="mt-2 text-sm text-gray-600">
                Selected: {selectedImage.name} ({(selectedImage.size / 1024 / 1024).toFixed(2)} MB)
              </div>
            )}
          </form>
        </div>
      )}
    </>
  );
}
