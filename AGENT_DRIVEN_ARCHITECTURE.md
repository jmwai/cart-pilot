# Agent-Driven Architecture Guide

## Overview

The Sole Search application follows an **agent-driven architecture** where the AI chat assistant orchestrates all shopping operations. This document explains how product discovery, cart management, checkout, payments, and customer support are handled through the agent interface.

## Core Principle

**The AI agent is the primary interface for all shopping operations.**

Instead of traditional e-commerce UI flows with multiple pages, forms, and buttons, users interact naturally through conversation. The agent:

1. **Interprets user intent** from natural language
2. **Routes requests** to specialized backend agents
3. **Maintains context** across the shopping journey
4. **Provides confirmations** and updates
5. **Handles edge cases** and errors gracefully

## Agent Responsibilities

### 1. Product Discovery Agent

**Handles:**
- Product search by text queries
- Image-based visual search
- Product filtering and recommendations
- Product detail retrieval

**Example Interactions:**
```
User: "Find me running shoes"
Agent: [Queries product_discovery_agent]
       [Returns: Air Jordan 1, Adidas Ultraboost, New Balance 550...]

User: "Show me shoes under $150"
Agent: [Filters products] [Returns: New Balance 550 ($110), Nike Dunk Low ($110)...]

User: "What's special about the Air Jordan 1?"
Agent: [Retrieves product details]
       "The Air Jordan 1 features premium materials and iconic design..."
```

### 2. Cart Agent

**Handles:**
- Adding items to cart
- Removing items from cart
- Updating quantities
- Viewing cart contents
- Calculating totals
- Creating AP2 intent mandates

**Example Interactions:**
```
User: "Add Air Jordan 1 to my cart"
Agent: [Calls cart_agent.add_to_cart()]
       "Added Air Jordan 1 to your cart. Your cart now has 1 item."

User: "Show me my cart"
Agent: [Calls cart_agent.get_cart()]
       "Your cart contains:
        - Air Jordan 1 x1 - $170
        Total: $170"

User: "Remove the Air Jordan from my cart"
Agent: [Calls cart_agent.remove_from_cart()]
       "Removed Air Jordan 1 from your cart."
```

### 3. Checkout Agent

**Handles:**
- Creating orders from cart
- Validating cart contents
- Collecting shipping information
- Order confirmation
- Creating AP2 cart mandates

**Example Interactions:**
```
User: "I want to checkout"
Agent: [Calls checkout_agent.validate_cart_for_checkout()]
       "Your cart contains 2 items totaling $260. What's your shipping address?"

User: "123 Main St, New York, NY 10001"
Agent: [Calls checkout_agent.create_order()]
       "Order created successfully!
        Order ID: ORD-12345
        Items: Air Jordan 1 x1, New Balance 550 x1
        Total: $260
        Shipping to: 123 Main St, New York, NY 10001"
```

### 4. Payment Agent

**Handles:**
- Processing payments
- Creating AP2 payment mandates
- Payment method selection
- Transaction confirmation
- Refunds
- Payment history

**Example Interactions:**
```
User: "Pay for my order"
Agent: [Calls payment_agent.create_payment_mandate()]
       "How would you like to pay?
        - Credit card
        - PayPal
        - Apple Pay"

User: "Credit card"
Agent: [Calls payment_agent.process_payment()]
       "Payment processed successfully!
        Transaction ID: TXN-67890
        Amount: $260
        Order ORD-12345 is now confirmed."
```

### 5. Customer Service Agent

**Handles:**
- Returns and refunds
- Order inquiries
- FAQ search
- Complaint handling
- General support

**Example Interactions:**
```
User: "I want to return my order"
Agent: [Calls customer_service_agent.initiate_return()]
       "Which order would you like to return?"

User: "ORD-12345"
Agent: "Return initiated for order ORD-12345.
        You'll receive a refund of $260 within 5-7 business days."

User: "What's your return policy?"
Agent: [Calls customer_service_agent.search_faq()]
       "We offer a 30-day return policy..."
```

## Complete Shopping Flow

### Example: Full Purchase Journey

