# Plan: Convert Landing Page to Client Component

## Overview
Convert `frontend/src/app/page.tsx` from a Server Component to a Client Component to ensure environment variables are correctly read at runtime and resolve the product loading issue.

## Current State Analysis

### Current Implementation (Server Component)
- **File**: `frontend/src/app/page.tsx`
- **Type**: Server Component (async function)
- **Data Fetching**: Uses `await` with `shoppingAPI.getProducts()` at server render time
- **Issues**:
  - Environment variables (`NEXT_PUBLIC_API_BASE_URL`) may not be available at server render time
  - Empty string fallback causes default to `http://localhost:8080`
  - No loading state (blocking render)
  - Error handling only logs to console

### Related Components
- `Chatbox.tsx`: Example of Client Component with `useState`, `useEffect`, loading states
- `ProductImage.tsx`: Client Component with error handling
- `ProductList.tsx`: Client Component for displaying products (alternative pattern)

## Conversion Plan

### Step 1: Add Client Component Directive
**File**: `frontend/src/app/page.tsx`
- Add `'use client'` directive at the top of the file
- This marks the component as a Client Component

### Step 2: Replace Async Function with React Hooks
**Changes**:
- Remove `async` from the component function
- Replace `async function getProducts()` with:
  - `useState` for products (initial: empty array)
  - `useState` for loading state (initial: `true`)
  - `useState` for error state (initial: `null`)
  - `useEffect` to fetch products on mount

### Step 3: Implement Data Fetching Hook
**Pattern** (similar to Chatbox.tsx):
```typescript
useEffect(() => {
  const fetchProducts = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const products = await shoppingAPI.getProducts();
      setProducts(products);
    } catch (err) {
      console.error('Failed to fetch products:', err);
      setError(err instanceof Error ? err.message : 'Failed to load products');
      setProducts([]); // Fallback to empty array
    } finally {
      setIsLoading(false);
    }
  };
  
  fetchProducts();
}, []); // Empty dependency array = run once on mount
```

### Step 4: Add Loading State UI
**Implementation**:
- Show loading spinner/skeleton while `isLoading === true`
- Placeholder text: "Loading products..."
- Use similar pattern to Chatbox loading states

### Step 5: Add Error State UI
**Implementation**:
- Display error message if `error !== null`
- User-friendly error message
- Optionally: Retry button to refetch products
- Fallback to empty state if error occurs

### Step 6: Update Imports
**Add**:
- `useState` from 'react'
- `useEffect` from 'react'
- (Optional) Loading spinner component if exists

### Step 7: Handle Empty State
**Keep**:
- Existing empty state UI (`products.length === 0`)
- Update condition to handle loading state: `!isLoading && products.length === 0`

## Implementation Details

### State Management
```typescript
const [products, setProducts] = useState<Product[]>([]);
const [isLoading, setIsLoading] = useState<boolean>(true);
const [error, setError] = useState<string | null>(null);
```

### Component Structure
```typescript
export default function Home() {
  // State declarations
  // useEffect for data fetching
  
  return (
    <div className="min-h-screen flex flex-col layout-with-chatbox">
      <Header />
      <main className="flex-1 main-content">
        <section>
          {/* Landing message */}
          
          {/* Loading state */}
          {isLoading && <LoadingIndicator />}
          
          {/* Error state */}
          {error && !isLoading && <ErrorDisplay error={error} />}
          
          {/* Empty state */}
          {!isLoading && !error && products.length === 0 && (
            <EmptyState />
          )}
          
          {/* Products grid */}
          {!isLoading && !error && products.length > 0 && (
            <ProductsGrid products={products} />
          )}
        </section>
      </main>
      <Footer />
      <Chatbox />
    </div>
  );
}
```

### Benefits of Client Component
1. **Runtime Environment Variables**: Reads `process.env.NEXT_PUBLIC_API_BASE_URL` at runtime (client-side)
2. **Better Error Handling**: User-visible error messages and retry capability
3. **Loading States**: Better UX with loading indicators
4. **Flexibility**: Can add features like refresh, pull-to-refresh, etc.
5. **Debugging**: Easier to debug in browser DevTools

### Potential Considerations
1. **SEO Impact**: Server Components provide better SEO (initial HTML contains products)
   - **Mitigation**: Consider adding a loading skeleton in initial HTML
   - **Alternative**: Keep as Server Component but fix environment variable issue (already addressed)
2. **Performance**: Client-side fetch adds a network request on page load
   - **Mitigation**: Consider caching or ISR (Incremental Static Regeneration)
3. **Hydration**: Ensure no hydration mismatches between server and client

## Testing Checklist

### Functional Testing
- [ ] Products load correctly on initial page load
- [ ] Loading state displays while fetching
- [ ] Error state displays if API fails
- [ ] Empty state displays if no products
- [ ] Products display correctly after loading
- [ ] Error handling works (simulate API failure)
- [ ] Environment variables read correctly at runtime

### Edge Cases
- [ ] Handles slow network connections
- [ ] Handles API timeout
- [ ] Handles empty API response
- [ ] Handles malformed API response
- [ ] Handles network errors

### Browser Testing
- [ ] Works in Chrome
- [ ] Works in Firefox
- [ ] Works in Safari
- [ ] Works on mobile browsers

## Rollback Plan
If issues arise:
1. Revert to Server Component (remove `'use client'`, restore async function)
2. Ensure environment variables are set correctly in Cloud Run
3. Verify build-time args are passed correctly

## Alternative Approach (If Needed)
If Client Component causes issues, consider:
- **Hybrid Approach**: Keep Server Component but create a Client Component wrapper
- **Server Actions**: Use Next.js Server Actions for data fetching
- **API Route**: Create an API route that handles the fetch server-side

## Files to Modify
1. `frontend/src/app/page.tsx` - Main conversion

## Files to Review (No Changes Needed)
1. `frontend/src/lib/shopping-api.ts` - Already works client-side
2. `frontend/src/components/Header.tsx` - No changes
3. `frontend/src/components/Footer.tsx` - No changes
4. `frontend/src/components/Chatbox.tsx` - Reference implementation
5. `frontend/src/components/ProductImage.tsx` - Already client component

## Estimated Time
- **Implementation**: 30-45 minutes
- **Testing**: 15-30 minutes
- **Total**: ~1 hour

## Success Criteria
- ✅ Products load correctly on Cloud Run deployment
- ✅ Loading state displays appropriately
- ✅ Error handling works correctly
- ✅ No console errors
- ✅ Environment variables read correctly at runtime
- ✅ UI matches current design

