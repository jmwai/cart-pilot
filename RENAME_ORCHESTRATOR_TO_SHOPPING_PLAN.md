# Rename orchestrator_agent to shopping_agent - Refactoring Plan

## Overview
Rename the `orchestrator_agent` directory to `shopping_agent` across the entire codebase. This involves updating all imports, references, and documentation.

## Clarification Needed

**Question**: Should the agent name `shopping_orchestrator` also be changed to `shopping_agent`?
- **Option A**: Rename directory only, keep agent name as `shopping_orchestrator`
- **Option B**: Rename both directory and agent name to `shopping_agent` (recommended for consistency)

**Plan assumes Option B (both renamed)** - will adjust if you prefer Option A.

## Current Structure

```
backend/app/
├── orchestrator_agent/           ← RENAME TO shopping_agent/
│   ├── __init__.py
│   ├── agent.py                  ← Contains agent with name="shopping_orchestrator"
│   └── sub_agents/
│       ├── cart_agent/
│       ├── checkout_agent/
│       ├── customer_service_agent/
│       └── product_discovery_agent/
└── payment_agent/
```

## Target Structure

```
backend/app/
├── shopping_agent/               ← RENAMED FROM orchestrator_agent/
│   ├── __init__.py
│   ├── agent.py                  ← Agent name="shopping_agent" (if Option B)
│   └── sub_agents/
│       ├── cart_agent/
│       ├── checkout_agent/
│       ├── customer_service_agent/
│       └── product_discovery_agent/
└── payment_agent/
```

## Files to Update

### Phase 1: Directory Rename
1. **Rename directory**: `backend/app/orchestrator_agent/` → `backend/app/shopping_agent/`
   - This will automatically update all relative imports within the directory

### Phase 2: Update Imports in Code

#### 2.1 Backend Code
**File**: `backend/app/a2a_executor.py`
- Change: `from app.orchestrator_agent import root_agent as shopping_orchestrator`
- To: `from app.shopping_agent import root_agent as shopping_agent` (or keep shopping_orchestrator if Option A)

**File**: `backend/app/orchestrator_agent/agent.py` → `backend/app/shopping_agent/agent.py`
- Change agent name: `name="shopping_orchestrator"` → `name="shopping_agent"` (if Option B)
- Update description if needed: "Orchestrates shopping workflow..." → "Shopping agent that coordinates..."

#### 2.2 Test Files
**Files to update** (all import paths):
- `backend/tests/unit/test_cart_tools.py`
- `backend/tests/unit/test_checkout_tools.py`
- `backend/tests/unit/test_customer_service_tools.py`
- `backend/tests/unit/test_product_discovery_tools.py`

**Change pattern**:
- `from app.orchestrator_agent.sub_agents.*` → `from app.shopping_agent.sub_agents.*`
- `patch('app.orchestrator_agent.sub_agents.*')` → `patch('app.shopping_agent.sub_agents.*')`

### Phase 3: Update Documentation

#### 3.1 Markdown Files
**File**: `AGENT_HIERARCHY_REFACTOR_PLAN.md`
- Update all references to `orchestrator_agent` → `shopping_agent`
- Update directory paths in examples

**File**: `backend/apidoc.md`
- Update references to `shopping_orchestrator` → `shopping_agent` (if Option B)
- Update paths: `app.orchestrator_agent` → `app.shopping_agent`
- Update API examples with new agent name

**File**: `backend/agents.md`
- Update references to orchestrator agent
- Update paths and examples

**File**: `backend/tests/README.md`
- Update example paths if they reference orchestrator_agent

### Phase 4: Update Comments and Docstrings

#### 4.1 Files with Comments
- `backend/app/a2a_executor.py` - Docstring mentions "orchestrator"
- Update any comments that mention "orchestrator_agent" or "orchestrator"

## Detailed Changes

### 1. Directory Rename
```bash
# Move directory
mv backend/app/orchestrator_agent backend/app/shopping_agent
```

### 2. Update `backend/app/shopping_agent/agent.py`
```python
# Change agent name (if Option B):
root_agent = LlmAgent(
    name="shopping_agent",  # Changed from "shopping_orchestrator"
    ...
)
```

