# Product Display Implementation - Next Steps

## Overview

Implement rich product cards in chat using A2A's `DataPart` for structured data exchange.

**Goal:** Display products as interactive cards with images, details, and add-to-cart functionality.

**Approach:** Protocol-compliant structured data exchange per A2A Section 9.8

---

## Phase 1: Backend - Structured Product Data (3-4 hours)

### Step 1.1: Verify DataPart Support (15 min)

**Goal:** Confirm A2A SDK supports DataPart

**Actions:**
```bash
cd backend
python3 -c "from a2a.types import DataPart, Part; print('DataPart available:', DataPart)"
```

**Expected Result:** Successfully imports DataPart

**If fails:** Fall back to text parsing approach

---

### Step 1.2: Update Product Tools to Return Full Details (30 min)

**File:** `backend/app/product_discovery_agent/tools.py`

**Changes:**
- Update `text_vector_search()` to return full product objects
- Include: id, name, description, picture, product_image_url, price
- Ensure image URLs are absolute/full paths

**Code:**
```python
def text_vector_search(query: str) -> List[Dict[str, Any]]:
    # ... existing code ...
    for row in result:
        out.append({
            "id": row[0],
            "name": row[1],
            "description": row[2],  # Add this
            "picture": row[3],
            "product_image_url": row[4],
            "price": 0.0,  # Or fetch from database
            "distance": float(row[5]),
        })
    return out
```

---

### Step 1.3: Modify Executor to Return Structured Data (2 hours)

**File:** `backend/app/a2a_executor.py`

**Changes:**
1. Import DataPart and Part types
2. Detect when response contains products
3. Create two artifacts: text response + product data
4. Use DataPart for product data with schema

**Key Implementation:**
```python
from a2a.types import Part, TextPart, DataPart

# After getting response from ADK agent
if contains_products(response_text):
    products = extract_products_from_response(response_text)
    
    # Text artifact
    await updater.add_artifact(
        [Part(root=TextPart(text=response_text))],
        name="response"
    )
    
    # Product data artifact
    product_data = {
        "type": "product_list",
        "products": format_products(products)
    }
    
    await updater.add_artifact(
        [Part(root=DataPart(
            data=product_data,
            mimeType="application/json"
        ))],
        name="products"
    )
```

**Testing:**
- Test with sample queries
- Verify artifacts are created correctly
- Check JSON serialization

---

### Step 1.4: Test Backend Response (30 min)

**Goal:** Verify backend returns correct A2A structure

**Test Queries:**
- "Find me running shoes"
- "Show me blue t-shirts"
- "What kitchen appliances do you have?"

**Expected Response:**
```json
{
  "artifacts": [
    {
      "name": "response",
      "parts": [{"kind": "text", "text": "..."}]
    },
    {
      "name": "products",
      "parts": [{"kind": "data", "data": {...}}]
    }
  ]
}
```

---

## Phase 2: Frontend - Parse and Display Products (4-5 hours)

### Step 2.1: Add TypeScript Types (15 min)

**File:** `frontend/src/types/index.ts`

**Add:**
```typescript
export interface Product {
  id: string;
  name: string;
  image_url: string;
  description: string;
  price?: number;
}

export interface ProductListData {
  type: "product_list";
  products: Product[];
}

export interface A2AArtifact {
  artifactId?: string;
  name: string;
  parts: A2APart[];
}

export interface A2APart {
  kind: "text" | "data" | "file";
  text?: string;
  data?: any;
}
```

---

### Step 2.2: Create ProductCard Component (1 hour)

**File:** `frontend/src/components/ProductCard.tsx` (NEW)

**Features:**
- Display product image
- Show product name
- Display price (if available)
- Add to cart button
- Click to view details

**Props:**
```typescript
interface ProductCardProps {
  product: Product;
  onAddToCart: (productId: string) => void;
  onViewDetails: (productId: string) => void;
}
```

**Styling:**
- Card layout with hover effects
- Responsive grid
- Loading states

---

### Step 2.3: Create ProductGrid Component (30 min)

**File:** `frontend/src/components/ProductGrid.tsx` (NEW)

**Features:**
- Render multiple ProductCard components
- Grid layout (responsive)
- Empty state handling

**Props:**
```typescript
interface ProductGridProps {
  products: Product[];
  onAddToCart: (productId: string) => void;
  onViewDetails: (productId: string) => void;
}
```

---

### Step 2.4: Add Parser Function (30 min)

**File:** `frontend/src/lib/a2a-parser.ts` (NEW)

**Function:**
```typescript
export function parseA2AResponse(response: any): {
  text: string;
  products: Product[];
} {
  let text = '';
  const products: Product[] = [];
  
  for (const artifact of response.artifacts || []) {
    for (const part of artifact.parts || []) {
      if (part.kind === 'text') {
        text += part.text + '\n';
      }
      
      if (part.kind === 'data' && artifact.name === 'products') {
        const data = part.data as ProductListData;
        if (data.type === 'product_list' && Array.isArray(data.products)) {
          products.push(...data.products);
        }
      }
    }
  }
  
  return { text: text.trim(), products };
}
```

