# Fix Cart Agent Product Selection from State - Plan

## Problem Analysis

### Root Cause:
The Cart Agent instructions tell it to "Access state["current_results"]" but:
1. **LLM agents cannot directly access state** - They can only access state through tools
2. The `add_to_cart` tool requires a `product_id` parameter, but the agent doesn't have a way to extract it from state
3. The agent is asking for product_id because it doesn't have a tool to look it up from state

### Current Flow Breakdown:
1. User searches → Product Discovery Agent calls `text_vector_search` → Stores results in `state["current_results"]` ✅
2. User says "add the blue shoes" → Shopping Agent transfers to Cart Agent ✅
3. Cart Agent tries to access `state["current_results"]` → **FAILS** - Agent can't access state directly ❌
4. Cart Agent asks user for product_id → **WRONG BEHAVIOR** ❌

## Solution Options

### Option 1: Create Helper Tool (Recommended)
Create a `find_product_in_results` tool that:
- Takes a product description
- Accesses `state["current_results"]` via ToolContext
- Matches description to product
- Returns product_id

**Pros**: Clean separation, reusable, follows ADK patterns
**Cons**: Requires agent to call two tools sequentially

### Option 2: Enhance add_to_cart Tool
Modify `add_to_cart` to:
- Accept either `product_id` OR `product_description`
- If description provided, match against `state["current_results"]` internally
- Return product_id and proceed with cart addition

**Pros**: Single tool call, simpler for agent
**Cons**: Tool becomes more complex, mixing concerns

### Option 3: Make add_to_cart Tool Smarter
Add logic to `add_to_cart`:
- If product_id not found, check `state["current_results"]`
- Auto-match based on description patterns

**Pros**: Most user-friendly
**Cons**: Complex logic, harder to debug

## Recommended Solution: Option 1 + Enhanced Instructions

### Implementation Plan

#### Phase 1: Create Helper Tool
**File**: `backend/app/shopping_agent/sub_agents/cart_agent/tools.py`

Create new tool:
```python
def find_product_in_results(tool_context: ToolContext, description: str) -> Dict[str, Any]:
    """
    Find a product from current search results by matching description.
    
    Args:
        tool_context: ADK tool context providing access to state
        description: Product description to match (e.g., "blue shoes", "the first one", "number 3")
    
    Returns:
        Dict with product_id and product details, or error if not found
    """
    # Access state["current_results"]
    current_results = tool_context.state.get("current_results", [])
    
    if not current_results:
        raise ValueError("No search results found. Please search for products first.")
    
    # Match description to product
    description_lower = description.lower()
    
    # Handle "first one", "number 1", etc.
    if description_lower in ["first", "first one", "number 1", "1", "one"]:
        product = current_results[0]
    elif description_lower in ["second", "second one", "number 2", "2"]:
        product = current_results[1] if len(current_results) > 1 else None
    elif description_lower in ["third", "third one", "number 3", "3"]:
        product = current_results[2] if len(current_results) > 2 else None
    else:
        # Match by keywords in name/description
        product = None
        for result in current_results:
            name = (result.get("name", "") or "").lower()
            desc = (result.get("description", "") or "").lower()
            if description_lower in name or description_lower in desc:
                product = result
                break
    
    if not product:
        raise ValueError(
            f"Could not find product matching '{description}' in search results. "
            f"Available products: {[r.get('name', 'Unknown') for r in current_results[:3]]}"
        )
    
    return {
        "product_id": product["id"],
        "name": product["name"],
        "description": product.get("description", ""),
        "picture": product.get("product_image_url") or product.get("picture", ""),
        "price_usd_units": product.get("price_usd_units", 0),
    }
```

#### Phase 2: Update Cart Agent Instructions
**File**: `backend/app/shopping_agent/sub_agents/cart_agent/agent.py`

Update instructions to use the helper tool:

