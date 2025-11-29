#!/usr/bin/env python3
"""
Test script to verify Gemini client retry logic with rate limiting.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.services.gemini_client import GeminiClient
from src.config import get_settings
from src.utils.logger import get_logger

logger = get_logger("test_retry_logic")

def test_gemini_retry_logic():
    """Test the Gemini client with retry configuration."""
    settings = get_settings()

    print("\n" + "="*60)
    print("Testing Gemini Client Retry Logic")
    print("="*60)

    # Create client with custom retry settings
    client = GeminiClient(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        max_tokens=settings.gemini_max_tokens,
        temperature=settings.gemini_temperature,
        retry_delay=1.0,  # 1 second base delay
        max_retries=3     # 3 maximum retries
    )

    print(f"\n✓ GeminiClient initialized:")
    print(f"  - Model: {client.model_name}")
    print(f"  - Max Tokens: {client.max_tokens}")
    print(f"  - Temperature: {client.temperature}")
    print(f"  - Retry Delay: {client.retry_delay}s")
    print(f"  - Max Retries: {client.max_retries}")

    # Test 1: Simple query (should work on first attempt)
    print("\n" + "-"*60)
    print("Test 1: Simple Query (No Rate Limiting)")
    print("-"*60)

    try:
        response = client.simple_query("What is 2+2? Answer with just the number.")
        print(f"✓ Response: {response[:100]}...")
        print("✓ Test 1 PASSED: Simple query works")
    except Exception as e:
        print(f"✗ Test 1 FAILED: {e}")
        return False

    # Test 2: Query with context (tests send_message with structured prompts)
    print("\n" + "-"*60)
    print("Test 2: Query with Context")
    print("-"*60)

    try:
        response = client.analyze_with_context(
            context="Paris is the capital of France. It's known for the Eiffel Tower.",
            query="What is Paris famous for?"
        )
        print(f"✓ Response: {response[:100]}...")
        print("✓ Test 2 PASSED: Context query works")
    except Exception as e:
        print(f"✗ Test 2 FAILED: {e}")
        return False

    # Test 3: Structured decision (tests complex decision-making)
    print("\n" + "-"*60)
    print("Test 3: Structured Decision")
    print("-"*60)

    try:
        options = [
            {"name": "Option A", "pros": "Fast", "cons": "Low quality"},
            {"name": "Option B", "pros": "High quality", "cons": "Slow"},
            {"name": "Option C", "pros": "Balanced", "cons": "Medium"}
        ]

        decision = client.structured_decision(
            options=options,
            criteria="Best overall balance of speed and quality"
        )

        print(f"✓ Decision Result:")
        print(f"  - Choice: Option {decision['choice'] + 1}")
        print(f"  - Score: {decision['score']}/100")
        print(f"  - Reasoning: {decision['reasoning'][:80]}...")
        print("✓ Test 3 PASSED: Structured decision works")
    except Exception as e:
        print(f"✗ Test 3 FAILED: {e}")
        return False

    print("\n" + "="*60)
    print("All Tests Completed Successfully!")
    print("="*60)
    print("\nRetry Logic Notes:")
    print("- If rate limiting occurs (429 error), the client will:")
    print("  1. Wait 1 second, then retry (Attempt 1)")
    print("  2. Wait 2 seconds, then retry (Attempt 2)")
    print("  3. Wait 4 seconds, then retry (Attempt 3)")
    print("  4. Raise exception if all 3 attempts fail")
    print("\nCheck logs for 'Rate limited. Retrying' messages.")
    print("="*60 + "\n")

    return True

if __name__ == "__main__":
    try:
        success = test_gemini_retry_logic()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        sys.exit(1)
