# Plan: Product Discovery & Cart Flow with A2A Protocol

## Overview

Create a seamless, natural shopping experience with rich product displays and cart management using A2A Protocol's structured data exchange standards.

## Goals

1. ✅ Return structured product data via A2A DataPart artifacts
2. ✅ Display products with images, titles, prices in chat interface
3. ✅ Show cart items with visual cards and totals
4. ✅ Maintain natural conversational flow throughout
5. ✅ Support real-time updates via streaming

---

## Phase 1: Backend - Structured Data Extraction & Return

### 1.1 Extract Products from State (Not Text Parsing)

**File:** `backend/app/a2a_executor.py`

**Current Issue:** Products are embedded in text; need to extract from ADK state instead.

**Solution:**
- Access `state["current_results"]` from the session after agent execution
- Format products with image URLs, prices, and all metadata
- Return as DataPart artifact per A2A Protocol

**Implementation:**
```python
# After agent execution, access session state
session_state = session.state if hasattr(session, 'state') else {}
current_results = session_state.get("current_results", [])

if current_results:
    # Format products with all required fields
    formatted_products = []
    for product in current_results:
        formatted_products.append({
            "id": product.get("id"),
            "name": product.get("name"),
            "description": product.get("description", ""),
            "image_url": product.get("product_image_url") or product.get("picture", ""),
            "price": product.get("price_usd_units", 0.0) / 100.0 if product.get("price_usd_units") else 0.0,
            "distance": product.get("distance", 0.0)
        })
    
    # Create DataPart artifact
    product_data = {
        "type": "product_list",
        "products": formatted_products
    }
    await updater.add_artifact(
        [Part(root=DataPart(
            data=product_data,
            mimeType="application/json"
        ))],
        name="products"
    )
```

---

### 1.2 Extract Cart Data from Agent Output

**File:** `backend/app/a2a_executor.py`

**Solution:**
- Detect when cart agent returns structured output
- Access cart data from `get_cart` tool results or session state
- Return as separate DataPart artifact named "cart"

**Implementation:**
```python
# Check if response contains cart data
cart_data = None
if "cart" in session_state or "cart_items" in session_state:
    # Get cart from state or tool results
    cart_data = format_cart_data(...)

if cart_data:
    await updater.add_artifact(
        [Part(root=DataPart(
            data={"type": "cart", "items": cart_data},
            mimeType="application/json"
        ))],
        name="cart"
    )
```

---

### 1.3 Update Agent Instructions to Ensure Images

**Files:** 
- `backend/app/product_discovery_agent/agent.py`
- `backend/app/cart_agent/agent.py`

**Add to Product Discovery Agent:**
```
When presenting search results, always include:
- Product images (use product_image_url or picture field)
- Product names with distinguishing features (color, size, style)
- Product prices if available
- Product IDs for reference
```

**Add to Cart Agent:**
```
When showing cart contents, always include:
- Product images
- Product names
- Quantities
- Prices and subtotals
- Use visual formatting to make cart easy to scan
```

---

## Phase 2: Frontend - Enhanced Parsing & Display

### 2.1 Enhance A2A Parser

**File:** `frontend/src/lib/a2a-parser.ts`

**Current:** Only handles products

**Enhancement:** Parse both products and cart data

```typescript
export interface ParsedA2AResponse {
  text: string;
  products: Product[];
  cart?: CartItem[];
}

export function parseA2AResponse(response: any): ParsedA2AResponse {
  let text = '';
  const products: Product[] = [];
  let cart: CartItem[] | undefined = undefined;
  
  const artifacts = response.result?.artifacts || response.artifacts || [];
  
  for (const artifact of artifacts) {
    const parts = artifact.parts || [];
    
    for (const part of parts) {
      // Text parts
      if (part.kind === 'text' || part.text) {
        text += (part.text || '') + '\n';
      }
      
      // Data parts - products
      if (part.kind === 'data' && artifact.name === 'products') {
        const data = part.data;
        if (data?.type === 'product_list' && Array.isArray(data.products)) {
          products.push(...data.products.map(formatProduct));
        }
      }
      
      // Data parts - cart
      if (part.kind === 'data' && artifact.name === 'cart') {
        const data = part.data;
        if (data?.type === 'cart' && Array.isArray(data.items)) {
          cart = data.items.map(formatCartItem);
        }
      }
    }
  }
  
  return { text: text.trim(), products, cart };
}
```

---

### 2.2 Create Cart Display Component

**File:** `frontend/src/components/CartDisplay.tsx` (NEW)