---

### Step 2.5: Update Chatbox Component (1.5 hours)

**File:** `frontend/src/components/Chatbox.tsx`

**Changes:**
1. Import parser and components
2. Parse response to extract text and products
3. Render text message
4. Render ProductGrid when products exist
5. Handle add to cart action

**Code:**
```typescript
import { parseA2AResponse } from '@/lib/a2a-parser';
import ProductGrid from './ProductGrid';

// In handleSend function:
const response = await shoppingAPI.sendMessage(userMessage);
const { text, products } = parseA2AResponse(response);

addMessage('assistant', text);

if (products.length > 0) {
  // Render products below the text message
  // Store products in state for rendering
}
```

---

### Step 2.6: Add Product Card Styles (30 min)

**File:** `frontend/src/app/globals.css`

**Add:**
```css
.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
  margin: 1rem 0;
}

.product-card {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 1rem;
  transition: transform 0.2s;
  cursor: pointer;
}

.product-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.product-card img {
  width: 100%;
  height: 200px;
  object-fit: cover;
  border-radius: 4px;
  margin-bottom: 0.5rem;
}
```

---

## Phase 3: Integration and Testing (2-3 hours)

### Step 3.1: End-to-End Testing (1 hour)

**Test Cases:**
1. ✅ Send query "Find me running shoes"
2. ✅ Verify products display as cards
3. ✅ Check product images load
4. ✅ Test add to cart functionality
5. ✅ Test mobile responsiveness
6. ✅ Test empty state (no products found)

**Tools:**
- Browser DevTools for network inspection
- React DevTools for component inspection
- Test queries covering various product types

---

### Step 3.2: Error Handling (30 min)

**Scenarios to Handle:**
- No products found
- Missing product data
- Image load failures
- Network errors
- Invalid data format

**Add:**
- Loading skeletons
- Error messages
- Fallback text display

---

### Step 3.3: Polish and Refine (1 hour)

**Enhancements:**
- Add product detail modal
- Implement quick add to cart from card
- Add product price display
- Improve card layout and spacing
- Add animations/transitions
- Optimize image loading

---

## Phase 4: Cart Integration (Optional - 2 hours)

### Step 4.1: Connect to Cart Agent

**Actions:**
- When user clicks "Add to Cart", send message to cart agent
- Update UI to show cart status
- Sync cart count in header

---

### Step 4.2: Product Detail View

**Features:**
- Click product card to see full details
- Modal or full page view
- Related products
- Add to cart from detail view

---

## Implementation Order

### Sprint 1 (MVP - 4-5 hours)
1. ✅ Step 1.2: Update product tools
2. ✅ Step 1.3: Modify executor to return DataPart
3. ✅ Step 1.4: Test backend response
4. ✅ Step 2.1: Add TypeScript types
5. ✅ Step 2.4: Add parser function
6. ✅ Step 2.5: Update Chatbox (basic rendering)

**Deliverable:** Products display as simple cards

### Sprint 2 (Enhancement - 2-3 hours)
1. ✅ Step 2.2: Create ProductCard component
2. ✅ Step 2.3: Create ProductGrid component
3. ✅ Step 2.6: Add styles
4. ✅ Step 3.1: End-to-end testing

**Deliverable:** Polished product cards with styling

### Sprint 3 (Polish - 1-2 hours)
1. ✅ Step 3.2: Error handling
2. ✅ Step 3.3: Polish and refine

**Deliverable:** Production-ready product display

---

## Testing Checklist

- [ ] Backend returns DataPart with products
- [ ] Frontend parses DataPart correctly
- [ ] Products display as cards
- [ ] Images load correctly
- [ ] Cards are clickable
- [ ] Add to cart works
- [ ] Mobile responsive
- [ ] Error states handled
- [ ] Loading states shown
- [ ] No console errors

---

## Success Criteria

**MVP:**
- Products show as cards with images
- Cards are clickable
- Add to cart button works

**Complete:**
- All MVP features plus:
- Product detail view
- Smooth animations
- Error handling
- Mobile optimized
- Fast image loading

---

## Rollback Plan

If DataPart is not supported:
1. Fall back to text parsing approach
2. Parse product names and IDs from text
3. Fetch product details separately
4. Render cards from fetched data

---

## Next Actions

**Immediate (Next 30 min):**
1. Verify DataPart support in backend
2. Start Step 1.2: Update product tools

**Today (Next 4 hours):**
1. Complete Phase 1 (Backend)
2. Start Phase 2 (Frontend parser)

**This Week:**
1. Complete all phases
2. Deploy and test
3. Gather user feedback

