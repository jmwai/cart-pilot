# Agent Executor Refactoring Plan

## Current State Analysis

The `agent_executor.py` file is **973 lines** long and handles multiple responsibilities:

1. **Message Parsing** (~240 lines): Extracting text and images from A2A messages with extensive defensive code
2. **Session Management** (~95 lines): Creating/retrieving sessions, managing state persistence
3. **Image Handling** (~335 lines): Complex image extraction, validation, and state persistence logic
4. **ADK Content Creation** (~70 lines): Converting A2A messages to ADK `Content` format
5. **Event Processing Loop** (~200 lines): Large async loop processing ADK events and streaming artifacts
6. **Artifact Formatting** (~65 lines): Helper functions for formatting products, cart, orders, order summaries
7. **Final Artifact Sending** (~80 lines): Duplicate logic ensuring artifacts are sent after execution
8. **State Tracking** (~20 lines): Tracking initial state for comparison

## Issues Identified

### 1. **Single Responsibility Violation**
   - The `execute()` method does too much (870+ lines)
   - Multiple concerns mixed together (parsing, session management, streaming, formatting)

### 2. **Code Duplication**
   - Artifact sending logic duplicated between event loop and final check
   - State comparison logic repeated for each artifact type
   - Image persistence logic duplicated in multiple places

### 3. **Excessive Debug Code**
   - ~150 lines of debug print/logging statements (lines 108-346, 477-582)
   - Should be removed or moved to debug mode

### 4. **Complex Nested Logic**
   - Deep nesting in message parsing (multiple try-except blocks)
   - Complex conditional logic in event processing loop
   - Hard to test individual components

### 5. **Tight Coupling**
   - All logic tightly coupled in one method
   - Hard to mock dependencies for testing
   - Difficult to reuse components

### 6. **State Management Complexity**
   - State tracking scattered throughout the method
   - Initial state capture mixed with execution logic
   - State comparison logic duplicated

## Refactoring Strategy

### Phase 1: Extract Helper Classes/Modules

#### 1.1 Create `MessageParser` Class
**File**: `backend/app/common/message_parser.py`

**Responsibilities**:
- Extract text and image data from A2A messages
- Handle multiple message formats defensively
- Validate image data (size, MIME type)

**Methods**:
```python
class MessageParser:
    def parse(self, context: RequestContext) -> ParsedMessage:
        """Extract text and image from A2A message."""
        pass
    
    def _extract_parts(self, message) -> List[Part]:
        """Extract parts from message using multiple strategies."""
        pass
    
    def _extract_text(self, part) -> Optional[str]:
        """Extract text from a part."""
        pass
    
    def _extract_image(self, part) -> Optional[ImageData]:
        """Extract and validate image from a part."""
        pass
```

**Benefits**:
- Isolates complex parsing logic
- Easier to test parsing independently
- Can remove debug code to separate debug module
- Reduces `execute()` method by ~240 lines

---

#### 1.2 Create `SessionManager` Class
**File**: `backend/app/common/session_manager.py`

**Responsibilities**:
- Create/retrieve sessions
- Manage session state (especially image persistence)
- Handle state updates and verification

**Methods**:
```python
class SessionManager:
    def __init__(self, runner: Runner, agent_name: str):
        pass
    
    async def get_or_create_session(
        self, 
        user_id: str, 
        session_id: str,
        initial_state: Optional[Dict] = None
    ) -> Session:
        """Get existing session or create new one."""
        pass
    
    async def update_session_state(
        self,
        session: Session,
        updates: Dict[str, Any]
    ) -> Session:
        """Update session state and verify persistence."""
        pass
    
    async def get_session_state(
        self,
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Get current session state."""
        pass
```

**Benefits**:
- Centralizes session management logic
- Simplifies image persistence handling
- Reduces `execute()` method by ~95 lines
- Easier to test session operations

---

#### 1.3 Create `ContentBuilder` Class
**File**: `backend/app/common/content_builder.py`

**Responsibilities**:
- Convert parsed messages to ADK `Content` format
- Handle multimodal content (text + images)
- Create appropriate `Part` objects

