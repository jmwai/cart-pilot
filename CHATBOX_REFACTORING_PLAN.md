# Chatbox.tsx Refactoring Plan

## Current State Analysis

**File Size**: 1,301 lines
**Issues Identified**:
1. **Code Duplication**: `handleSend` and `handlePromptClick` share ~400 lines of duplicated streaming logic
2. **Duplicated Utilities**: `extractStatusMessage` appears twice (lines 196-238, 750-792)
3. **Mixed Concerns**: UI, state management, business logic, and event handling all in one component
4. **Large Component**: Too many responsibilities (message management, streaming, UI rendering, image handling)
5. **Complex State**: Multiple useState hooks managing related state
6. **Inline Logic**: Complex logic embedded in JSX (loading message extraction)

## Refactoring Strategy

Following Next.js 13+ App Router best practices:
- Extract custom hooks for reusable logic
- Create smaller, focused components
- Separate utilities into dedicated files
- Use TypeScript for type safety
- Maintain client-side rendering where needed

---

## Phase 1: Extract Types and Interfaces

### 1.1 Move Types to Types File
**File**: `frontend/src/types/chat.ts` (new file)

**Extract**:
- `MessageWithArtifacts` interface
- Streaming state types
- Event handler types

**Benefits**:
- Reusable types across components
- Better type organization
- Easier to maintain

---

## Phase 2: Extract Utility Functions

### 2.1 Message Utilities
**File**: `frontend/src/lib/utils/messageUtils.ts` (new file)

**Extract**:
- `createMessage()` - Message creation helper
- `ensureAssistantMessage()` - Assistant message management
- `updateMessageWithArtifacts()` - Message update helper

**Benefits**:
- Reusable message logic
- Easier to test
- Single source of truth

### 2.2 Status Message Utilities
**File**: `frontend/src/lib/utils/statusMessageUtils.ts` (new file)

**Extract**:
- `extractStatusMessage()` - Extract status from event data
- `getContextualLoadingMessage()` - Generate contextual loading messages

**Benefits**:
- Remove duplication
- Testable utilities
- Consistent status handling

### 2.3 Streaming Utilities
**File**: `frontend/src/lib/utils/streamingUtils.ts` (new file)

**Extract**:
- `createStreamingState()` - Initialize streaming state
- `processStreamingEvent()` - Process individual events
- `updateMessageFromStreamingState()` - Update message from state

**Benefits**:
- Centralized streaming logic
- Reusable across handlers
- Easier to maintain

---

## Phase 3: Extract Custom Hooks

### 3.1 useChatMessages Hook
**File**: `frontend/src/hooks/useChatMessages.ts` (new file)

**Responsibilities**:
- Message state management
- Message CRUD operations
- Assistant message tracking
- Auto-scroll functionality

**API**:
```typescript
const {
  messages,
  addMessage,
  updateMessage,
  clearMessages
} = useChatMessages();
```

**Benefits**:
- Encapsulated message logic
- Reusable across components
- Easier to test

### 3.2 useStreamingMessage Hook
**File**: `frontend/src/hooks/useStreamingMessage.ts` (new file)

**Responsibilities**:
- Handle message streaming
- Process A2A events
- Update messages incrementally
- Manage loading states

**API**:
```typescript
const {
  sendMessage,
  isLoading,
  loadingMessage,
  error
} = useStreamingMessage(messages, updateMessage);
```

**Benefits**:
- Removes duplication between handleSend and handlePromptClick
- Centralized streaming logic
- Better error handling

### 3.3 useMobileDetection Hook
**File**: `frontend/src/hooks/useMobileDetection.ts` (new file)

**Responsibilities**:
- Detect mobile/desktop
- Handle window resize
- Manage responsive state

**API**:
```typescript
const { isMobile, isDesktop } = useMobileDetection();
```

**Benefits**:
- Reusable responsive logic
- Cleaner component code
- Better performance (debounced resize)

