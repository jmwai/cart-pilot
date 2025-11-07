/**
 * Status message utility functions
 */

/**
 * Safely extract status message from event data.
 * Handles various data formats and prevents [object Object] strings.
 */
export function extractStatusMessage(data: any): string {
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
        const extracted =
          msgObj.text ||
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
}

/**
 * Generate contextual loading message based on user query
 */
export function getContextualLoadingMessage(userMessage: string): string {
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
  if (
    lowerMessage.includes('find') ||
    lowerMessage.includes('search') ||
    lowerMessage.includes('show') ||
    lowerMessage.includes('looking')
  ) {
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
  if (
    lowerMessage.includes('checkout') ||
    lowerMessage.includes('place order') ||
    lowerMessage.includes('buy') ||
    (lowerMessage.includes('yes') && lowerMessage.includes('checkout'))
  ) {
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
}

/**
 * Safely render loading message, ensuring it's always a string
 */
export function renderLoadingMessage(loadingMessage: any): string {
  // Extra defensive check to ensure we never render an object
  if (typeof loadingMessage === 'string') {
    // Make sure it's not [object Object]
    return loadingMessage !== '[object Object]' ? loadingMessage : '';
  }
  
  const msgObj = loadingMessage as any;
  if (msgObj && typeof msgObj === 'object') {
    // If it's an object, try to extract a string
    const extracted =
      msgObj.message ||
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
}