```python
### find_product_in_results(description: str) → ProductMatch
**Purpose**: Find a product from current search results by matching description
**Usage**:
- Takes a product description (e.g., "blue shoes", "the first one", "number 3")
- Accesses state["current_results"] automatically
- Matches description to product
- Returns product_id and product details

**When to use**:
- User references items from search results (e.g., "add the blue shoes", "I want the white ones")
- BEFORE calling add_to_cart when user doesn't provide product_id directly

**Matching logic**:
- "blue shoes" → finds product with "blue" in name or description
- "white ones" → finds product with "white" in name/description
- "the first one" → uses first product (index 0)
- "number 3" → uses third product (index 2)

**Example workflow**:
- User: "Add the blue running shoes to cart"
- Step 1: Call find_product_in_results("blue running shoes")
  - Returns: {"product_id": "prod_123", "name": "Blue Running Shoes", ...}
- Step 2: Call add_to_cart(product_id="prod_123", quantity=1)
- Step 3: Call get_cart() to show updated cart
```

Update the "Pattern 1: Add Item After Search" workflow:
```python
### Pattern 1: Add Item After Search
1. User references item from search results
2. **Call find_product_in_results(description)** to get product_id
   - If not found: Ask user to clarify or suggest searching again
3. **Call add_to_cart with product_id** from step 2
4. Call get_cart to show updated cart
5. Confirm addition and show cart summary
```

#### Phase 3: Update Tool Imports
**File**: `backend/app/shopping_agent/sub_agents/cart_agent/agent.py`

Add new tool to imports and tools list:
```python
from .tools import (
    add_to_cart,
    get_cart,
    update_cart_item,
    remove_from_cart,
    clear_cart,
    get_cart_total,
    find_product_in_results,  # NEW
)

# In root_agent tools list:
tools=[
    add_to_cart,
    get_cart,
    update_cart_item,
    remove_from_cart,
    clear_cart,
    get_cart_total,
    find_product_in_results,  # NEW
],
```

## Alternative: Simpler Fix (Option 2)

If we want a simpler solution, we can enhance `add_to_cart` to optionally accept a description:

```python
def add_to_cart(
    tool_context: ToolContext, 
    product_id: Optional[str] = None, 
    product_description: Optional[str] = None,
    quantity: int = 1
) -> Dict[str, Any]:
    """
    Add product to cart. Can use product_id OR product_description.
    If product_description provided, will match against state["current_results"].
    """
    # If description provided, find product_id first
    if product_description and not product_id:
        current_results = tool_context.state.get("current_results", [])
        if not current_results:
            raise ValueError("No search results found. Please search for products first.")
        
        # Match logic (same as find_product_in_results)
        # ... match description to product ...
        product_id = matched_product["id"]
    
    # Continue with existing logic using product_id
    # ...
```

But this makes the tool more complex and mixes concerns.

## Recommended Approach: Option 1

**Why Option 1 is better**:
1. **Separation of concerns**: Finding vs. adding are separate operations
2. **Reusability**: `find_product_in_results` can be used elsewhere
3. **Clearer agent instructions**: Agent learns to use helper tool first
4. **Easier debugging**: Each tool has single responsibility
5. **More flexible**: Can return product details before adding

## Implementation Checklist

- [ ] Create `find_product_in_results` tool in `cart_agent/tools.py`
- [ ] Add tool to cart agent imports
- [ ] Add tool to cart agent tools list
- [ ] Update cart agent instructions to document new tool
- [ ] Update workflow pattern to use helper tool
- [ ] Test with real user flow

## Testing Scenarios

1. **Search → Add by description**:
   - User: "Find running shoes"
   - User: "Add the blue ones"
   - Expected: Finds product with "blue" in name, adds to cart

2. **Search → Add by position**:
   - User: "Find shoes"
   - User: "Add the first one"
   - Expected: Adds first product from results

3. **Add without search**:
   - User: "Add blue shoes to cart" (no prior search)
   - Expected: Error message asking user to search first

4. **Ambiguous description**:
   - User: "Add the shoes" (multiple shoes in results)
   - Expected: Adds first matching product or asks for clarification

