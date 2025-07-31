# Home Assistant

A Python-based voice-controlled home automation system with speech recognition and text-to-speech capabilities.

## Features

- **Voice Control**: Speech recognition for hands-free operation
- **Text-to-Speech**: Natural voice responses using system voices
- **Wake Word Detection**: Customizable wake word for activation
- **AI Integration**: ChatGPT integration for natural language understanding
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
```

**For Ubuntu/Debian:**
```bash
# Install PortAudio
sudo apt-get install portaudio19-dev python3-pyaudio
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
   # Minimal installation (Google Speech Recognition only)
   pip install -r requirements.txt
   
   # Full installation (all speech recognition engines)
   pip install -r requirements-full.txt
   ```

4. Configure the system:
   ```bash
   # Edit config.yaml to customize voice and speech settings
   nano config.yaml
   ```

5. Run the application:
   ```bash
   python main.py
   ```

## Configuration

### Voice Settings (`config.yaml`)

```yaml
tts:
  voice_id: "com.apple.voice.compact.en-US.Samantha"  # Voice selection
  rate: 150  # Speech rate (words per minute)
  volume: 1.0  # Volume level (0.0 to 1.0)

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

### Available Voices

The system supports various voices depending on your OS:

**macOS Voices:**
- `com.apple.voice.compact.en-US.Samantha` (Female, US English)
- `com.apple.voice.compact.en-US.Alex` (Male, US English)
- `com.apple.voice.compact.en-GB.Daniel` (Male, UK English)

## Testing

### Scenario-Based Testing

The project uses **scenario-based testing** for better organization and clarity. Each scenario tests specific functionality in a standardized way.

#### Run All Scenarios
```bash
python tests/run_scenarios.py
```

#### Run Specific Scenario Categories
```bash
# Test TTS functionality
python tests/run_scenarios.py --scenario tts

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
- Welcome message testing
- Voice configuration
- Short phrases
- Long text handling

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
- **No sound**: Check audio device settings and volume
- **Wrong voice**: Update `voice_id` in `config.yaml`
- **Rate issues**: Adjust `rate` setting in `config.yaml`

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