```
1. USER: "Find me running shoes"
   AGENT: Routes to product_discovery_agent
   RETURNS: List of running shoes with prices

2. USER: "Add the New Balance 550 to my cart"
   AGENT: Routes to cart_agent
   RETURNS: "Added New Balance 550 to your cart"

3. USER: "What's in my cart?"
   AGENT: Routes to cart_agent
   RETURNS: Cart summary with total

4. USER: "Checkout with 123 Main St, New York"
   AGENT: Routes to checkout_agent
   RETURNS: Order confirmation

5. USER: "Pay with credit card"
   AGENT: Routes to payment_agent
   RETURNS: Payment confirmation

6. USER: "Where is my order?"
   AGENT: Routes to customer_service_agent
   RETURNS: Order status
```

## Backend Agent Communication

The frontend communicates with backend agents via A2A protocol:

```typescript
// Frontend sends message
await shoppingAPI.sendMessage("Add Air Jordan 1 to my cart");

// Backend orchestrator routes to cart_agent
// cart_agent calls add_to_cart tool
// Returns structured response with cart data

// Frontend displays confirmation
"Added Air Jordan 1 to your cart. Your cart now has 1 item ($170)."
```

## Benefits of Agent-Driven Architecture

### 1. Natural Language Interface
- Users express intent in their own words
- No need to learn UI patterns
- Context-aware conversations

### 2. Unified Experience
- Single chat interface for all operations
- No switching between pages
- Conversation history maintained

### 3. Smart Orchestration
- Agent routes to correct specialized agent
- Handles complex multi-step flows
- Manages state across operations

### 4. AP2 Compliance
- All financial transactions cryptographically verified
- Complete audit trail
- Secure mandate chain

### 5. Accessibility
- Chat interface works for all users
- Voice input ready
- Screen reader friendly

### 6. Scalability
- Easy to add new capabilities
- New agents integrate seamlessly
- No UI changes needed

## UI Role

The UI serves as a **visual catalog** and **interaction trigger**:

### What UI Provides:
- ✅ **Product Display** - Visual browsing of catalog
- ✅ **Product Details** - Images, specs, descriptions
- ✅ **Chat Interface** - Communication with agent
- ✅ **Visual Feedback** - Confirmation messages
- ✅ **Navigation** - Links between products

### What UI Does NOT Provide:
- ❌ Search bars (agent handles search)
- ❌ Cart management UI (agent handles cart)
- ❌ Checkout forms (agent handles checkout)
- ❌ Payment forms (agent handles payment)
- ❌ Return forms (agent handles returns)

## Technical Implementation

### Frontend Chatbox Component

```typescript
// User sends message
const response = await shoppingAPI.sendMessage(userMessage);

// Agent processes and returns structured data
{
  output: {
    parts: [{
      text: "Added Air Jordan 1 to your cart..."
    }]
  }
}

// UI displays confirmation
```

### Backend Orchestrator

```python
# Receives message from frontend
# Routes to appropriate agent based on intent

if "cart" in user_message:
    return cart_agent.handle(user_message)
elif "checkout" in user_message:
    return checkout_agent.handle(user_message)
elif "pay" in user_message:
    return payment_agent.handle(user_message)
```

## Agent Capabilities Matrix

| Capability | Traditional UI | Agent-Driven |
|------------|----------------|--------------|
| Product Search | Search bar | Natural language chat |
| Add to Cart | "Add to Cart" button | "Add [product] to my cart" |
| View Cart | Navigate to cart page | "Show me my cart" |
| Checkout | Fill checkout form | Provide address in chat |
| Payment | Enter payment details | "Pay with [method]" |
| Returns | Fill return form | "Return order [ID]" |
| Support | Navigate to support | Ask question in chat |

## Migration Path

For users familiar with traditional e-commerce:

1. **Product Selection**: Same visual browsing
2. **Cart Operations**: Instead of buttons, tell agent
3. **Checkout**: Provide info conversationally
4. **Support**: Ask questions naturally

The agent learns user preferences and speeds up future interactions.

## Future Enhancements

- [ ] Voice input support
- [ ] Image upload for visual search
- [ ] Cart visualization triggered by agent
- [ ] Order tracking with live updates
- [ ] Payment method management
- [ ] Multi-language support
- [ ] Context-aware recommendations
- [ ] Integration with external services

## Conclusion

The agent-driven architecture provides a natural, conversational shopping experience while maintaining all e-commerce functionality. Users get a unified interface, while the backend leverages specialized agents for optimal performance and compliance.
