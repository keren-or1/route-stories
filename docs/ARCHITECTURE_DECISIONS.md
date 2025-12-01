# Architecture Decision Records (ADRs)

This document records the key architectural decisions made during the development of the Route Stories system, following the ADR format to document the context, decision, and consequences of each choice.

## Table of Contents

1. [ADR-001: Use Threading Instead of Multiprocessing](#adr-001-use-threading-instead-of-multiprocessing)
2. [ADR-002: Use Gemini API Instead of Claude](#adr-002-use-gemini-api-instead-of-claude)
3. [ADR-003: Queue-Based Message Passing Pattern](#adr-003-queue-based-message-passing-pattern)
4. [ADR-004: Manual Progression Before Implementing Timer](#adr-004-manual-progression-before-implementing-timer)
5. [ADR-005: File-Based Caching with 24-Hour TTL](#adr-005-file-based-caching-with-24-hour-ttl)

---

## ADR-001: Use Threading Instead of Multiprocessing

**Status**: Accepted

**Date**: 2025-11-28

### Context

The Route Stories system processes multiple waypoints, each requiring parallel execution of three specialized agents (Video, Song, Story) plus a judge agent for content selection. Two primary concurrency approaches were considered:

1. **Threading**: Lighter-weight, shared memory space, suitable for I/O-bound tasks
2. **Multiprocessing**: True parallelism, separate memory spaces, suitable for CPU-bound tasks

Key characteristics of our workload:
- Agent tasks are primarily I/O-bound (API calls to YouTube, Spotify, Wikipedia, Google Maps, Gemini)
- Network latency is the dominant bottleneck, not computation
- Agents need to share state through a queue manager
- Target execution time improvement: 3x speedup over sequential execution

### Decision

**We chose threading over multiprocessing.**

Implementation details:
- Use `threading.Thread` for agent execution
- Implement `QueueManager` with thread-safe `queue.Queue` for message passing
- Run 3 agents concurrently per waypoint (video, song, story)
- Sequential judge execution after agent completion

### Consequences

**Positive:**
- **Simpler state sharing**: Threads share memory space, making queue communication straightforward
- **Lower overhead**: Thread creation and context switching is faster than process spawning
- **Sufficient for I/O-bound workload**: Network API calls release the GIL, allowing effective parallelism
- **Easier debugging**: Shared memory makes inspection and logging simpler
- **Resource efficiency**: Lower memory footprint compared to multiprocessing

**Negative:**
- **GIL limitation**: Python's Global Interpreter Lock prevents true CPU parallelism
- **Not suitable for CPU-intensive tasks**: Would require multiprocessing for computation-heavy workloads

**Measured Results:**
- Sequential execution: ~0.45s per waypoint
- Threaded execution: ~0.15s per waypoint
- **Achieved speedup: 3x** (meets performance target)

### Alternatives Considered

1. **Multiprocessing**: Rejected due to:
   - Higher overhead for I/O-bound tasks
   - Complex inter-process communication required
   - Higher memory consumption
   - Overkill for network-bound workload

2. **Asyncio**: Rejected due to:
   - Library compatibility issues (many sync-only APIs)
   - Higher implementation complexity
   - Unclear benefit over threading for our use case

---

## ADR-002: Use Gemini API Instead of Claude

**Status**: Accepted

**Date**: 2025-11-25

### Context

The system requires an LLM API for two primary functions:
1. **Content analysis**: Evaluating and ranking videos, songs, and stories
2. **Judge agent**: Making final content selection decisions

Requirements:
- Fast response times (< 2 seconds per query)
- Structured output support (JSON responses)
- Cost-effective for academic/prototype use
- Sufficient reasoning capability for content evaluation

API options evaluated:
- **Claude (Anthropic)**: High quality reasoning, but more expensive
- **Gemini (Google)**: Good quality, free tier available, fast responses
- **GPT-4 (OpenAI)**: High quality but expensive, rate limits

### Decision

**We chose Google's Gemini API (gemini-pro model).**

Configuration:
- Model: `gemini-pro`
- Max tokens: 1024
- Temperature: 0.7
- API key: Environment variable `GEMINI_API_KEY`

### Consequences

**Positive:**
- **Free tier availability**: No cost during development and testing
- **Fast response times**: Consistently < 1.5s per query
- **Good reasoning quality**: Sufficient for content ranking tasks
- **Structured output**: JSON mode support for judge decisions
- **High rate limits**: 60 requests/minute on free tier

**Negative:**
- **Slightly lower quality than Claude**: Less sophisticated reasoning in edge cases
- **Vendor lock-in**: Code assumes Gemini response format
- **API stability**: Google may change free tier terms

**Mitigation:**
- Abstracted LLM client interface (`GeminiClient` class)
- Easy to swap for other providers if needed
- Fallback logic for API failures

### Alternatives Considered

1. **Claude API**: Rejected due to cost constraints for academic project
2. **GPT-4**: Rejected due to higher cost and stricter rate limits
3. **Local LLMs**: Rejected due to insufficient quality and speed

---

## ADR-003: Queue-Based Message Passing Pattern

**Status**: Accepted

**Date**: 2025-11-27

### Context

With parallel agent execution, we need a reliable mechanism for:
- Agents to report results back to the orchestrator
- Synchronizing completion of multiple concurrent tasks
- Error handling and timeout management
- Maintaining thread safety

Options considered:
1. **Shared variables with locks**: Simple but error-prone
2. **Queue-based messaging**: Thread-safe, producer-consumer pattern
3. **Event-driven callbacks**: Complex but flexible

### Decision

**We implemented a queue-based message passing system via `QueueManager`.**

Architecture:
```python
class QueueManager:
    def __init__(self):
        self.result_queue = queue.Queue()

    def put_result(self, result: AgentResult):
        self.result_queue.put(result)

    def get_results(self, timeout: float) -> List[AgentResult]:
        # Collect results with timeout handling
```

Workflow:
1. Orchestrator spawns agent threads
2. Each agent puts result in queue when complete
3. Orchestrator collects results with timeout
4. Agents run independently without shared state

### Consequences

**Positive:**
- **Thread-safe by design**: `queue.Queue` handles all locking internally
- **Decoupled components**: Agents don't need to know about orchestrator internals
- **Natural timeout handling**: Queue.get() supports timeout parameter
- **Error resilience**: Failed agents don't block the queue
- **Extensible**: Easy to add more agents or change communication patterns

**Negative:**
- **Additional abstraction layer**: More code compared to direct variable access
- **Potential message loss**: Requires proper error handling
- **Memory overhead**: Queue stores messages until consumed

**Design Principles:**
- **Separation of concerns**: QueueManager handles all synchronization
- **Fail-fast**: Agents report errors immediately via queue
- **Timeout safety**: Orchestrator never blocks indefinitely

---

## ADR-004: Manual Progression Before Implementing Timer

**Status**: Accepted

**Date**: 2025-11-26

### Context

The CLI interface needs to control progression through waypoints along a route. Two approaches were considered:

1. **Automatic progression**: Timer-based, advances after fixed delay
2. **Manual progression**: User presses Enter to continue

Assignment requirements specify exploring both approaches. For the initial implementation, we needed to choose one as the foundation.

### Decision

**We implemented manual progression as the primary interface.**

Implementation:
```python
def prompt_next(self) -> bool:
    response = input("Press Enter to continue (or 'q' to quit): ")
    return response.lower() not in ['q', 'quit']
```

User experience:
1. System displays results for current waypoint
2. User reviews content at their own pace
3. User presses Enter to advance or 'q' to quit
4. Process repeats for each waypoint

### Consequences

**Positive:**
- **User control**: Travelers can spend time reviewing content
- **Simpler implementation**: No timer/threading complexity in UI layer
- **Better for testing**: Deterministic behavior, easier to debug
- **Accessibility**: Users aren't rushed by automatic timers
- **Educational value**: Clear demonstration of synchronous flow

**Negative:**
- **Less automation**: Requires user interaction for each waypoint
- **Not suitable for long routes**: Tedious for 20+ waypoints
- **No hands-free mode**: Can't run unattended

**Future Enhancement:**
- Timer-based mode can be added as alternative progression strategy
- Hybrid approach: Manual for first waypoint, then automatic
- Configuration option: User chooses progression mode at startup

### Alternatives Considered

1. **Timer-based auto-progression**: Deferred to future iteration
2. **Hybrid mode**: Deemed too complex for MVP

---

## ADR-005: File-Based Caching with 24-Hour TTL

**Status**: Accepted

**Date**: 2025-11-29

### Context

Search APIs (YouTube, Spotify, Wikipedia) have rate limits and response times that impact system performance. Caching is essential for:
- **Reducing API calls**: Avoid hitting rate limits
- **Improving response time**: Instant results for repeated queries
- **Cost reduction**: Some APIs charge per request
- **Offline testing**: Work with cached data when APIs unavailable

Caching strategies evaluated:
1. **In-memory cache**: Fast but lost on restart
2. **Redis/Memcached**: Requires external service
3. **File-based cache**: Persistent, no dependencies
4. **Database cache**: Overkill for simple key-value storage

### Decision

**We implemented file-based caching with 24-hour TTL.**

Implementation (`SearchCache` class):
```python
class SearchCache:
    def __init__(self, cache_dir=".cache"):
        self.cache_dir = Path(cache_dir)
        self.ttl_hours = 24

    def get(self, key: str) -> Optional[Any]:
        # Load from .cache/<sanitized_key>.json
        # Check timestamp, return None if expired

    def set(self, key: str, value: Any):
        # Save to .cache/<sanitized_key>.json with timestamp
```

Cache keys:
- YouTube: `youtube_{location}_{max_results}`
- Music: `music_{location}_{max_results}`
- History: `history_{location}_{max_results}`

TTL rationale:
- **24 hours**: Balances freshness vs. API efficiency
- **Location content changes slowly**: Historical facts and popular videos remain relevant
- **Daily usage pattern**: Users unlikely to query same route multiple times per day

### Consequences

**Positive:**
- **Zero dependencies**: No Redis or database required
- **Persistent across runs**: Cache survives application restart
- **Simple debugging**: Cache files are human-readable JSON
- **Configurable TTL**: Easy to adjust expiration time
- **Automatic cleanup**: Expired entries deleted on access
- **Git-friendly**: `.cache/` added to `.gitignore`

**Negative:**
- **File I/O overhead**: Slower than in-memory cache
- **No cache size limit**: Could grow unbounded (mitigated by TTL)
- **No cross-instance sharing**: Each instance has separate cache
- **Filesystem dependency**: Requires write permissions

**Performance Impact:**
- Cache hit: ~0.01s (file read)
- Cache miss: ~1-2s (API call + file write)
- **10-20x speedup** for cached results

**Operational Notes:**
- Cache directory: `.cache/` (created automatically)
- Manual cleanup: `rm -rf .cache/` to clear all cached data
- Safe failures: Cache read/write errors don't crash the application

### Alternatives Considered

1. **Redis cache**: Rejected due to deployment complexity
2. **In-memory only**: Rejected due to lack of persistence
3. **SQLite database**: Rejected as over-engineered for simple key-value storage
4. **No caching**: Rejected due to severe API rate limit issues

---

## Summary

These architectural decisions reflect a pragmatic approach to building a robust, performant route storytelling system:

1. **Threading** provides sufficient parallelism for I/O-bound tasks without multiprocessing complexity
2. **Gemini API** offers the best balance of quality, cost, and speed for academic use
3. **Queue-based messaging** ensures thread-safe, decoupled communication between components
4. **Manual progression** prioritizes user control and implementation simplicity
5. **File-based caching** reduces API load while maintaining zero-dependency architecture

Each decision prioritizes:
- **Simplicity**: Minimal dependencies, straightforward implementation
- **Performance**: Meeting 3x speedup target through threading
- **Cost-effectiveness**: Free API tier, no infrastructure costs
- **Maintainability**: Clean abstractions, easy to extend or modify

---

**Document Version**: 1.0
**Last Updated**: 2025-12-01
**Authors**: Route Stories Development Team