### 3.4 useChatInitialization Hook
**File**: `frontend/src/hooks/useChatInitialization.ts` (new file)

**Responsibilities**:
- Initialize shopping API
- Handle initialization errors
- Set initial welcome message

**API**:
```typescript
const { isInitialized, error } = useChatInitialization();
```

**Benefits**:
- Separated initialization logic
- Better error handling
- Reusable initialization

### 3.5 useImageUpload Hook
**File**: `frontend/src/hooks/useImageUpload.ts` (new file)

**Responsibilities**:
- Image file selection
- File validation
- Image preview URL creation
- File size/type validation

**API**:
```typescript
const {
  selectedImage,
  imageUrl,
  handleImageSelect,
  clearImage
} = useImageUpload();
```

**Benefits**:
- Encapsulated image logic
- Reusable image handling
- Better validation

---

## Phase 4: Extract UI Components

### 4.1 ChatHeader Component
**File**: `frontend/src/components/chat/ChatHeader.tsx` (new file)

**Extract**: Lines 1056-1076
- Header with title
- Close button (mobile)
- Avatar/icon

**Props**:
```typescript
interface ChatHeaderProps {
  onClose?: () => void;
  showCloseButton?: boolean;
}
```

### 4.2 ChatMessages Component
**File**: `frontend/src/components/chat/ChatMessages.tsx` (new file)

**Extract**: Lines 1078-1242
- Messages list rendering
- Loading indicator
- Discovery prompts
- Auto-scroll ref

**Props**:
```typescript
interface ChatMessagesProps {
  messages: MessageWithArtifacts[];
  isLoading: boolean;
  loadingMessage: string;
  onPromptClick: (prompt: string) => void;
  messagesEndRef: RefObject<HTMLDivElement>;
}
```

### 4.3 MessageBubble Component
**File**: `frontend/src/components/chat/MessageBubble.tsx` (new file)

**Extract**: Lines 1083-1110
- Individual message rendering
- User/assistant styling
- Image display
- Timestamp

**Props**:
```typescript
interface MessageBubbleProps {
  message: MessageWithArtifacts;
}
```

### 4.4 MessageArtifacts Component
**File**: `frontend/src/components/chat/MessageArtifacts.tsx` (new file)

**Extract**: Lines 1112-1185
- Product list rendering
- Cart display
- Order summary
- Payment methods
- Order display

**Props**:
```typescript
interface MessageArtifactsProps {
  message: MessageWithArtifacts;
  onAddToCart: (productId: string, quantity?: number) => void;
  onUpdateQuantity: (cartItemId: string, quantity: number) => void;
  onRemoveFromCart: (cartItemId: string) => void;
  onSelectPaymentMethod: (paymentMethodId: string) => void;
}
```

### 4.5 ChatInput Component
**File**: `frontend/src/components/chat/ChatInput.tsx` (new file)

**Extract**: Lines 1244-1295
- Input form
- Image upload button
- Send button
- Image preview
- Input validation

**Props**:
```typescript
interface ChatInputProps {
  input: string;
  setInput: (value: string) => void;
  selectedImage: File | null;
  onImageSelect: (file: File | null) => void;
  onSubmit: (e: React.FormEvent) => void;
  isLoading: boolean;
  isInitialized: boolean;
  inputRef: RefObject<HTMLInputElement>;
  fileInputRef: RefObject<HTMLInputElement>;
}
```

### 4.6 LoadingIndicator Component
**File**: `frontend/src/components/chat/LoadingIndicator.tsx` (new file)

**Extract**: Lines 1206-1240
- Typing animation
- Loading message display
- Safe string rendering

**Props**:
```typescript
interface LoadingIndicatorProps {
  message: string;
}
```

### 4.7 DiscoveryPrompts Component
**File**: `frontend/src/components/chat/DiscoveryPrompts.tsx` (new file)

**Extract**: Lines 1188-1204
- Prompt suggestions
- Click handlers

