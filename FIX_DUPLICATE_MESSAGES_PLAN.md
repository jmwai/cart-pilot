# Fix Duplicate Messages in Chatbox

## Problem Analysis

The chatbox is showing duplicate messages because of several issues in the message state management:

### Root Causes:

1. **Race Condition with `assistantMessageIndex`**:
   - `assistantMessageIndex` is a local variable that gets reset for each request
   - Multiple streaming events can arrive before the index is properly set
   - When `assistantMessageIndex === -1`, each event creates a new message, causing duplicates

2. **State Closure Issues**:
   - Multiple `setMessages` calls happening in quick succession can see stale state
   - The closure captures the initial `assistantMessageIndex` value (-1) for all events
   - React state updates are asynchronous, so rapid events can all see the same initial state

3. **No Message Deduplication**:
   - Messages don't have unique IDs
   - Can't identify and remove duplicate messages

4. **Multiple Message Creation Paths**:
   - Text events can create messages
   - Product/cart/order events can also create messages
   - If these arrive before `assistantMessageIndex` is set, multiple messages are created

## Solution Plan

### Phase 1: Use React Ref for Message Index Tracking
- Replace local `assistantMessageIndex` variable with `useRef`
- Ref persists across renders and provides immediate access to current value
- Ensures all streaming events see the same index value

### Phase 2: Add Message IDs for Deduplication
- Add unique `id` field to each message
- Use UUID or timestamp-based ID
- Track message IDs to prevent duplicates

### Phase 3: Improve State Update Logic
- Use functional setState to always work with latest state
- Ensure only one assistant message is created per request
- Set the index immediately when creating the message

### Phase 4: Add Message Deduplication Check
- Before adding a message, check if one with same ID already exists
- Prevent duplicate messages from being added

## Implementation Steps

### Step 1: Update Message Type
```typescript
interface MessageWithArtifacts extends ChatMessage {
  id: string; // Add unique ID
  products?: Product[];
  cart?: CartItem[];
  order?: Order;
}
```

### Step 2: Use Ref for Assistant Message Index
```typescript
const assistantMessageIndexRef = useRef<number>(-1);
```

### Step 3: Update Message Creation Logic
- Check ref first before creating new message
- Set ref immediately when creating
- Use functional setState to ensure consistency

### Step 4: Add Deduplication Helper
```typescript
const ensureAssistantMessage = (messages: MessageWithArtifacts[]) => {
  if (assistantMessageIndexRef.current >= 0 && 
      messages[assistantMessageIndexRef.current]?.role === 'assistant') {
    return assistantMessageIndexRef.current;
  }
  // Create new message
  const newIndex = messages.length;
  assistantMessageIndexRef.current = newIndex;
  return newIndex;
};
```

### Step 5: Update All Streaming Event Handlers
- Use `ensureAssistantMessage` helper
- Always update existing message if index is valid
- Reset ref to -1 when starting new request

## Testing Checklist

- [ ] Send a message and verify only one assistant message appears
- [ ] Send rapid messages and verify no duplicates
- [ ] Verify streaming updates work correctly
- [ ] Verify products/cart/order artifacts appear in correct message
- [ ] Test with slow network to ensure no race conditions
- [ ] Test component remounting (doesn't duplicate messages)

## Files to Modify

1. `frontend/src/components/Chatbox.tsx`
   - Add message ID generation
   - Replace `assistantMessageIndex` with `useRef`
   - Add `ensureAssistantMessage` helper
   - Update all streaming event handlers
   - Reset ref when starting new request

2. `frontend/src/types/index.ts` (if needed)
   - Add `id` field to `ChatMessage` interface

