# Phase 2.4: Add Streaming Support - Detailed Plan

## Overview

Transform the current synchronous integration to support real-time streaming, enabling incremental text updates, progressive artifact rendering (products/cart), and better user experience with immediate feedback.

## Current State Analysis

### Backend (`backend/app/a2a_executor.py`)
- ✅ Uses `runner.run_async()` which yields events incrementally
- ❌ Currently waits for `is_final_response()` before processing
- ❌ Accumulates all text before sending artifacts
- ❌ Sends all artifacts at once after completion

### Frontend (`frontend/src/lib/shopping-api.ts`)
- ✅ Already has `sendMessageStream()` method implemented
- ❌ Currently unused by Chatbox component
- ✅ Uses A2A SDK async generator pattern

### Frontend (`frontend/src/components/Chatbox.tsx`)
- ❌ Uses synchronous `sendMessage()` method
- ❌ Waits for complete response before displaying
- ✅ Has loading state management
- ✅ Supports artifact display (products, cart)

---

## Phase 2.4.1: Backend - Stream Events from ADK Runner

### Goal
Modify the executor to emit events as they arrive from the ADK runner, enabling real-time streaming.

### Changes to `backend/app/a2a_executor.py`

**Current Flow:**
```python
# Wait for final response
async for event in self.runner.run_async(...):
    if event.is_final_response():
        # Accumulate text
        response_text += part.text
# After loop, send all artifacts
```

**New Flow:**
```python
# Stream events as they arrive
async for event in self.runner.run_async(...):
    if event.content and event.content.parts:
        # Stream text chunks immediately
        for part in event.content.parts:
            if hasattr(part, 'text') and part.text:
                await updater.add_artifact([...], incremental=True)
    
    # Stream status updates
    if event.status:
        await updater.update_status(...)
    
    # Stream artifacts as they become available
    if event.artifacts:
        await updater.add_artifact([...], incremental=True)
```

### Implementation Steps

1. **Extract Text Incrementally**
   - Instead of accumulating `response_text`, send text parts as they arrive via `updater.add_artifact()`
   - Use incremental artifact updates for text chunks

2. **Stream Session State Updates**
   - Periodically check session state during execution
   - When `current_results` appears, send products artifact immediately
   - When cart state updates, send cart artifact immediately

3. **Handle ADK Events**
   - Process `streaming` events (partial responses)
   - Process `function_call` events (tool invocations)
   - Process `status` events (agent state changes)
   - Process `final_response` events (completion)

4. **Error Handling**
   - Stream error messages if they occur mid-execution
   - Maintain task state throughout

### Code Structure

```python
async def execute(self, context, event_queue):
    # ... setup code ...
    
    # Track accumulated text for final response
    accumulated_text = ''
    products_sent = False
    cart_sent = False
    
    async for event in self.runner.run_async(...):
        # Handle text streaming
        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    accumulated_text += part.text
                    # Stream incremental text updates
                    await updater.add_artifact(
                        [Part(root=TextPart(text=part.text))],
                        name=self.artifact_name,
                        incremental=True
                    )
        
        # Check for state updates (products, cart)
        if not event.is_final_response():
            # Periodically check session state
            session = await self.runner.session_service.get_session(...)
            session_state = session.state if hasattr(session, 'state') else {}
            
            # Stream products if available
            if not products_sent and "current_results" in session_state:
                products = format_products(session_state["current_results"])
                if products:
                    await updater.add_artifact([...], name="products", incremental=True)
                    products_sent = True
            
            # Stream cart if available
            if not cart_sent and ("cart" in session_state or "cart_items" in session_state):
                cart = format_cart(session_state)
                if cart:
                    await updater.add_artifact([...], name="cart", incremental=True)
                    cart_sent = True
        
        # Handle final response
        if event.is_final_response():
            # Ensure all artifacts are sent
            # Complete the task
            await updater.complete()
```

---

## Phase 2.4.2: Frontend - Parse Streaming Events

### Goal
Create a streaming event parser that handles incremental updates from A2A protocol.

### Changes to `frontend/src/lib/a2a-parser.ts`

