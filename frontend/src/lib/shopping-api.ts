import { A2AClient, MessageSendParams } from '@a2a-js/sdk/client';
import { v4 as uuidv4 } from 'uuid';
import { Product } from '@/types';

const AGENT_CARD_URL = process.env.NEXT_PUBLIC_AGENT_CARD_URL || 
  'http://localhost:8080/.well-known/agent-card.json';
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 
  'http://localhost:8080';

class ShoppingAPI {
  private client: A2AClient | null = null;
  private sessionId: string;

  constructor() {
    // Get or create session ID from localStorage
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('shopping_session_id');
      this.sessionId = stored || 'session_' + Date.now();
      if (!stored) {
        localStorage.setItem('shopping_session_id', this.sessionId);
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

  // Send message to agent (non-streaming)
  async sendMessage(text: string): Promise<any> {
    await this.initialize();

    const params: MessageSendParams = {
      message: {
        messageId: uuidv4(),
        role: 'user',
        parts: [{ kind: 'text', text }],
        kind: 'message',
      },
      configuration: {
        blocking: true,
        acceptedOutputModes: ['text/plain'],
      },
    };

    return await this.client!.sendMessage(params);
  }

  // Send message with streaming support
  async *sendMessageStream(text: string): AsyncGenerator<any> {
    await this.initialize();

    const params: MessageSendParams = {
      message: {
        messageId: uuidv4(),
        role: 'user',
        parts: [{ kind: 'text', text }],
        kind: 'message',
      },
      configuration: {
        blocking: false,
        acceptedOutputModes: ['text/plain'],
      },
    };

    const stream = this.client!.sendMessageStream(params);
    
    for await (const event of stream) {
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
}

export const shoppingAPI = new ShoppingAPI();
