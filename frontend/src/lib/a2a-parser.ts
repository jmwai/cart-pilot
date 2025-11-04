import { Product, ProductListData, CartItem, CartData, Order, OrderData, OrderItem } from '@/types';

/**
 * Streaming event from A2A protocol
 */
export interface StreamingEvent {
  type: 'text' | 'products' | 'cart' | 'order' | 'status' | 'complete';
  data: any;
  isIncremental: boolean;
}

/**
 * Parsed A2A response containing text, products, cart data, and order data
 */
export interface ParsedA2AResponse {
  text: string;
  products: Product[];
  cart?: CartItem[];
  order?: Order;
}

/**
 * Helper function to format product data
 */
function formatProduct(product: any): Product {
  return {
    id: product.id || '',
    name: product.name || '',
    description: product.description || '',
    picture: product.picture,
    product_image_url: product.product_image_url,
    image_url: product.image_url || product.product_image_url || product.picture || '',
    price: product.price || 0,
    price_usd_units: product.price_usd_units,
    distance: product.distance || 0,
  };
}

/**
 * Helper function to format cart item data
 */
function formatCartItem(item: any): CartItem {
  return {
    cart_item_id: item.cart_item_id || '',
    product_id: item.product_id || '',
    name: item.name || '',
    picture: item.picture || '',
    quantity: item.quantity || 0,
    price: item.price || 0,
    subtotal: item.subtotal || 0,
  };
}

/**
 * Helper function to format order item data
 */
function formatOrderItem(item: any): OrderItem {
  return {
    product_id: item.product_id || '',
    name: item.name || '',
    quantity: item.quantity || 0,
    price: item.price || 0,
    picture: item.picture || '',
    subtotal: item.subtotal || (item.price || 0) * (item.quantity || 0),
  };
}

/**
 * Helper function to format order data
 */
function formatOrder(order: any): Order {
  return {
    order_id: order.order_id || '',
    status: order.status || '',
    items: (order.items || []).map(formatOrderItem),
    total_amount: order.total_amount || 0,
    shipping_address: order.shipping_address,
    created_at: order.created_at,
  };
}

/**
 * Parse A2A response to extract text, product data, and cart data
 * @param response - The A2A response object (JSON-RPC format)
 * @returns Object containing text message, products array, and optional cart array
 */
export function parseA2AResponse(response: any): ParsedA2AResponse {
  let text = '';
  const products: Product[] = [];
  let cart: CartItem[] | undefined = undefined;
  let order: Order | undefined = undefined;
  
  // Handle JSON-RPC response structure: response.result.artifacts
  const artifacts = response.result?.artifacts || response.artifacts || response.output?.artifacts || [];
  
  for (const artifact of artifacts) {
    const parts = artifact.parts || artifact.output?.parts || [];
    
    for (const part of parts) {
      // Extract text from text parts
      if (part.kind === 'text' || part.text) {
        text += (part.text || '') + '\n';
      }
      
      // Extract products from data parts
      if (part.kind === 'data' && artifact.name === 'products') {
        try {
          const data = part.data as ProductListData;
          if (data?.type === 'product_list' && Array.isArray(data.products)) {
            products.push(...data.products.map(formatProduct));
          }
        } catch (error) {
          console.error('Error parsing product data:', error);
        }
      }
      
      // Extract cart from data parts
      if (part.kind === 'data' && artifact.name === 'cart') {
        try {
          const data = part.data as CartData;
          if (data?.type === 'cart' && Array.isArray(data.items)) {
            cart = data.items.map(formatCartItem);
          }
        } catch (error) {
          console.error('Error parsing cart data:', error);
        }
      }
      
      // Extract order from data parts
      if (part.kind === 'data' && artifact.name === 'order') {
        try {
          const data = part.data as OrderData;
          if (data?.type === 'order') {
            order = formatOrder(data);
          }
        } catch (error) {
          console.error('Error parsing order data:', error);
        }
      }
    }
  }
  
  return { 
    text: text.trim(), 
    products, 
    cart,
    order
  };
}

/**
 * Parse streaming A2A events incrementally
 * @param event - The A2A streaming event
 * @returns StreamingEvent object or null if event type is not recognized
 */
