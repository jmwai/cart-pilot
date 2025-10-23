# Shopping Orchestrator API Documentation

## Overview

The Shopping Orchestrator is an AI-powered e-commerce assistant that coordinates between specialized agents to help users complete their shopping journey. It supports product discovery, cart management, checkout, payment processing, and customer service.

**Agent Name:** `shopping_orchestrator`

---

## Quick Start

### 1. Create a Session

```bash
curl -X POST http://localhost:8080/apps/shopping_orchestrator/users/user_123/sessions/session_abc \
  -H "Content-Type: application/json" \
  -d '{"state": {"preferred_language": "English"}}'
```

**Response:**
```json
{
  "id": "session_abc",
  "appName": "shopping_orchestrator",
  "userId": "user_123",
  "state": {"state": {"preferred_language": "English"}},
  "events": [],
  "lastUpdateTime": 1761234567.0
}
```

### 2. Interact with the Agent

```bash
curl -X POST http://localhost:8080/run_sse \
  -H "Content-Type: application/json" \
  -d '{
    "app_name": "shopping_orchestrator",
    "user_id": "user_123",
    "session_id": "session_abc",
    "new_message": {
      "role": "user",
      "parts": [{"text": "Find me some running shoes"}]
    },
    "streaming": false
  }'
```

---

## Agent Capabilities

The orchestrator automatically routes your requests to specialized agents:

### Product Discovery
- **Keywords:** "find", "search", "looking for", "products"
- **Example:** "Find me some sunglasses" or "Search for running shoes"

### Cart Management
- **Keywords:** "add to cart", "remove from cart", "view cart", "update cart"
- **Example:** "Add running shoes to my cart" or "Show me my cart"

### Checkout
- **Keywords:** "checkout", "place order", "buy", "purchase"
- **Example:** "Checkout with address 123 Main St" or "Place my order"

### Payment
- **Keywords:** "pay", "payment", "process payment"
- **Example:** "Pay for my order with credit card" or "Process payment"

### Customer Service
- **Keywords:** "return", "refund", "help", "support", "complaint"
- **Example:** "I want to return my order" or "Help with refund"

---

## API Endpoints

### Base URL
```
http://localhost:8080
```

### List Available Agents
```bash
GET /list-apps
```

**Response:**
```json
["cart_agent", "checkout_agent", "customer_service_agent", "orchestrator_agent", "payment_agent", "product_discovery_agent"]
```

### Create/Update Session
```bash
POST /apps/{app_name}/users/{user_id}/sessions/{session_id}
```

**Request Body:**
```json
{
  "state": {
    "preferred_language": "English",
    "user_preferences": {}
  }
}
```

### Run Agent (Execute Query)
```bash
POST /run_sse
```

**Request Body:**
```json
{
  "app_name": "shopping_orchestrator",
  "user_id": "user_123",
  "session_id": "session_abc",
  "new_message": {
    "role": "user",
    "parts": [{"text": "Your query here"}]
  },
  "streaming": false
}
```

**Notes:**
- Set `streaming: true` for Server-Sent Events (SSE) streaming responses
- Set `streaming: false` for complete response after processing

### Health Check
```bash
GET /healthz
```

**Response:**
```json
{
  "status": "ok",
  "message": "Agents Gateway is healthy"
}
```

---

## Example Workflows

### Complete Shopping Flow

#### 1. Search for Products
```json
{
  "new_message": {
    "role": "user",
    "parts": [{"text": "Find me some running shoes"}]
  }
}
```

#### 2. Add to Cart
```json
{
  "new_message": {
    "role": "user",
    "parts": [{"text": "Add the first running shoes to my cart"}]
  }
}
```

#### 3. View Cart
```json
{
  "new_message": {
    "role": "user",
    "parts": [{"text": "Show me my cart"}]
  }
}
```

#### 4. Checkout
```json
{
  "new_message": {
    "role": "user",
    "parts": [{"text": "Checkout with shipping address 123 Main St, New York, NY 10001"}]
  }
}
```

#### 5. Process Payment
```json
{
  "new_message": {
    "role": "user",
    "parts": [{"text": "Pay for my order with credit card"}]
  }
}
```

