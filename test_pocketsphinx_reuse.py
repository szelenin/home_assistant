#!/usr/bin/env python3
"""
Test script to verify PocketSphinx audio stream reuse functionality.
"""

import sys
import os
import time

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(__file__))

from home_assistant.wake_word.providers.pocketsphinx_provider import PocketSphinxProvider

def test_pocketsphinx_reuse():
    """Test PocketSphinx audio stream reuse by making multiple calls."""
    print("Testing PocketSphinx audio stream reuse...")

    try:
        # Create PocketSphinx provider
        config = {
            'keyphrase_threshold': 1e-20
        }
        provider = PocketSphinxProvider(config)

        if not provider.is_available():
            print("❌ PocketSphinx provider not available")
            return False

        print("✅ PocketSphinx provider initialized")

        # Test 1: First call with short timeout
        print("\n🔍 Test 1: First wake word detection call (3 second timeout)")
        start_time = time.time()
        detected, confidence = provider.listen_for_wake_word("jarvis", timeout=3)
        duration = time.time() - start_time
        print(f"Result: detected={detected}, confidence={confidence:.3f}, duration={duration:.1f}s")

        # Test 2: Second call immediately after (this would fail before the fix)
        print("\n🔍 Test 2: Second wake word detection call (3 second timeout)")
        start_time = time.time()
        detected, confidence = provider.listen_for_wake_word("jarvis", timeout=3)
        duration = time.time() - start_time
        print(f"Result: detected={detected}, confidence={confidence:.3f}, duration={duration:.1f}s")

        # Test 3: Third call to confirm it's working
        print("\n🔍 Test 3: Third wake word detection call (3 second timeout)")
        start_time = time.time()
        detected, confidence = provider.listen_for_wake_word("jarvis", timeout=3)
        duration = time.time() - start_time
        print(f"Result: detected={detected}, confidence={confidence:.3f}, duration={duration:.1f}s")

        print("\n✅ All tests completed! Audio stream reuse is working.")

        # Cleanup
        provider.cleanup()
        print("✅ Cleanup completed")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pocketsphinx_reuse()
    sys.exit(0 if success else 1)