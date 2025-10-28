import { Product, ProductListData, A2AArtifact } from '@/types';

/**
 * Parse A2A response to extract text and product data
 * @param response - The A2A response object
 * @returns Object containing text message and products array
 */
export function parseA2AResponse(response: any): {
  text: string;
  products: Product[];
} {
  let text = '';
  const products: Product[] = [];
  
  // Handle different response structures
  const artifacts = response.artifacts || response.output?.artifacts || [];
  
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
          if (data.type === 'product_list' && Array.isArray(data.products)) {
            products.push(...data.products);
          }
        } catch (error) {
          console.error('Error parsing product data:', error);
        }
      }
    }
  }
  
  return { text: text.trim(), products };
}

