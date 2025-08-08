#!/usr/bin/env python3
"""
Home Assistant - Main Entry Point

Complete voice-controlled home automation system with wake word detection,
speech recognition, AI processing, and text-to-speech response.

State Machine: LISTENING → WAKE_DETECTED → PROCESSING → RESPONDING → LISTENING
"""

import sys
import os
import time
from enum import Enum
from typing import Optional, Tuple

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from home_assistant.utils.config import ConfigManager
from home_assistant.utils.name_collector import NameCollector
from home_assistant.speech.tts import TextToSpeech
from home_assistant.speech.recognizer import SpeechRecognizer
from home_assistant.wake_word.detector import WakeWordDetector
from home_assistant.ai.orchestrator import AIOrchestrator
from home_assistant.utils.logger import setup_logging


class AssistantState(Enum):
    """States for the home assistant state machine."""
    LISTENING_FOR_WAKE_WORD = "listening"
    WAKE_WORD_DETECTED = "wake_detected"
    PROCESSING_COMMAND = "processing"
    RESPONDING = "responding"
    ERROR = "error"
    SHUTTING_DOWN = "shutdown"


class HomeAssistant:
    """
    Main Home Assistant class implementing the complete voice control loop.
    """
    
    def __init__(self):
        """Initialize the Home Assistant system."""
        self.logger = setup_logging("home_assistant.main")
        self.logger.info("Initializing Home Assistant...")
        
        # Configuration
        self.config_manager = ConfigManager()
        
        # Components (initialized lazily)
        self.tts = None
        self.speech_recognizer = None  
        self.wake_word_detector = None
        self.ai_orchestrator = None
        
        # State management
        self.current_state = AssistantState.LISTENING_FOR_WAKE_WORD
        self.should_continue = True
        
        # Performance tracking
        self.stats = {
            'wake_word_detections': 0,
            'commands_processed': 0,
            'errors': 0,
            'start_time': time.time()
        }
        
    def initialize_components(self):
        """Initialize all system components."""
        self.logger.info("Initializing system components...")
        
        try:
            # Initialize TTS (always needed)
            self.tts = TextToSpeech()
            self.logger.info("✅ TTS initialized")
            
            # Initialize Speech Recognizer  
            self.speech_recognizer = SpeechRecognizer()
            if self.speech_recognizer.is_available():
                self.logger.info("✅ Speech Recognition initialized")
            else:
                self.logger.warning("⚠️  Speech Recognition not available")
            
            # Initialize Wake Word Detector
            self.wake_word_detector = WakeWordDetector()
            if self.wake_word_detector.is_available():
                self.logger.info("✅ Wake Word Detection initialized")
            else:
                self.logger.warning("⚠️  Wake Word Detection not available")
            
            # Initialize AI Orchestrator
            self.ai_orchestrator = AIOrchestrator(self.config_manager)
            self.logger.info("✅ AI Orchestrator initialized")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            return False
    
    def setup_wake_word(self) -> bool:
        """
        Handle wake word setup (name collection if needed).
        
        Returns:
            bool: True if wake word is ready, False if setup failed
        """
        wake_word = self.config_manager.get_wake_word()
        
        if not wake_word:
            self.logger.info("Wake word not configured. Starting name collection process...")
            
            if not self.tts:
                self.logger.error("TTS not available for name collection")
                return False
            
            # Welcome message
            self.tts.speak("Hello! I'm your new Home Assistant. I need you to give me a name so I know when you're talking to me.")
            
            # Collect the name
            name_collector = NameCollector()
            collected_name = name_collector.collect_name(timeout_minutes=1)
            
            if collected_name:
                self.config_manager.set_wake_word(collected_name)
                self.logger.info(f"Wake word configured: {collected_name}")
                self.tts.speak(f"Perfect! From now on, just say '{collected_name}' to get my attention.")
                return True
            else:
                self.logger.error("Failed to collect wake word")
                self.tts.speak("I couldn't understand your response. Please try running the assistant again.")
                return False
        else:
            self.logger.info(f"Wake word already configured: {wake_word}")
            if self.tts:
                self.tts.speak(f"Hello! I'm {wake_word}, your Home Assistant. I'm ready to help!")
            return True
    
    def listen_for_wake_word(self) -> Tuple[bool, float]:
        """
        Listen for the wake word.
        
        Returns:
            Tuple[bool, float]: (detected, confidence) or (False, 0.0) if error
        """
        if not self.wake_word_detector or not self.wake_word_detector.is_available():
            self.logger.error("Wake word detector not available")
            time.sleep(5)  # Wait before retrying
            return False, 0.0
        
        wake_word = self.config_manager.get_wake_word()
        if not wake_word:
            self.logger.error("No wake word configured")
            return False, 0.0
        
        try:
            self.logger.debug(f"Listening for wake word: '{wake_word}'")
            return self.wake_word_detector.listen_for_wake_word(wake_word, timeout=None)
        except KeyboardInterrupt:
            self.logger.info("Wake word detection interrupted")
            self.should_continue = False
            return False, 0.0
        except Exception as e:
            self.logger.error(f"Wake word detection error: {e}")
            self.stats['errors'] += 1
            return False, 0.0
    
    def process_voice_command(self) -> Optional[str]:
        """
        Process voice command using speech recognition.
        
        Returns:
            Optional[str]: Recognized command text, or None if failed
        """
        if not self.speech_recognizer or not self.speech_recognizer.is_available():
            self.logger.error("Speech recognizer not available")
            return None
        
        try:
            self.logger.info("Listening for voice command...")
            if self.tts:
                # Short acknowledgment sound or phrase
                self.tts.speak("Yes?")
            
            success, text = self.speech_recognizer.listen_for_speech(timeout=10, phrase_timeout=5)
            
            if success and text:
                self.logger.info(f"Command recognized: '{text}'")
                return text
            else:
                self.logger.info("No command recognized or speech recognition timeout")
                if self.tts:
                    self.tts.speak("I didn't hear anything. Try again.")
                return None
                
        except Exception as e:
            self.logger.error(f"Voice command processing error: {e}")
            self.stats['errors'] += 1
            return None
    
    def process_with_ai(self, command: str) -> Optional[str]:
        """
        Process command with AI and return response.
        
        Args:
            command: The voice command text
            
        Returns:
            Optional[str]: AI response text, or None if failed
        """
        try:
            self.logger.info(f"Processing command with AI: '{command}'")
            
            # Prepare context
            context = {
                'wake_word': self.config_manager.get_wake_word(),
                'timestamp': time.time(),
                'input_method': 'voice'
            }
            
            # Get AI response
            response = self.ai_orchestrator.chat(command, context)
            
            if response and response.text:
                self.logger.info(f"AI response: '{response.text}'")
                return response.text
            else:
                self.logger.warning("AI returned empty response")
                return "I'm not sure how to help with that."
                
        except Exception as e:
            self.logger.error(f"AI processing error: {e}")
            self.stats['errors'] += 1
            return "I'm having trouble processing your request right now."
    
    def speak_response(self, response: str) -> bool:
        """
        Speak the response using TTS.
        
        Args:
            response: Text to speak
            
        Returns:
            bool: True if successful
        """
        if not self.tts:
            self.logger.error("TTS not available")
            return False
        
        try:
            self.logger.info(f"Speaking response: '{response}'")
            return self.tts.speak(response)
        except Exception as e:
            self.logger.error(f"TTS error: {e}")
            self.stats['errors'] += 1
            return False
    
    def run_state_machine(self):
        """Run the main assistant state machine."""
        self.logger.info("Starting Home Assistant state machine...")
        
        while self.should_continue:
            try:
                if self.current_state == AssistantState.LISTENING_FOR_WAKE_WORD:
                    self.logger.debug("State: LISTENING_FOR_WAKE_WORD")
                    detected, confidence = self.listen_for_wake_word()
                    
                    if detected:
                        self.logger.info(f"Wake word detected! Confidence: {confidence:.3f}")
                        self.stats['wake_word_detections'] += 1
                        self.current_state = AssistantState.WAKE_WORD_DETECTED
                    elif not self.should_continue:
                        break
                
                elif self.current_state == AssistantState.WAKE_WORD_DETECTED:
                    self.logger.debug("State: WAKE_WORD_DETECTED")
                    command = self.process_voice_command()
                    
                    if command:
                        self.current_state = AssistantState.PROCESSING_COMMAND
                        self.command_to_process = command
                    else:
                        # No command received, go back to listening for wake word
                        self.current_state = AssistantState.LISTENING_FOR_WAKE_WORD
                
                elif self.current_state == AssistantState.PROCESSING_COMMAND:
                    self.logger.debug("State: PROCESSING_COMMAND")
                    response = self.process_with_ai(self.command_to_process)
                    
                    if response:
                        self.current_state = AssistantState.RESPONDING
                        self.response_to_speak = response
                        self.stats['commands_processed'] += 1
                    else:
                        # AI processing failed, go back to listening
                        self.current_state = AssistantState.LISTENING_FOR_WAKE_WORD
                
                elif self.current_state == AssistantState.RESPONDING:
                    self.logger.debug("State: RESPONDING")
                    success = self.speak_response(self.response_to_speak)
                    
                    # Always return to listening after responding
                    self.current_state = AssistantState.LISTENING_FOR_WAKE_WORD
                    
                    # Clear processed data
                    self.command_to_process = None
                    self.response_to_speak = None
                
                elif self.current_state == AssistantState.ERROR:
                    self.logger.warning("State: ERROR - attempting recovery")
                    time.sleep(2)  # Brief pause before recovery
                    self.current_state = AssistantState.LISTENING_FOR_WAKE_WORD
                
                else:
                    self.logger.error(f"Unknown state: {self.current_state}")
                    self.current_state = AssistantState.ERROR
                    
            except KeyboardInterrupt:
                self.logger.info("State machine interrupted by user")
                break
            except Exception as e:
                self.logger.error(f"State machine error: {e}")
                self.stats['errors'] += 1
                self.current_state = AssistantState.ERROR
                time.sleep(1)  # Brief pause before retry
        
        self.current_state = AssistantState.SHUTTING_DOWN
        self.logger.info("Home Assistant state machine stopped")
    
    def print_stats(self):
        """Print runtime statistics."""
        runtime = time.time() - self.stats['start_time']
        self.logger.info(f"""
Home Assistant Session Statistics:
Runtime: {runtime:.1f} seconds
Wake word detections: {self.stats['wake_word_detections']}
Commands processed: {self.stats['commands_processed']}
Errors: {self.stats['errors']}
""")
    
    def shutdown(self):
        """Clean shutdown of all components."""
        self.logger.info("Shutting down Home Assistant...")
        
        try:
            if self.wake_word_detector:
                self.wake_word_detector.cleanup()
            
            if self.speech_recognizer:
                self.speech_recognizer.cleanup() if hasattr(self.speech_recognizer, 'cleanup') else None
            
            self.print_stats()
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
        
        self.logger.info("Home Assistant shutdown complete")
    
    def run(self):
        """Main entry point for running the Home Assistant."""
        try:
            # Initialize components
            if not self.initialize_components():
                self.logger.error("Component initialization failed")
                return False
            
            # Setup wake word
            if not self.setup_wake_word():
                self.logger.error("Wake word setup failed")
                return False
            
            # Run the main loop
            self.run_state_machine()
            
            return True
            
        except KeyboardInterrupt:
            self.logger.info("Home Assistant interrupted by user")
            return True
        except Exception as e:
            self.logger.critical(f"Critical error in Home Assistant: {e}")
            return False
        finally:
            self.shutdown()


def main():
    """Main function to start the Home Assistant."""
    assistant = HomeAssistant()
    success = assistant.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()