**Methods**:
```python
class ContentBuilder:
    def build(self, parsed_message: ParsedMessage) -> types.Content:
        """Build ADK Content from parsed message."""
        pass
    
    def _create_text_part(self, text: str) -> types.Part:
        """Create text part."""
        pass
    
    def _create_image_part(self, image_data: ImageData) -> Optional[types.Part]:
        """Create image part, handling multiple ADK formats."""
        pass
```

**Benefits**:
- Isolates ADK-specific content creation
- Handles ADK API variations in one place
- Reduces `execute()` method by ~70 lines

---

#### 1.4 Create `ArtifactFormatter` Class
**File**: `backend/app/common/artifact_formatter.py`

**Responsibilities**:
- Format session state data into A2A artifacts
- Handle different artifact types (products, cart, order, order_summary)

**Methods**:
```python
class ArtifactFormatter:
    def format_products(self, products_list: List[Dict]) -> Dict:
        """Format products for artifact."""
        pass
    
    def format_cart(self, cart_state: Dict) -> Optional[Dict]:
        """Format cart for artifact."""
        pass
    
    def format_order(self, order_state: Dict) -> Optional[Dict]:
        """Format order for artifact."""
        pass
    
    def format_order_summary(self, summary_state: Dict) -> Optional[Dict]:
        """Format order summary for artifact."""
        pass
```

**Benefits**:
- Centralizes formatting logic
- Easier to maintain artifact schemas
- Reduces `execute()` method by ~65 lines
- Can be reused by other components

---

#### 1.5 Create `StateTracker` Class
**File**: `backend/app/common/state_tracker.py`

**Responsibilities**:
- Track initial state for comparison
- Detect state changes
- Determine which artifacts need to be sent

**Methods**:
```python
class StateTracker:
    def __init__(self, initial_state: Dict[str, Any]):
        """Initialize with initial state snapshot."""
        pass
    
    def has_products_changed(self, current_state: Dict) -> bool:
        """Check if products changed."""
        pass
    
    def has_cart_changed(self, current_state: Dict) -> bool:
        """Check if cart changed."""
        pass
    
    def has_order_changed(self, current_state: Dict) -> bool:
        """Check if order changed."""
        pass
    
    def has_order_summary_changed(self, current_state: Dict) -> bool:
        """Check if order summary changed."""
        pass
```

**Benefits**:
- Centralizes state comparison logic
- Reduces duplication
- Makes change detection explicit and testable

---

#### 1.6 Create `ArtifactStreamer` Class
**File**: `backend/app/common/artifact_streamer.py`

**Responsibilities**:
- Stream artifacts to A2A event queue
- Track which artifacts have been sent
- Handle both incremental and final artifact sending

**Methods**:
```python
class ArtifactStreamer:
    def __init__(self, updater: TaskUpdater, formatter: ArtifactFormatter):
        pass
    
    async def stream_if_changed(
        self,
        artifact_type: str,
        current_state: Dict,
        tracker: StateTracker,
        sent_flags: Dict[str, bool]
    ) -> bool:
        """Stream artifact if state changed and not already sent."""
        pass
    
    async def ensure_all_sent(
        self,
        current_state: Dict,
        tracker: StateTracker,
        sent_flags: Dict[str, bool]
    ) -> None:
        """Ensure all artifacts are sent after execution."""
        pass
```

**Benefits**:
- Eliminates duplication between loop and final check
- Centralizes artifact sending logic
- Reduces `execute()` method by ~80 lines

---

#### 1.7 Create `StatusMessageHandler` Class
**File**: `backend/app/common/status_message_handler.py`

**Responsibilities**:
- Handle dynamic status messages based on tool calls
- Map function names to user-friendly messages
- Update task status via A2A protocol

**Methods**:
```python
class StatusMessageHandler:
    def __init__(self, status_messages: Dict[str, str]):
        pass
    
    async def handle_function_call(
        self,
        function_call,
        updater: TaskUpdater,
        task: Task,
        last_function_name: Optional[str]
    ) -> Optional[str]:
        """Handle function call and update status if needed."""
        pass
```

**Benefits**:
- Isolates status update logic
- Makes status message mapping configurable
- Easier to test status updates

---

### Phase 2: Refactor Main `execute()` Method

After extracting helper classes, the `execute()` method becomes much simpler:

```python
async def execute(
    self,
    context: RequestContext,
    event_queue: EventQueue,
) -> None:
    """Execute a task received via A2A protocol."""
    # 1. Parse message (extract text/image)
    parsed_message = self.message_parser.parse(context)
    
    # 2. Create/get session
    task = context.current_task or new_task(context.message)
    await event_queue.enqueue_event(task)
    updater = TaskUpdater(event_queue, task.id, task.context_id)
    
    user_id = self._extract_user_id(context)
    
    # 3. Initialize state tracking
    initial_state = await self.session_manager.get_session_state(
        user_id, task.context_id
    )
    tracker = StateTracker(initial_state)
    
    # 4. Get/create session with image state
    session = await self.session_manager.get_or_create_session(
        user_id=user_id,
        session_id=task.context_id,
        initial_state={"current_image_bytes": parsed_message.image_bytes} if parsed_message.image_bytes else None
    )
    
    # 5. Build ADK content
    content = self.content_builder.build(parsed_message)
    
    # 6. Process events and stream artifacts
    sent_flags = {"products": False, "cart": False, "order": False, "order_summary": False}
    
    async for event in self.runner.run_async(
        user_id=user_id, session_id=task.context_id, new_message=content
    ):
        # Stream text chunks
        await self._stream_text_chunks(event, updater)
        
        # Handle function calls and update status
        await self.status_handler.handle_function_call(
            event, updater, task, last_function_name
        )
        
        # Stream artifacts if state changed
        if not event.is_final_response():
            current_state = await self.session_manager.get_session_state(
                user_id, task.context_id
            )
            await self.artifact_streamer.stream_if_changed(
                "products", current_state, tracker, sent_flags
            )
            # ... similar for cart, order, order_summary
    
    # 7. Ensure all artifacts are sent
    final_state = await self.session_manager.get_session_state(
        user_id, task.context_id
    )
    await self.artifact_streamer.ensure_all_sent(
        final_state, tracker, sent_flags
    )
    
    # 8. Complete task
    await updater.complete()
```

**Estimated reduction**: From 870+ lines to ~150 lines

---

### Phase 3: File Structure

```
backend/app/
├── agent_executor.py        # Main ShoppingAgentExecutor (refactored, stays in current location)
└── common/                  # New directory for shared helper classes
    ├── __init__.py
    ├── message_parser.py        # MessageParser class
    ├── session_manager.py       # SessionManager class
    ├── content_builder.py       # ContentBuilder class
    ├── artifact_formatter.py    # ArtifactFormatter class
    ├── state_tracker.py         # StateTracker class
    ├── artifact_streamer.py    # ArtifactStreamer class
    ├── status_message_handler.py # StatusMessageHandler class
    └── constants.py             # TOOL_STATUS_MESSAGES and other constants
```

**Note**: The `agent_executor.py` file remains in its current location (`backend/app/agent_executor.py`). All helper classes will be placed in the new `backend/app/common/` directory, making them reusable across the application.

**Import Example**: The refactored `agent_executor.py` will import helpers like this:
```python
from app.common.message_parser import MessageParser
from app.common.session_manager import SessionManager
from app.common.content_builder import ContentBuilder
from app.common.artifact_formatter import ArtifactFormatter
from app.common.state_tracker import StateTracker
from app.common.artifact_streamer import ArtifactStreamer
from app.common.status_message_handler import StatusMessageHandler
from app.common.constants import TOOL_STATUS_MESSAGES
```

---

## Implementation Order

### Step 1: Extract Constants
- Create `backend/app/common/` directory
- Move `TOOL_STATUS_MESSAGES` to `backend/app/common/constants.py`
- Update imports in `agent_executor.py`
- **Risk**: Low
- **Impact**: Immediate organization improvement

### Step 2: Extract Artifact Formatters
- Create `ArtifactFormatter` class in `backend/app/common/artifact_formatter.py`
- Move formatting functions
- Update imports in `agent_executor.py`
- **Risk**: Low (pure functions)
- **Impact**: Reduces ~65 lines from main file

### Step 3: Extract Message Parser
- Create `MessageParser` class in `backend/app/common/message_parser.py`
- Move parsing logic
- Remove debug code (or move to debug mode)
- Update imports in `agent_executor.py`
- **Risk**: Medium (complex logic)
- **Impact**: Reduces ~240 lines from main file

