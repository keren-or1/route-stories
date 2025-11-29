# Manual Test Scripts

These are exploratory test scripts that verify the Route Stories system works correctly with real APIs and configurations. They are **NOT** part of the formal pytest test suite.

## Purpose

- Verify real API integrations (YouTube, Wikipedia, Spotify, Google Maps, Gemini)
- Test rate limit handling and retry logic
- Validate search API functionality
- Check web application initialization

## Running Manual Tests

```bash
# Run a specific manual test
python scripts/manual_tests/test_agents_search.py

# Run all manual tests (requires manual execution)
cd scripts/manual_tests/
for f in test_*.py; do python "$f"; done
```

## Test Files

| Script | Purpose |
|--------|---------|
| `test_agents_search.py` | Verify agents can find and process search results with retry logic |
| `test_e2e_real_apis.py` | End-to-end test of search tools with real APIs |
| `test_rate_limit_handling.py` | Verify rate limit handling in API calls |
| `test_retry_logic.py` | Test exponential backoff and retry mechanisms |
| `test_search_apis.py` | Test real search API integrations |
| `test_setup.py` | Verify system setup and configuration |
| `test_waypoint_extraction.py` | Test Google Maps waypoint extraction |
| `test_web_app.py` | Test Flask web application initialization |

## Notes

- These scripts use real API calls (may consume API quota)
- Set required environment variables (.env file) before running
- Some tests require valid API keys
- Not automated as part of CI/CD pipeline

## Formal Test Suite

The formal pytest test suite is located in `tests/` and includes:
- Unit tests with mocks (no real API calls)
- Integration tests
- All tests run automatically with `pytest tests/`