export function parseStreamingEvent(event: any): StreamingEvent | null {
  // Skip if event is null or undefined
  if (!event || typeof event !== 'object') {
    return null;
  }
  
  // Handle task events
  if (event.kind === 'task') {
    return { 
      type: 'status', 
      data: { taskId: event.id }, 
      isIncremental: true 
    };
  }
  
  // Handle status updates
  if (event.kind === 'status-update') {
    // Extract and ensure message is a string
    let statusMessage = '';
    
    // Try to extract message from various possible structures
    const messageObj = event.status?.message || event.message || event.data?.message;
    
    if (messageObj) {
      if (typeof messageObj === 'string') {
        statusMessage = messageObj;
      } else if (typeof messageObj === 'object') {
        // Handle message object structures (TextPart, etc.)
        // Try common properties that might contain the text
        statusMessage = messageObj.text || 
                       messageObj.value || 
                       messageObj.content ||
                       (messageObj.parts && Array.isArray(messageObj.parts) 
                         ? messageObj.parts
                             .map((p: any) => p.text || p.value || '')
                             .filter((t: string) => t)
                             .join(' ')
                         : '') ||
                       '';
        
        // If still empty, try JSON.stringify fallback (but prefer avoiding it)
        if (!statusMessage && typeof messageObj === 'object') {
          // Last resort: try to extract any string-like property
          const keys = Object.keys(messageObj);
          for (const key of keys) {
            const val = messageObj[key];
            if (typeof val === 'string' && val.length > 0) {
              statusMessage = val;
              break;
            }
          }
        }
        
        // Final fallback: empty string (don't show [object Object])
        if (!statusMessage || statusMessage === '[object Object]') {
          statusMessage = '';
        }
      } else {
        statusMessage = String(messageObj || '');
      }
    }
    
    return { 
      type: 'status', 
      data: { 
        state: event.status?.state || event.state,
        message: statusMessage
      },
      isIncremental: true 
    };
  }
  
  // Handle artifact updates
  if (event.kind === 'artifact-update') {
    const artifact = event.artifact || event;
    // Handle different artifact structures
    const parts = artifact.parts || artifact.output?.parts || artifact.output || [];
    
    // If parts is not an array, make it an array
    const partsArray = Array.isArray(parts) ? parts : [parts];
    
    for (const part of partsArray) {
      if (!part || typeof part !== 'object') continue;
      
      // Text artifact - handle multiple formats
      if (part.kind === 'text' || part.text !== undefined) {
        // Ensure text is a string, not an object
        let textValue = '';
        
        if (typeof part.text === 'string') {
          textValue = part.text;
        } else if (part.root && typeof part.root === 'object') {
          // Check root property (TextPart structure)
          if (typeof part.root.text === 'string') {
            textValue = part.root.text;
          } else {
            textValue = String(part.root.text || '');
          }
        } else if (part.text && typeof part.text === 'object') {
          // If text is an object, try to extract text from nested properties
          textValue = part.text.text || part.text.value || String(part.text || '');
        } else {
          textValue = String(part.text || '');
        }
        
        // Check if text is JSON that matches artifact data structures
        if (textValue && (textValue.trim().startsWith('{') || textValue.trim().startsWith('['))) {
          try {
            const parsed = JSON.parse(textValue);
            
            // If this is artifact data we've already processed, skip it
            if (parsed.type === 'cart' || parsed.type === 'product_list' || parsed.type === 'order') {
              // This is duplicate artifact data, skip displaying as text
              // But extract message field if it exists
              if (parsed.message && typeof parsed.message === 'string' && parsed.message.trim()) {
                return {
                  type: 'text',
                  data: { text: parsed.message },
                  isIncremental: artifact.incremental !== false
                };
              }
              // Skip if no message field - we already have the artifact
              return null;
            }
            
            // If JSON contains a message field, extract it
            if (parsed.message && typeof parsed.message === 'string' && parsed.message.trim()) {
              textValue = parsed.message;
            } else {
              // If it's JSON but doesn't have a message field, skip it
              // (it's likely artifact data that will be sent separately)
              return null;
            }
          } catch {
            // Not valid JSON, use as-is
          }
        }
        
        // Only return if we have actual text content
        if (textValue && textValue.trim()) {
          return {
            type: 'text',
            data: { text: textValue },
            isIncremental: artifact.incremental !== false
          };
        }
      }
      
      // Products artifact
      if (part.kind === 'data' && artifact.name === 'products') {
        try {
          const data = part.data as ProductListData;
          if (data?.type === 'product_list' && Array.isArray(data.products)) {
            return {
              type: 'products',
              data: { products: data.products.map(formatProduct) },
              isIncremental: artifact.incremental !== false
            };
          }
        } catch (error) {
          console.error('Error parsing product data:', error);
        }
      }
      
      // Cart artifact
      if (part.kind === 'data' && artifact.name === 'cart') {
        try {
          const data = part.data as CartData;
          if (data?.type === 'cart' && Array.isArray(data.items)) {
            return {
              type: 'cart',
              data: { 
                items: data.items.map(formatCartItem),
                total_items: data.total_items || 0,
                subtotal: data.subtotal || 0
              },
              isIncremental: artifact.incremental !== false
            };
          }
        } catch (error) {
          console.error('Error parsing cart data:', error);
        }
      }
      
      // Order artifact
      if (part.kind === 'data' && artifact.name === 'order') {
        try {
          const data = part.data as OrderData;
          if (data?.type === 'order') {
            return {
              type: 'order',
              data: { 
                order: formatOrder(data)
              },
              isIncremental: artifact.incremental !== false
            };
          }
        } catch (error) {
          console.error('Error parsing order data:', error);
        }
      }
    }
  }
  
  // Handle completion events
  if (event.kind === 'task-complete' || event.kind === 'complete' || event.kind === 'done') {
    return {
      type: 'complete',
      data: {},
      isIncremental: false
    };
  }
  
  // Handle message events (if they come through as-is)
  if (event.kind === 'message' && event.parts) {
    // Extract text from message parts
    const partsArray = Array.isArray(event.parts) ? event.parts : [event.parts];
    for (const part of partsArray) {
      if (part.kind === 'text' && typeof part.text === 'string') {
        return {
          type: 'text',
          data: { text: part.text },
          isIncremental: true
        };
      }
    }
  }
  
  // If we don't recognize the event, log it for debugging but don't crash
  if (process.env.NODE_ENV === 'development') {
    console.debug('Unrecognized streaming event:', event);
  }
  
  return null;
}

/**
 * Accumulate streaming text chunks
 */
export function accumulateText(currentText: string, newChunk: string): string {
  return currentText + newChunk;
}

