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
   pip install -r requirements.txt
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
  provider: vosk  # Speech recognition provider

wake_word:
  name: null  # Custom wake word (null for default)
  sensitivity: 0.5  # Wake word sensitivity
```

### Available Voices

The system supports various voices depending on your OS:

**macOS Voices:**
- `com.apple.voice.compact.en-US.Samantha` (Female, US English)
- `com.apple.voice.compact.en-US.Alex` (Male, US English)
- `com.apple.voice.compact.en-GB.Daniel` (Male, UK English)

## Testing

### Test Speech Recognition
```bash
python tests/test_recognizer.py
```

### Test Text-to-Speech
```bash
python tests/test_tts.py
```

### Test Configuration Loading
```bash
python test_config_loading.py
```

## Project Structure

```
home_assistant/
├── config.yaml              # Main configuration file
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
├── src/
│   ├── speech/
│   │   ├── recognizer.py   # Speech recognition
│   │   └── tts.py         # Text-to-speech
│   ├── utils/
│   │   ├── config.py      # Configuration management
│   │   └── name_collector.py
│   └── modules/
│       ├── chatgpt.py     # AI integration
│       └── chatgpt_showcase.py
├── tests/
│   ├── test_recognizer.py # Speech recognition tests
│   ├── test_tts.py        # TTS tests
│   └── test_config.py     # Configuration tests
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