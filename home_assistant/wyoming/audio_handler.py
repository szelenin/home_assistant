"""Audio handler for Wyoming protocol streams.

Handles buffering, processing, and conversion of audio data
from Wyoming satellites.
"""

import asyncio
import logging
import numpy as np
from typing import Optional, List
import struct
import wave
import io
from dataclasses import dataclass

from ..utils.logger import setup_logging


@dataclass
class AudioFormat:
    """Audio format configuration."""

    rate: int = 16000
    width: int = 2
    channels: int = 1

    @property
    def sample_format(self) -> str:
        """Get numpy dtype for samples."""
        if self.width == 1:
            return 'int8'
        elif self.width == 2:
            return 'int16'
        elif self.width == 4:
            return 'int32'
        else:
            raise ValueError(f"Unsupported width: {self.width}")

    @property
    def bytes_per_sample(self) -> int:
        """Get bytes per sample."""
        return self.width * self.channels


class AudioHandler:
    """Handles audio streaming from Wyoming satellites."""

    def __init__(
        self,
        client_id: str,
        rate: int = 16000,
        width: int = 2,
        channels: int = 1
    ):
        """Initialize audio handler.

        Args:
            client_id: ID of the client connection
            rate: Sample rate in Hz
            width: Sample width in bytes
            channels: Number of audio channels
        """
        self.client_id = client_id
        self.rate = rate
        self.width = width
        self.channels = channels
        self.format = AudioFormat(rate, width, channels)

        self.logger = setup_logging(f"wyoming.audio.{client_id}")
        self._audio_buffer: List[bytes] = []
        self._total_bytes = 0

        self.logger.debug(
            f"Audio handler initialized: rate={rate}Hz, width={width}B, channels={channels}"
        )

    async def process_chunk(self, audio_chunk: bytes) -> None:
        """Process an audio chunk from the satellite.

        Args:
            audio_chunk: Raw audio data chunk
        """
        self._audio_buffer.append(audio_chunk)
        self._total_bytes += len(audio_chunk)

        # Log progress periodically
        if len(self._audio_buffer) % 50 == 0:  # Every 50 chunks
            duration = self._total_bytes / (self.format.bytes_per_sample * self.rate)
            self.logger.debug(f"Buffered {duration:.2f}s of audio ({self._total_bytes} bytes)")

    async def get_complete_audio(self) -> bytes:
        """Get the complete buffered audio.

        Returns:
            Complete audio data as bytes
        """
        if not self._audio_buffer:
            return b''

        complete_audio = b''.join(self._audio_buffer)
        duration = len(complete_audio) / (self.format.bytes_per_sample * self.rate)

        self.logger.info(f"Complete audio: {duration:.2f}s ({len(complete_audio)} bytes)")
        return complete_audio

    def convert_to_wav(self, audio_data: bytes) -> bytes:
        """Convert raw audio data to WAV format.

        Args:
            audio_data: Raw audio data

        Returns:
            WAV file data as bytes
        """
        with io.BytesIO() as wav_buffer:
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(self.width)
                wav_file.setframerate(self.rate)
                wav_file.writeframes(audio_data)

            return wav_buffer.getvalue()

    def convert_to_numpy(self, audio_data: bytes) -> np.ndarray:
        """Convert raw audio data to numpy array.

        Args:
            audio_data: Raw audio data

        Returns:
            Numpy array of audio samples
        """
        # Convert bytes to numpy array
        dtype = np.dtype(self.format.sample_format)
        samples = np.frombuffer(audio_data, dtype=dtype)

        # Reshape for multi-channel audio
        if self.channels > 1:
            samples = samples.reshape(-1, self.channels)

        return samples

    def convert_from_numpy(self, samples: np.ndarray) -> bytes:
        """Convert numpy array to raw audio data.

        Args:
            samples: Numpy array of audio samples

        Returns:
            Raw audio data as bytes
        """
        # Ensure correct dtype
        dtype = np.dtype(self.format.sample_format)
        if samples.dtype != dtype:
            samples = samples.astype(dtype)

        return samples.tobytes()

    def resample(self, audio_data: bytes, target_rate: int) -> bytes:
        """Resample audio to a different rate.

        Args:
            audio_data: Raw audio data
            target_rate: Target sample rate

        Returns:
            Resampled audio data
        """
        if self.rate == target_rate:
            return audio_data

        # Convert to numpy
        samples = self.convert_to_numpy(audio_data)

        # Simple resampling using numpy (for better quality, use scipy.signal.resample)
        ratio = target_rate / self.rate
        new_length = int(len(samples) * ratio)

        if self.channels == 1:
            # Mono audio
            x_old = np.arange(len(samples))
            x_new = np.linspace(0, len(samples) - 1, new_length)
            resampled = np.interp(x_new, x_old, samples)
        else:
            # Multi-channel audio
            resampled = np.zeros((new_length, self.channels), dtype=samples.dtype)
            for channel in range(self.channels):
                x_old = np.arange(len(samples))
                x_new = np.linspace(0, len(samples) - 1, new_length)
                resampled[:, channel] = np.interp(x_new, x_old, samples[:, channel])

        return self.convert_from_numpy(resampled.astype(self.format.sample_format))

    def apply_volume(self, audio_data: bytes, volume: float) -> bytes:
        """Apply volume adjustment to audio.

        Args:
            audio_data: Raw audio data
            volume: Volume multiplier (1.0 = no change)

        Returns:
            Volume-adjusted audio data
        """
        if volume == 1.0:
            return audio_data

        samples = self.convert_to_numpy(audio_data)
        adjusted = samples * volume

        # Clip to prevent overflow
        dtype_info = np.iinfo(samples.dtype)
        adjusted = np.clip(adjusted, dtype_info.min, dtype_info.max)

        return self.convert_from_numpy(adjusted.astype(samples.dtype))

    def get_audio_stats(self, audio_data: bytes) -> dict:
        """Get statistics about audio data.

        Args:
            audio_data: Raw audio data

        Returns:
            Dictionary with audio statistics
        """
        samples = self.convert_to_numpy(audio_data)

        # Calculate statistics
        if self.channels == 1:
            rms = np.sqrt(np.mean(samples.astype(np.float32) ** 2))
            peak = np.max(np.abs(samples))
        else:
            # For multi-channel, calculate per channel
            rms = np.sqrt(np.mean(samples.astype(np.float32) ** 2, axis=0))
            peak = np.max(np.abs(samples), axis=0)

        duration = len(samples) / self.rate

        return {
            'duration': duration,
            'samples': len(samples),
            'rms': float(rms) if self.channels == 1 else rms.tolist(),
            'peak': int(peak) if self.channels == 1 else peak.tolist(),
            'rate': self.rate,
            'channels': self.channels,
            'width': self.width
        }

    def clear(self) -> None:
        """Clear the audio buffer."""
        self._audio_buffer.clear()
        self._total_bytes = 0
        self.logger.debug("Audio buffer cleared")