### 3. Update `backend/app/a2a_executor.py`
```python
# Old:
from app.orchestrator_agent import root_agent as shopping_orchestrator

# New:
from app.shopping_agent import root_agent as shopping_agent
# (or keep shopping_orchestrator if Option A)
```

### 4. Update Test Files (4 files)
**Pattern**: Replace all occurrences
- `app.orchestrator_agent` → `app.shopping_agent`

**Example**:
```python
# Old:
from app.orchestrator_agent.sub_agents.cart_agent.tools import add_to_cart
with patch('app.orchestrator_agent.sub_agents.cart_agent.tools.get_db_session') as mock:

# New:
from app.shopping_agent.sub_agents.cart_agent.tools import add_to_cart
with patch('app.shopping_agent.sub_agents.cart_agent.tools.get_db_session') as mock:
```

### 5. Update Documentation Files
- Find and replace `orchestrator_agent` → `shopping_agent`
- Find and replace `shopping_orchestrator` → `shopping_agent` (if Option B)

## Implementation Checklist

### Step 1: Directory Structure
- [ ] Rename `backend/app/orchestrator_agent/` → `backend/app/shopping_agent/`

### Step 2: Backend Code
- [ ] Update `backend/app/a2a_executor.py` import
- [ ] Update `backend/app/shopping_agent/agent.py` agent name (if Option B)
- [ ] Update docstrings/comments if needed

### Step 3: Test Files
- [ ] Update `backend/tests/unit/test_cart_tools.py`
- [ ] Update `backend/tests/unit/test_checkout_tools.py`
- [ ] Update `backend/tests/unit/test_customer_service_tools.py`
- [ ] Update `backend/tests/unit/test_product_discovery_tools.py`

### Step 4: Documentation
- [ ] Update `AGENT_HIERARCHY_REFACTOR_PLAN.md`
- [ ] Update `backend/apidoc.md`
- [ ] Update `backend/agents.md`
- [ ] Update `backend/tests/README.md` (if needed)

### Step 5: Verification
- [ ] Verify all imports resolve correctly
- [ ] Check for any remaining references to `orchestrator_agent`
- [ ] Verify agent name consistency (if Option B)
- [ ] Run linter to check for errors

## Search Patterns to Update

### In Code Files:
1. `from app.orchestrator_agent` → `from app.shopping_agent`
2. `app.orchestrator_agent.sub_agents` → `app.shopping_agent.sub_agents`
3. `shopping_orchestrator` → `shopping_agent` (if Option B)
4. `orchestrator_agent` → `shopping_agent`

### In Documentation:
1. `orchestrator_agent/` → `shopping_agent/`
2. `shopping_orchestrator` → `shopping_agent` (if Option B)
3. Update API examples with new names

## Files Summary

### To Rename:
- `backend/app/orchestrator_agent/` (entire directory)

### To Modify:
- `backend/app/a2a_executor.py` (1 import)
- `backend/app/shopping_agent/agent.py` (agent name if Option B)
- `backend/tests/unit/test_cart_tools.py` (~15 patch calls)
- `backend/tests/unit/test_checkout_tools.py` (~13 patch calls)
- `backend/tests/unit/test_customer_service_tools.py` (~17 patch calls)
- `backend/tests/unit/test_product_discovery_tools.py` (~24 patch calls)
- `AGENT_HIERARCHY_REFACTOR_PLAN.md` (documentation)
- `backend/apidoc.md` (documentation)
- `backend/agents.md` (documentation)

## Notes

- Relative imports within `shopping_agent/` directory will work automatically after rename
- Sub-agents' imports don't need to change (they use relative imports)
- The agent name `shopping_orchestrator` is used in the ADK agent definition and may be referenced in API calls
- Consider if any external systems or configurations reference the agent name

## Risk Assessment

- **Low Risk**: Most changes are straightforward find/replace operations
- **Consideration**: If Option B (rename agent name), API endpoints might change (if they use agent name)
- **Testing**: Verify imports work after rename, especially in test files

## Questions for User

1. **Agent Name**: Rename `shopping_orchestrator` → `shopping_agent`? (Option A or B)
2. **Variable Names**: Keep `shopping_orchestrator` variable name in `a2a_executor.py` or rename to `shopping_agent`?
3. **API Compatibility**: Are there any external systems/APIs that reference `shopping_orchestrator` that we need to maintain compatibility for?

