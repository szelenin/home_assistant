#!/usr/bin/env python3
"""
Home Assistant - Main Entry Point

This script initializes the Home Assistant and handles the initial setup
including wake word configuration.
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.config import ConfigManager
from src.utils.name_collector import NameCollector
from src.speech.tts import TextToSpeech


def main():
    print("Home Assistant Starting...")
    
    # Initialize configuration manager
    config_manager = ConfigManager()
    
    # Check if wake word is configured
    wake_word = config_manager.get_wake_word()
    
    if not wake_word:
        print("Wake word not configured. Starting name collection process...")
        
        # Initialize TTS for welcome message
        tts = TextToSpeech()
        tts.speak("Hello! I'm your new Home Assistant. I need you to give me a name so I know when you're talking to me.")
        
        # Collect the name
        name_collector = NameCollector()
        collected_name = name_collector.collect_name(timeout_minutes=1)
        
        if collected_name:
            config_manager.set_wake_word(collected_name)
            print(f"Wake word configured: {collected_name}")
            tts.speak(f"Perfect! From now on, just say '{collected_name}' to get my attention.")
        else:
            print("Failed to collect wake word. Exiting...")
            tts.speak("I couldn't understand your response. Please try running the assistant again.")
            sys.exit(1)
    else:
        print(f"Wake word already configured: {wake_word}")
        tts = TextToSpeech()
        tts.speak(f"Hello! I'm {wake_word}, your Home Assistant. I'm ready to help!")
    
    # TODO: Continue with main assistant loop
    print("Assistant setup complete. Main functionality not yet implemented.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nShutting down Home Assistant...")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)