**New Function:**
```typescript
export interface StreamingEvent {
  type: 'text' | 'products' | 'cart' | 'status' | 'complete';
  data: any;
  isIncremental: boolean;
}

/**
 * Parse streaming A2A events incrementally
 */
export function parseStreamingEvent(event: any): StreamingEvent | null {
  // Handle task events
  if (event.kind === 'task') {
    return { type: 'status', data: { taskId: event.id }, isIncremental: true };
  }
  
  // Handle status updates
  if (event.kind === 'status-update') {
    return { 
      type: 'status', 
      data: { state: event.status.state, message: event.status.message },
      isIncremental: true 
    };
  }
  
  // Handle artifact updates
  if (event.kind === 'artifact-update') {
    const artifact = event.artifact;
    const parts = artifact.parts || artifact.output?.parts || [];
    
    for (const part of parts) {
      // Text artifact
      if (part.kind === 'text' || part.text) {
        return {
          type: 'text',
          data: { text: part.text || '' },
          isIncremental: artifact.incremental || false
        };
      }
      
      // Products artifact
      if (part.kind === 'data' && artifact.name === 'products') {
        try {
          const data = part.data as ProductListData;
          if (data?.type === 'product_list' && Array.isArray(data.products)) {
            return {
              type: 'products',
              data: { products: data.products.map(formatProduct) },
              isIncremental: artifact.incremental || false
            };
          }
        } catch (error) {
          console.error('Error parsing product data:', error);
        }
      }
      
      // Cart artifact
      if (part.kind === 'data' && artifact.name === 'cart') {
        try {
          const data = part.data as CartData;
          if (data?.type === 'cart' && Array.isArray(data.items)) {
            return {
              type: 'cart',
              data: { 
                items: data.items.map(formatCartItem),
                total_items: data.total_items || 0,
                subtotal: data.subtotal || 0
              },
              isIncremental: artifact.incremental || false
            };
          }
        } catch (error) {
          console.error('Error parsing cart data:', error);
        }
      }
    }
  }
  
  return null;
}
```

### Helper Function for Accumulating Text

```typescript
/**
 * Accumulate streaming text chunks
 */
export function accumulateText(currentText: string, newChunk: string): string {
  return currentText + newChunk;
}
```

---

## Phase 2.4.3: Frontend - Update Chatbox for Streaming

### Goal
Modify Chatbox component to handle streaming events and update UI incrementally.

### Changes to `frontend/src/components/Chatbox.tsx`

**New State Management:**
```typescript
const [streamingMessage, setStreamingMessage] = useState<{
  text: string;
  products?: Product[];
  cart?: CartItem[];
} | null>(null);
```

**Updated handleSend Function:**
```typescript
const handleSend = async (e: React.FormEvent) => {
  e.preventDefault();
  
  if (!input.trim() || isLoading || !isInitialized) return;

  const userMessage = input.trim();
  setInput('');
  addMessage('user', userMessage);
  setLoadingMessage(getContextualLoadingMessage(userMessage));
  setIsLoading(true);
  
  // Initialize streaming message
  setStreamingMessage({ text: '' });
  
  // Create placeholder assistant message
  const assistantMessageIndex = messages.length + 1;

  try {
    // Use streaming method
    for await (const event of shoppingAPI.sendMessageStream(userMessage)) {
      const parsedEvent = parseStreamingEvent(event);
      
      if (!parsedEvent) continue;
      
      switch (parsedEvent.type) {
        case 'text':
          // Accumulate text incrementally
          setStreamingMessage(prev => ({
            ...prev!,
            text: (prev?.text || '') + parsedEvent.data.text
          }));
          
          // Update message in real-time
          setMessages(prev => {
            const updated = [...prev];
            if (updated[assistantMessageIndex]) {
              updated[assistantMessageIndex].content = streamingMessage.text + parsedEvent.data.text;
            } else {
              updated.push({
                role: 'assistant',
                content: streamingMessage.text + parsedEvent.data.text,
                timestamp: new Date()
              });
            }
            return updated;
          });
          break;
          
        case 'products':
          // Update products immediately
          setStreamingMessage(prev => ({
            ...prev!,
            products: parsedEvent.data.products
          }));
          
          setMessages(prev => {
            const updated = [...prev];
            if (updated[assistantMessageIndex]) {
              updated[assistantMessageIndex].products = parsedEvent.data.products;
            }
            return updated;
          });
          break;
          
        case 'cart':
          // Update cart immediately
          setStreamingMessage(prev => ({
            ...prev!,
            cart: parsedEvent.data.items
          }));
          
          setMessages(prev => {
            const updated = [...prev];
            if (updated[assistantMessageIndex]) {
              updated[assistantMessageIndex].cart = parsedEvent.data.items;
            }
            return updated;
          });
          break;
          
        case 'status':
          // Update loading message if needed
          if (parsedEvent.data.message) {
            setLoadingMessage(parsedEvent.data.message);
          }
          break;
          
        case 'complete':
          // Finalize message
          setIsLoading(false);
          setStreamingMessage(null);
          break;
      }
    }
  } catch (error) {
    console.error('Error in streaming:', error);
    addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
    setIsLoading(false);
    setStreamingMessage(null);
  }
};
```

**Optimized Rendering:**
- Render streaming text immediately as it arrives
- Show products as soon as they're available (before text completes)
- Display cart updates in real-time
- Hide loading indicator when streaming completes

---

## Phase 2.4.4: Backend - Optimize State Checking

