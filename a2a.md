# A2A Protocol Implementation Plan

## Corrected A2A Protocol Implementation Plan

Based on the **correct** Agent2Agent (A2A) Protocol from [a2a-protocol.org](https://a2a-protocol.org/latest/)

---

## Key Understanding: The Real A2A Protocol

From the [A2A documentation](https://a2a-protocol.org/latest/):
- Originally developed by Google, now donated to Linux Foundation
- Designed to work WITH ADK (not replace it)
- Uses `A2AStarletteApplication` for the server
- Agent Executor pattern for task handling
- JSON-RPC 2.0 for communication

---

## Updated Architecture

```
Frontend (@a2a-js/sdk)
    ↓
A2AStarletteApplication (A2A Protocol Server)
    ↓
AgentExecutor (Custom Implementation)
    ↓ Bridges to
ADK Agents (shopping_orchestrator)
    ↓
Response back through A2A Protocol
```

---

## Implementation Steps

### Phase 1: Install A2A Python SDK

**Command:**
```bash
pip install a2a-sdk
```

**Or use the samples repository:**
```bash
git clone https://github.com/a2aproject/a2a-samples.git
cd a2a-samples
pip install -r samples/python/requirements.txt
```

---

### Phase 2: Create Agent Card

**File:** `backend/app/a2a_agent_card.py` (NEW)

Using the A2A SDK's AgentCard:

```python
from a2a import AgentCard, AgentSkill, InputMode, OutputMode

def create_shopping_agent_card() -> AgentCard:
    return AgentCard(
        name="Shopping Assistant",
        description="AI-powered shopping assistant for e-commerce",
        provider="Your Company",
        url="http://localhost:8080",
        version="1.0.0",
        capabilities={
            "streaming": True,
            "pushNotifications": False,
            "stateTransitionHistory": False
        },
        defaultInputModes=[InputMode.TEXT, InputMode.TEXT_PLAIN],
        defaultOutputModes=[OutputMode.TEXT, OutputMode.TEXT_PLAIN],
        skills=[
            AgentSkill(
                id="discover_products",
                name="Product Discovery",
                description="Search and discover products",
                inputModes=[InputMode.TEXT],
                outputModes=[OutputMode.TEXT],
                examples=["Find me running shoes", "Show me blue t-shirts"]
            ),
            AgentSkill(
                id="manage_cart",
                name="Cart Management",
                description="Add items to cart, view cart contents",
                inputModes=[InputMode.TEXT],
                outputModes=[OutputMode.TEXT],
                examples=["Add running shoes to my cart", "Show me my cart"]
            ),
            # ... more skills
        ]
    )
```

---

### Phase 3: Implement Agent Executor

**File:** `backend/app/a2a_executor.py` (NEW)

Bridge between A2A and ADK:

```python
from a2a import AgentExecutor, Task, TaskResult
from app.orchestrator_agent import root_agent as orchestrator

class ShoppingAgentExecutor(AgentExecutor):
    """Executor that bridges A2A protocol to ADK agents."""
    
    async def execute(self, task: Task) -> TaskResult:
        """
        Execute a task received via A2A protocol.
        Converts A2A task to ADK format and executes.
        """
        # Extract message from A2A task
        message_parts = task.message.parts if hasattr(task.message, 'parts') else []
        text_content = ""
        for part in message_parts:
            if part.kind == "text":
                text_content += part.text + " "
        
        # Create ADK-compatible message
        adk_message = {
            "role": "user",
            "parts": [{"text": text_content.strip()}]
        }
        
        # Execute using orchestrator agent
        # Note: You'll need to adapt this to call ADK agents properly
        response = await self._call_adk_agent(adk_message, task.session_id)
        
        # Convert response to A2A format
        return TaskResult(
            status="completed",
            output={"parts": [{"kind": "text", "text": response}]}
        )
    
    async def _call_adk_agent(self, message: dict, session_id: str) -> str:
        """Call the ADK orchestrator agent."""
        # Implementation depends on how you call ADK agents
        # This is a placeholder
        pass
```

---

### Phase 4: Replace FastAPI App with A2A Server

**File:** `backend/app/main.py` (MAJOR MODIFICATION)

Replace the current ADK FastAPI app setup with A2A:

```python
from a2a import A2AStarletteApplication, DefaultRequestHandler, InMemoryTaskStore
from app.a2a_agent_card import create_shopping_agent_card
from app.a2a_executor import ShoppingAgentExecutor
import uvicorn

# Create agent card
agent_card = create_shopping_agent_card()

# Create executor
executor = ShoppingAgentExecutor()

# Create task store
task_store = InMemoryTaskStore()

# Create request handler
request_handler = DefaultRequestHandler(executor, task_store)

# Create A2A application
app = A2AStarletteApplication(agent_card, request_handler)

# Keep existing endpoints working alongside A2A
@app.get("/healthz")
def healthz():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

---

### Phase 5: Update Requirements

**File:** `backend/requirements.txt` (MODIFY)

Add A2A SDK:
```
a2a-sdk>=0.3.0
# ... existing requirements
```

---

## Key Differences from Previous Plan

| Previous (Wrong) | Correct A2A |
|-----------------|-------------|
| JSON-RPC on custom endpoints | Use A2A SDK |
| Manual message handling | Agent Executor pattern |
| Custom protocol bridge | `A2AStarletteApplication` |
| Separate endpoints | Integrated via A2A SDK |

---

## Updated Effort Estimate

- **Phase 1:** 0.5 hours (Install SDK)
- **Phase 2:** 2-3 hours (Agent Card)
- **Phase 3:** 4-6 hours (Agent Executor)
- **Phase 4:** 3-4 hours (Replace FastAPI app)
- **Phase 5:** 0.5 hours (Update requirements)
- **Testing:** 2-3 hours

**Total:** 12-17 hours

---

## Key Benefits

1. ✅ Uses official A2A SDK (maintained by Linux Foundation)
2. ✅ Native compatibility with frontend `@a2a-js/sdk`
3. ✅ Maintains ADK integration (doesn't replace it)
4. ✅ Follows documented pattern from A2A protocol
5. ✅ Enables interoperability with other A2A agents

---

## References

- [A2A Protocol Official Site](https://a2a-protocol.org/latest/)
- [A2A Python Tutorial](https://a2a-protocol.org/dev/tutorials/python/)
- [A2A Samples Repository](https://github.com/a2aproject/a2a-samples)
- [A2A Specification](https://a2a-protocol.org/latest/specification/)

---

## Next Steps

1. Review the [A2A Python Quickstart](https://a2a-protocol.org/dev/tutorials/python/)
2. Clone the [A2A samples repository](https://github.com/a2aproject/a2a-samples)
3. Study the telemetry agent example
4. Begin implementation following this plan

This plan correctly follows the [official A2A Protocol specification](https://a2a-protocol.org/latest/).

