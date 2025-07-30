import unittest
from unittest.mock import Mock, patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.speech.tts import TextToSpeech


class TestTextToSpeech(unittest.TestCase):
    
    @patch('src.speech.tts.pyttsx3.init')
    def test_initialization_success(self, mock_init):
        """Test successful TTS initialization."""
        mock_engine = Mock()
        mock_init.return_value = mock_engine
        
        # Mock voices
        mock_voice = Mock()
        mock_voice.gender = 'female'
        mock_voice.id = 'voice_1'
        mock_engine.getProperty.return_value = [mock_voice]
        
        tts = TextToSpeech()
        
        self.assertEqual(tts.engine, mock_engine)
        mock_init.assert_called_once()
        mock_engine.setProperty.assert_called()
    
    @patch('src.speech.tts.pyttsx3.init', side_effect=Exception("Init failed"))
    @patch('builtins.print')
    def test_initialization_failure(self, mock_print, mock_init):
        """Test TTS initialization failure."""
        tts = TextToSpeech()
        
        self.assertIsNone(tts.engine)
        mock_print.assert_called_with("Failed to initialize TTS engine: Init failed")
    
    @patch('src.speech.tts.pyttsx3.init')
    def test_speak_success(self, mock_init):
        """Test successful speech synthesis."""
        mock_engine = Mock()
        mock_init.return_value = mock_engine
        mock_engine.getProperty.return_value = []
        
        tts = TextToSpeech()
        result = tts.speak("Hello, world!")
        
        self.assertTrue(result)
        mock_engine.say.assert_called_with("Hello, world!")
        mock_engine.runAndWait.assert_called_once()
    
    @patch('src.speech.tts.pyttsx3.init')
    def test_speak_engine_failure(self, mock_init):
        """Test speech synthesis with engine error."""
        mock_engine = Mock()
        mock_engine.say.side_effect = Exception("Speech error")
        mock_init.return_value = mock_engine
        mock_engine.getProperty.return_value = []
        
        with patch('builtins.print') as mock_print:
            tts = TextToSpeech()
            result = tts.speak("Hello, world!")
        
        self.assertFalse(result)
        mock_print.assert_called_with("Failed to speak text: Speech error")
    
    def test_speak_no_engine(self):
        """Test speaking when engine is not available."""
        with patch('src.speech.tts.pyttsx3.init', side_effect=Exception("No engine")):
            with patch('builtins.print') as mock_print:
                tts = TextToSpeech()
                result = tts.speak("Hello, world!")
        
        self.assertFalse(result)
        mock_print.assert_called_with("TTS not available, would say: Hello, world!")
    
    @patch('src.speech.tts.pyttsx3.init')
    def test_voice_configuration(self, mock_init):
        """Test voice configuration with multiple voices."""
        mock_engine = Mock()
        mock_init.return_value = mock_engine
        
        # Create mock voices
        male_voice = Mock()
        male_voice.gender = 'male'
        male_voice.id = 'voice_male'
        
        female_voice = Mock()
        female_voice.gender = 'female'
        female_voice.id = 'voice_female'
        
        mock_engine.getProperty.return_value = [male_voice, female_voice]
        
        tts = TextToSpeech()
        
        # Should select female voice
        mock_engine.setProperty.assert_any_call('voice', 'voice_female')


if __name__ == '__main__':
    unittest.main()