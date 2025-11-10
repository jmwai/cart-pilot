# Cart Pilot Frontend

A modern e-commerce frontend with AI-powered shopping assistant, built with Next.js 16 and integrated with the Cart Pilot backend via A2A protocol. Experience the future of shopping with AI agents that orchestrate your entire shopping journey.

## Features

- 🏠 **Product Listing Page** - Browse featured products in a clean grid layout
- 📦 **Product Detail Page** - Detailed product view with images, specs, and "You Might Also Like" recommendations
- 💬 **AI Chat Assistant** - Floating chatbox that handles ALL shopping operations:
  - 🔍 Product discovery and search
  - 🛒 Cart management (add, remove, update)
  - 📦 Checkout and order creation
  - 💳 Payment processing (AP2-compliant)
  - 🎧 Customer support and returns
- 🎨 **Modern UI** - Clean, minimalist design for a futuristic shopping experience
- 📱 **Responsive Design** - Works seamlessly on desktop, tablet, and mobile devices

## Architecture: Agent-Driven Shopping

This application follows an **agent-driven architecture** where the AI chat assistant orchestrates all shopping operations. Users interact naturally through conversation while the agent:

1. **Routes requests** to specialized backend agents (product discovery, cart, checkout, payment, support)
2. **Maintains context** across the entire shopping journey
3. **Handles AP2 compliance** for all financial transactions
4. **Provides recommendations** based on user preferences

The UI serves as a visual catalog while the agent handles all transactions.

## Tech Stack

- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS v4
- **AI Integration**: @a2a-js/sdk
- **Build Tool**: pnpm

## Getting Started

### Prerequisites

- Node.js 18+ and pnpm installed
- Backend server running on `http://localhost:8080`

### Installation

```bash
# Install dependencies
pnpm install

# Run development server
pnpm dev
```

The frontend will be available at `http://localhost:3000`

### Environment Variables

Create a `.env.local` file in the `frontend` directory:

```env
NEXT_PUBLIC_AGENT_CARD_URL=http://localhost:8080/.well-known/agent-card.json
NEXT_PUBLIC_BACKEND_URL=http://localhost:8080
NEXT_PUBLIC_DEFAULT_USER_ID=user_guest
```

## Project Structure

```
frontend/
├── src/
│   ├── app/                 # Next.js App Router pages
│   │   ├── page.tsx        # Landing page (product listing)
│   │   ├── products/[id]/  # Product detail pages
│   │   ├── layout.tsx       # Root layout
│   │   └── globals.css      # Global styles
│   ├── components/         # React components
│   │   ├── Chatbox.tsx      # Floating AI chat assistant
│   │   ├── Header.tsx       # Site header/navigation
│   │   └── Footer.tsx       # Site footer
│   ├── lib/                # Utility libraries
│   │   ├── shopping-api.ts  # A2A client integration
│   │   └── mock-products.ts # Mock product data
│   └── types/              # TypeScript types
│       └── index.ts        # Shared type definitions
├── public/                 # Static assets
├── package.json
└── README.md
```

## Components

### Chatbox Component

The floating chatbox provides AI assistant functionality:

- **Location**: Fixed bottom-right corner
- **Features**: Minimizable, message history, typing indicators
- **Integration**: Uses @a2a-js/sdk to communicate with backend orchestrator
- **Session Management**: Persists session ID in localStorage

### Product Pages

- **Landing Page** (`/`): Grid layout of featured products
- **Product Detail** (`/products/[id]`): Single product view with details, size selection, and related products

## AI Integration

The frontend uses the A2A (Agent-to-Agent) protocol to communicate with the Cart Pilot backend:

1. **Initialization**: Connects to backend via agent card URL
2. **Session Management**: Creates and maintains session IDs
3. **Message Handling**: Sends user messages and receives AI responses
4. **Streaming Support**: Ready for real-time streaming responses

### Example Usage

```typescript
import { shoppingAPI } from '@/lib/shopping-api';

// Send a message to the AI assistant
const response = await shoppingAPI.sendMessage("Find me running shoes");

// Access session ID
const sessionId = shoppingAPI.getSessionId();
```

## Styling

The UI follows a minimalist design with:
- **Primary Color**: Blue (#2563eb / blue-600)
- **Font**: Geist Sans (Google Fonts)
- **Layout**: Responsive grid system with Tailwind CSS

## Development

### Available Scripts

```bash
# Development server
pnpm dev

# Production build
pnpm build

# Start production server
pnpm start

# Lint code
pnpm lint
```

### Mock Data

Currently using mock product data (`src/lib/mock-products.ts`). Replace with actual API calls to backend when ready.

## Testing

1. Start the backend server:
   ```bash
   cd backend
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
   ```

2. Start the frontend:
   ```bash
   cd frontend
   pnpm dev
   ```

3. Open `http://localhost:3000` in your browser

4. Test the agent-driven shopping flow:

### Product Discovery
```
Click chat icon → "Find me running shoes"
Agent searches and returns matching products
```

### Add to Cart
```
"Add Air Jordan 1 to my cart"
Agent creates cart item and confirms
```

### View Cart
```
"Show me my cart"
Agent displays cart contents with total
```

### Checkout
```
"Checkout with address 123 Main St, New York"
Agent creates order and confirms shipping
```

### Payment
```
"Pay for my order with credit card"
Agent processes payment with AP2 compliance
```

### Customer Support
```
"I want to return my order ORD-123"
Agent initiates return process
```

## Example Agent Interactions

### Shopping Journey

1. **Browse Products**
   ```
   User: "Show me all shoes"
   Agent: [Returns product list with descriptions]
   ```

2. **Search Specific Items**
   ```
   User: "Find me Nike shoes under $150"
   Agent: [Filters and returns matching products]
   ```

3. **Add to Cart**
   ```
   User: "Add the first Nike shoe to my cart"
   Agent: "Added Nike Air Max 270 to your cart"
   ```

4. **Review Cart**
   ```
   User: "What's in my cart?"
   Agent: [Shows cart items with total]
   ```

5. **Checkout**
   ```
   User: "I want to checkout"
   Agent: "What's your shipping address?"
   User: "123 Main St, New York, NY 10001"
   Agent: "Order created: ORD-12345"
   ```

6. **Pay**
   ```
   User: "How do I pay?"
   Agent: "You can pay with credit card. Total is $160"
   User: "Pay with card ending in 1234"
   Agent: "Payment processed successfully"
   ```

7. **Track Order**
   ```
   User: "Where is my order?"
   Agent: "Order ORD-12345 is being shipped"
   ```

8. **Returns**
   ```
   User: "I want to return order ORD-12345"
   Agent: "Return initiated. You'll receive a refund"
   ```

## Future Enhancements

**Agent Integration:**
- [ ] Real product images from backend
- [ ] Cart counter badge showing live item count
- [ ] Visual cart panel triggered by agent
- [ ] Order status updates in UI
- [ ] Image upload for visual product search
- [ ] Voice input support
- [ ] Multi-language support

**UI Enhancements:**
- [ ] User authentication
- [ ] Wishlist functionality
- [ ] Product reviews display
- [ ] Image zoom on product detail page
- [ ] Quick action buttons ("Ask agent about this")
- [ ] Order history page
- [ ] Payment method management

## Troubleshooting

### Chatbox Not Connecting

- Verify backend is running on port 8080
- Check browser console for connection errors
- Ensure `.env.local` has correct agent card URL

### Products Not Loading

- Check that mock data is properly imported
- Verify product IDs match routes

