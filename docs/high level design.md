# Home Assistant

A lightweight, modular voice-controlled API orchestration system that supports multiple languages and can intelligently call APIs based on natural language commands.

## 🎯 Project Overview

This project creates a voice assistant that:
- Runs efficiently on Raspberry Pi (tested on Pi 3B+ and Pi 4)
- Listens for a wake word using minimal CPU resources
- Processes voice commands in multiple languages
- Uses AI to understand intent and orchestrate API calls
- Provides a flexible architecture for switching between local and cloud providers

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Raspberry Pi System                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐     ┌──────────────┐     ┌─────────────┐ │
│  │  Wake Word  │────▶│    Audio     │────▶│   Speech    │ │
│  │  Detection  │     │   Capture    │     │ Recognition │ │
│  │(OpenWakeWord)     │              │     │  (Hybrid)   │ │
│  └─────────────┘     └──────────────┘     └──────┬──────┘ │
│                                                   │         │
│                      ┌──────────────┐             │         │
│                      │      AI      │◀────────────┘         │
│                      │ Orchestrator │                       │
│                      │  (GPT/Claude)│                       │
│                      └──────┬───────┘                       │
│                             │                               │
│                      ┌──────┴───────┐                       │
│                      │     API      │                       │
│                      │   Manager    │                       │
│                      └──────┬───────┘                       │
│                             │                               │
│  ┌──────────────────────────┴──────────────────────────┐  │
│  │                   Local APIs                         │  │
│  ├─────────────┬──────────────┬────────────┬──────────┤  │
│  │   Lights    │  Temperature │   Security │  Custom  │  │
│  │    API      │     API      │     API    │   APIs   │  │
│  └─────────────┴──────────────┴────────────┴──────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Features

### Core Features
- **Wake Word Detection**: Energy-efficient continuous listening
- **Multi-Language Support**: 20+ languages supported
- **Hybrid Recognition**: Automatic fallback from cloud to offline
- **AI-Powered Understanding**: Natural language processing for complex commands
- **Modular Architecture**: Easy to swap providers and add new capabilities

### Supported Voice Providers
- **Google Speech-to-Text** (default for cloud)
- **OpenAI Whisper API** (for complex commands)
- **Vosk** (offline fallback)
- **Azure Speech Services** (optional)

### Wake Word Solutions
- **OpenWakeWord** (recommended - free & open source)
- **Porcupine** (highest accuracy)
- **PocketSphinx** (most lightweight)

## 📋 Requirements

### Hardware
- Raspberry Pi 3B+ or newer (Pi 4 recommended)
- USB Microphone or I2S MEMS microphone
- Speaker (USB, 3.5mm jack, or I2S)
- MicroSD card (16GB minimum)
- Stable internet connection (for cloud services)

### Software
- Raspberry Pi OS (Bullseye or newer)
- Python 3.8+
- PortAudio
- Git

## 🛠️ Installation

### 1. System Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y \
    python3-pip \
    python3-venv \
    git \
    portaudio19-dev \
    python3-pyaudio \
    libatlas-base-dev \
    libgfortran5

# Install audio utilities
sudo apt install -y alsa-utils pulseaudio
```

### 2. Clone Repository
```bash
git clone https://github.com/szelenin/home_assistant.git
cd home_assistant
```

### 3. Python Environment
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt
```

### 4. Configure Audio
```bash
# Test microphone
arecord -l  # List recording devices
arecord -D plughw:1,0 -d 5 test.wav  # Test recording
aplay test.wav  # Test playback

# Set default audio devices
sudo nano /etc/asound.conf
```

### 5. Download Models (for offline support)
```bash
# Download Vosk model
cd models
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip

# Download wake word models
python download_wake_models.py
```

## 📁 Project Structure

```
home_assistant/
├── README.md
├── requirements.txt
├── config.yaml                 # Configuration file
├── .env.example               # Environment variables template
├── src/
│   ├── __init__.py
│   ├── wake_word/
│   │   ├── __init__.py
│   │   ├── detector.py        # Wake word detection interface
│   │   ├── openwakeword.py    # OpenWakeWord implementation
│   │   └── porcupine.py       # Porcupine implementation
│   ├── speech/
│   │   ├── __init__.py
│   │   ├── recognizer.py      # Speech recognition interface
│   │   ├── google_stt.py      # Google STT provider
│   │   ├── whisper.py         # OpenAI Whisper provider
│   │   └── vosk_stt.py        # Vosk offline provider
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── orchestrator.py    # AI command processing
│   │   └── providers.py       # AI provider implementations
│   ├── api/
│   │   ├── __init__.py
│   │   ├── manager.py         # API endpoint manager
│   │   └── endpoints/         # Local API implementations
│   └── utils/
│       ├── __init__.py
│       ├── audio.py           # Audio utilities
│       └── config.py          # Configuration manager
├── models/                    # Offline models directory
├── tests/                     # Unit tests
├── examples/                  # Example API endpoints
│   ├── lights_api.py
│   ├── temperature_api.py
│   └── README.md
└── scripts/
    ├── setup.sh              # Setup script
    └── run_assistant.sh      # Start script
```

