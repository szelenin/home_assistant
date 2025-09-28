#!/usr/bin/env python3
"""
Test script to verify the language API functionality without full system.
"""

import sys
import os

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(__file__))

from home_assistant.apis.home_apis import HomeAPIs

def test_language_api():
    """Test the language support API directly."""
    print("Testing Language Support API...")

    try:
        # Create API instance
        api = HomeAPIs()

        # Call the language support method
        result = api.get_supported_languages()

        print("✅ API call successful!")
        print(f"Result: {result}")

        # Check if we got expected fields
        if 'supported_languages' in result:
            print(f"Found {len(result['supported_languages'])} supported languages")
            print(f"TTS Provider: {result.get('tts_provider', 'unknown')}")
            print(f"STT Provider: {result.get('stt_provider', 'unknown')}")

            # Show first few languages
            if result['supported_languages']:
                print("First 5 languages:")
                for lang in result['supported_languages'][:5]:
                    print(f"  - {lang['name']} ({lang['code']})")

        return True

    except Exception as e:
        print(f"❌ API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_language_api()
    sys.exit(0 if success else 1)