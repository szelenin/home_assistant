#!/usr/bin/env python3
"""
ChatGPT Showcase - Main Entry Point

This script demonstrates the ChatGPT module functionality.
"""

import sys
import os

# Add parent directory to Python path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from modules.chatgpt import ChatGPT


def main():
    """Main function to demonstrate ChatGPT functionality."""
    print("🤖 ChatGPT Showcase Starting...")
    
    try:
        # Initialize ChatGPT
        gpt = ChatGPT()
        
        # Check if we have a real API key or should use demo mode
        api_key = os.getenv('OPENAI_API_KEY', 'your-api-key')
        
        if api_key == 'your-api-key':
            print("⚠️  No real API key found. Running in demo mode...")
            print("📝 To test with real API, set OPENAI_API_KEY environment variable")
            print("🔧 Demo mode will show the structure without making API calls")
            
            # Demo mode - show the structure
            print("\n📋 ChatGPT Module Structure:")
            print("✅ Model: gpt-4")
            print("✅ Temperature: 0.7")
            print("✅ Message logging: Enabled")
            print("✅ Auto-cleanup: 30 days")
            
            print("\n🎯 Example prompt: 'What's the capital of France?'")
            print("🤖 Expected response: 'The capital of France is Paris.'")
            
            print("\n✅ ChatGPT showcase completed successfully!")
            return
        
        # Configure the model with real API key
        gpt.token(api_key)
        gpt.model("gpt-4")
        gpt.customiseResponse({"temperature": 0.7})
        
        # Test the model
        print("📝 Testing ChatGPT with a simple question...")
        response = gpt.prompt("What's the capital of France?")
        print(f"🤖 Response: {response}")
        
        # Clean up old messages
        print("🧹 Cleaning up old messages...")
        gpt.clearMessages()  # Will also delete logs older than 1 month
        
        print("✅ ChatGPT showcase completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in ChatGPT showcase: {e}")
        if "API key" in str(e):
            print("\n💡 Tip: Set your OpenAI API key as environment variable:")
            print("   export OPENAI_API_KEY='your-actual-api-key'")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 ChatGPT showcase interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)
