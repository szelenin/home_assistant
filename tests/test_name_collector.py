import unittest
from unittest.mock import Mock, patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.utils.name_collector import NameCollector


class TestNameCollector(unittest.TestCase):
    
    def setUp(self):
        with patch('src.utils.name_collector.TextToSpeech'), \
             patch('src.utils.name_collector.SpeechRecognizer'):
            self.name_collector = NameCollector()
    
    def test_extract_name_from_response_patterns(self):
        """Test extracting names from various response patterns."""
        test_cases = [
            ("your name is Jarvis", "Jarvis"),
            ("you are Alexa", "Alexa"),
            ("call you Friday", "Friday"),
            ("name you Computer", "Computer"),
            ("my name is John", "John"),  # Common mistake
        ]
        
        for text, expected in test_cases:
            with self.subTest(text=text):
                result = self.name_collector._extract_name_from_response(text)
                self.assertEqual(result, expected)
    
    def test_extract_name_single_word(self):
        """Test extracting name from single word response."""
        result = self.name_collector._extract_name_from_response("jarvis")
        self.assertEqual(result, "Jarvis")
    
    def test_extract_name_short_phrase(self):
        """Test extracting name from short phrase."""
        result = self.name_collector._extract_name_from_response("call me Bob")
        self.assertEqual(result, "Bob")
    
    def test_extract_name_no_match(self):
        """Test extracting name when no clear pattern matches."""
        result = self.name_collector._extract_name_from_response("I think you should be called something really awesome")
        self.assertIsNone(result)
    
    def test_is_positive_response(self):
        """Test detecting positive responses."""
        positive_responses = [
            "yes", "yeah", "yep", "correct", "right", 
            "exactly", "sure", "ok", "okay"
        ]
        
        for response in positive_responses:
            with self.subTest(response=response):
                result = self.name_collector._is_positive_response(response)
                self.assertTrue(result)
        
        # Test negative responses
        negative_responses = ["no", "nope", "wrong", "incorrect"]
        for response in negative_responses:
            with self.subTest(response=response):
                result = self.name_collector._is_positive_response(response)
                self.assertFalse(result)
    
    @patch('src.utils.name_collector.time.sleep')
    def test_collect_name_success_first_try(self, mock_sleep):
        """Test successful name collection on first attempt."""
        with patch('src.utils.name_collector.TextToSpeech') as mock_tts_class, \
             patch('src.utils.name_collector.SpeechRecognizer') as mock_sr_class:
            
            mock_tts = Mock()
            mock_sr = Mock()
            mock_tts_class.return_value = mock_tts
            mock_sr_class.return_value = mock_sr
            
            mock_sr.listen_for_speech.side_effect = [
                (True, "your name is Jarvis"),  # Initial response
                (True, "yes")  # Confirmation
            ]
            mock_sr.is_available.return_value = True
            
            name_collector = NameCollector()
            result = name_collector.collect_name(timeout_minutes=10)
            
            self.assertEqual(result, "Jarvis")
            mock_tts.speak.assert_any_call("What is my name?")
            mock_tts.speak.assert_any_call("Did you say my name is Jarvis?")
            mock_tts.speak.assert_any_call("Great! I'll remember that my name is Jarvis.")
    
    @patch('src.utils.name_collector.time.sleep')
    def test_collect_name_retry_with_funny_prompt(self, mock_sleep):
        """Test name collection with retry using funny prompt."""
        with patch('src.utils.name_collector.TextToSpeech') as mock_tts_class, \
             patch('src.utils.name_collector.SpeechRecognizer') as mock_sr_class:
            
            mock_tts = Mock()
            mock_sr = Mock()
            mock_tts_class.return_value = mock_tts
            mock_sr_class.return_value = mock_sr
            
            mock_sr.listen_for_speech.side_effect = [
                (False, None),  # First attempt fails
                (True, "call you Friday"),  # Second attempt succeeds
                (True, "yes")  # Confirmation
            ]
            mock_sr.is_available.return_value = True
            
            name_collector = NameCollector()
            result = name_collector.collect_name(timeout_minutes=1)  # Short timeout for test
            
            self.assertEqual(result, "Friday")
            # Should have called speak at least 3 times (initial + funny prompt + confirmation)
            self.assertGreaterEqual(mock_tts.speak.call_count, 3)
    
    def test_collect_name_recognizer_unavailable(self):
        """Test name collection when speech recognizer is unavailable."""
        with patch('src.utils.name_collector.TextToSpeech') as mock_tts_class, \
             patch('src.utils.name_collector.SpeechRecognizer') as mock_sr_class:
            
            mock_tts = Mock()
            mock_sr = Mock()
            mock_tts_class.return_value = mock_tts
            mock_sr_class.return_value = mock_sr
            
            mock_sr.is_available.return_value = False
            
            name_collector = NameCollector()
            result = name_collector._listen_for_name()
            
            self.assertIsNone(result)
    
    def test_funny_prompts_exist(self):
        """Test that funny prompts are defined and not empty."""
        with patch('src.utils.name_collector.TextToSpeech'), \
             patch('src.utils.name_collector.SpeechRecognizer'):
            name_collector = NameCollector()
            
            self.assertIsInstance(name_collector.funny_prompts, list)
            self.assertGreater(len(name_collector.funny_prompts), 5)
            
            # Check that all prompts are strings and not empty
            for prompt in name_collector.funny_prompts:
                self.assertIsInstance(prompt, str)
                self.assertGreater(len(prompt.strip()), 0)


if __name__ == '__main__':
    unittest.main()