### Goal
Reduce overhead of checking session state during streaming by implementing smart polling.

### Strategy

**Option 1: Event-based State Updates**
- Modify ADK tools to emit state change events
- Subscribe to state changes in executor
- Stream artifacts only when state actually changes

**Option 2: Debounced State Checking**
```python
last_state_check = 0
STATE_CHECK_INTERVAL = 0.5  # Check every 500ms

async for event in self.runner.run_async(...):
    current_time = time.time()
    
    if current_time - last_state_check > STATE_CHECK_INTERVAL:
        # Check session state
        session = await self.runner.session_service.get_session(...)
        # Stream if changed
        last_state_check = current_time
```

**Option 3: Tool Call Hooks**
- Detect when product discovery tools are called
- Stream products immediately after tool execution
- Detect when cart tools are called
- Stream cart updates immediately

**Recommended:** Option 3 (most efficient)

---

## Phase 2.4.5: Error Handling & Edge Cases

### Error Scenarios

1. **Stream Interruption**
   - Handle network disconnections gracefully
   - Show partial results if available
   - Allow retry mechanism

2. **Incomplete Artifacts**
   - Handle partial product data
   - Validate artifact structure before rendering
   - Fallback to accumulated text if artifacts fail

3. **Race Conditions**
   - Ensure message ordering
   - Handle concurrent updates to same message
   - Prevent duplicate artifact rendering

### Implementation

```typescript
// Error handling wrapper
try {
  for await (const event of stream) {
    try {
      await processStreamingEvent(event);
    } catch (eventError) {
      console.error('Error processing event:', eventError);
      // Continue processing other events
    }
  }
} catch (streamError) {
  // Handle stream-level errors
  if (streamingMessage) {
    // Save partial results
    finalizeMessage(streamingMessage);
  }
}
```

---

## Phase 2.4.6: Testing Strategy

### Unit Tests

1. **Backend Executor**
   - Test incremental text streaming
   - Test artifact streaming timing
   - Test state checking logic
   - Test error scenarios

2. **Frontend Parser**
   - Test event parsing for each event type
   - Test text accumulation
   - Test artifact extraction

3. **Frontend Chatbox**
   - Test streaming text updates
   - Test product rendering during stream
   - Test cart updates during stream
   - Test error recovery

### Integration Tests

1. **End-to-End Streaming**
   - Search for products → verify streaming text → verify products appear
   - Add to cart → verify streaming → verify cart updates
   - Mixed operations → verify correct ordering

2. **Performance Tests**
   - Measure time to first text chunk
   - Measure time to product display
   - Compare with synchronous flow

---

## Implementation Order

1. **Phase 2.4.1**: Backend streaming (foundation)
2. **Phase 2.4.2**: Frontend parser (abstraction layer)
3. **Phase 2.4.3**: Frontend Chatbox integration (UI)
4. **Phase 2.4.4**: Backend optimization (performance)
5. **Phase 2.4.5**: Error handling (robustness)
6. **Phase 2.4.6**: Testing (quality assurance)

---

## Success Criteria

✅ **Backend**
- Text streams incrementally as it's generated
- Products artifact sent as soon as available
- Cart artifact sent immediately after updates
- No performance degradation vs synchronous flow

✅ **Frontend**
- Text appears character-by-character or chunk-by-chunk
- Products render before text completes
- Cart updates appear in real-time
- Loading indicator disappears when streaming completes
- UI remains responsive during streaming

✅ **User Experience**
- Faster perceived response time
- Better feedback during long operations
- Progressive disclosure of information
- Smooth, non-jarring updates

---

## Backwards Compatibility

**Option A: Feature Flag**
- Keep synchronous `sendMessage()` as default
- Add flag to enable streaming: `sendMessageStream()`
- Gradual migration path

**Option B: Full Migration**
- Replace `sendMessage()` with streaming internally
- Make streaming the default behavior
- Simpler codebase, but requires thorough testing

**Recommended:** Option A for initial release, Option B for future

---

## Performance Considerations

1. **Debouncing Updates**
   - Don't update UI on every single character
   - Batch text updates (e.g., every 50-100ms)
   - Use React's `useDeferredValue` for non-critical updates

2. **Memory Management**
   - Clear streaming state after completion
   - Limit accumulated text size
   - Clean up event listeners

3. **Network Optimization**
   - Minimize event payload size
   - Use compression if needed
   - Handle slow connections gracefully

---

## Future Enhancements

1. **Progressive Artifact Updates**
   - Stream partial product lists
   - Update product cards as they're discovered
   - Show "Loading more..." indicators

2. **Streaming Analytics**
   - Track time to first byte
   - Measure streaming performance
   - A/B test synchronous vs streaming

3. **Advanced Features**
   - Cancel streaming requests
   - Pause/resume streaming
   - Stream history replay
