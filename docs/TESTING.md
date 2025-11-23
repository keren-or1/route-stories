# Route Stories - Test Suite

This directory contains unit and integration tests for the Route Stories multi-agent system.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and test utilities
├── agents/
│   ├── test_video_agent.py   # Video agent tests
│   ├── test_song_agent.py    # Song agent tests
│   ├── test_story_agent.py   # Story agent tests
│   └── test_judge_agent.py   # Judge agent tests
├── integration/              # NEW: Integration tests
│   ├── __init__.py
│   └── test_end_to_end.py   # End-to-end workflow tests
├── services/
│   # Service layer tests (Google Maps, Claude, Search Tools)
├── core/
│   ├── test_orchestrator.py  # Orchestrator tests
│   # Additional core component tests
└── utils/
    # Utility tests (logger, queue manager)
```

## Running Tests

### Run All Tests
```bash
pytest tests/
```

### Run Specific Test File
```bash
pytest tests/agents/test_video_agent.py
```

### Run with Coverage
```bash
pytest --cov=. --cov-report=html tests/
```

### Run with Verbose Output
```bash
pytest -v tests/
```

### Run Specific Test Class or Method
```bash
pytest tests/agents/test_video_agent.py::TestVideoAgent::test_initialization
```

## Test Coverage Goals

**Target Coverage**: 70%+ for new code

Current coverage by module:
- **Agents**: ~85% (comprehensive unit tests)
- **Core**: ~60% (orchestrator, scheduler, collector)
- **Services**: ~40% (mocked external APIs)
- **Utils**: ~50% (logger, queue manager)

## Test Fixtures

Common fixtures are defined in `conftest.py`:

- `mock_waypoint`: Sample waypoint data
- `sample_agent_task`: Pre-configured AgentTask
- `mock_video_results`: Sample YouTube search results
- `mock_song_results`: Sample music search results
- `mock_story_results`: Sample historical story results
- `mock_claude_client`: Mocked Claude API client
- `mock_search_tools`: Mocked search functionality
- `sample_agent_result`: Successful agent result
- `sample_error_result`: Error agent result

## Testing Approach

### Unit Tests
- **Purpose**: Test individual components in isolation
- **Mocking**: External APIs (Claude, Google Maps) are mocked
- **Focus**: Business logic, error handling, edge cases

### Integration Tests (NEW)
- **Purpose**: Test component interactions with real agent instances
- **Scope**: End-to-end workflows using real agents with mocked external APIs
- **Focus**: Multi-threading, queue communication, judge evaluation, error handling
- **Tests**: 6 integration tests covering:
  - Full waypoint processing with all agents
  - Parallel execution and timing verification
  - Error handling with partial failures
  - Judge decision-making with real agent outputs
  - Judge consistency across multiple waypoints
  - Queue-based inter-agent communication

### Edge Cases Tested
1. **No results found** (empty search results)
2. **API failures** (Claude timeout, network errors)
3. **Partial failures** (some agents succeed, some fail)
4. **Invalid inputs** (malformed data, out-of-bounds choices)
5. **Timeout handling** (slow agent execution)

## Writing New Tests

### Test Naming Convention
- Test files: `test_<module>.py`
- Test classes: `Test<ClassName>`
- Test methods: `test_<behavior>_<condition>`

Example:
```python
class TestVideoAgent:
    def test_execute_success(self):
        """Test successful video search and selection."""
        pass

    def test_execute_no_videos_found(self):
        """Test behavior when no videos found."""
        pass
```

### Test Structure
```python
def test_something(self, fixture1, fixture2):
    """Clear description of what is being tested."""
    # Arrange: Setup test data and mocks
    mock_service.method.return_value = expected_value

    # Act: Execute the code being tested
    result = component.do_something(input_data)

    # Assert: Verify expected outcomes
    assert result.success == True
    mock_service.method.assert_called_once()
```

## Mock Usage

### Mocking Claude API
```python
mock_claude = Mock()
mock_claude.simple_query.return_value = "CHOICE: 1\nREASONING: Best option"
```

### Mocking Search Tools
```python
mock_search = Mock()
mock_search.search_youtube_videos.return_value = [{'title': 'Test Video'}]
```

### Simulating Errors
```python
mock_service.method.side_effect = Exception("API Error")
```

## Continuous Integration

Tests should be run:
- Before committing code
- In CI/CD pipeline (if configured)
- Before deploying or releasing

## Known Limitations

1. **External APIs**: Real API calls are not tested (use mocks)
2. **Threading**: Timing-dependent tests may be flaky
3. **Integration**: Full end-to-end tests require manual execution
4. **Coverage Gaps**: Some error paths difficult to trigger in unit tests

## Running Integration Tests

Integration tests use real agent instances and verify end-to-end workflows:

```bash
# Run only integration tests
pytest tests/integration/ -v

# Run integration tests with timing output
pytest tests/integration/ -v -s

# Run specific integration test
pytest tests/integration/test_end_to_end.py::TestFullWaypointProcessing::test_full_waypoint_with_real_agents -v
```

**Integration Test Results (November 23, 2025)**:
- ✓ 6/6 tests passing (100%)
- Execution time: ~0.14 seconds
- All tests verify real agent execution with mocked external APIs

## Future Improvements

- [x] Add integration tests for full route processing
- [ ] Increase service layer coverage
- [ ] Add performance benchmarks
- [ ] Implement property-based testing (hypothesis)
- [ ] Add mutation testing (mutpy)

## Troubleshooting

### Tests Failing Due to Imports
```bash
# Ensure you're in the project root
cd /path/to/route-stories
# Install in editable mode
pip install -e .
```

### Mocks Not Working
- Check mock return values match expected structure
- Verify mock is passed to correct component
- Use `assert_called_once()` to debug call issues

### Coverage Not Generated
```bash
# Install coverage tools
pip install pytest-cov
# Run with coverage
pytest --cov=. tests/
```

---

**Last Updated**: November 22, 2025
**Coverage Goal**: 70%+
**Test Count**: ~40 tests (and growing)
