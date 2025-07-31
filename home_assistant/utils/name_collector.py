import random
import time
from typing import Optional, List
from ..speech.tts import TextToSpeech
from ..speech.recognizer import SpeechRecognizer
from .logger import setup_logging


class NameCollector:
    def __init__(self):
        self.tts = TextToSpeech()
        self.recognizer = SpeechRecognizer()
        self.logger = setup_logging("home_assistant.name_collector")
        
        self.funny_prompts = [
            "It seems like you forgot to give me a name. What is my name?",
            "Hello? Anyone there? I'm still waiting for my name!",
            "I'm feeling a bit nameless here. Care to help me out?",
            "My identity crisis is getting worse. What should I call myself?",
            "I've been thinking... and I still don't have a name. Ideas?",
            "The silence is deafening! What name would you like to give me?",
            "I'm starting to feel like Voldemort - the assistant who must not be named!",
            "Knock knock! Who's there? I don't know because I don't have a name yet!",
            "I'm having an existential crisis. Who am I without a name?",
            "Is this thing on? I'm still waiting for you to name me!"
        ]
    
    def collect_name(self, timeout_minutes: int = 10) -> Optional[str]:
        """
        Collect the assistant's name from the user.
        
        Args:
            timeout_minutes: Minutes to wait before asking again
            
        Returns:
            Optional[str]: The collected name, or None if failed
        """
        self.logger.info("Starting name collection process...")
        
        # First attempt - polite
        self.tts.speak("What is my name?")
        name = self._listen_for_name()
        
        if name:
            return name
        
        # Continue asking with funny prompts
        attempts = 0
        max_attempts = 50  # Prevent infinite loop
        
        while attempts < max_attempts:
            self.logger.info(f"Waiting {timeout_minutes} minutes before asking again...")
            time.sleep(timeout_minutes * 60)  # Convert to seconds
            
            # Select a random funny prompt
            prompt = random.choice(self.funny_prompts)
            self.tts.speak(prompt)
            
            name = self._listen_for_name()
            if name:
                return name
            
            attempts += 1
        
        self.logger.warning("Max attempts reached. Giving up on name collection.")
        return None
    
    def _listen_for_name(self) -> Optional[str]:
        """
        Listen for a name response.
        
        Returns:
            Optional[str]: The recognized name, or None if not recognized
        """
        if not self.recognizer.is_available():
            self.logger.error("Speech recognizer not available")
            return None
        
        success, text = self.recognizer.listen_for_speech(timeout=30, phrase_timeout=10)
        
        if success and text:
            # Clean up the response - extract potential name
            name = self._extract_name_from_response(text)
            if name:
                # Confirm the name
                confirmation = f"Did you say my name is {name}?"
                self.tts.speak(confirmation)
                
                success, response = self.recognizer.listen_for_speech(timeout=15, phrase_timeout=5)
                if success and response and self._is_positive_response(response):
                    self.tts.speak(f"Great! I'll remember that my name is {name}.")
                    return name
                else:
                    self.tts.speak("Let me try again.")
                    return None
        
        return None
    
    def _extract_name_from_response(self, text: str) -> Optional[str]:
        """
        Extract a potential name from the user's response.
        
        Args:
            text: The recognized speech text
            
        Returns:
            Optional[str]: Extracted name, or None if not found
        """
        text = text.lower().strip()
        
        # Common patterns people might use
        patterns = [
            "your name is ",
            "you are ",
            "call you ",
            "name you ",
            "my name is ",  # User might say this by mistake
        ]
        
        for pattern in patterns:
            if pattern in text:
                name = text.split(pattern, 1)[1].strip()
                if name:
                    # Take only the first word as the name
                    return name.split()[0].capitalize()
        
        # If no pattern matches, assume the whole text might be the name
        words = text.split()
        if len(words) == 1:
            return words[0].capitalize()
        elif len(words) <= 3:  # Might be a short phrase like "call me John"
            return words[-1].capitalize()
        
        return None
    
    def _is_positive_response(self, text: str) -> bool:
        """
        Check if the response is positive (yes, correct, etc.).
        
        Args:
            text: The recognized speech text
            
        Returns:
            bool: True if positive response
        """
        text = text.lower().strip()
        positive_words = ["yes", "yeah", "yep", "correct", "right", "exactly", "sure", "ok", "okay"]
        
        return any(word in text for word in positive_words)