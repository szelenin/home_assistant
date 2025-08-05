# Home Assistant

A Python-based voice-controlled home automation system with speech recognition and text-to-speech capabilities.

## Features

- **Voice Control**: Speech recognition for hands-free operation
- **Multi-Provider Text-to-Speech**: Support for pyttsx3, eSpeak-NG, and Piper neural TTS with configurable providers
- **Wake Word Detection**: Customizable wake word for activation
- **AI Integration**: Claude (Anthropic) and ChatGPT (OpenAI) support with automatic fallback
- **Intent Recognition**: Understands weather, device control, personal info, and general questions
- **Natural Language Processing**: Translates commands to device API calls
- **Device Management**: Control smart lights, thermostats, and other IoT devices
- **Automation**: Create custom automation rules for your smart home
- **Configuration**: YAML-based configuration system
- **Multi-Engine Speech Recognition**: Support for Google, Vosk, Sphinx, and Whisper

## Getting Started

### Prerequisites

- Python 3.8 or higher
- macOS (for voice features) or Linux
- Git

### System Dependencies

**For macOS:**
```bash
# Install PortAudio (required for PyAudio)
brew install portaudio

# Install eSpeak-NG (optional, for direct eSpeak TTS provider)
brew install espeak-ng
```

**For Ubuntu/Debian:**
```bash
# Install PortAudio
sudo apt-get install portaudio19-dev python3-pyaudio

# Install eSpeak-NG (optional, for direct eSpeak TTS provider)
sudo apt-get install espeak-ng
```

**For other Linux distributions:**
```bash
# Fedora/RHEL/CentOS
sudo dnf install portaudio-devel espeak-ng

# Arch Linux
sudo pacman -S portaudio espeak-ng
```

### Installation

1. Clone the repository:
   ```bash
   git clone git@github.com:szelenin/home_assistant.git
   cd home_assistant
   ```

2. Create and activate virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install Python dependencies:
   ```bash
   # Install core dependencies including AI providers
   pip install -r requirements.txt
   
   # Full installation (all speech recognition engines)
   pip install -r requirements-full.txt
   ```

