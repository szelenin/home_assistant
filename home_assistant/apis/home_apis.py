from typing import Optional
from .decorators import api_method


class HomeAPIs:
    @api_method(
        name="Weather Information",
        description="Get current weather conditions and forecast for any location. Use this when users ask about weather, temperature, rain, forecasts, or outdoor conditions."
    )
    def get_weather(
        self, 
        location: str,
        units: str = "metric",
        days: int = 1
    ) -> dict:
        """
        Get weather information for a specific location.
        
        Args:
            location: City name or address (e.g., "Tampa, FL")
            units: Temperature units - "metric", "imperial", or "kelvin"
            days: Number of forecast days (1-7)
            
        Returns:
            Weather information dictionary
        """
        # Mock implementation for now
        return {
            "location": location,
            "temperature": 85,
            "description": "sunny",
            "forecast": f"{days} day forecast",
            "units": units
        }

    @api_method(
        name="Language Support",
        description="Get list of languages supported for both speech recognition and text-to-speech. Use this when users ask about language capabilities, what languages you speak, or multilingual support."
    )
    def get_supported_languages(self) -> dict:
        """
        Get languages that both TTS and STT support.

        Returns:
            Dictionary with supported languages and provider info
        """
        try:
            # Import here to avoid circular imports
            from ..speech.tts import TextToSpeech
            from ..speech.recognizer import SpeechRecognizer

            # Get current providers' supported languages
            tts = TextToSpeech()
            recognizer = SpeechRecognizer()

            tts_languages = set(tts.get_supported_languages())
            stt_languages = set(recognizer.get_supported_languages())

            # Find intersection (languages supported by both)
            common_languages = sorted(list(tts_languages.intersection(stt_languages)))

            # Language code to name mapping for better user experience
            language_names = {
                'af': 'Afrikaans', 'ar': 'Arabic', 'bg': 'Bulgarian', 'bn': 'Bengali',
                'bs': 'Bosnian', 'ca': 'Catalan', 'cs': 'Czech', 'cy': 'Welsh',
                'da': 'Danish', 'de': 'German', 'el': 'Greek', 'en': 'English',
                'es': 'Spanish', 'et': 'Estonian', 'eu': 'Basque', 'fa': 'Persian',
                'fi': 'Finnish', 'fr': 'French', 'ga': 'Irish', 'gl': 'Galician',
                'gu': 'Gujarati', 'he': 'Hebrew', 'hi': 'Hindi', 'hr': 'Croatian',
                'hu': 'Hungarian', 'hy': 'Armenian', 'id': 'Indonesian', 'is': 'Icelandic',
                'it': 'Italian', 'ja': 'Japanese', 'ka': 'Georgian', 'kk': 'Kazakh',
                'km': 'Khmer', 'kn': 'Kannada', 'ko': 'Korean', 'lo': 'Lao',
                'lt': 'Lithuanian', 'lv': 'Latvian', 'mk': 'Macedonian', 'ml': 'Malayalam',
                'mn': 'Mongolian', 'mr': 'Marathi', 'ms': 'Malay', 'mt': 'Maltese',
                'ne': 'Nepali', 'nl': 'Dutch', 'no': 'Norwegian', 'pa': 'Punjabi',
                'pl': 'Polish', 'pt': 'Portuguese', 'ro': 'Romanian', 'ru': 'Russian',
                'si': 'Sinhala', 'sk': 'Slovak', 'sl': 'Slovenian', 'sq': 'Albanian',
                'sr': 'Serbian', 'sv': 'Swedish', 'sw': 'Swahili', 'ta': 'Tamil',
                'te': 'Telugu', 'th': 'Thai', 'tr': 'Turkish', 'uk': 'Ukrainian',
                'ur': 'Urdu', 'uz': 'Uzbek', 'vi': 'Vietnamese', 'zh': 'Chinese',
                'zu': 'Zulu'
            }

            # Convert language codes to readable names
            supported_languages = []
            for code in common_languages:
                name = language_names.get(code, code.upper())
                supported_languages.append({"code": code, "name": name})

            return {
                "supported_languages": supported_languages,
                "language_count": len(supported_languages),
                "tts_provider": tts.provider_name,
                "stt_provider": recognizer.provider_name,
                "tts_total_languages": len(tts_languages),
                "stt_total_languages": len(stt_languages)
            }

        except Exception as e:
            # Fallback response if there's an error
            return {
                "supported_languages": [{"code": "en", "name": "English"}],
                "language_count": 1,
                "error": f"Could not determine full language support: {str(e)}",
                "tts_provider": "unknown",
                "stt_provider": "unknown"
            }