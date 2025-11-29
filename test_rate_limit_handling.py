#!/usr/bin/env python3
"""
Test rate limit handling by simulating heavy API load.
"""

import sys
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.services.gemini_client import GeminiClient
from src.config import get_settings
from src.utils.logger import get_logger
import time

logger = get_logger("test_rate_limit")

def test_concurrent_queries(num_queries: int = 5):
    """Test multiple concurrent API queries to potentially trigger rate limiting."""
    settings = get_settings()

    print("\n" + "="*70)
    print(f"Testing Concurrent API Queries ({num_queries} parallel requests)")
    print("="*70)

    client = GeminiClient(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        max_tokens=settings.gemini_max_tokens,
        temperature=settings.gemini_temperature,
        retry_delay=1.0,  # 1 second base delay
        max_retries=3     # 3 maximum retries
    )

    print(f"\nClient Configuration:")
    print(f"  - Retry Delay: {client.retry_delay}s")
    print(f"  - Max Retries: {client.max_retries}")
    print(f"  - Model: {client.model_name}")

    queries = [
        "What is the capital of France?",
        "List 3 famous landmarks in Rome",
        "Tell me about the history of the Statue of Liberty",
        "What are the top 5 tourist attractions in Tokyo?",
        "Describe the architectural style of Big Ben"
    ]

    results = {"success": 0, "failed": 0, "retry_count": 0}

    def execute_query(query_idx: int, query: str):
        """Execute a single query and track results."""
        print(f"\n[Query {query_idx + 1}] Sending: {query[:50]}...")
        try:
            start_time = time.time()
            response = client.simple_query(query)
            elapsed = time.time() - start_time
            print(f"[Query {query_idx + 1}] ✓ Success in {elapsed:.2f}s: {response[:80]}...")
            return {"status": "success", "time": elapsed, "response": response[:100]}
        except Exception as e:
            print(f"[Query {query_idx + 1}] ✗ Failed: {str(e)[:100]}")
            return {"status": "failed", "error": str(e)}

    print(f"\n{'-'*70}")
    print(f"Executing {num_queries} queries in parallel...")
    print(f"{'-'*70}\n")

    with ThreadPoolExecutor(max_workers=num_queries) as executor:
        futures = []
        for i, query in enumerate(queries[:num_queries]):
            future = executor.submit(execute_query, i, query)
            futures.append(future)

        for future in as_completed(futures):
            result = future.result()
            if result["status"] == "success":
                results["success"] += 1
            else:
                results["failed"] += 1

    # Summary
    print(f"\n{'='*70}")
    print("Test Results")
    print(f"{'='*70}")
    print(f"Total Queries: {num_queries}")
    print(f"Successful: {results['success']}")
    print(f"Failed: {results['failed']}")
    print(f"Success Rate: {(results['success'] / num_queries * 100):.1f}%")

    if results['success'] == num_queries:
        print(f"\n✓ All queries succeeded!")
        print(f"  The retry logic handled the load without issues.")
    elif results['failed'] > 0:
        print(f"\n⚠ Some queries failed")
        print(f"  Check logs for rate limit (429) errors and retry attempts.")

    print(f"{'='*70}\n")

    return results['success'] == num_queries

if __name__ == "__main__":
    try:
        success = test_concurrent_queries(num_queries=3)
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)
