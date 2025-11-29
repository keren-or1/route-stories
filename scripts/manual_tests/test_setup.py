#!/usr/bin/env python3
"""
Setup verification script for Route Stories.
Checks that all dependencies and configuration are correct.
"""

import sys
from pathlib import Path


def test_imports():
    """Test that all required packages can be imported."""
    print("Testing package imports...")

    packages = [
        ("anthropic", "Anthropic Claude API"),
        ("googlemaps", "Google Maps API"),
        ("dotenv", "python-dotenv"),
        ("requests", "requests"),
        ("pydantic", "pydantic"),
        ("pydantic_settings", "pydantic-settings"),
    ]

    all_ok = True
    for package, name in packages:
        try:
            __import__(package)
            print(f"  ✓ {name}")
        except ImportError as e:
            print(f"  ✗ {name} - MISSING")
            all_ok = False

    return all_ok


def test_env_file():
    """Test that .env file exists and has required keys."""
    print("\nChecking .env file...")

    env_path = Path(__file__).parent / ".env"

    if not env_path.exists():
        print("  ✗ .env file not found")
        print("    Run: cp .env.example .env")
        return False

    print("  ✓ .env file exists")

    # Try to load it
    try:
        from dotenv import load_dotenv
        import os

        load_dotenv()

        required_keys = [
            "GOOGLE_MAPS_API_KEY",
            "ANTHROPIC_API_KEY"
        ]

        all_ok = True
        for key in required_keys:
            value = os.getenv(key)
            if not value or value.startswith("your_"):
                print(f"  ✗ {key} not set or still has placeholder value")
                all_ok = False
            else:
                # Show first/last 4 chars for verification
                masked = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
                print(f"  ✓ {key} = {masked}")

        return all_ok

    except Exception as e:
        print(f"  ✗ Error loading .env: {e}")
        return False


def test_project_structure():
    """Test that all required directories and files exist."""
    print("\nChecking project structure...")

    base_dir = Path(__file__).parent

    required_items = [
        "main.py",
        "config.py",
        "requirements.txt",
        "agents/__init__.py",
        "services/__init__.py",
        "core/__init__.py",
        "ui/__init__.py",
        "utils/__init__.py",
    ]

    all_ok = True
    for item in required_items:
        path = base_dir / item
        if path.exists():
            print(f"  ✓ {item}")
        else:
            print(f"  ✗ {item} - MISSING")
            all_ok = False

    return all_ok


def test_api_connections():
    """Test API connections (requires valid API keys)."""
    print("\nTesting API connections...")

    try:
        from config import get_settings

        settings = get_settings()

        # Test Google Maps
        try:
            from services import GoogleMapsService
            gm = GoogleMapsService(settings.google_maps_api_key)
            print("  ✓ Google Maps client initialized")

            # Try a simple geocode
            result = gm.geocode_address("Tel Aviv, Israel")
            if result:
                print(f"  ✓ Google Maps API working (geocoded Tel Aviv to {result})")
            else:
                print("  ⚠ Google Maps API initialized but geocoding failed")

        except Exception as e:
            print(f"  ✗ Google Maps API error: {e}")
            return False

        # Test Anthropic Claude
        try:
            from services import ClaudeClient
            claude = ClaudeClient(
                api_key=settings.anthropic_api_key,
                model=settings.claude_model
            )
            print("  ✓ Claude client initialized")

            # Try a simple query
            response = claude.simple_query(
                "Respond with just the word 'OK' if you can read this.",
                temperature=0
            )
            if response and "OK" in response.upper():
                print("  ✓ Claude API working")
            else:
                print(f"  ⚠ Claude API responded but unexpected response: {response}")

        except Exception as e:
            print(f"  ✗ Claude API error: {e}")
            return False

        return True

    except Exception as e:
        print(f"  ✗ Configuration error: {e}")
        return False


def main():
    """Run all tests."""
    print("="*80)
    print("Route Stories - Setup Verification")
    print("="*80)

    results = {
        "Imports": test_imports(),
        "Environment File": test_env_file(),
        "Project Structure": test_project_structure(),
    }

    # Only test API connections if previous tests passed
    if all(results.values()):
        print("\n" + "="*80)
        response = input("All basic checks passed. Test API connections? (y/n): ")
        if response.lower() == 'y':
            results["API Connections"] = test_api_connections()

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")

    print("="*80)

    if all(results.values()):
        print("\n✓ All tests passed! You're ready to run Route Stories.")
        print("\nRun: python main.py\n")
        return 0
    else:
        print("\n✗ Some tests failed. Please fix the issues above.")
        print("\nRefer to QUICKSTART.md for setup instructions.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
