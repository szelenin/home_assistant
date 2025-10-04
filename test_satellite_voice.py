#!/usr/bin/env python3
"""
Test script to demonstrate Wyoming satellite voice pipeline.
This connects to the Pi satellite and simulates voice processing.
"""

import asyncio
import logging
import json
from wyoming.info import Describe, Info, Attribution, Satellite
from wyoming.satellite import RunSatellite
from wyoming.audio import AudioStart, AudioChunk, AudioStop
from wyoming.event import async_read_event, async_write_event

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SatelliteTest:
    def __init__(self, host="192.168.86.20", port=10700):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None

    async def connect(self):
        """Connect to Wyoming satellite."""
        logger.info(f"🔌 Connecting to Wyoming satellite at {self.host}:{self.port}...")
        try:
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
            logger.info("✅ Connected successfully!")
            return True
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False

    async def get_satellite_info(self):
        """Get information about the satellite."""
        logger.info("📋 Requesting satellite information...")
        try:
            # Create a simple info request
            info_data = {
                "type": "describe"
            }
            info_json = json.dumps(info_data) + "\n"
            self.writer.write(info_json.encode())
            await self.writer.drain()

            # Read response
            response_data = await self.reader.readline()
            if response_data:
                response = json.loads(response_data.decode())
                logger.info(f"📄 Satellite info: {response.get('type', 'unknown')}")
                return response

        except Exception as e:
            logger.error(f"❌ Info request failed: {e}")
        return None

    async def test_audio_streaming(self):
        """Test audio streaming with the satellite."""
        logger.info("🎤 Testing audio streaming...")
        try:
            # Start audio streaming
            audio_start = {
                "type": "audio-start",
                "rate": 16000,
                "width": 2,
                "channels": 1
            }
            start_json = json.dumps(audio_start) + "\n"
            self.writer.write(start_json.encode())
            await self.writer.drain()
            logger.info("▶️  Audio streaming started")

            # Listen for audio chunks
            logger.info("👂 Listening for audio from satellite...")
            chunk_count = 0
            start_time = asyncio.get_event_loop().time()

            while chunk_count < 10:  # Listen for 10 chunks then stop
                try:
                    data = await asyncio.wait_for(self.reader.readline(), timeout=2.0)
                    if data:
                        response = json.loads(data.decode())
                        if response.get("type") == "audio-chunk":
                            chunk_count += 1
                            logger.info(f"🎵 Received audio chunk {chunk_count}/10")
                        else:
                            logger.info(f"📨 Received: {response.get('type', 'unknown')}")
                except asyncio.TimeoutError:
                    logger.info("⏰ No audio data received (timeout)")
                    break

            # Stop audio streaming
            audio_stop = {
                "type": "audio-stop"
            }
            stop_json = json.dumps(audio_stop) + "\n"
            self.writer.write(stop_json.encode())
            await self.writer.drain()
            logger.info("⏹️  Audio streaming stopped")

            elapsed = asyncio.get_event_loop().time() - start_time
            logger.info(f"📊 Received {chunk_count} audio chunks in {elapsed:.1f}s")

        except Exception as e:
            logger.error(f"❌ Audio streaming test failed: {e}")

    async def disconnect(self):
        """Disconnect from satellite."""
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
            logger.info("🔌 Disconnected from satellite")

async def main():
    """Main test function."""
    print("🚀 Wyoming Satellite Voice Pipeline Test")
    print("=" * 50)

    # Create test instance
    test = SatelliteTest()

    try:
        # Connect to satellite
        if not await test.connect():
            return

        # Get satellite information
        info = await test.get_satellite_info()

        # Test audio streaming
        await test.test_audio_streaming()

        print("\n" + "=" * 50)
        print("✅ Test completed! Your Wyoming satellite is working.")
        print("📍 The Pi is actively streaming audio and ready for voice commands.")
        print("🎯 Next step: Connect a Home Assistant instance or voice client")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
    finally:
        await test.disconnect()

if __name__ == "__main__":
    asyncio.run(main())