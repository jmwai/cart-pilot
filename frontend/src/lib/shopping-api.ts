import { A2AClient } from '@a2a-js/sdk/client';
import { v4 as uuidv4 } from 'uuid';
import { Product } from '@/types';

const AGENT_CARD_URL = process.env.NEXT_PUBLIC_AGENT_CARD_URL || 
  'http://localhost:8080/.well-known/agent-card.json';
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 
  'http://localhost:8080';

class ShoppingAPI {
  private client: A2AClient | null = null;
  private sessionId: string;
  private contextId: string | null = null; // Track contextId to maintain session

  constructor() {
    // Get or create session ID from localStorage
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('shopping_session_id');
      this.sessionId = stored || 'session_' + Date.now();
      if (!stored) {
        localStorage.setItem('shopping_session_id', this.sessionId);
      }
      
      // Get or create contextId from localStorage (for A2A session continuity)
      const storedContextId = localStorage.getItem('shopping_context_id');
      if (storedContextId) {
        this.contextId = storedContextId;
      }
    } else {
      this.sessionId = 'session_' + Date.now();
    }
  }

  // Initialize A2A client from agent card
  async initialize(): Promise<void> {
    if (!this.client) {
      this.client = await A2AClient.fromCardUrl(AGENT_CARD_URL);
    }
  }

  // Helper method to create FilePart from File
  private async createFilePartFromFile(file: File): Promise<any> {
    // Convert File to ArrayBuffer, then to base64
    const arrayBuffer = await file.arrayBuffer();
    const bytes = new Uint8Array(arrayBuffer);
    const base64 = btoa(String.fromCharCode(...bytes));
    
    return {
      kind: "file",
      file: {
        bytes: base64, // A2A spec: FileWithBytes uses base64-encoded bytes
        mimeType: file.type,
        name: file.name,
      }
    };
  }

  // Send message to agent (non-streaming)
  async sendMessage(text: string): Promise<any> {
    await this.initialize();

    const params: any = {
      message: {
        messageId: uuidv4(),
        role: 'user',
        parts: [{ kind: 'text', text }],
        kind: 'message',
        contextId: this.contextId || undefined, // Pass contextId to maintain session
      },
      configuration: {
        blocking: true,
        acceptedOutputModes: ['text/plain'],
      },
    };

    return await this.client!.sendMessage(params);
  }

  // Send message with streaming support (supports text and/or image)
  async *sendMessageStream(text?: string, imageFile?: File): AsyncGenerator<any> {
    await this.initialize();

    const parts: any[] = [];
    
    // Add text part if provided
    if (text && text.trim()) {
      parts.push({ kind: 'text', text: text.trim() });
    }
    
    // Add file part if image provided
    if (imageFile) {
      console.log('DEBUG: Creating FilePart for image:', imageFile.name, imageFile.type, imageFile.size);
      const filePart = await this.createFilePartFromFile(imageFile);
      console.log('DEBUG: Created FilePart:', filePart);
      parts.push(filePart);
    }

    // Must have at least one part
    if (parts.length === 0) {
      throw new Error('Message must contain either text or image');
    }

    console.log('DEBUG: Sending message with parts:', parts.map(p => ({ kind: p.kind, hasFile: !!p.file })));

    const params: any = {
      message: {
        messageId: uuidv4(),
        role: 'user',
        parts: parts,
        kind: 'message',
        contextId: this.contextId || undefined, // Pass contextId to maintain session
      },
      configuration: {
        blocking: false,
        acceptedOutputModes: ['text/plain'],
      },
    };

    console.log('DEBUG: Message params:', JSON.stringify({
      messageId: params.message.messageId,
      role: params.message.role,
      partsCount: params.message.parts.length,
      parts: params.message.parts.map((p: any) => ({ kind: p.kind, hasFile: !!p.file }))
    }));

    const stream = this.client!.sendMessageStream(params);
    
    for await (const event of stream) {
      // Extract contextId from response to maintain session
      // Check various possible event structures
      const eventData = (event as any);
      if (eventData?.result?.contextId) {
        const newContextId = eventData.result.contextId;
        if (newContextId && newContextId !== this.contextId) {
          this.contextId = newContextId;
          if (typeof window !== 'undefined' && this.contextId) {
            localStorage.setItem('shopping_context_id', this.contextId);
          }
        }
      } else if (eventData?.contextId) {
        const newContextId = eventData.contextId;
        if (newContextId && newContextId !== this.contextId) {
          this.contextId = newContextId;
          if (typeof window !== 'undefined' && this.contextId) {
            localStorage.setItem('shopping_context_id', this.contextId);
          }
        }
      }
      yield event;
    }
  }

  // Health check
  async healthCheck(): Promise<boolean> {
    try {
      await this.initialize();
      return this.client !== null;
    } catch {
      return false;
    }
  }

  // Get session ID
  getSessionId(): string {
    return this.sessionId;
  }

  // Product API methods
  async getProducts(): Promise<Product[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/products`);
      if (!response.ok) {
        throw new Error(`Failed to fetch products: ${response.statusText}`);
      }
      const data = await response.json();
      return data.products || [];
    } catch (error) {
      console.error('Error fetching products:', error);
      throw error;
    }
  }

  async getProductById(id: string): Promise<Product> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/products/${id}`);
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error(`Product with ID '${id}' not found`);
        }
        throw new Error(`Failed to fetch product: ${response.statusText}`);
      }
      const product = await response.json();
      return product;
    } catch (error) {
      console.error(`Error fetching product ${id}:`, error);
      throw error;
    }
  }

  async getSimilarProducts(productId: string, limit: number = 6): Promise<Product[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/products/${productId}/similar?limit=${limit}`);
      if (!response.ok) {
        // If API fails, return empty array (will fall back to random products)
        console.warn(`Failed to fetch similar products for ${productId}: ${response.statusText}`);
        return [];
      }
      const data = await response.json();
      return data.products || [];
    } catch (error) {
      console.error(`Error fetching similar products for ${productId}:`, error);
      // Return empty array on error (will fall back to random products)
      return [];
    }
  }
}

export const shoppingAPI = new ShoppingAPI();
