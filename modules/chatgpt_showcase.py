#!/usr/bin/env python3
"""
ChatGPT Showcase - Demo of ChatGPT Integration

This script demonstrates the ChatGPT module functionality
and provides a simple interface for testing.
"""

import os
import sys
import time

# Add src directory to Python path for logger import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from utils.logger import setup_logging
from chatgpt import ChatGPT


def main():
    logger = setup_logging("home_assistant.chatgpt_showcase")
    logger.info("ChatGPT Showcase Starting...")
    
    # Initialize ChatGPT
    chatgpt = ChatGPT()
    
    # Configure ChatGPT
    chatgpt.model("gpt-4")
    chatgpt.customiseResponse({
        "temperature": 0.7,
        "max_tokens": 150
    })
    
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.warning("No real API key found. Running in demo mode...")
        logger.info("To test with real API, set OPENAI_API_KEY environment variable")
        logger.info("Demo mode will show the structure without making API calls")
        
        logger.info("ChatGPT Module Structure:")
        logger.info("Model: gpt-4")
        logger.info("Temperature: 0.7")
        logger.info("Message logging: Enabled")
        logger.info("Auto-cleanup: 30 days")
        
        logger.info("Example prompt: 'What's the capital of France?'")
        logger.info("Expected response: 'The capital of France is Paris.'")
        
        logger.info("ChatGPT showcase completed successfully!")
        return
    
    # Set API token
    chatgpt.token(api_key)
    
    try:
        logger.info("Testing ChatGPT with a simple question...")
        response = chatgpt.prompt("What's the capital of France?")
        logger.info(f"Response: {response}")
        
        # Test cleanup
        logger.info("Cleaning up old messages...")
        chatgpt.clearMessages()
        logger.info("ChatGPT showcase completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in ChatGPT showcase: {e}")
        
        logger.info("Tip: Set your OpenAI API key as environment variable:")
        logger.info("export OPENAI_API_KEY='your-actual-api-key'")
        
    except KeyboardInterrupt:
        logger.info("ChatGPT showcase interrupted by user")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger = setup_logging("home_assistant.chatgpt_showcase")
        logger.info("ChatGPT showcase interrupted by user")
    except Exception as e:
        logger = setup_logging("home_assistant.chatgpt_showcase")
        logger.critical(f"Fatal error: {e}")