### Customer Service Flow

#### Return Request
```json
{
  "new_message": {
    "role": "user",
    "parts": [{"text": "I want to return order ORD-123"}]
  }
}
```

#### FAQ Search
```json
{
  "new_message": {
    "role": "user",
    "parts": [{"text": "What is your return policy?"}]
  }
}
```

---

## Response Format

### Success Response
```json
{
  "content": {
    "parts": [{
      "text": "Agent response text here"
    }],
    "role": "model"
  },
  "finishReason": "STOP",
  "usageMetadata": {
    "totalTokenCount": 1234
  }
}
```

### Error Response
```json
{
  "error": "Error message describing what went wrong"
}
```

---

## Agent Descriptions

### Shopping Orchestrator
- **Purpose:** Routes requests to specialized agents
- **Description:** "Orchestrates shopping workflow by routing to specialized agents"

### Product Discovery Agent
- **Purpose:** Search for products
- **Description:** "Handles product discovery through text and image search"

### Cart Agent
- **Purpose:** Manage shopping cart
- **Description:** "Manages shopping cart operations including adding, updating, and removing items"

### Checkout Agent
- **Purpose:** Create orders
- **Description:** "Handles order creation from cart and order management"

### Payment Agent
- **Purpose:** Process payments (AP2-compliant)
- **Description:** "Processes payments using AP2 protocol with cryptographic mandates"

### Customer Service Agent
- **Purpose:** Handle support
- **Description:** "Handles customer support including returns, refunds, and inquiries"

---

## Authentication

Currently, no authentication is required for local development. The agent uses session-based state management.

---

## Testing

Use the provided test script:

```bash
./test_agent.sh
```

This script will:
1. Create a session
2. Query the agent with product search
3. Query again with a different question

---

## Notes

- All agents are automatically discovered by ADK
- Sessions persist state across interactions
- The orchestrator intelligently routes requests based on natural language
- AP2 compliance ensures secure payment processing with cryptographic mandates
- Each agent has its own output schema for consistent responses

---

## Next.js Chatbot Integration

### Overview

This section provides a complete guide for implementing a Next.js chatbot frontend that interacts with the Shopping Orchestrator.

### Setup

#### 1. Create Next.js Project

```bash
npx create-next-app@latest shopping-chatbot --typescript --tailwind --app
cd shopping-chatbot
```

#### 2. Install Dependencies

```bash
npm install axios
npm install @types/node
```

### API Client Implementation

Create `lib/shopping-api.ts`:

```typescript
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

interface Session {
  id: string;
  appName: string;
  userId: string;
  state: any;
}

interface MessagePart {
  text: string;
}

interface Message {
  role: 'user' | 'model';
  parts: MessagePart[];
}

interface RunRequest {
  app_name: string;
  user_id: string;
  session_id: string;
  new_message: Message;
  streaming: boolean;
}

class ShoppingAPI {
  private baseURL: string;
  private userId: string;
  private sessionId: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
    this.userId = 'user_' + Math.random().toString(36).substr(2, 9);
    this.sessionId = 'session_' + Date.now();
  }

  // Create or update session
  async createSession(): Promise<Session> {
    const response = await axios.post(
      `${this.baseURL}/apps/shopping_orchestrator/users/${this.userId}/sessions/${this.sessionId}`,
      { state: { preferred_language: 'English' } }
    );
    return response.data;
  }

  // Send message to agent
  async sendMessage(text: string): Promise<any> {
    const request: RunRequest = {
      app_name: 'shopping_orchestrator',
      user_id: this.userId,
      session_id: this.sessionId,
      new_message: {
        role: 'user',
        parts: [{ text }]
      },
      streaming: false
    };

    const response = await axios.post(
      `${this.baseURL}/run_sse`,
      request
    );

    return response.data;
  }

  // Health check
  async healthCheck(): Promise<boolean> {
    try {
      const response = await axios.get(`${this.baseURL}/healthz`);
      return response.data.status === 'ok';
    } catch {
      return false;
    }
  }
}

export const shoppingAPI = new ShoppingAPI();
```