4. Configure AI Provider (Required):
   
   The system uses AI providers for natural language understanding. You need at least one API key:

   **Step 1: Get API Key**
   
   **Option A: Anthropic Claude (Recommended)**
   - Sign up at [Anthropic Console](https://console.anthropic.com/)
   - Go to [API Keys](https://console.anthropic.com/settings/keys) and create a new key
   - Add credits to your account at [Billing](https://console.anthropic.com/settings/billing)
   
   **Option B: OpenAI ChatGPT**
   - Sign up at [OpenAI Platform](https://platform.openai.com/)
   - Go to [API Keys](https://platform.openai.com/api-keys) and create a new key
   - Add billing information at [Billing](https://platform.openai.com/settings/organization/billing/overview)

   **Step 2: Create AI Configuration**
   ```bash
   # Copy the template file
   cp ai_config.example.yaml ai_config.yaml
   
   # Edit with your API keys
   nano ai_config.yaml
   ```

   **Step 3: Add your API keys to ai_config.yaml:**
   ```yaml
   # API Keys (replace with your actual keys)
   anthropic_api_key: "your-anthropic-key-here"  # For Claude
   openai_api_key: "your-openai-key-here"        # For ChatGPT
   ```
   
   **Note**: `ai_config.yaml` is automatically ignored by git to keep your API keys secure.

5. Configure other settings:
   ```bash
   # Edit config.yaml to customize voice and speech settings
   nano config.yaml
   ```

6. Run the application:
   ```bash
   python main.py
   ```

## Configuration

### Voice Settings (`config.yaml`)

The system now supports multiple TTS providers with configurable settings:

```yaml
tts:
  provider: pyttsx  # Options: pyttsx, espeak, piper
  providers:
    pyttsx:
      voice_id: "com.apple.voice.compact.en-US.Samantha"
      rate: 150
      volume: 0.5
    espeak:
      voice: en
      rate: 175
      volume: 80
      pitch: 50
      gap: 0
    piper:
      model: en_US-lessac-medium
      rate: 1.0
      volume: 1.0
      speaker_id: null
      output_raw: false

speech:
  language: en-US  # Speech recognition language
  recognition_engines:
    - google  # Primary (requires internet)
    - vosk    # Secondary (offline fallback)
    - sphinx  # Tertiary (offline fallback)

wake_word:
  name: null  # Custom wake word (null for default)
  sensitivity: 0.5  # Wake word sensitivity
```

### Speech Recognition Engines

The system supports multiple speech recognition engines with automatic fallback:

**Online Engines:**
- **Google Speech Recognition** (default) - High accuracy, requires internet
- **Google Cloud Speech** - Enterprise-grade, requires API key
- **Azure Speech Services** - Microsoft's speech recognition
- **Amazon Transcribe** - AWS speech recognition

**Offline Engines:**
- **Vosk** - Fast, accurate offline recognition
- **Sphinx** - CMU's offline speech recognition
- **Whisper** - OpenAI's offline speech recognition

**Engine Priority:**
1. **Google** (online, best accuracy)
2. **Vosk** (offline, good accuracy)
3. **Sphinx** (offline, basic accuracy)

### Text-to-Speech Providers

The system supports multiple TTS providers with automatic availability detection and graceful fallback:

#### 1. Pyttsx (Default)
**Description:** Uses pyttsx3 library with eSpeak-NG backend  
**Status:** ✅ Available on all platforms  
**Quality:** Good, system voice support  
**Requirements:** No additional installation (included in requirements.txt)

**Configuration:**
```yaml
tts:
  provider: pyttsx
  providers:
    pyttsx:
      voice_id: "com.apple.voice.compact.en-US.Samantha"  # System voice ID
      rate: 150      # Words per minute (50-400)
      volume: 0.5    # Volume level (0.0-1.0)
```

#### 2. eSpeak-NG (Direct)
**Description:** Direct subprocess calls to eSpeak-NG  
**Status:** ⚠️ Requires system installation  
**Quality:** Basic, robotic but clear  
**Requirements:** Install eSpeak-NG system package

**Installation:**
```bash
# macOS
brew install espeak-ng

# Ubuntu/Debian
sudo apt-get install espeak-ng

# Fedora/RHEL/CentOS
sudo dnf install espeak-ng

# Arch Linux
sudo pacman -S espeak-ng
```

**Configuration:**
```yaml
tts:
  provider: espeak
  providers:
    espeak:
      voice: en        # Language/voice code
      rate: 175        # Words per minute (80-450)
      volume: 80       # Volume level (0-200, 100=normal)
      pitch: 50        # Pitch level (0-99)
      gap: 0           # Gap between words (10ms units)
```

**Available eSpeak voices:** Run `espeak-ng --voices` to see all available voices

#### 3. Piper Neural TTS
**Description:** High-quality neural text-to-speech  
**Status:** ⚠️ Requires model download  
**Quality:** Excellent, human-like  
**Requirements:** Models must be downloaded separately

**Installation:**
```bash
# Install Piper (already in requirements.txt)
pip install piper-tts>=1.3.0

# Download a voice model (example)
# Models available at: https://github.com/rhasspy/piper/releases
# Download .onnx and .onnx.json files to your project directory
```

**Popular Models:**
- `en_US-lessac-medium` - Female US English (recommended)
- `en_US-ljspeech-medium` - Female US English
- `en_US-danny-low` - Male US English  
- `en_GB-alan-medium` - Male UK English
- `de_DE-thorsten-medium` - German
- `fr_FR-mls_1840-low` - French

**Configuration:**
```yaml
tts:
  provider: piper
  providers:
    piper:
      model: en_US-lessac-medium  # Model name (without .onnx extension)
      rate: 1.0                   # Speed multiplier (0.25-4.0)
      volume: 1.0                 # Volume multiplier (0.0-2.0)
      speaker_id: null            # Speaker ID for multi-speaker models
      output_raw: false           # Stream raw audio
```

**Model Download Instructions:**
1. Visit [Piper Releases](https://github.com/rhasspy/piper/releases)
2. Download both `.onnx` and `.onnx.json` files for your chosen model
3. Place them in your project directory
4. Update the `model` setting in config.yaml

#### Provider Selection Priority
1. **Configured provider** (from config.yaml)
2. **Automatic fallback** to pyttsx if configured provider fails
3. **Availability detection** - unavailable providers are automatically skipped

#### Testing TTS Providers
```bash
# Test all available providers
python tests/integration/test_tts.py

# Check provider availability
python -c "
from home_assistant.speech.tts import TextToSpeech
tts = TextToSpeech()
print('Available providers:', tts.get_available_providers())
"
```

### Available Voices

#### Pyttsx Voices (System Voices)
**macOS:**
- `com.apple.voice.compact.en-US.Samantha` (Female, US English)
- `com.apple.voice.compact.en-US.Alex` (Male, US English)
- `com.apple.voice.compact.en-GB.Daniel` (Male, UK English)

**Linux/Windows:**
Voice availability depends on system installation. Common voices include:
- English voices (various)
- Multi-language support based on system TTS

**List available voices:**
```python
from home_assistant.speech.tts import TextToSpeech
tts = TextToSpeech('pyttsx')
tts.list_voices()
```

#### eSpeak Voices
eSpeak supports 100+ languages and variants:
- `en` - English (default)
- `en-us` - US English
- `en-gb` - British English
- `de` - German
- `fr` - French
- `es` - Spanish
- `it` - Italian
- And many more...

**List available eSpeak voices:**
```bash
espeak-ng --voices
```

#### Piper Neural Voices
High-quality neural voices (requires model download):
- **English:** lessac, ljspeech, amy, danny, ryan, and more
- **Multi-language:** German, French, Spanish, Italian, Dutch, etc.
- **Voice samples:** Available on [Piper releases page](https://github.com/rhasspy/piper/releases)

## Testing

### Scenario-Based Testing

The project uses **scenario-based testing** for better organization and clarity. Each scenario tests specific functionality in a standardized way.

#### Run All Scenarios
```bash
python tests/run_scenarios.py
```

#### Run Specific Scenario Categories
```bash
# Test TTS functionality (legacy scenarios)
python tests/run_scenarios.py --scenario tts

# Test multi-provider TTS system (new)
python tests/integration/test_tts.py

# Test speech recognition
python tests/run_scenarios.py --scenario recognizer

# Test integration between TTS and recognizer
python tests/run_scenarios.py --scenario integration

# Test name collection functionality
python tests/run_scenarios.py --scenario name_collection
```

#### Individual Scenario Files
```bash
# Run individual scenario files directly
python tests/scenarios/tts_scenarios.py
python tests/scenarios/recognizer_scenarios.py
python tests/scenarios/integration_scenarios.py
python tests/scenarios/name_collection_scenarios.py
```

### Legacy Tests (Still Available)
```bash
# Original test files (for backward compatibility)
python tests/test_recognizer.py
python tests/test_tts.py
python tests/test_recognizer_tts_integration.py
python tests/test_config.py
```

### Test Structure

```
tests/
├── run_scenarios.py                    # Main test runner
├── scenarios/                          # Scenario-based tests
│   ├── __init__.py
│   ├── tts_scenarios.py               # TTS test scenarios
│   ├── recognizer_scenarios.py        # Speech recognition scenarios
│   ├── integration_scenarios.py       # TTS + Recognizer integration
│   └── name_collection_scenarios.py   # Name collection scenarios
├── test_recognizer.py                 # Legacy recognizer tests
├── test_tts.py                        # Legacy TTS tests
├── test_recognizer_tts_integration.py # Legacy integration tests
└── test_config.py                     # Configuration tests
```

### Scenario Categories

**🎤 TTS Scenarios:**
- Multi-provider testing (pyttsx, espeak, piper)
- Provider availability detection
- Voice configuration per provider
- Error handling and fallback
- Legacy: Welcome message testing, short phrases, long text handling

**🎵 Recognizer Scenarios:**
- Microphone initialization
- Ambient noise adjustment
- Single speech recognition
- Continuous recognition
- Engine fallback testing

**🎤🎵 Integration Scenarios:**
- Speak and listen (TTS → Recognizer)
- Conversation flow simulation
- Configuration testing
- Error handling

**📝 Name Collection Scenarios:**
- Initial setup testing
- Name collection flow
- Configuration management
- Error handling

## Project Structure

```
home_assistant/
├── config.yaml              # Main configuration file
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
├── requirements-full.txt    # All dependencies (including optional)
├── setup.py                # Package installation script
├── home_assistant/         # Main package
│   ├── __init__.py
│   ├── main.py            # Application entry point
│   ├── speech/
│   │   ├── __init__.py
│   │   ├── recognizer.py  # Speech recognition
│   │   └── tts.py        # Text-to-speech
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config.py     # Configuration management
│   │   ├── logger.py     # Logging utilities
│   │   └── name_collector.py
│   ├── modules/
│   │   └── __init__.py
│   ├── chatgpt.py        # AI integration
│   └── chatgpt_showcase.py
├── tests/
│   ├── run_scenarios.py   # Main test runner
│   ├── scenarios/         # Scenario-based tests
│   │   ├── __init__.py
│   │   ├── tts_scenarios.py
│   │   ├── recognizer_scenarios.py
│   │   ├── integration_scenarios.py
│   │   └── name_collection_scenarios.py
│   ├── test_recognizer.py # Legacy tests
│   ├── test_tts.py
│   ├── test_recognizer_tts_integration.py
│   └── test_config.py
├── logs/                  # Application logs
└── docs/
    └── high level design.md
```

## Troubleshooting

### Speech Recognition Issues
- **"Could not find PyAudio"**: Install PortAudio first, then PyAudio
- **Microphone not working**: Check system permissions and microphone settings
- **Speech not recognized**: Ensure good microphone quality and clear speech

### Text-to-Speech Issues

#### General TTS Issues
- **No sound**: Check audio device settings and volume
- **Provider not available**: Check system dependencies and installation
- **Fallback to pyttsx**: Other providers failed, check logs for details

#### Pyttsx Issues
- **Wrong voice**: Update `voice_id` in `providers.pyttsx` section
- **Rate issues**: Adjust `rate` setting (50-400 WPM)
- **macOS voice issues**: Some voices may not respect rate/volume changes

#### eSpeak Issues
- **"espeak-ng not found"**: Install eSpeak-NG system package
  ```bash
  # macOS: brew install espeak-ng
  # Ubuntu: sudo apt-get install espeak-ng
  ```
- **Robotic voice**: Normal for eSpeak, try adjusting pitch and rate
- **Voice not found**: Run `espeak-ng --voices` to see available voices

#### Piper Issues
- **"Unable to find voice" error**: Download the required model files
  1. Visit [Piper Releases](https://github.com/rhasspy/piper/releases)
  2. Download both `.onnx` and `.onnx.json` files
  3. Place in project directory
- **Model loading slow**: Large models take time to load initially
- **Audio quality issues**: Try different models or adjust volume settings

#### Debugging TTS Issues
```bash
# Check provider availability
python -c "
from home_assistant.speech.tts import TextToSpeech
tts = TextToSpeech()
print('Available providers:', tts.get_available_providers())
for name, available in tts.get_available_providers().items():
    if available:
        provider_tts = TextToSpeech(name)
        print(f'{name} info:', provider_tts.get_provider_info())
"

# Test specific provider
python -c "
from home_assistant.speech.tts import TextToSpeech
tts = TextToSpeech('espeak')  # or 'piper', 'pyttsx'
print('Testing provider:', tts.provider_name)
success = tts.speak('Hello, this is a test.')
print('Success:', success)
"
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

- GitHub: [@szelenin](https://github.com/szelenin)
- Project Link: [https://github.com/szelenin/home_assistant](https://github.com/szelenin/home_assistant) 