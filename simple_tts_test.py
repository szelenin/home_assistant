#!/usr/bin/env python3
"""
Simple TTS test script with single engine instance.
Tests basic TTS and wake word functionality without reinitialization.
"""

import pyttsx3
import threading
import time
import sys
import speech_recognition as sr
from pocketsphinx import LiveSpeech

def print_with_flush(msg):
    """Print with immediate flush for background processes."""
    print(msg)
    sys.stdout.flush()

class SimpleTTSTest:
    def __init__(self):
        self.engine = None
        self.state = "initializing"
        self.tts_thread = None
        self.speaking = False
        self.tts_lock = threading.Lock()

    def initialize_tts(self):
        """Initialize TTS engine once."""
        print_with_flush("🔧 Initializing TTS engine...")
        try:
            self.engine = pyttsx3.init()

            # Configure voice
            voices = self.engine.getProperty('voices')
            if voices:
                # Try to find Samantha voice
                for voice in voices:
                    if 'samantha' in voice.name.lower():
                        self.engine.setProperty('voice', voice.id)
                        break
                else:
                    # Use first available voice
                    self.engine.setProperty('voice', voices[0].id)

            # Set properties
            self.engine.setProperty('rate', 150)
            self.engine.setProperty('volume', 0.7)

            print_with_flush("✅ TTS engine initialized successfully")
            return True

        except Exception as e:
            print_with_flush(f"❌ Failed to initialize TTS: {e}")
            return False

    def speak_sync(self, text):
        """Speak text synchronously."""
        print(f"🔊 Speaking (sync): {text}")
        try:
            self.engine.say(text)
            self.engine.runAndWait()
            print("✅ Sync speech completed")
            return True
        except Exception as e:
            print(f"❌ Sync speech failed: {e}")
            return False

    def _tts_worker(self, text):
        """Async TTS worker thread."""
        try:
            with self.tts_lock:
                self.speaking = True

            print(f"🔊 Speaking (async): {text}")

            # Time the TTS operation to detect degradation
            start_time = time.time()

            # Use the same engine instance
            self.engine.say(text)

            # Use startLoop for non-blocking operation if available
            if hasattr(self.engine, 'startLoop'):
                print("🔧 Using startLoop for async TTS")
                self.engine.startLoop(False)

                # Wait for speech to complete
                while self.engine.isBusy():
                    time.sleep(0.01)

                self.engine.endLoop()
            else:
                print("🔧 Using runAndWait for async TTS")
                # Fallback to blocking mode
                self.engine.runAndWait()

            duration = time.time() - start_time
            print(f"✅ Async speech completed in {duration:.2f}s")

            # Check for TTS degradation
            if duration < 0.1 and len(text) > 5:
                print(f"⚠️ WARNING: TTS completed too quickly ({duration:.2f}s) - possible degradation!")

        except Exception as e:
            print(f"❌ Async speech failed: {e}")
        finally:
            with self.tts_lock:
                self.speaking = False
                # Change state back to listening when done
                self.state = "listening"
                print("🎯 State changed to: listening")

    def speak_async(self, text):
        """Speak text asynchronously."""
        try:
            # Change state to speaking
            self.state = "speaking"
            print("🎯 State changed to: speaking")

            # Start TTS in separate thread
            self.tts_thread = threading.Thread(target=self._tts_worker, args=(text,))
            self.tts_thread.daemon = True
            self.tts_thread.start()

            return True

        except Exception as e:
            print(f"❌ Failed to start async speech: {e}")
            self.state = "listening"
            return False

    def is_speaking(self):
        """Check if currently speaking."""
        with self.tts_lock:
            return self.speaking

    def initialize_wake_word(self):
        """Initialize wake word detection using same settings as Jarvis."""
        print("🔧 Initializing wake word detection...")
        try:
            from pocketsphinx import Config, Decoder
            import pyaudio

            # Create PocketSphinx configuration (exact copy from working Jarvis)
            config = Config()

            # Set sample rate
            config.set_string('-samprate', '16000')

            # Configure for keyphrase spotting
            config.set_string('-keyphrase', 'jarvis')
            config.set_float('-kws_threshold', 1e-20)  # Very sensitive threshold

            # Disable unnecessary components for efficiency (CRITICAL!)
            config.set_string('-lm', None)  # Disable language model
            config.set_string('-bestpath', 'no')  # Disable best path search
            config.set_string('-maxwpf', '1')  # Max words per frame

            # Create decoder
            self.decoder = Decoder(config)

            # Set up audio recording
            self.audio = pyaudio.PyAudio()
            self.audio_stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024
            )

            print("✅ Wake word detection initialized")
            return True

        except Exception as e:
            print(f"❌ Failed to initialize wake word detection: {e}")
            return False

    def listen_for_wake_word(self):
        """Listen for wake word in main thread."""
        print("🎤 Listening for wake word 'jarvis'...")

        try:
            self.decoder.start_utt()

            while True:
                if self.state == "listening":
                    # Read audio data
                    audio_data = self.audio_stream.read(1024, exception_on_overflow=False)

                    # Process with PocketSphinx
                    self.decoder.process_raw(audio_data, False, False)

                    # Check for wake word detection
                    if self.decoder.hyp() is not None:
                        detected_text = self.decoder.hyp().hypstr.lower()
                        confidence = self.decoder.hyp().prob

                        if 'jarvis' in detected_text:
                            print(f"✅ Wake word detected: '{detected_text}' (confidence: {confidence})")

                            # Change state and speak asynchronously
                            self.state = "wake_detected"
                            print("🎯 State changed to: wake_detected")

                            self.speak_async("I heard you")

                            # Restart decoder for next detection
                            self.decoder.end_utt()
                            self.decoder.start_utt()

                elif self.state == "speaking":
                    # Skip wake word detection while speaking but keep audio stream active
                    self.audio_stream.read(1024, exception_on_overflow=False)

                # Small delay to prevent excessive CPU usage
                time.sleep(0.01)

        except KeyboardInterrupt:
            print("\n🛑 Stopping wake word detection...")
            self.decoder.end_utt()
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            self.audio.terminate()
        except Exception as e:
            print(f"❌ Wake word detection error: {e}")

    def run(self):
        """Run the test."""
        print("🚀 Starting Simple TTS Test")
        print("="*50)

        # Initialize TTS
        if not self.initialize_tts():
            return False

        # Initial greeting
        self.speak_sync("Hello I'm Jarvis")

        # Initialize wake word detection
        if not self.initialize_wake_word():
            return False

        # Change to listening state
        self.state = "listening"
        print("🎯 State changed to: listening")

        # Listen for wake word in main thread
        print("\n🎤 Say 'jarvis' to test async TTS")
        print("Press Ctrl+C to exit")

        try:
            self.listen_for_wake_word()
        except KeyboardInterrupt:
            print("\n✅ Test completed")

        return True

def main():
    """Main function."""
    test = SimpleTTSTest()
    test.run()

if __name__ == "__main__":
    main()