## ⚙️ Configuration

### config.yaml
```yaml
# Wake word configuration
wake_word:
  provider: "openwakeword"  # Options: openwakeword, porcupine, pocketsphinx
  models:
    - "hey_jarvis"
    - "ok_computer"
  sensitivity: 0.5

# Speech recognition configuration  
speech:
  provider: "hybrid"  # Options: google, whisper, vosk, hybrid
  primary:
    type: "google"
    language: "en-US"
  fallback:
    type: "vosk"
    model_path: "models/vosk-model-small-en-us-0.15"
  
# AI orchestrator configuration
ai:
  provider: "openai"  # Options: openai, anthropic, local
  model: "gpt-4"
  temperature: 0.7

# API endpoints configuration
apis:
  - name: "lights"
    description: "Control smart lights"
    base_url: "http://localhost:8001"
    endpoints:
      on:
        method: "POST"
        path: "/lights/on"
        description: "Turn lights on"
      off:
        method: "POST"
        path: "/lights/off"
        description: "Turn lights off"
        
# Audio configuration
audio:
  input_device: 1  # Use arecord -l to find
  sample_rate: 16000
  chunk_size: 512
```

### Environment Variables (.env)
```bash
# API Keys
OPENAI_API_KEY=your_openai_key_here
GOOGLE_CLOUD_KEY=your_google_key_here  # Optional
PICOVOICE_ACCESS_KEY=your_picovoice_key_here  # If using Porcupine

# Optional configurations
LOG_LEVEL=INFO
MAX_RECORDING_SECONDS=10
SILENCE_THRESHOLD=500
```

## 🎮 Usage

### Basic Usage
```bash
# Start the assistant
python main.py

# Or use the convenience script
./scripts/run_assistant.sh
```

### Command Examples
```
You: "Hey Jarvis"
Assistant: *listening beep*
You: "Turn on the living room lights"
Assistant: "Living room lights turned on"

You: "Hey Jarvis"
Assistant: *listening beep*
You: "What's the temperature in the bedroom?"
Assistant: "The bedroom temperature is 22 degrees Celsius"
```

### Adding Custom APIs
1. Define your API in `config.yaml`
2. Implement the endpoint (see `examples/`)
3. Restart the assistant

Example API implementation:
```python
# examples/custom_api.py
from fastapi import FastAPI

app = FastAPI()

@app.post("/custom/action")
async def custom_action(params: dict):
    # Your logic here
    return {"status": "success", "message": "Action completed"}
```

## 🌍 Multi-Language Support

Configure language in `config.yaml`:
```yaml
speech:
  primary:
    type: "google"
    language: "es-ES"  # Spanish
    # Supported: en-US, es-ES, fr-FR, de-DE, it-IT, pt-BR, ja-JP, ko-KR, zh-CN
```

## 🔧 Advanced Configuration

### Performance Tuning
```yaml
# For Raspberry Pi Zero/3A+
performance:
  mode: "low_power"
  wake_word_cpu_limit: 5  # Percentage
  buffer_size: 8192
  
# For Raspberry Pi 4
performance:
  mode: "balanced"
  wake_word_cpu_limit: 10
  buffer_size: 16384
```

### Custom Wake Words
```bash
# Train custom wake word with OpenWakeWord
python scripts/train_wake_word.py --word "custom_word" --samples 50
```

## 🐛 Troubleshooting

### Common Issues

1. **No audio input detected**
   ```bash
   # Check audio devices
   arecord -l
   # Test recording
   arecord -D plughw:1,0 -f S16_LE -r 16000 test.wav
   ```

2. **High CPU usage**
   - Switch to lighter wake word model
   - Reduce sample rate to 8000Hz
   - Use PocketSphinx instead of OpenWakeWord

3. **Network timeouts**
   - Enable offline mode in config
   - Increase timeout values
   - Check internet connection

4. **Permission errors**
   ```bash
   # Add user to audio group
   sudo usermod -a -G audio $USER
   # Logout and login again
   ```

## 📊 Performance Metrics

| Component | CPU Usage (Pi 4) | CPU Usage (Pi 3) | Memory |
|-----------|------------------|------------------|---------|
| Wake Word | 3-5% | 5-8% | 50MB |
| Idle | <1% | <1% | 100MB |
| Recognition | 15-20% | 25-30% | 200MB |
| AI Processing | 5-10% | 10-15% | 150MB |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenWakeWord team for the efficient wake word detection
- Vosk project for offline speech recognition
- Raspberry Pi Foundation for the amazing hardware

## 📮 Support

- Create an issue for bugs or feature requests
- Check the [Wiki](https://github.com/szelenin/home_assistant/wiki) for detailed guides
- Join our [Discord community](https://discord.gg/yourlink)

## 🗺️ Roadmap

- [ ] Home Assistant integration
- [ ] Custom skill framework
- [ ] Voice feedback/TTS
- [ ] Multi-room support
- [ ] Bluetooth speaker support
- [ ] Web dashboard for configuration
- [ ] Docker container support
- [ ] Voice training interface