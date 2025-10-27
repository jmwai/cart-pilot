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

This section provides a complete guide for implementing a Next.js chatbot frontend using the official A2A JavaScript SDK to interact with the Shopping Orchestrator.

**References:**
- [A2A JavaScript SDK](https://github.com/a2aproject/a2a-js)
- [A2A Protocol Documentation](https://a2aprotocol.org)

### Setup

#### 1. Create Next.js Project

```bash
npx create-next-app@latest shopping-chatbot --typescript --tailwind --app
cd shopping-chatbot
```

#### 2. Install Dependencies

```bash
npm install @a2a-js/sdk
npm install uuid
npm install @types/uuid
```

### API Client Implementation Using A2A SDK

Create `lib/shopping-api.ts`:

```typescript
import { A2AClient, MessageSendParams } from '@a2a-js/sdk/client';
import { v4 as uuidv4 } from 'uuid';

const AGENT_CARD_URL = process.env.NEXT_PUBLIC_AGENT_CARD_URL || 
  'http://localhost:8080/.well-known/agent-card.json';

class ShoppingAPI {
  private client: A2AClient | null = null;
  private contextId: string;

  constructor() {
    this.contextId = 'context_' + Date.now();
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
      // A2A client initialization itself is a health check
      return this.client !== null;
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
  const [isInitialized, setIsInitialized] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Initialize A2A client on mount
    const init = async () => {
      try {
        await shoppingAPI.initialize();
        setIsInitialized(true);
        addMessage('assistant', 'Hello! I\'m your shopping assistant. How can I help you today?');
      } catch (error) {
        console.error('Failed to initialize A2A client:', error);
        addMessage('assistant', 'Failed to connect to the shopping assistant. Please try again.');
      }
    };

    init();
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
    
    if (!input.trim() || isLoading || !isInitialized) return;

    const userMessage = input.trim();
    setInput('');
    addMessage('user', userMessage);
    setIsLoading(true);

    try {
      const response = await shoppingAPI.sendMessage(userMessage);
      
      // Extract agent response from A2A response structure
      let assistantMessage = 'I received your message.';
      
      if (response.output?.parts) {
        assistantMessage = response.output.parts.map((p: any) => p.text).join(' ');
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
            disabled={isLoading || !isInitialized}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim() || !isInitialized}
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
NEXT_PUBLIC_AGENT_CARD_URL=http://localhost:8080/.well-known/agent-card.json
```

**Note:** The A2A SDK fetches the agent card from `.well-known/agent-card.json` endpoint. This card contains the agent's capabilities and API endpoints.

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

### Streaming Support

Using A2A SDK's built-in streaming:

```typescript
// In Chat component
const handleSendStream = async (e: React.FormEvent) => {
  e.preventDefault();
  
  if (!input.trim() || isLoading || !isInitialized) return;

  const userMessage = input.trim();
  setInput('');
  addMessage('user', userMessage);
  setIsLoading(true);

  let fullResponse = '';

  try {
    // Use streaming method
    for await (const event of shoppingAPI.sendMessageStream(userMessage)) {
      if (event.kind === 'task') {
        console.log(`Task created: ${event.id}`);
      } else if (event.kind === 'status-update') {
        console.log(`Status: ${event.status.state}`);
      } else if (event.kind === 'artifact-update') {
        // Extract text from artifact
        const text = event.artifact.output?.parts?.map((p: any) => p.text).join(' ') || '';
        fullResponse += text;
        
        // Update the latest assistant message with streaming content
        setMessages(prev => {
          const updated = [...prev];
          const lastMsg = updated[updated.length - 1];
          if (lastMsg.role === 'assistant') {
            lastMsg.content = fullResponse;
          } else {
            updated.push({
              role: 'assistant',
              content: fullResponse,
              timestamp: new Date()
            });
          }
          return updated;
        });
      }
    }
  } catch (error) {
    console.error('Error in streaming:', error);
    addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
  } finally {
    setIsLoading(false);
  }
};
```

**Benefits of A2A SDK Streaming:**
- **Event Types**: `task`, `status-update`, `artifact-update` events
- **Clean API**: No manual SSE parsing
- **Progress Tracking**: Real-time status updates
- **Task Management**: Built-in task lifecycle handling

### Best Practices

1. **Agent Card**: A2A SDK fetches agent capabilities from `.well-known/agent-card.json`
2. **Client Initialization**: Initialize A2A client once, reuse throughout session
3. **Loading States**: Show "Thinking..." indicator during agent processing
4. **Error Handling**: Implement retry logic and user-friendly error messages
5. **Auto-scroll**: Scroll to latest message automatically
6. **Input Validation**: Disable send button when input is empty
7. **Responsive Design**: Use Tailwind for mobile-friendly layout
8. **Message Persistence**: Optional - save messages to localStorage or database
9. **Event Handling**: Process A2A events (`task`, `status-update`, `artifact-update`) for rich UX
10. **Task Lifecycle**: Use task status updates to show progress (working → completed)

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

## Future Refactoring: A2A AgentExecutor Pattern

### Overview

Currently, the orchestrator uses ADK's native `LlmAgent` with `AgentTool` delegation. For enhanced A2A compliance and Cloud Run deployment, consider refactoring to use the AgentExecutor pattern that wraps ADK agents for A2A protocol compatibility.

**Benefits:**
- Full A2A protocol compliance
- Task lifecycle management
- Better Cloud Run integration
- Cancellation support
- Event-driven architecture

### Reference Implementation

The A2A samples project provides reference implementations:
- [ADK Cloud Run Agent Executor](https://github.com/a2aproject/a2a-samples/blob/main/samples/python/agents/adk_cloud_run/agent_executor.py)
- [ADK Cloud Run Agent](https://github.com/a2aproject/a2a-samples/blob/main/samples/python/agents/adk_cloud_run/agent.py)
- [ADK Cloud Run Main](https://github.com/a2aproject/a2a-samples/blob/main/samples/python/agents/adk_cloud_run/__main__.py)

### Proposed Refactoring Steps

#### 1. Create Agent Executor Wrapper

```python
# app/orchestrator_agent/agent_executor.py
from typing import Set
from a2a_python import AgentExecutor, RequestContext, ExecutionEventBus
from app.orchestrator_agent.agent import root_agent

class OrchestratorAgentExecutor(AgentExecutor):
    """A2A-compliant wrapper for ADK orchestrator agent."""
    
    def __init__(self):
        self.cancelled_tasks: Set[str] = set()
        self.adk_agent = root_agent
    
    async def cancel_task(self, task_id: str, event_bus: ExecutionEventBus) -> None:
        """Handle task cancellation."""
        self.cancelled_tasks.add(task_id)
        # Publish cancellation event
    
    async def execute(self, request_context: RequestContext, event_bus: ExecutionEventBus) -> None:
        """Execute orchestration using ADK agent."""
        task_id = request_context.task_id
        user_message = request_context.user_message
        
        # Check for cancellation
        if task_id in self.cancelled_tasks:
            # Publish cancelled status
            return
        
        # Publish working status
        # Run ADK agent with user message
        # Publish results as artifacts
        # Publish completed status
```

#### 2. Integration Considerations

**Current Architecture:**
- Uses `get_fast_api_app()` from ADK
- Agents discovered via directory structure
- Session-based state management

**Refactored Architecture:**
- AgentExecutor wraps ADK agents
- A2A protocol for client communication
- Task-based lifecycle management
- Event-driven updates

**Migration Path:**
1. Add A2A Python SDK to requirements
2. Create executor wrapper for orchestrator
3. Update main.py to use executor pattern
4. Test with A2A JS SDK client
5. Gradually migrate other agents

#### 3. When to Refactor

**Good reasons to refactor:**
- Need full A2A compliance
- Planning Cloud Run deployment
- Require task cancellation
- Want event-driven updates
- Need agent-to-agent communication

**Current implementation is sufficient if:**
- Using ADK's built-in FastAPI app
- Primary use case is web chatbot
- Simplicity is priority
- No need for A2A agent-to-agent features

### Testing the Refactored Version

After refactoring:

```bash
# Test with A2A client
from a2a_python import A2AClient

client = await A2AClient.from_card_url("http://localhost:8080/.well-known/agent-card.json")
response = await client.send_message({
    "message": {
        "messageId": "msg_123",
        "role": "user",
        "parts": [{"kind": "text", "text": "Find running shoes"}]
    }
})
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

