#!/usr/bin/env python3
"""
Home Assistant - Main Entry Point

This script initializes the Home Assistant and handles the initial setup
including wake word configuration.
"""

import sys
import os

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from home_assistant.utils.config import ConfigManager
from home_assistant.utils.name_collector import NameCollector
from home_assistant.speech.tts import TextToSpeech
from home_assistant.utils.logger import setup_logging


def main():
    # Setup logging
    logger = setup_logging("home_assistant.main")
    logger.info("Home Assistant Starting...")
    
    # Initialize configuration manager
    config_manager = ConfigManager()
    
    # Check if wake word is configured
    wake_word = config_manager.get_wake_word()
    
    if not wake_word:
        logger.info("Wake word not configured. Starting name collection process...")
        
        # Initialize TTS for welcome message
        tts = TextToSpeech()
        tts.speak("Hello! I'm your new Home Assistant. I need you to give me a name so I know when you're talking to me.")
        
        # Collect the name
        name_collector = NameCollector()
        collected_name = name_collector.collect_name(timeout_minutes=1)
        
        if collected_name:
            config_manager.set_wake_word(collected_name)
            logger.info(f"Wake word configured: {collected_name}")
            tts.speak(f"Perfect! From now on, just say '{collected_name}' to get my attention.")
        else:
            logger.error("Failed to collect wake word. Exiting...")
            tts.speak("I couldn't understand your response. Please try running the assistant again.")
            sys.exit(1)
    else:
        logger.info(f"Wake word already configured: {wake_word}")
        tts = TextToSpeech()
        tts.speak(f"Hello! I'm {wake_word}, your Home Assistant. I'm ready to help!")
    
    # TODO: Continue with main assistant loop
    logger.info("Assistant setup complete. Main functionality not yet implemented.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger = setup_logging("home_assistant.main")
        logger.info("Shutting down Home Assistant...")
        sys.exit(0)
    except Exception as e:
        logger = setup_logging("home_assistant.main")
        logger.critical(f"Fatal error: {e}")
        sys.exit(1)