**Features:**
- Display cart items as cards
- Show images, names, quantities, prices
- Show total
- Remove/update quantity actions

**Design:**
```typescript
interface CartDisplayProps {
  items: CartItem[];
  onUpdateQuantity?: (cartItemId: string, quantity: number) => void;
  onRemove?: (cartItemId: string) => void;
}

export default function CartDisplay({ items, onUpdateQuantity, onRemove }: CartDisplayProps) {
  // Display cart items with images, prices, quantities
  // Show total at bottom
}
```

---

### 2.3 Update Chatbox for Multi-Artifact Display

**File:** `frontend/src/components/Chatbox.tsx`

**Enhancements:**
1. Parse both products and cart from response
2. Display products inline after assistant message
3. Display cart when cart data is present
4. Support streaming for real-time updates
5. Better message ordering

**Changes:**
```typescript
interface MessageWithArtifacts extends ChatMessage {
  products?: Product[];
  cart?: CartItem[];
}

// Display structure:
// 1. Assistant text message
// 2. Products grid (if products exist)
// 3. Cart display (if cart exists)
```

---

### 2.4 Add Streaming Support

**File:** `frontend/src/lib/shopping-api.ts`

**Enhancement:** Use streaming for real-time product/cart updates

**Implementation:**
```typescript
async *sendMessageStream(text: string): AsyncGenerator<ParsedA2AResponse> {
  // Use existing streaming
  // Parse artifacts as they arrive
  // Yield partial updates
}
```

---

## Phase 3: UI/UX Enhancements

### 3.1 Product Card Enhancements

**File:** `frontend/src/components/ProductCard.tsx`

**Improvements:**
- Better image loading/error handling
- Price display with currency formatting
- Add to cart button with loading state
- Click to view details
- Hover effects

---

### 3.2 Message Flow Improvements

**File:** `frontend/src/components/Chatbox.tsx`

**Features:**
- Loading indicators during search
- Progressive rendering (text first, then products)
- Smooth animations
- Clear visual separation between messages and artifacts
- Typing indicators

---

### 3.3 Cart Integration

**Features:**
- Show cart count in header
- Quick add from product cards
- Cart summary when items added
- Update cart inline

---

## Phase 4: Data Format Standardization

### 4.1 Product Data Schema

**Standard Structure:**
```typescript
interface Product {
  id: string;
  name: string;
  description?: string;
  image_url: string;  // Always required
  price: number;       // In dollars (e.g., 19.99)
  price_usd_units?: number;  // In cents (e.g., 1999)
  distance?: number;
}
```

### 4.2 Cart Data Schema

**Standard Structure:**
```typescript
interface CartData {
  type: "cart";
  items: CartItem[];
  total_items: number;
  subtotal: number;
}
```

---

## Implementation Steps

### Step 1: Backend Data Extraction (Priority 1)
1. ✅ Access `session.state["current_results"]` after agent execution
2. ✅ Format products with all fields (especially images)
3. ✅ Return as DataPart artifact
4. ✅ Extract cart data when cart agent is called
5. ✅ Return cart as separate DataPart artifact

### Step 2: Frontend Parsing (Priority 1)
1. ✅ Enhance parser to handle products and cart
2. ✅ Add proper TypeScript types
3. ✅ Handle missing/partial data gracefully

### Step 3: UI Components (Priority 2)
1. ✅ Create CartDisplay component
2. ✅ Enhance ProductCard component
3. ✅ Update Chatbox to display both

### Step 4: Streaming (Priority 3)
1. ✅ Implement streaming for real-time updates
2. ✅ Handle progressive artifact rendering

### Step 5: Polish (Priority 4)
1. ✅ Add animations
2. ✅ Improve error handling
3. ✅ Add loading states
4. ✅ Optimize image loading

---

## Success Criteria

✅ Products display with images, titles, prices  
✅ Cart displays with images and totals  
✅ Natural conversational flow  
✅ Structured data via A2A DataPart  
✅ Real-time updates via streaming  
✅ Good UX with proper loading/error states

---

## Technical Notes

**A2A Protocol Compliance:**
- Use `DataPart` with `mimeType: "application/json"` per [A2A Protocol Specification](https://a2a-protocol.org/latest/specification/)
- Separate artifacts for different data types (products vs cart)
- Maintain backward compatibility with text-only responses

**State Management:**
- Products stored in `state["current_results"]` by tools
- Accessible to executor after agent completion
- Cart data accessible via tool results or state

**References:**
- [A2A JS SDK](https://github.com/a2aproject/a2a-js)
- [A2A Protocol Specification](https://a2a-protocol.org/latest/specification/)

