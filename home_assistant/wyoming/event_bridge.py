"""Event bridge between Wyoming protocol and Home Assistant.

This module bridges Wyoming protocol events to the existing Home Assistant
voice control system, enabling seamless integration of distributed satellites.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
import io
import wave

from wyoming.audio import AudioStart, AudioChunk, AudioStop
from wyoming.event import Event

from ..utils.logger import setup_logging


@dataclass
class SatelliteSession:
    """Represents an active satellite session."""

    client_id: str
    satellite_name: str
    is_processing: bool = False
    current_audio: Optional[bytes] = None
    transcribed_text: Optional[str] = None
    ai_response: Optional[str] = None


class EventBridge:
    """Bridges Wyoming events to Home Assistant voice control system."""

    def __init__(self):
        """Initialize the event bridge."""
        self.logger = setup_logging("wyoming.bridge")
        self.sessions: Dict[str, SatelliteSession] = {}

        # References to Home Assistant components (will be set during integration)
        self.speech_recognizer = None
        self.tts_engine = None
        self.ai_orchestrator = None
        self.wake_word_detector = None

        # Event callbacks
        self._event_callbacks: Dict[str, List[Callable]] = {}

        self.logger.info("Wyoming event bridge initialized")

    def set_home_assistant_components(
        self,
        speech_recognizer=None,
        tts_engine=None,
        ai_orchestrator=None,
        wake_word_detector=None
    ) -> None:
        """Set references to Home Assistant components.

        Args:
            speech_recognizer: Speech recognition component
            tts_engine: Text-to-speech component
            ai_orchestrator: AI conversation component
            wake_word_detector: Wake word detection component
        """
        self.speech_recognizer = speech_recognizer
        self.tts_engine = tts_engine
        self.ai_orchestrator = ai_orchestrator
        self.wake_word_detector = wake_word_detector

        self.logger.info("Home Assistant components connected to Wyoming bridge")

    async def on_satellite_connected(self, client_id: str, satellite_name: str) -> None:
        """Handle satellite connection.

        Args:
            client_id: Client connection ID
            satellite_name: Name of the satellite
        """
        self.logger.info(f"Satellite connected: {satellite_name} ({client_id})")

        # Create session for this satellite
        self.sessions[client_id] = SatelliteSession(
            client_id=client_id,
            satellite_name=satellite_name
        )

        # Trigger connected callbacks
        await self._trigger_callbacks('satellite_connected', client_id, satellite_name)

    async def on_satellite_disconnected(self, client_id: str) -> None:
        """Handle satellite disconnection.

        Args:
            client_id: Client connection ID
        """
        self.logger.info(f"Satellite disconnected: {client_id}")

        # Clean up session
        if client_id in self.sessions:
            del self.sessions[client_id]

        # Trigger disconnected callbacks
        await self._trigger_callbacks('satellite_disconnected', client_id)

    async def on_audio_start(self, client_id: str, event: AudioStart) -> None:
        """Handle start of audio streaming.

        Args:
            client_id: Client connection ID
            event: AudioStart event
        """
        if client_id not in self.sessions:
            self.logger.warning(f"Unknown client {client_id} starting audio")
            return

        session = self.sessions[client_id]
        session.is_processing = True
        session.current_audio = b''

        self.logger.debug(
            f"Audio started from {session.satellite_name}: "
            f"rate={event.rate}, width={event.width}, channels={event.channels}"
        )

    async def on_audio_chunk(self, client_id: str, event: AudioChunk) -> None:
        """Handle audio chunk from satellite.

        Args:
            client_id: Client connection ID
            event: AudioChunk event
        """
        if client_id not in self.sessions:
            return

        session = self.sessions[client_id]
        if session.current_audio is not None:
            session.current_audio += event.audio

    async def on_audio_complete(
        self,
        client_id: str,
        audio_data: bytes,
        rate: int,
        width: int,
        channels: int
    ) -> Optional[Dict[str, Any]]:
        """Handle complete audio from satellite.

        Args:
            client_id: Client connection ID
            audio_data: Complete audio data
            rate: Sample rate
            width: Sample width
            channels: Number of channels

        Returns:
            Dictionary with processing results
        """
        if client_id not in self.sessions:
            return None

        session = self.sessions[client_id]
        session.current_audio = audio_data
        session.is_processing = True

        self.logger.info(f"Processing audio from {session.satellite_name}")

        result = {}

        try:
            # 1. Speech Recognition (STT)
            if self.speech_recognizer and audio_data:
                # Convert audio to format expected by speech recognizer
                wav_data = self._convert_to_wav(audio_data, rate, width, channels)

                # Perform speech recognition
                transcript = await self._perform_speech_recognition(wav_data)

                if transcript:
                    session.transcribed_text = transcript
                    result['transcript'] = transcript
                    self.logger.info(f"Transcript: {transcript}")

                    # 2. AI Processing
                    if self.ai_orchestrator:
                        ai_response = await self._process_with_ai(transcript)

                        if ai_response:
                            session.ai_response = ai_response
                            result['ai_response'] = ai_response
                            self.logger.info(f"AI Response: {ai_response[:100]}...")

                            # 3. Text-to-Speech (TTS)
                            if self.tts_engine:
                                tts_audio = await self._generate_tts(ai_response, rate)

                                if tts_audio:
                                    result['tts_audio'] = tts_audio
                                    self.logger.info(f"Generated TTS audio: {len(tts_audio)} bytes")

        except Exception as e:
            self.logger.error(f"Error processing audio from {session.satellite_name}: {e}")
            result['error'] = str(e)

        finally:
            session.is_processing = False

        return result

    async def run_pipeline(
        self,
        client_id: str,
        pipeline_name: Optional[str],
        text: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Run a voice pipeline for a satellite.

        Args:
            client_id: Client connection ID
            pipeline_name: Name of pipeline to run
            text: Optional text input (for text-based pipelines)

        Returns:
            Dictionary with pipeline results
        """
        if client_id not in self.sessions:
            return None

        session = self.sessions[client_id]
        self.logger.info(f"Running pipeline '{pipeline_name}' for {session.satellite_name}")

        result = {}

        try:
            if text:
                # Text-based pipeline
                session.transcribed_text = text

                # Process with AI
                if self.ai_orchestrator:
                    ai_response = await self._process_with_ai(text)

                    if ai_response:
                        session.ai_response = ai_response
                        result['ai_response'] = ai_response

                        # Generate TTS
                        if self.tts_engine:
                            tts_audio = await self._generate_tts(ai_response)

                            if tts_audio:
                                result['tts_audio'] = tts_audio

        except Exception as e:
            self.logger.error(f"Error running pipeline: {e}")
            result['error'] = str(e)

        return result

    async def _perform_speech_recognition(self, audio_data: bytes) -> Optional[str]:
        """Perform speech recognition on audio data.

        Args:
            audio_data: WAV audio data

        Returns:
            Transcribed text or None
        """
        if not self.speech_recognizer:
            return None

        try:
            # Use the existing speech recognizer from Home Assistant
            # This would typically call your Whisper-based recognizer
            transcript = await asyncio.get_event_loop().run_in_executor(
                None,
                self.speech_recognizer.recognize_from_audio_data,
                audio_data
            )
            return transcript
        except Exception as e:
            self.logger.error(f"Speech recognition failed: {e}")
            return None

    async def _process_with_ai(self, text: str) -> Optional[str]:
        """Process text with AI orchestrator.

        Args:
            text: Input text

        Returns:
            AI response or None
        """
        if not self.ai_orchestrator:
            return None

        try:
            # Use the existing AI orchestrator from Home Assistant
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                self.ai_orchestrator.process_query,
                text
            )
            return response
        except Exception as e:
            self.logger.error(f"AI processing failed: {e}")
            return None

    async def _generate_tts(self, text: str, target_rate: int = 22050) -> Optional[bytes]:
        """Generate TTS audio from text.

        Args:
            text: Text to synthesize
            target_rate: Target sample rate for audio

        Returns:
            Raw audio data or None
        """
        if not self.tts_engine:
            return None

        try:
            # Use the existing TTS engine from Home Assistant
            # This needs to return raw audio data
            audio_data = await asyncio.get_event_loop().run_in_executor(
                None,
                self._generate_tts_sync,
                text,
                target_rate
            )
            return audio_data
        except Exception as e:
            self.logger.error(f"TTS generation failed: {e}")
            return None

    def _generate_tts_sync(self, text: str, target_rate: int) -> bytes:
        """Synchronous TTS generation.

        Args:
            text: Text to synthesize
            target_rate: Target sample rate

        Returns:
            Raw audio data
        """
        # This is a placeholder - you'll need to integrate with your actual TTS
        # For now, return empty audio
        return b''

    def _convert_to_wav(
        self,
        audio_data: bytes,
        rate: int,
        width: int,
        channels: int
    ) -> bytes:
        """Convert raw audio to WAV format.

        Args:
            audio_data: Raw audio data
            rate: Sample rate
            width: Sample width
            channels: Number of channels

        Returns:
            WAV file data
        """
        with io.BytesIO() as wav_buffer:
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(channels)
                wav_file.setsampwidth(width)
                wav_file.setframerate(rate)
                wav_file.writeframes(audio_data)

            return wav_buffer.getvalue()

    def register_callback(self, event_type: str, callback: Callable) -> None:
        """Register a callback for an event type.

        Args:
            event_type: Type of event
            callback: Callback function
        """
        if event_type not in self._event_callbacks:
            self._event_callbacks[event_type] = []

        self._event_callbacks[event_type].append(callback)
        self.logger.debug(f"Registered callback for {event_type}")

    async def _trigger_callbacks(self, event_type: str, *args, **kwargs) -> None:
        """Trigger all callbacks for an event type.

        Args:
            event_type: Type of event
            args: Positional arguments for callbacks
            kwargs: Keyword arguments for callbacks
        """
        if event_type not in self._event_callbacks:
            return

        for callback in self._event_callbacks[event_type]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(*args, **kwargs)
                else:
                    await asyncio.get_event_loop().run_in_executor(
                        None,
                        callback,
                        *args,
                        **kwargs
                    )
            except Exception as e:
                self.logger.error(f"Callback error for {event_type}: {e}")

    def get_session(self, client_id: str) -> Optional[SatelliteSession]:
        """Get session for a client.

        Args:
            client_id: Client connection ID

        Returns:
            Satellite session or None
        """
        return self.sessions.get(client_id)

    def get_all_sessions(self) -> Dict[str, SatelliteSession]:
        """Get all active sessions.

        Returns:
            Dictionary of all sessions
        """
        return self.sessions.copy()