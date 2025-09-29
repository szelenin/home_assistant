#!/usr/bin/env python3
"""Test script to run Wyoming server."""

import asyncio
import logging
import signal
from home_assistant.wyoming.jarvis_integration import WyomingJarvisIntegration

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    """Main function."""
    print("Starting Wyoming Server for Home Assistant...")
    print("=" * 50)

    # Create integration
    integration = WyomingJarvisIntegration()

    # Handle shutdown
    shutdown_event = asyncio.Event()

    def signal_handler(sig, frame):
        print("\n\nShutting down Wyoming server...")
        shutdown_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Initialize and start
        print("Initializing Wyoming-Jarvis integration...")
        await integration.initialize()

        print("Starting Wyoming server on port 10700...")
        await integration.start()

        print("\n" + "=" * 50)
        print("Wyoming server is running!")
        print("Listening on: 0.0.0.0:10700")
        print("")
        print("You can now:")
        print("1. Connect Wyoming satellites to this server")
        print("2. Run the test client: ./venv/bin/python test_wyoming_client.py")
        print("")
        print("Press Ctrl+C to stop the server")
        print("=" * 50 + "\n")

        # Get status
        status = integration.get_status()
        print(f"Status: {status}")

        # Wait for shutdown
        await shutdown_event.wait()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Clean shutdown
        print("\nStopping server...")
        await integration.stop()
        print("Server stopped. Goodbye!")


if __name__ == "__main__":
    asyncio.run(main())