class AudioMixer:
    """Mix multiple audio streams together."""

    def __init__(self, format: AudioFormat):
        """Initialize audio mixer.

        Args:
            format: Audio format for mixing
        """
        self.format = format
        self.logger = setup_logging("wyoming.mixer")

    def mix(self, *audio_streams: bytes) -> bytes:
        """Mix multiple audio streams together.

        Args:
            audio_streams: Variable number of audio streams to mix

        Returns:
            Mixed audio data
        """
        if not audio_streams:
            return b''

        if len(audio_streams) == 1:
            return audio_streams[0]

        # Convert all streams to numpy arrays
        arrays = []
        max_length = 0
        for stream in audio_streams:
            if stream:
                arr = np.frombuffer(stream, dtype=self.format.sample_format)
                arrays.append(arr)
                max_length = max(max_length, len(arr))

        # Pad arrays to same length
        for i, arr in enumerate(arrays):
            if len(arr) < max_length:
                arrays[i] = np.pad(arr, (0, max_length - len(arr)), mode='constant')

        # Mix by averaging
        mixed = np.mean(arrays, axis=0)

        # Convert back to correct dtype
        dtype_info = np.iinfo(self.format.sample_format)
        mixed = np.clip(mixed, dtype_info.min, dtype_info.max)

        return mixed.astype(self.format.sample_format).tobytes()