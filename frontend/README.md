# Sole Search Frontend

A modern e-commerce frontend with AI-powered shopping assistant, built with Next.js 16 and integrated with the Shopping Orchestrator backend via A2A protocol.

## Features

- 🏠 **Product Listing Page** - Browse featured products in a clean grid layout
- 📦 **Product Detail Page** - Detailed product view with images, specs, and "You Might Also Like" recommendations
- 💬 **AI Chat Assistant** - Floating chatbox for real-time interaction with the shopping orchestrator agent
- 🎨 **Modern UI** - Clean, minimalist design inspired by the Sole Search reference images
- 📱 **Responsive Design** - Works seamlessly on desktop, tablet, and mobile devices

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

The frontend uses the A2A (Agent-to-Agent) protocol to communicate with the backend shopping orchestrator:

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

4. Test the chatbox by clicking the floating chat icon and sending messages like:
   - "Find me running shoes"
   - "Show me the picture of Air Jordan 1"
   - "Add Air Jordan 1 to my cart"

## Future Enhancements

- [ ] Real product images from backend
- [ ] Shopping cart functionality
- [ ] User authentication
- [ ] Payment integration
- [ ] Order tracking
- [ ] Product search and filters
- [ ] Wishlist functionality
- [ ] Product reviews and ratings

## Troubleshooting

### Chatbox Not Connecting

- Verify backend is running on port 8080
- Check browser console for connection errors
- Ensure `.env.local` has correct agent card URL

### Products Not Loading

- Check that mock data is properly imported
- Verify product IDs match routes

## License

MIT