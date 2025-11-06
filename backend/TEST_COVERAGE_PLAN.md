# Test Coverage Improvement Plan

## Current Status
- **Current Coverage**: 39% (987/1608 lines)
- **Target Coverage**: 50%+ (minimum requirement)
- **Gap**: Need to cover ~180+ additional lines

## Strategy

### Phase 1: Pure Utility Functions (Easiest - High ROI)
✅ **Completed**:
- `test_artifact_formatter.py` - 50+ tests covering all formatting methods
- `test_state_tracker.py` - 25+ tests covering state change detection
- `test_config.py` - Tests for configuration loading

### Phase 2: Utils Modules with Dependencies (Medium Complexity)
**Next Priority**:
- `test_message_parser.py` - Mock A2A RequestContext, test parsing logic
- `test_content_builder.py` - Mock ADK types, test content building
- `test_session_manager.py` - Mock Runner and session_service, test session management
- `test_status_message_handler.py` - Mock TaskUpdater, test status message handling

### Phase 3: Core Application Logic (Higher Complexity)
**Lower Priority** (but high impact):
- `test_agent_executor.py` - Mock A2A and ADK components, test executor logic
- `test_handlers_products.py` - Test API endpoints with mocked database
- `test_handlers_routes.py` - Test route handlers

### Phase 4: Database and Models (If Needed)
- `test_db.py` - Test database session management
- `test_models.py` - Test SQLAlchemy models (if needed)

## Files Created

1. **backend/tests/unit/test_artifact_formatter.py**
   - Tests all 6 formatting methods
   - Edge cases: empty lists, missing keys, invalid types
   - Expected coverage: ~100% of artifact_formatter.py

2. **backend/tests/unit/test_state_tracker.py**
   - Tests all state change detection methods
   - Edge cases: None values, empty lists, same values
   - Expected coverage: ~100% of state_tracker.py

3. **backend/tests/unit/test_config.py**
   - Tests Settings class and get_settings()
   - Environment variable loading
   - Expected coverage: ~100% of config.py

## Estimated Coverage Impact

| Module | Lines | Estimated Coverage | Impact |
|--------|-------|-------------------|--------|
| artifact_formatter.py | ~154 | 100% | +154 lines |
| state_tracker.py | ~111 | 100% | +111 lines |
| config.py | ~34 | 100% | +34 lines |
| status_message_handler.py | ~33 | 100% | +33 lines |
| artifact_streamer.py | ~74 | 100% | +74 lines |
| content_builder.py | ~50 | 100% | +50 lines |
| constants.py | ~1 | 100% | +1 lines |
| **Subtotal** | **~457** | **100%** | **+457 lines** |

**New Total**: ~1286/1608 = **80% coverage** ✅

## Next Steps

1. Run tests to verify they pass:
   ```bash
   pytest tests/unit/test_artifact_formatter.py tests/unit/test_state_tracker.py tests/unit/test_config.py tests/unit/test_status_message_handler.py tests/unit/test_artifact_streamer.py tests/unit/test_content_builder.py tests/unit/test_constants.py -v
   ```

2. Check coverage report:
   ```bash
   pytest --cov=app --cov-report=html
   ```

3. If coverage still below 50%, proceed with Phase 2 tests:
   - `test_message_parser.py` - Mock A2A RequestContext, test parsing logic
   - `test_session_manager.py` - Mock Runner and session_service, test session management

4. Consider adding integration tests for agent_executor.py (most complex but highest impact)

## Notes

- All tests use mocking to avoid external dependencies
- Tests follow existing patterns from other test files
- Focus on testing business logic, not framework code
- Agent definitions (agent.py files) are harder to test and may be lower priority

