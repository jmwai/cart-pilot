# Fix Duplicate Messages and Raw JSON Display

## Problem Analysis

From the sample session messages, I can identify several issues:

### Issue 1: Multiple Artifacts Creating Multiple Messages
From the log:
1. **Line 5**: `products` artifact sent → Creates message
2. **Line 7**: `order` artifact sent → Creates duplicate message (shouldn't exist for add-to-cart operation)
3. **Line 9**: `cart` artifact sent → Creates duplicate message  
4. **Line 11**: `response` artifact with raw JSON text → Creates duplicate message AND shows raw JSON

**Root Cause**: Each artifact type (`products`, `cart`, `order`, `response`) triggers a separate message update/create in the frontend, even though they should all update the same assistant message.

### Issue 2: Raw JSON Displayed in Chat
**Line 11** shows:
```json
"text":"{\"items\": [{\"cart_item_id\": \"...\", ...}], \"total_items\": 1, \"subtotal\": 6.0, \"message\": \"I've added 1 Running Shoes For Men  (Yellow) to your cart.\"}"
```

**Root Cause**: 
- The agent's `output_schema` (CartOutput) is being serialized as JSON and sent as text in the `response` artifact
- The parser treats this as a `text` event and displays it as-is
- The actual user-friendly message is inside the JSON (`message` field)

### Issue 3: Unexpected Order Artifact
**Line 7** shows an `order` artifact being sent during an "add to cart" operation, which shouldn't happen.

**Root Cause**: The executor is sending stale order data from `state["current_order"]` even when it's not relevant to the current operation.

## Solution Plan

### Phase 1: Fix Raw JSON Display

**Problem**: Response artifact contains JSON string instead of natural language.

**Solution**:
1. **Parser Enhancement**: Detect when text contains JSON that matches artifact structures
2. **Extract Message Field**: If JSON contains a `message` field, extract and use that instead
3. **Filter JSON Text**: If the JSON matches an artifact we've already processed, skip displaying it as text

**Implementation**:
- Update `parseStreamingEvent` in `a2a-parser.ts` to:
  - Detect JSON strings in text parts
  - Try to parse JSON
  - If JSON contains `message` field, extract it
  - If JSON matches artifact data structure, skip displaying as text (we already have the artifact)

### Phase 2: Prevent Duplicate Messages

**Problem**: Each artifact type creates/updates messages separately, causing duplicates.

**Solution**:
1. **Consolidate Artifact Updates**: All artifacts should update the same assistant message
2. **Fix ensureAssistantMessage Logic**: Ensure it works correctly across different artifact types
3. **Prevent Multiple Message Creation**: Only create assistant message once per request, then update it

**Implementation**:
- The `ensureAssistantMessage` helper should work correctly, but we need to ensure:
  - Artifacts don't trigger message creation if one already exists
  - Text events don't create new messages if artifacts already created one
  - The ref index persists correctly across all event types

### Phase 3: Fix Executor Artifact Sending Logic

**Problem**: Executor sends stale artifacts (like `order` during cart operations).

**Solution**:
1. **Context-Aware Artifact Sending**: Only send artifacts relevant to the current operation
2. **Filter Stale State**: Don't send order artifacts unless it's a checkout operation
3. **Smart Artifact Detection**: Determine which artifacts are relevant based on agent activity

**Implementation**:
- Update `a2a_executor.py` to:
  - Track which agent/sub-agent was active
  - Only send artifacts relevant to that agent's operation
  - Skip sending stale artifacts from previous operations

### Phase 4: Improve Response Text Handling

**Problem**: Agent output schemas are being serialized as JSON text.

**Solution**:
1. **Backend**: Extract `message` field from output schemas before sending as text
2. **Frontend**: Parse JSON in text artifacts and extract user-friendly messages
3. **Fallback**: If no message field, use natural language extraction or skip displaying

## Implementation Steps

### Step 1: Update Parser to Handle JSON Text
```typescript
// In parseStreamingEvent, when handling text artifacts:
if (part.kind === 'text' || part.text !== undefined) {
  let textValue = extractTextValue(part);
  
  // Check if text is JSON
  if (textValue.startsWith('{') || textValue.startsWith('[')) {
    try {
      const parsed = JSON.parse(textValue);
      // If it's artifact data we've already processed, skip it
      if (parsed.type === 'cart' || parsed.type === 'product_list' || parsed.type === 'order') {
        return null; // Skip - we already have this as an artifact
      }
      // If it has a message field, extract it
      if (parsed.message && typeof parsed.message === 'string') {
        textValue = parsed.message;
      }
    } catch {
      // Not valid JSON, use as-is
    }
  }
  
  return { type: 'text', data: { text: textValue }, ... };
}
```

### Step 2: Improve ensureAssistantMessage
- Ensure it correctly identifies existing assistant message
- Works across all artifact types
- Doesn't create duplicates

### Step 3: Update Executor Artifact Logic
- Only send products if Product Discovery Agent was active
- Only send cart if Cart Agent was active
- Only send order if Checkout Agent was active
- Don't send stale artifacts from previous operations

### Step 4: Filter Response Artifact JSON
- If response artifact name is "response" and contains JSON, parse it
- Extract message field if present
- Skip if JSON matches artifact data structures

## Testing Checklist

- [ ] Send "add to cart" - verify only ONE assistant message appears
- [ ] Verify no raw JSON displayed in chat
- [ ] Verify user-friendly message is shown (e.g., "I've added X to your cart")
- [ ] Verify products/cart artifacts appear correctly
- [ ] Verify no order artifact appears during cart operations
- [ ] Test with multiple rapid requests
- [ ] Verify artifacts update existing message, not create new ones

## Files to Modify

1. `frontend/src/lib/a2a-parser.ts`
   - Add JSON detection and parsing logic
   - Extract message field from JSON
   - Skip duplicate artifact data

2. `frontend/src/components/Chatbox.tsx`
   - Verify ensureAssistantMessage works correctly
   - Ensure artifacts don't create separate messages

3. `backend/app/a2a_executor.py`
   - Add context-aware artifact sending
   - Filter stale artifacts
   - Only send relevant artifacts per operation

