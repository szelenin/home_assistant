#!/usr/bin/env python3
"""
Voice Configuration Test Script

This script helps you explore different voice settings and find the perfect voice for your Home Assistant.
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.speech.tts import TextToSpeech

def test_voice_configurations():
    """Test different voice configurations."""
    print("🎤 Voice Configuration Test")
    print("=" * 50)
    
    # Test 1: Default settings (like test_tts_detailed.py)
    print("\n1️⃣ Testing default configuration (like test_tts_detailed.py):")
    tts_default = TextToSpeech()
    tts_default.speak("Hello! This is the default voice configuration.")
    
    # Test 2: List all available voices
    print("\n2️⃣ Available voices on your system:")
    tts_default.list_voices()
    
    # Test 3: Different speech rates
    print("\n3️⃣ Testing different speech rates:")
    rates = [100, 150, 200, 250]
    for rate in rates:
        print(f"\n--- Testing rate: {rate} WPM ---")
        tts = TextToSpeech(rate=rate)
        tts.speak(f"This is speech at {rate} words per minute.")
    
    # Test 4: Different volumes
    print("\n4️⃣ Testing different volumes:")
    volumes = [0.3, 0.6, 1.0]
    for volume in volumes:
        print(f"\n--- Testing volume: {volume} ---")
        tts = TextToSpeech(volume=volume)
        tts.speak(f"This is speech at volume level {volume}.")
    
    print("\n✅ Voice configuration test completed!")
    print("\n💡 Tips:")
    print("   - Use tts.list_voices() to see all available voices")
    print("   - Use tts.set_voice('voice_id') to change voice")
    print("   - Use tts.set_rate(150) to change speech speed")
    print("   - Use tts.set_volume(0.8) to change volume")

def interactive_voice_test():
    """Interactive voice testing."""
    print("\n🎤 Interactive Voice Testing")
    print("=" * 50)
    
    tts = TextToSpeech()
    
    while True:
        print("\nOptions:")
        print("1. List all voices")
        print("2. Test current voice")
        print("3. Change voice")
        print("4. Change speech rate")
        print("5. Change volume")
        print("6. Exit")
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == '1':
            tts.list_voices()
        
        elif choice == '2':
            text = input("Enter text to speak: ")
            tts.speak(text)
        
        elif choice == '3':
            voice_id = input("Enter voice ID: ")
            tts.set_voice(voice_id)
        
        elif choice == '4':
            try:
                rate = int(input("Enter speech rate (WPM): "))
                tts.set_rate(rate)
            except ValueError:
                print("❌ Please enter a valid number")
        
        elif choice == '5':
            try:
                volume = float(input("Enter volume (0.0-1.0): "))
                if 0.0 <= volume <= 1.0:
                    tts.set_volume(volume)
                else:
                    print("❌ Volume must be between 0.0 and 1.0")
            except ValueError:
                print("❌ Please enter a valid number")
        
        elif choice == '6':
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please enter 1-6.")

if __name__ == "__main__":
    print("🎤 Voice Configuration Explorer")
    print("=" * 50)
    
    # Run automatic tests
    test_voice_configurations()
    
    # Ask if user wants interactive testing
    response = input("\nWould you like to try interactive voice testing? (y/n): ").strip().lower()
    if response in ['y', 'yes']:
        interactive_voice_test() 