### Chat Component Implementation

Create `components/Chat.tsx`:

```typescript
'use client';

import { useState, useRef, useEffect } from 'react';
import { shoppingAPI } from '@/lib/shopping-api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionCreated, setSessionCreated] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Initialize session on mount
    const initSession = async () => {
      try {
        await shoppingAPI.createSession();
        setSessionCreated(true);
        addMessage('assistant', 'Hello! I\'m your shopping assistant. How can I help you today?');
      } catch (error) {
        console.error('Failed to create session:', error);
        addMessage('assistant', 'Failed to connect to the shopping assistant. Please try again.');
      }
    };

    initSession();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const addMessage = (role: 'user' | 'assistant', content: string) => {
    setMessages(prev => [...prev, {
      role,
      content,
      timestamp: new Date()
    }]);
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!input.trim() || isLoading || !sessionCreated) return;

    const userMessage = input.trim();
    setInput('');
    addMessage('user', userMessage);
    setIsLoading(true);

    try {
      const response = await shoppingAPI.sendMessage(userMessage);
      
      // Extract agent response from the response structure
      let assistantMessage = 'I received your message.';
      
      if (response.content?.parts?.[0]?.text) {
        assistantMessage = response.content.parts[0].text;
      } else if (response.error) {
        assistantMessage = `Error: ${response.error}`;
      }

      addMessage('assistant', assistantMessage);
    } catch (error) {
      console.error('Error sending message:', error);
      addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto">
      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                msg.role === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-200 text-gray-800'
              }`}
            >
              <p className="text-sm">{msg.content}</p>
              <p className="text-xs mt-1 opacity-70">
                {msg.timestamp.toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-200 text-gray-800 px-4 py-2 rounded-lg">
              <p className="text-sm">Thinking...</p>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <form onSubmit={handleSend} className="p-4 border-t">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading || !sessionCreated}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim() || !sessionCreated}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
}
```

### Main Page Integration

Update `app/page.tsx`:

```typescript
import Chat from '@/components/Chat';

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50">
      <div className="container mx-auto py-8">
        <h1 className="text-3xl font-bold text-center mb-8">
          Shopping Assistant
        </h1>
        <Chat />
      </div>
    </main>
  );
}
```

### Environment Variables

Create `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8080
```

### Error Handling

Add error boundaries and retry logic:

```typescript
// Add to Chat component
const handleSendWithRetry = async (message: string, retries = 3) => {
  for (let i = 0; i < retries; i++) {
    try {
      return await shoppingAPI.sendMessage(message);
    } catch (error) {
      if (i === retries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
};
```

### Streaming Support (Optional)

For real-time streaming responses:

```typescript
async sendMessageStream(text: string, onChunk: (chunk: string) => void) {
  const request = {
    app_name: 'shopping_orchestrator',
    user_id: this.userId,
    session_id: this.sessionId,
    new_message: {
      role: 'user',
      parts: [{ text }]
    },
    streaming: true
  };

  const response = await fetch(`${this.baseURL}/run_sse`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request)
  });

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader!.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        if (data.content?.parts?.[0]?.text) {
          onChunk(data.content.parts[0].text);
        }
      }
    }
  }
}
```

### Best Practices

1. **Session Management**: Create session once on mount, reuse throughout
2. **Loading States**: Show "Thinking..." indicator during agent processing
3. **Error Handling**: Implement retry logic and user-friendly error messages
4. **Auto-scroll**: Scroll to latest message automatically
5. **Input Validation**: Disable send button when input is empty
6. **Responsive Design**: Use Tailwind for mobile-friendly layout
7. **Message Persistence**: Optional - save messages to localStorage or database

### Testing

```bash
# Run Next.js dev server
npm run dev

# Visit http://localhost:3000
# Test queries:
# - "Find me some running shoes"
# - "Add the first one to my cart"
# - "Show me my cart"
# - "Checkout with address 123 Main St"
```

---

## Support

For issues or questions, check the logs:

```bash
docker logs <container_id>
```

Or visit the health endpoint:
```bash
curl http://localhost:8080/healthz
```

