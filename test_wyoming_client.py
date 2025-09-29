#!/usr/bin/env python3
"""Test client for Wyoming server.

This script tests the Wyoming server by simulating a satellite connection.
"""

import asyncio
import logging
import sys
from wyoming.info import Describe
from wyoming.satellite import RunSatellite
from wyoming.ping import Ping
from wyoming.audio import AudioStart, AudioChunk, AudioStop
from wyoming.event import async_read_event, async_write_event

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_client")


async def test_wyoming_connection():
    """Test connection to Wyoming server."""
    host = "localhost"
    port = 10700

    logger.info(f"Connecting to Wyoming server at {host}:{port}...")

    try:
        # Connect to server
        reader, writer = await asyncio.open_connection(host, port)
        logger.info("Connected to Wyoming server")

        # Request server info
        logger.info("Requesting server info...")
        describe = Describe()
        await async_write_event(describe, writer)

        # Read server info response
        response = await async_read_event(reader)
        logger.info(f"Server info: {response}")

        # Register as a satellite
        logger.info("Registering as satellite...")
        run_satellite = RunSatellite(name="test_satellite")
        await async_write_event(run_satellite, writer)

        # Read connection confirmation
        response = await async_read_event(reader)
        logger.info(f"Registration response: {response}")

        # Send a ping
        logger.info("Sending ping...")
        ping = Ping(text="test_ping")
        await async_write_event(ping, writer)

        # Read pong response
        response = await async_read_event(reader)
        logger.info(f"Pong response: {response}")

        # Simulate audio streaming
        logger.info("Starting audio stream simulation...")

        # Send audio start
        audio_start = AudioStart(rate=16000, width=2, channels=1)
        await async_write_event(audio_start, writer)

        # Wait for streaming started confirmation
        response = await async_read_event(reader)
        logger.info(f"Streaming start response: {response}")

        # Send some fake audio chunks
        for i in range(5):
            # Create fake audio data (silence)
            audio_data = bytes(1024)  # 1024 bytes of silence
            audio_chunk = AudioChunk(
                audio=audio_data,
                rate=16000,
                width=2,
                channels=1
            )
            await async_write_event(audio_chunk, writer)
            logger.debug(f"Sent audio chunk {i+1}/5")
            await asyncio.sleep(0.1)

        # Send audio stop
        audio_stop = AudioStop()
        await async_write_event(audio_stop, writer)

        # Wait for streaming stopped confirmation
        response = await async_read_event(reader)
        logger.info(f"Streaming stop response: {response}")

        # Wait a bit for any additional responses
        logger.info("Waiting for any additional responses...")
        try:
            response = await asyncio.wait_for(async_read_event(reader), timeout=2.0)
            logger.info(f"Additional response: {response}")
        except asyncio.TimeoutError:
            logger.info("No additional responses (expected)")

        # Clean disconnect
        logger.info("Disconnecting...")
        writer.close()
        await writer.wait_closed()

        logger.info("Test completed successfully!")
        return True

    except ConnectionRefusedError:
        logger.error(f"Connection refused - is the Wyoming server running on {host}:{port}?")
        return False
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False


async def main():
    """Main function."""
    logger.info("Starting Wyoming server test client...")

    success = await test_wyoming_connection()

    if success:
        logger.info("✅ All tests passed!")
        sys.exit(0)
    else:
        logger.error("❌ Tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())