"""Wyoming Protocol Server implementation.

This server accepts connections from Wyoming satellites and bridges them
to the existing Home Assistant voice control system.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, Set
from dataclasses import dataclass
import json
import struct
import time

from wyoming.asr import Transcript
from wyoming.audio import AudioChunk, AudioStart, AudioStop
from wyoming.event import Event, async_read_event, async_write_event
from wyoming.info import Describe, Info, AsrProgram, AsrModel, TtsProgram, TtsVoice, Attribution
from wyoming.pipeline import PipelineStage, RunPipeline
from wyoming.ping import Ping, Pong
from wyoming.satellite import (
    SatelliteConnected,
    SatelliteDisconnected,
    RunSatellite,
    StreamingStarted,
    StreamingStopped
)
from wyoming.tts import Synthesize

from ..utils.logger import setup_logging
from .audio_handler import AudioHandler
from .event_bridge import EventBridge


@dataclass
class ClientConnection:
    """Represents a connected Wyoming satellite client."""

    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter
    client_id: str
    satellite_name: Optional[str] = None
    is_streaming: bool = False
    audio_handler: Optional[AudioHandler] = None
    last_ping: float = 0


class WyomingServer:
    """Wyoming Protocol server for Home Assistant voice control."""

    def __init__(self, host: str = "0.0.0.0", port: int = 10700):
        """Initialize Wyoming server.

        Args:
            host: Host to bind to (default: all interfaces)
            port: Port to listen on (default: 10700)
        """
        self.host = host
        self.port = port
        self.logger = setup_logging("wyoming.server")

        self.server: Optional[asyncio.Server] = None
        self.clients: Dict[str, ClientConnection] = {}
        self.event_bridge = EventBridge()
        self._next_client_id = 0
        self._running = False

        self.logger.info(f"Wyoming server initialized for {host}:{port}")

    async def start(self) -> None:
        """Start the Wyoming server."""
        try:
            self.server = await asyncio.start_server(
                self._handle_client,
                self.host,
                self.port
            )
            self._running = True

            addrs = ', '.join(str(sock.getsockname()) for sock in self.server.sockets)
            self.logger.info(f"Wyoming server listening on {addrs}")

            async with self.server:
                await self.server.serve_forever()

        except Exception as e:
            self.logger.error(f"Failed to start Wyoming server: {e}")
            raise

    async def stop(self) -> None:
        """Stop the Wyoming server."""
        self._running = False

        # Close all client connections
        for client_id in list(self.clients.keys()):
            await self._disconnect_client(client_id)

        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.logger.info("Wyoming server stopped")

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter
    ) -> None:
        """Handle a new client connection.

        Args:
            reader: Stream reader for the connection
            writer: Stream writer for the connection
        """
        client_id = f"client_{self._next_client_id}"
        self._next_client_id += 1

        addr = writer.get_extra_info('peername')
        self.logger.info(f"New Wyoming client connected: {client_id} from {addr}")

        # Create client connection
        client = ClientConnection(
            reader=reader,
            writer=writer,
            client_id=client_id,
            last_ping=time.time()
        )
        self.clients[client_id] = client

        try:
            # Send server info
            await self._send_server_info(writer)

            # Handle client events
            while self._running:
                try:
                    event = await asyncio.wait_for(
                        async_read_event(reader),
                        timeout=30.0  # 30 second timeout for events
                    )

                    if event is None:
                        break

                    await self._handle_event(client, event)

                except asyncio.TimeoutError:
                    # Send ping to check if client is alive
                    await self._send_ping(client)

                except Exception as e:
                    self.logger.error(f"Error handling event from {client_id}: {e}")
                    break

        except Exception as e:
            self.logger.error(f"Client handler error for {client_id}: {e}")

        finally:
            await self._disconnect_client(client_id)

    async def _handle_event(self, client: ClientConnection, event: Event) -> None:
        """Handle an event from a Wyoming client.

        Args:
            client: Client connection
            event: Event to handle
        """
        self.logger.debug(f"Received event from {client.client_id}: {event.__class__.__name__}")

        # Handle different event types
        if isinstance(event, Describe):
            await self._handle_describe(client)

        elif isinstance(event, Ping):
            await self._handle_ping(client, event)

        elif isinstance(event, RunSatellite):
            await self._handle_run_satellite(client, event)

        elif isinstance(event, AudioStart):
            await self._handle_audio_start(client, event)

        elif isinstance(event, AudioChunk):
            await self._handle_audio_chunk(client, event)

        elif isinstance(event, AudioStop):
            await self._handle_audio_stop(client, event)

        elif isinstance(event, RunPipeline):
            await self._handle_run_pipeline(client, event)

        else:
            self.logger.debug(f"Unhandled event type: {event.__class__.__name__}")

    async def _handle_describe(self, client: ClientConnection) -> None:
        """Handle Describe request from client."""
        await self._send_server_info(client.writer)

    async def _handle_ping(self, client: ClientConnection, ping: Ping) -> None:
        """Handle ping from client."""
        client.last_ping = time.time()
        pong = Pong(text=ping.text)
        await async_write_event(pong, client.writer)

    async def _handle_run_satellite(self, client: ClientConnection, event: RunSatellite) -> None:
        """Handle satellite registration."""
        client.satellite_name = event.name
        self.logger.info(f"Satellite '{event.name}' registered as {client.client_id}")

        # Send connection confirmation
        connected = SatelliteConnected()
        await async_write_event(connected, client.writer)

        # Bridge to Home Assistant
        await self.event_bridge.on_satellite_connected(client.client_id, event.name)

    async def _handle_audio_start(self, client: ClientConnection, event: AudioStart) -> None:
        """Handle start of audio streaming from satellite."""
        client.is_streaming = True

        # Create audio handler for this stream
        client.audio_handler = AudioHandler(
            client_id=client.client_id,
            rate=event.rate,
            width=event.width,
            channels=event.channels
        )

        # Notify that streaming has started
        streaming_started = StreamingStarted()
        await async_write_event(streaming_started, client.writer)

        self.logger.info(f"Audio streaming started from {client.client_id}")

        # Bridge to Home Assistant
        await self.event_bridge.on_audio_start(client.client_id, event)

    async def _handle_audio_chunk(self, client: ClientConnection, event: AudioChunk) -> None:
        """Handle audio chunk from satellite."""
        if client.audio_handler:
            # Process audio chunk
            await client.audio_handler.process_chunk(event.audio)

            # Bridge to Home Assistant for processing
            await self.event_bridge.on_audio_chunk(client.client_id, event)

    async def _handle_audio_stop(self, client: ClientConnection, event: AudioStop) -> None:
        """Handle end of audio streaming from satellite."""
        client.is_streaming = False

        # Finalize audio handler
        if client.audio_handler:
            audio_data = await client.audio_handler.get_complete_audio()

            self.logger.info(f"Processing {len(audio_data)} bytes of audio from {client.client_id}")

            # Process complete audio through Home Assistant (STT -> AI -> TTS)
            result = await self.event_bridge.on_audio_complete(
                client.client_id,
                audio_data,
                client.audio_handler.rate,
                client.audio_handler.width,
                client.audio_handler.channels
            )

            # Send transcript if we have one
            if result and result.get('transcript'):
                transcript = Transcript(text=result['transcript'])
                await async_write_event(transcript, client.writer)
                self.logger.info(f"Sent transcript: {result['transcript'][:50]}...")

            # Send TTS audio back to satellite for playback
            if result and result.get('tts_audio'):
                self.logger.info(f"Sending TTS audio to satellite: {len(result['tts_audio'])} bytes")
                await self._send_tts_audio(client, result['tts_audio'])
            elif result and result.get('ai_response'):
                # If we have AI response but no TTS audio, generate it now
                self.logger.info("Generating TTS for AI response...")
                tts_audio = self.event_bridge._generate_tts_sync(result['ai_response'])
                if tts_audio:
                    await self._send_tts_audio(client, tts_audio)

            client.audio_handler = None

        # Notify that streaming has stopped
        streaming_stopped = StreamingStopped()
        await async_write_event(streaming_stopped, client.writer)

        self.logger.info(f"Audio streaming stopped from {client.client_id}")

    async def _handle_run_pipeline(self, client: ClientConnection, event: RunPipeline) -> None:
        """Handle pipeline run request from satellite."""
        self.logger.info(f"Running pipeline for {client.client_id}: {event.name}")

        # Bridge to Home Assistant pipeline
        result = await self.event_bridge.run_pipeline(
            client.client_id,
            event.name,
            event.text if hasattr(event, 'text') else None
        )

        # Send results back to satellite
        if result:
            if result.get('tts_audio'):
                # Send TTS audio back
                await self._send_tts_audio(client, result['tts_audio'])

    async def _send_tts_audio(self, client: ClientConnection, audio_data: bytes) -> None:
        """Send TTS audio to satellite.

        Args:
            client: Client connection
            audio_data: Audio data to send
        """
        # Send audio start
        audio_start = AudioStart(
            rate=22050,  # Default TTS rate
            width=2,
            channels=1
        )
        await async_write_event(audio_start, client.writer)

        # Send audio chunks (4096 bytes at a time)
        chunk_size = 4096
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i + chunk_size]
            audio_chunk = AudioChunk(
                audio=chunk,
                rate=22050,
                width=2,
                channels=1
            )
            await async_write_event(audio_chunk, client.writer)

        # Send audio stop
        audio_stop = AudioStop()
        await async_write_event(audio_stop, client.writer)

    async def _send_server_info(self, writer: asyncio.StreamWriter) -> None:
        """Send server info to client."""
        info = Info(
            asr=[
                AsrProgram(
                    name="whisper",
                    description="OpenAI Whisper speech recognition",
                    attribution=Attribution(
                        name="OpenAI",
                        url="https://openai.com"
                    ),
                    installed=True,
                    models=[
                        AsrModel(
                            name="base",
                            description="Base Whisper model",
                            attribution=Attribution(
                                name="OpenAI",
                                url="https://openai.com"
                            ),
                            installed=True,
                            languages=["en"]
                        )
                    ]
                )
            ],
            tts=[
                TtsProgram(
                    name="pyttsx3",
                    description="Text-to-speech using pyttsx3",
                    attribution=Attribution(
                        name="pyttsx3",
                        url="https://github.com/nateshmbhat/pyttsx3"
                    ),
                    installed=True,
                    voices=[
                        TtsVoice(
                            name="default",
                            description="Default TTS voice",
                            attribution=Attribution(
                                name="System",
                                url=""
                            ),
                            installed=True,
                            languages=["en"]
                        )
                    ]
                )
            ]
        )
        await async_write_event(info, writer)

    async def _send_ping(self, client: ClientConnection) -> None:
        """Send ping to client."""
        ping = Ping(text=f"ping_{time.time()}")
        try:
            await async_write_event(ping, client.writer)
        except Exception as e:
            self.logger.error(f"Failed to send ping to {client.client_id}: {e}")

    async def _disconnect_client(self, client_id: str) -> None:
        """Disconnect a client.

        Args:
            client_id: ID of client to disconnect
        """
        if client_id not in self.clients:
            return

        client = self.clients[client_id]

        try:
            # Send disconnection event
            disconnected = SatelliteDisconnected()
            await async_write_event(disconnected, client.writer)
        except:
            pass  # Client may already be disconnected

        # Close connection
        client.writer.close()
        await client.writer.wait_closed()

        # Remove from clients
        del self.clients[client_id]

        # Notify bridge
        await self.event_bridge.on_satellite_disconnected(client_id)

        self.logger.info(f"Client {client_id} disconnected")