**Props**:
```typescript
interface DiscoveryPromptsProps {
  prompts: string[];
  onPromptClick: (prompt: string) => void;
  isLoading: boolean;
}
```

### 4.8 ChatToggleButton Component
**File**: `frontend/src/components/chat/ChatToggleButton.tsx` (new file)

**Extract**: Lines 1031-1041
- Floating chat button (mobile)
- Open/close functionality

**Props**:
```typescript
interface ChatToggleButtonProps {
  onClick: () => void;
}
```

---

## Phase 5: Refactor Main Component

### 5.1 Simplified Chatbox Component
**File**: `frontend/src/components/Chatbox.tsx` (refactored)

**New Structure**:
```typescript
export default function Chatbox() {
  // Hooks
  const { isMobile } = useMobileDetection();
  const { isInitialized } = useChatInitialization();
  const { messages, addMessage, updateMessage } = useChatMessages();
  const { selectedImage, imageUrl, handleImageSelect, clearImage } = useImageUpload();
  const { sendMessage, isLoading, loadingMessage } = useStreamingMessage(messages, updateMessage);
  
  // Local state (minimal)
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  
  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  
  // Handlers (simplified)
  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() && !selectedImage) return;
    
    const userMessage = input.trim();
    addMessage('user', userMessage || 'Image search', undefined, undefined, undefined, undefined, imageUrl);
    
    await sendMessage(userMessage || undefined, selectedImage || undefined);
    
    setInput('');
    clearImage();
  };
  
  const handlePromptClick = async (prompt: string) => {
    await sendMessage(prompt);
  };
  
  // Render
  return (
    <>
      <ChatToggleButton onClick={() => setIsOpen(true)} />
      {isOpen && (
        <ChatPanel>
          <ChatHeader onClose={() => setIsOpen(false)} />
          <ChatMessages 
            messages={messages}
            isLoading={isLoading}
            loadingMessage={loadingMessage}
            onPromptClick={handlePromptClick}
            messagesEndRef={messagesEndRef}
          />
          <ChatInput
            input={input}
            setInput={setInput}
            selectedImage={selectedImage}
            onImageSelect={handleImageSelect}
            onSubmit={handleSend}
            isLoading={isLoading}
            isInitialized={isInitialized}
            inputRef={inputRef}
          />
        </ChatPanel>
      )}
    </>
  );
}
```

**Estimated Size**: ~150-200 lines (down from 1,301)

---

## File Structure After Refactoring

```
frontend/src/
├── components/
│   ├── chat/
│   │   ├── Chatbox.tsx (main component, ~200 lines)
│   │   ├── ChatHeader.tsx (~30 lines)
│   │   ├── ChatMessages.tsx (~80 lines)
│   │   ├── ChatInput.tsx (~80 lines)
│   │   ├── MessageBubble.tsx (~40 lines)
│   │   ├── MessageArtifacts.tsx (~100 lines)
│   │   ├── LoadingIndicator.tsx (~30 lines)
│   │   ├── DiscoveryPrompts.tsx (~30 lines)
│   │   └── ChatToggleButton.tsx (~20 lines)
│   └── [existing components]
├── hooks/
│   ├── useChatMessages.ts (~100 lines)
│   ├── useStreamingMessage.ts (~200 lines)
│   ├── useMobileDetection.ts (~40 lines)
│   ├── useChatInitialization.ts (~30 lines)
│   └── useImageUpload.ts (~60 lines)
├── lib/
│   └── utils/
│       ├── messageUtils.ts (~80 lines)
│       ├── statusMessageUtils.ts (~100 lines)
│       └── streamingUtils.ts (~150 lines)
└── types/
    └── chat.ts (~50 lines)
```

**Total**: ~1,300 lines (same as original, but better organized)

---

## Implementation Order

### Step 1: Extract Types and Utilities (Low Risk)
1. Create `types/chat.ts` with `MessageWithArtifacts`
2. Create `lib/utils/messageUtils.ts`
3. Create `lib/utils/statusMessageUtils.ts`
4. Create `lib/utils/streamingUtils.ts`
5. Update imports in `Chatbox.tsx`

