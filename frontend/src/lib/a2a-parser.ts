import { Product, ProductListData, CartItem, CartData } from '@/types';

/**
 * Parsed A2A response containing text, products, and cart data
 */
export interface ParsedA2AResponse {
  text: string;
  products: Product[];
  cart?: CartItem[];
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
 * Parse A2A response to extract text, product data, and cart data
 * @param response - The A2A response object (JSON-RPC format)
 * @returns Object containing text message, products array, and optional cart array
 */
export function parseA2AResponse(response: any): ParsedA2AResponse {
  let text = '';
  const products: Product[] = [];
  let cart: CartItem[] | undefined = undefined;
  
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
    }
  }
  
  return { 
    text: text.trim(), 
    products, 
    cart 
  };
}

