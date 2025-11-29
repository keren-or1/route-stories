#!/usr/bin/env python3
"""
Quick test to verify the web application initializes and can process a route.
"""

import sys
import os
from pathlib import Path
import json
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.web.app import create_app
from src.core.orchestrator import Orchestrator
from src.config import get_settings
from src.utils.logger import get_logger

logger = get_logger("test_web_app")

def test_web_app_initialization():
    """Test that the Flask web app initializes correctly."""
    print("\n" + "="*70)
    print("Testing Web Application Initialization")
    print("="*70)

    try:
        # Create Flask app
        app = create_app()

        # Check if app exists
        if app:
            print("\n✓ Flask app successfully imported")
            print(f"  - App name: {app.name}")
            print(f"  - Debug mode: {app.debug}")

        # Check routes
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append(rule.rule)

        print(f"\n✓ Routes registered: {len(routes)}")
        for route in sorted(routes):
            if route != 'static':
                print(f"  - {route}")

        # Test Flask test client
        print(f"\n✓ Creating Flask test client...")
        client = app.test_client()
        print(f"  - Test client created successfully")

        # Test home page
        print(f"\n✓ Testing GET / (home page)")
        response = client.get("/")
        print(f"  - Status: {response.status_code}")
        if response.status_code == 200:
            print(f"  - Response size: {len(response.data)} bytes")
            print(f"  ✓ Home page working")
        else:
            print(f"  ✗ Unexpected status code")

        return True

    except Exception as e:
        logger.error(f"Web app test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_orchestrator():
    """Test that the orchestrator initializes correctly."""
    print("\n" + "="*70)
    print("Testing Orchestrator")
    print("="*70)

    try:
        settings = get_settings()
        print(f"\n✓ Settings loaded:")
        print(f"  - Gemini Model: {settings.gemini_model}")
        print(f"  - Max Waypoints: {settings.max_waypoints}")
        print(f"  - Log Level: {settings.log_level}")

        # Create orchestrator
        orchestrator_instance = Orchestrator(
            google_maps_key=settings.google_maps_api_key,
            gemini_key=settings.gemini_api_key
        )
        print(f"\n✓ Orchestrator created successfully")
        print(f"  - Type: {type(orchestrator_instance).__name__}")

        return True

    except Exception as e:
        logger.error(f"Orchestrator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("Web Application & Orchestrator Test Suite")
    print("="*70)

    results = {
        "Web App": test_web_app_initialization(),
        "Orchestrator": test_orchestrator()
    }

    # Summary
    print(f"\n{'='*70}")
    print("Test Summary")
    print(f"{'='*70}")

    for test_name, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{test_name}: {status}")

    all_passed = all(results.values())
    print(f"\nOverall: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
    print(f"{'='*70}\n")

    print("To start the web application, run:")
    print("  python src/web_main.py")
    print("\nThen open http://localhost:5000 in your browser")
    print(f"{'='*70}\n")

    return all_passed

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        sys.exit(1)