**Testing**: Unit tests for utilities

### Step 2: Extract Custom Hooks (Medium Risk)
1. Create `hooks/useMobileDetection.ts`
2. Create `hooks/useChatInitialization.ts`
3. Create `hooks/useImageUpload.ts`
4. Create `hooks/useChatMessages.ts`
5. Create `hooks/useStreamingMessage.ts` (most complex)
6. Update `Chatbox.tsx` to use hooks

**Testing**: Hook tests, integration tests

### Step 3: Extract UI Components (Low Risk)
1. Create `components/chat/ChatToggleButton.tsx`
2. Create `components/chat/ChatHeader.tsx`
3. Create `components/chat/LoadingIndicator.tsx`
4. Create `components/chat/DiscoveryPrompts.tsx`
5. Create `components/chat/MessageBubble.tsx`
6. Create `components/chat/MessageArtifacts.tsx`
7. Create `components/chat/ChatMessages.tsx`
8. Create `components/chat/ChatInput.tsx`
9. Refactor `Chatbox.tsx` to use components

**Testing**: Component tests, visual regression

### Step 4: Final Cleanup
1. Remove unused code
2. Optimize imports
3. Add JSDoc comments
4. Update tests
5. Performance optimization

---

## Benefits of Refactoring

### Maintainability
- ✅ Single Responsibility Principle
- ✅ Easier to locate and fix bugs
- ✅ Clearer code organization
- ✅ Better code reusability

### Testability
- ✅ Unit test utilities independently
- ✅ Test hooks in isolation
- ✅ Test components separately
- ✅ Mock dependencies easily

### Performance
- ✅ Smaller component re-renders
- ✅ Memoization opportunities
- ✅ Code splitting potential
- ✅ Better React DevTools profiling

### Developer Experience
- ✅ Easier onboarding
- ✅ Faster feature development
- ✅ Better IDE autocomplete
- ✅ Clearer file structure

### Code Quality
- ✅ Reduced duplication (~400 lines)
- ✅ Better TypeScript types
- ✅ Consistent patterns
- ✅ Easier code reviews

---

## Migration Strategy

### Approach: Incremental Refactoring

1. **Phase 1**: Extract utilities (no breaking changes)
2. **Phase 2**: Extract hooks (minimal changes to Chatbox)
3. **Phase 3**: Extract components (gradual replacement)
4. **Phase 4**: Final cleanup and optimization

### Testing Strategy

1. **Unit Tests**: Utilities and hooks
2. **Integration Tests**: Component interactions
3. **E2E Tests**: Full chat flow
4. **Visual Tests**: UI regression testing

### Rollback Plan

- Keep original `Chatbox.tsx` as backup
- Use feature flags if needed
- Gradual migration allows partial rollback

---

## Risk Assessment

### Low Risk
- Type extraction
- Utility function extraction
- UI component extraction

### Medium Risk
- Hook extraction (state management changes)
- Message state refactoring

### High Risk
- Streaming logic refactoring (complex async flow)
- Message update logic (critical functionality)

### Mitigation
- Comprehensive testing at each phase
- Feature flags for gradual rollout
- Keep original code until fully tested
- Code review at each step

---

## Success Metrics

- ✅ Reduce `Chatbox.tsx` from 1,301 to ~200 lines
- ✅ Eliminate code duplication
- ✅ Improve test coverage
- ✅ Maintain all existing functionality
- ✅ No performance regression
- ✅ Better developer experience

---

## Next Steps

1. **Review Plan**: Get approval on refactoring approach
2. **Create Branch**: `refactor/chatbox-component`
3. **Phase 1**: Extract types and utilities
4. **Phase 2**: Extract hooks
5. **Phase 3**: Extract components
6. **Phase 4**: Final cleanup
7. **Testing**: Comprehensive test suite
8. **Merge**: After thorough testing