### Step 4: Extract Session Manager
- Create `SessionManager` class in `backend/app/common/session_manager.py`
- Move session creation/retrieval logic
- Update imports in `agent_executor.py`
- **Risk**: Medium (state management)
- **Impact**: Reduces ~95 lines from main file

### Step 5: Extract Content Builder
- Create `ContentBuilder` class in `backend/app/common/content_builder.py`
- Move ADK content creation
- Update imports in `agent_executor.py`
- **Risk**: Low
- **Impact**: Reduces ~70 lines from main file

### Step 6: Extract State Tracker
- Create `StateTracker` class in `backend/app/common/state_tracker.py`
- Move state comparison logic
- Update imports in `agent_executor.py`
- **Risk**: Low
- **Impact**: Reduces duplication

### Step 7: Extract Artifact Streamer
- Create `ArtifactStreamer` class in `backend/app/common/artifact_streamer.py`
- Consolidate artifact sending logic
- Update imports in `agent_executor.py`
- **Risk**: Medium (streaming logic)
- **Impact**: Eliminates duplication, reduces ~80 lines

### Step 8: Extract Status Handler
- Create `StatusMessageHandler` class in `backend/app/common/status_message_handler.py`
- Move status update logic
- Update imports in `agent_executor.py`
- **Risk**: Low
- **Impact**: Isolates status updates

### Step 9: Refactor Main Method
- Integrate all helper classes
- Simplify `execute()` method
- **Risk**: Medium (integration)
- **Impact**: Main method becomes readable and maintainable

---

## Testing Strategy

### Unit Tests
- Test each helper class independently
- Mock dependencies (Runner, SessionService, etc.)
- Test edge cases (missing parts, invalid images, etc.)

### Integration Tests
- Test `execute()` method with mocked helpers
- Test full flow with real ADK Runner (if possible)
- Test error handling paths

### Benefits
- Each component can be tested in isolation
- Easier to mock dependencies
- Faster test execution
- Better test coverage

---

## Benefits Summary

1. **Maintainability**: Each class has a single responsibility
2. **Testability**: Components can be tested independently
3. **Readability**: Main `execute()` method becomes clear and concise
4. **Reusability**: Helper classes can be reused elsewhere
5. **Debuggability**: Easier to add logging/debugging to specific components
6. **Extensibility**: Easy to add new artifact types or message formats
7. **Code Size**: Main file reduces from 973 lines to ~200 lines

---

## Risks and Mitigation

### Risk 1: Breaking Existing Functionality
**Mitigation**: 
- Implement incrementally (one class at a time)
- Maintain backward compatibility during transition
- Add comprehensive tests before refactoring
- Test each step thoroughly before proceeding

### Risk 2: Performance Impact
**Mitigation**:
- Profile before and after refactoring
- Ensure async operations remain async
- Avoid unnecessary object creation

### Risk 3: Increased Complexity (More Files)
**Mitigation**:
- Well-organized file structure
- Clear naming conventions
- Good documentation
- The complexity is better organized, not increased

---

## Migration Path

1. **Phase 1**: Create `backend/app/common/` directory and helper classes alongside existing code (no changes to `execute()`)
2. **Phase 2**: Gradually refactor `execute()` in `agent_executor.py` to use helpers (one helper at a time)
3. **Phase 3**: Remove old code from `agent_executor.py` once all helpers are integrated
4. **Phase 4**: Clean up and optimize

This incremental approach minimizes risk and allows for testing at each step. The `agent_executor.py` file stays in its current location, importing helpers from `app.common`.

---

## Estimated Effort

- **Step 1-2**: 2-3 hours (constants, formatters)
- **Step 3**: 4-6 hours (message parser - most complex)
- **Step 4**: 2-3 hours (session manager)
- **Step 5**: 1-2 hours (content builder)
- **Step 6**: 1-2 hours (state tracker)
- **Step 7**: 3-4 hours (artifact streamer)
- **Step 8**: 1-2 hours (status handler)
- **Step 9**: 3-4 hours (main method refactoring)
- **Testing**: 4-6 hours

**Total**: ~21-32 hours

---

## Next Steps

1. Review and approve this plan
2. Start with Step 1 (extract constants) - lowest risk
3. Proceed incrementally, testing at each step
4. Document any deviations or discoveries during implementation

