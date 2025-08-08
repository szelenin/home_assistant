# Home Assistant

A Python-based voice-controlled home automation system with wake word detection, speech recognition, and text-to-speech capabilities.

## Features

- **Voice Control**: Speech recognition for hands-free operation
- **Multi-Provider Text-to-Speech**: Support for pyttsx3, eSpeak-NG, and Piper neural TTS with configurable providers
- **Multi-Provider Speech Recognition**: Support for Vosk (offline), Google (online), and OpenAI Whisper (offline) with configurable providers
- **Multi-Provider Wake Word Detection**: Support for OpenWakeWord (offline custom), Porcupine (commercial), and PocketSphinx (basic free) with configurable providers
- **AI Integration**: Claude (Anthropic) and ChatGPT (OpenAI) support with automatic fallback
- **Intent Recognition**: Understands weather, device control, personal info, and general questions
- **Natural Language Processing**: Translates commands to device API calls
- **Device Management**: Control smart lights, thermostats, and other IoT devices
- **Automation**: Create custom automation rules for your smart home
- **Configuration**: YAML-based configuration system

## Getting Started

### Prerequisites

- Python 3.8 or higher
- macOS (for voice features) or Linux
- Git

### System Dependencies

#### Core Dependencies (Required)

**PortAudio** - Required for speech recognition (PyAudio)

**macOS:**
```bash
brew install portaudio
```

**Ubuntu/Debian:**
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
```

**Fedora/RHEL/CentOS:**
```bash
sudo dnf install portaudio-devel
```

**Arch Linux:**
```bash
sudo pacman -S portaudio
```

#### Speech Recognition Engine Dependencies (Optional)

Choose the speech recognition engines you want to use. The default `vosk` provider offers excellent offline recognition ideal for Raspberry Pi deployment.

##### Vosk Offline Speech Recognition (Default)
**Description:** Lightweight offline speech recognition, perfect for Raspberry Pi  
**Documentation:** [Vosk API Docs](https://alphacephei.com/vosk/) • [GitHub](https://github.com/alphacep/vosk-api)  
**Voice Samples:** [Demo Page](https://alphacephei.com/vosk/samples) • Test with various languages and accents

**Installation:**
1. **Download Models** from [Vosk Models](https://alphacephei.com/vosk/models):
```bash
# Recommended for Raspberry Pi (40MB, fast)
curl -LO https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip

# Better accuracy (50MB, balanced)
curl -LO https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip
unzip vosk-model-en-us-0.22.zip

# Highest accuracy (1.8GB, resource intensive)
curl -LO https://alphacephei.com/vosk/models/vosk-model-en-us-0.42-gigaspeech.zip
unzip vosk-model-en-us-0.42-gigaspeech.zip
```

2. **Configure:**
```yaml
speech:
  provider: vosk
  providers:
    vosk:
      model_path: "./vosk-model-small-en-us-0.15"
      confidence_threshold: 0.8  # 0.0-1.0
      sample_rate: 16000
```

**Available Languages:** English, German, French, Spanish, Russian, Portuguese, Turkish, Vietnamese, Italian, Dutch, Catalan, Arabic, Greek, Farsi, Filipino, Ukrainian, Kazakh, Swedish, Japanese, Esperanto, Hindi, Czech, Polish, Uzbek, Korean, Brazilian Portuguese, Chinese

**Model Comparison:**
- **Small** (40MB): ~85% accuracy, 0.5s latency, ideal for Pi
- **Medium** (50MB): ~90% accuracy, 1s latency, balanced choice  
- **Large** (1.8GB): ~95% accuracy, 2s latency, desktop/server use

##### Google Speech Recognition (Online)
**Description:** High-accuracy online speech recognition with extensive language support  
**Documentation:** [Google Speech-to-Text](https://cloud.google.com/speech-to-text) • [Python Client](https://github.com/googleapis/python-speech)  
**Voice Samples:** [Language Support](https://cloud.google.com/speech-to-text/docs/languages) • 125+ languages and variants

**Installation:** Included with `SpeechRecognition` library (no additional setup)

**Configuration:**
```yaml
speech:
  provider: google
  providers:
    google:
      show_all: false  # true = confidence scores, false = best result only
```

**Free Tier Limits:**
- **No API key** required for basic usage via SpeechRecognition library
- **60 minutes/month** free recognition time
- **15-second clips** maximum per request
- **Rate limited** but suitable for personal/development use
- **Internet required** for all requests

**Supported Features:**
- **Automatic punctuation** and capitalization
- **Profanity filtering** available
- **Real-time streaming** (with Cloud Speech API)
- **Noise robustness** excellent in various environments

**Languages:** English (US/UK/AU/IN), Spanish, French, German, Italian, Portuguese, Russian, Japanese, Korean, Mandarin, Hindi, Arabic, Dutch, Polish, Turkish, and 100+ more

##### OpenAI Whisper (Offline)
**Description:** State-of-the-art offline speech recognition with exceptional multilingual support  
**Documentation:** [Whisper GitHub](https://github.com/openai/whisper) • [Model Card](https://github.com/openai/whisper/blob/main/model-card.md) • [Paper](https://arxiv.org/abs/2212.04356)  
**Voice Samples:** [Interactive Demo](https://huggingface.co/spaces/openai/whisper) • Test with 99 languages

**Installation:** Included with requirements.txt (`openai-whisper` package)

**Models:** Auto-downloaded on first use from Hugging Face:
| Model | Size | VRAM | Speed | WER* |
|-------|------|------|--------|-----|
| **tiny** | 39MB | ~1GB | ~32x | 9.4% |
| **base** | 74MB | ~1GB | ~16x | 7.0% |
| **small** | 244MB | ~2GB | ~6x | 5.7% |
| **medium** | 769MB | ~5GB | ~2x | 4.9% |
| **large** | 1550MB | ~10GB | 1x | **4.3%** |

*WER = Word Error Rate (lower is better)

**Configuration:**
```yaml
# For Raspberry Pi - use tiny/base models
speech:
  provider: whisper
  providers:
    whisper:
      model: base         # tiny, base, small, medium, large
      device: cpu         # cpu or cuda
      temperature: 0.0    # 0.0 = deterministic, higher = more creative
```

**Supported Languages:** Afrikaans, Arabic, Armenian, Azerbaijani, Belarusian, Bosnian, Bulgarian, Catalan, Chinese, Croatian, Czech, Danish, Dutch, English, Estonian, Finnish, French, Galician, German, Greek, Hebrew, Hindi, Hungarian, Icelandic, Indonesian, Italian, Japanese, Kannada, Kazakh, Korean, Latvian, Lithuanian, Macedonian, Malay, Marathi, Maori, Nepali, Norwegian, Persian, Polish, Portuguese, Romanian, Russian, Serbian, Slovak, Slovenian, Spanish, Swahili, Swedish, Tagalog, Tamil, Thai, Turkish, Ukrainian, Urdu, Vietnamese, Welsh, and more

**Hardware Requirements:**
- **CPU**: 2+ cores recommended, 4+ for larger models
- **RAM**: 4GB+ (8GB+ for medium/large models)
- **GPU**: CUDA-compatible GPU optional but provides 5-10x speedup
- **Disk**: 40MB-1.5GB depending on model

#### Wake Word Detection Engine Dependencies (Optional)

Choose the wake word detection engines you want to use. The default `openwakeword` provider offers excellent custom wake word support with offline operation.

##### OpenWakeWord (Default)
**Description:** Free offline wake word detection with custom word support  
**Documentation:** [OpenWakeWord GitHub](https://github.com/dscripka/openWakeWord) • [Model Hub](https://github.com/dscripka/openWakeWord/tree/main/openwakeword/models)  
**Demo:** [Interactive Web Demo](https://openwakeword.com/demo/) • Test custom wake words

**Prerequisites:**
```bash
# Install OpenWakeWord Python package (included in requirements.txt)
pip install openwakeword

# For ONNX framework support (recommended)
pip install onnxruntime
```

**Installation:**
1. **Download Models** (automatically using Python utility - recommended):
```bash
# After installing requirements.txt, download models using the official utility
python -c "
import openwakeword.utils
openwakeword.utils.download_models(target_directory='./openwakeword_models')
print('✅ Models downloaded successfully')

# Copy core models to OpenWakeWord package directory (required for ONNX framework)
import os, shutil, openwakeword
package_path = os.path.dirname(openwakeword.__file__)
package_models_dir = os.path.join(package_path, 'resources', 'models')
os.makedirs(package_models_dir, exist_ok=True)

core_models = ['embedding_model.onnx', 'melspectrogram.onnx', 'silero_vad.onnx']
for model in core_models:
    local_path = f'./openwakeword_models/{model}'
    package_path_file = os.path.join(package_models_dir, model)
    if os.path.exists(local_path) and not os.path.exists(package_path_file):
        shutil.copy2(local_path, package_path_file)
        print(f'✅ Copied {model} to package directory')
print('✅ Core models installed in package directory')
"
```

**Alternative: Manual Installation** (if Python utility fails):
```bash
# Step 1: Create models directory
mkdir -p openwakeword_models
cd openwakeword_models

# Step 2: Download core models (required for all wake words)
curl -LO https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/embedding_model.onnx
curl -LO https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/melspectrogram.onnx
curl -LO https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/silero_vad.onnx

# Step 3: Download wake word models (choose what you need)
curl -LO https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/alexa_v0.1.onnx
curl -LO https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/hey_jarvis_v0.1.onnx
curl -LO https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/hey_mycroft_v0.1.onnx
curl -LO https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/timer_v0.1.onnx
curl -LO https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/weather_v0.1.onnx

# Step 4: Return to project directory
cd ..

# Step 5: Copy core models to OpenWakeWord package directory (CRITICAL STEP)
# This step is required because OpenWakeWord looks for core models in its package directory
python -c "
import os, shutil, openwakeword

# Find OpenWakeWord package directory
package_path = os.path.dirname(openwakeword.__file__)
package_models_dir = os.path.join(package_path, 'resources', 'models')

# Create the directory if it doesn't exist
os.makedirs(package_models_dir, exist_ok=True)
print(f'📁 Package models directory: {package_models_dir}')

# Copy each core model
core_models = ['embedding_model.onnx', 'melspectrogram.onnx', 'silero_vad.onnx']
for model in core_models:
    local_path = f'./openwakeword_models/{model}'
    package_path_file = os.path.join(package_models_dir, model)
    
    if os.path.exists(local_path):
        if not os.path.exists(package_path_file):
            shutil.copy2(local_path, package_path_file)
            print(f'✅ Copied {model} to package directory')
        else:
            print(f'ℹ️  {model} already exists in package directory')
    else:
        print(f'❌ {model} not found in local directory')

print('✅ Core model installation complete')
"

# Step 6: Verify installation
python -c "
from home_assistant.wake_word.detector import WakeWordDetector
detector = WakeWordDetector('openwakeword')
if detector.is_available():
    print('🎉 OpenWakeWord installation successful!')
    info = detector.get_provider_info()
    print(f'   Available models in {info[\"model_path\"]}')
    detector.cleanup()
else:
    print('❌ OpenWakeWord installation failed')
"
```

**Troubleshooting OpenWakeWord Installation:**

If you encounter issues:

1. **"Protobuf parsing failed" error**: Core models missing from package directory
   ```bash
   # Check if core models exist in package directory
   python -c "
   import openwakeword, os
   package_dir = os.path.join(os.path.dirname(openwakeword.__file__), 'resources', 'models')
   core_models = ['embedding_model.onnx', 'melspectrogram.onnx', 'silero_vad.onnx']
   for model in core_models:
       path = os.path.join(package_dir, model)
       exists = os.path.exists(path)
       print(f'{model}: {\"✅ Found\" if exists else \"❌ Missing\"} at {path}')
   "
   ```

2. **"File doesn't exist" error**: Run the core model copy step again (Step 5 above)

3. **"tflite runtime not found" warning**: This is normal when using ONNX framework, ignore it

4. **Permission errors**: Use `sudo` for the copy command or check directory permissions

2. **Configure:**
```yaml
wake_word:
  name: "TestAssistant"  # Your assistant's name
  detection:
    provider: openwakeword
    providers:
      openwakeword:
        model_path: "./openwakeword_models"
        threshold: 0.5        # 0.0-1.0 detection sensitivity
        inference_framework: "onnx"  # onnx or tflite
```

**Available Models:**
- **Alexa** - Amazon's wake word
- **Hey Jarvis** - Iron Man inspired
- **Hey Mycroft** - Open source assistant  
- **Computer** - Star Trek inspired
- **Custom Models** - Train your own with OpenWakeWord toolkit

**Model Performance:**
- **Accuracy**: 85-95% (varies by model and environment)
- **Latency**: 100-300ms detection time
- **Resource Usage**: Medium (40-200MB models, moderate CPU)
- **Custom Training**: Supported with toolkit

##### Picovoice Porcupine (Commercial)
**Description:** High-accuracy commercial wake word detection with very low latency  
**Documentation:** [Porcupine Docs](https://picovoice.ai/docs/porcupine/) • [Console](https://console.picovoice.ai/)  
**Demo:** [Interactive Demo](https://picovoice.ai/demos/) • Test built-in keywords

**Installation:**
1. **Get Access Key** from [Picovoice Console](https://console.picovoice.ai/):
   - Sign up for free account
   - Create a new access key
   - Note: Free tier has usage limits

2. **Configure:**
```yaml
wake_word:
  detection:
    provider: porcupine
    providers:
      porcupine:
        access_key: "your-picovoice-key-here"  # From console
        keyword_path: null  # Use built-in keywords or custom .ppn file
```

**Built-in Keywords:** Alexa, Computer, Jarvis, Smart Mirror, Hey Google, Hey Siri, Bumblebee, Grasshopper, Picovoice, Terminator

**Features:**
- **Accuracy**: 95%+ with optimized models
- **Latency**: ~30ms (very low)
- **Resource Usage**: Very low (optimized for edge devices)
- **Custom Keywords**: Available with subscription
- **Commercial License**: Required for commercial use

##### PocketSphinx (Free/Basic)
**Description:** Free offline keyword spotting using CMU Sphinx  
**Documentation:** [PocketSphinx](https://github.com/cmusphinx/pocketsphinx) • [CMU Sphinx](https://cmusphinx.github.io/)

**Installation:** Included with requirements.txt (`pocketsphinx` package)

**Configuration:**
```yaml
wake_word:
  detection:
    provider: pocketsphinx
    providers:
      pocketsphinx:
        hmm_path: null              # Acoustic model (uses default)
        dict_path: null             # Dictionary (uses default)
        keyphrase_threshold: 1e-20  # Detection sensitivity
```

**Features:**
- **Accuracy**: 70-85% (depends on conditions and tuning)
- **Latency**: 200-500ms
- **Resource Usage**: Low-medium
- **Custom Keywords**: Any phrase supported
- **Licensing**: BSD (completely free)

#### Quick Comparison - Wake Word Detection

| Provider | Type | Accuracy | Latency | Resource Usage | Custom Words | Cost |
|----------|------|----------|---------|----------------|--------------|------|
| **OpenWakeWord** | Offline | 85-95% | 100-300ms | Medium | ✅ Toolkit | Free |
| **Porcupine** | Offline | 95%+ | ~30ms | Very Low | ✅ Paid | Freemium |  
| **PocketSphinx** | Offline | 70-85% | 200-500ms | Low-Medium | ✅ Any phrase | Free |

**Recommendations:**
- **Privacy/Custom**: OpenWakeWord (default)
- **Best Performance**: Porcupine (commercial)
- **Basic/Free**: PocketSphinx (simple setup)

#### TTS Engine Dependencies (Optional)

Choose the TTS engines you want to use. The default `piper` provider offers the highest quality neural speech synthesis.

##### eSpeak-NG (Direct Provider)
For using the direct eSpeak TTS provider:

**macOS:**
```bash
brew install espeak-ng
```

**Ubuntu/Debian:**
```bash
sudo apt-get install espeak-ng
```

**Fedora/RHEL/CentOS:**
```bash
sudo dnf install espeak-ng
```

**Arch Linux:**
```bash
sudo pacman -S espeak-ng
```

##### Piper Neural TTS (Default - Model Download Required)
Piper TTS is the default high-quality neural TTS engine. It requires downloading neural voice models:

**1. Download Voice Models:**
Choose and download models from [Piper Releases](https://github.com/rhasspy/piper/releases):

**Popular English Models:**
```bash
# Download en_US-lessac-medium (Female US English) - Recommended
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/en_US-lessac-medium.onnx
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/en_US-lessac-medium.onnx.json

# Download en_US-danny-low (Male US English)
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/en_US-danny-low.onnx
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/en_US-danny-low.onnx.json

# Download en_GB-alan-medium (Male UK English)
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/en_GB-alan-medium.onnx
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/en_GB-alan-medium.onnx.json
```

**Other Languages:**
```bash
# German
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/de_DE-thorsten-medium.onnx
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/de_DE-thorsten-medium.onnx.json

# French
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/fr_FR-mls_1840-low.onnx
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/fr_FR-mls_1840-low.onnx.json

# Spanish
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/es_ES-mls_9972-low.onnx
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/es_ES-mls_9972-low.onnx.json
```

**2. Place model files in your project directory:**
```bash
# Models should be in the same directory as your main.py
ls *.onnx *.onnx.json
# en_US-lessac-medium.onnx  en_US-lessac-medium.onnx.json
```

**3. Update config.yaml:**
```yaml
tts:
  provider: piper
  providers:
    piper:
      model: en_US-lessac-medium  # Model name without .onnx extension
```

**Model Size Reference:**
- **X-Low quality**: ~20MB, basic quality, fast
- **Low quality**: ~40MB, good quality, fast  
- **Medium quality**: ~60MB, high quality, moderate speed
- **High quality**: ~100MB+, excellent quality, slower

**Browse all available models**: [Piper Voice Samples](https://rhasspy.github.io/piper-samples/)

### Quick Installation

**🚀 One-Command Installation (Recommended):**

Run the appropriate command for your operating system:

**macOS:**
```bash
curl -fsSL https://raw.githubusercontent.com/szelenin/home_assistant/main/install-macos.sh | bash
```

**Linux/Raspberry Pi:**
```bash
curl -fsSL https://raw.githubusercontent.com/szelenin/home_assistant/main/install-linux.sh | bash
```

**Alternative - Download and Run Locally:**
```bash
# Download the script first (safer approach)
curl -fsSL https://raw.githubusercontent.com/szelenin/home_assistant/main/install-macos.sh > install-macos.sh
# or
curl -fsSL https://raw.githubusercontent.com/szelenin/home_assistant/main/install-linux.sh > install-linux.sh

# Review the script (optional but recommended)
less install-macos.sh  # or install-linux.sh

# Make executable and run
chmod +x install-macos.sh
./install-macos.sh
```

#### What the Installation Script Does:

**🔍 System Check:**
1. **Detects operating system** (macOS, Ubuntu, Debian, Fedora, Arch, Raspberry Pi OS)
2. **Validates Python 3.8+** installation
3. **Checks for required tools** (git, curl, unzip)

**📦 System Dependencies:**
4. **Installs system packages:**
   - **PortAudio** (required for speech recognition)
   - **Development tools** (build-essential, python3-dev)
   - **Audio libraries** (ALSA on Linux)
   - **Homebrew** (macOS, if not installed)

**🏠 Project Setup:**
5. **Clones Home Assistant repository** (if not already present)
6. **Creates Python virtual environment** (`venv/`)
7. **Installs Python dependencies** from `requirements.txt`

**🎤 Speech Recognition Setup:**
8. **Downloads optimized Vosk model:**
   - **Raspberry Pi**: `vosk-model-small-en-us-0.15` (40MB, fast)
   - **Linux/macOS**: `vosk-model-en-us-0.22` (50MB, better accuracy)
9. **Configures model path** in `config.yaml`

**👂 Wake Word Detection Setup:**
10. **Downloads OpenWakeWord models** (all wake words and core models)
11. **Copies core models** to OpenWakeWord package directory automatically
12. **Configures wake word detection** in `config.yaml`

**🔧 Configuration:**
13. **Creates AI configuration template** (`ai_config.yaml`)
14. **Sets up audio permissions** (Linux/Pi: adds user to audio group)
15. **Configures ALSA** (Raspberry Pi specific)

**✅ Verification:**
16. **Runs system tests** to verify installation
17. **Displays next steps** with API key setup instructions

#### Installation Output:
The script provides colored output showing progress:
- 🔵 **[STEP]** - Major installation phases
- 🟢 **[INFO]** - Successful operations  
- 🟡 **[WARNING]** - Non-critical issues
- 🔴 **[ERROR]** - Critical failures

#### Common Installation Issues:

**🔴 "Python 3.8+ required" error:**
- **macOS**: Install from [python.org](https://www.python.org/downloads/) or `brew install python3`
- **Linux**: `sudo apt update && sudo apt install python3 python3-venv python3-pip`

**🔴 "PortAudio not found" error:**
- **macOS**: `brew install portaudio`  
- **Ubuntu/Debian**: `sudo apt install portaudio19-dev python3-pyaudio`
- **Raspberry Pi**: Reboot may be required after installation

**🔴 "Permission denied" for microphone:**
- **macOS**: System Preferences → Security & Privacy → Privacy → Microphone
- **Linux**: Ensure user is in `audio` group: `sudo usermod -a -G audio $USER`

**🔴 Vosk model download fails:**
- Manual download: [Vosk Models](https://alphacephei.com/vosk/models)
- Extract to project directory and update `config.yaml`

**🔴 "No module named 'home_assistant'" error:**
- Ensure virtual environment is activated: `source venv/bin/activate`
- Check you're in the correct directory with `main.py` and `config.yaml`

#### After Installation:
1. **Add AI API keys** to `ai_config.yaml`:
   - [Get Anthropic Claude key](https://console.anthropic.com/settings/keys) (recommended)
   - [Get OpenAI ChatGPT key](https://platform.openai.com/api-keys) (alternative)

2. **Grant microphone permissions** (macOS):
   - System Preferences → Security & Privacy → Privacy → Microphone
   - Enable access for Terminal/your IDE

3. **Run the application:**
   ```bash
   source venv/bin/activate
   python main.py
   ```

### Manual Installation

If you prefer to install manually or need custom configuration:

#### Prerequisites
Ensure you have the required system dependencies installed first (see [System Dependencies](#system-dependencies) section above).

#### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/szelenin/home_assistant.git
   cd home_assistant
   ```

2. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies:**
   ```bash
   # Install all dependencies (includes TTS providers and speech recognition engines)
   pip install -r requirements.txt
   ```

4. **Download Vosk speech recognition model:**
   ```bash
   # For Raspberry Pi (small model, 40MB):
   curl -LO https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
   unzip vosk-model-small-en-us-0.15.zip
   
   # For desktop/server (medium model, 50MB):
   curl -LO https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip
   unzip vosk-model-en-us-0.22.zip
   
   # Update config.yaml with correct model path:
   # Edit the 'model_path' setting to point to your downloaded model
   ```

5. **Configure AI Provider (Required):**
   
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

6. **Test the installation:**
   ```bash
   # Test speech recognition providers
   python tests/integration/test_recognizer.py
   
   # Test TTS providers  
   python tests/integration/test_tts.py
   
   # Quick system check
   python -c "
   from home_assistant.speech.recognizer import SpeechRecognizer
   recognizer = SpeechRecognizer()
   print('Available providers:', recognizer.get_available_providers())
   "
   ```

7. **Run the application:**
   ```bash
   python main.py
   ```

## Configuration

### Voice Settings (`config.yaml`)

The system now supports multiple TTS providers with configurable settings:

```yaml
tts:
  provider: piper  # Options: piper, pyttsx, espeak (piper is default)
  providers:
    piper:
      model: en_US-lessac-medium
      rate: 1.0
      volume: 1.0
      speaker_id: null
      output_raw: false
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

speech:
  provider: vosk  # Options: vosk, google, whisper
  language: en-US
  providers:
    vosk:
      model_path: "./vosk-model-en-us-0.22"
      confidence_threshold: 0.8
      sample_rate: 16000
    google:
      show_all: false
    whisper:
      model: base
      device: cpu
      temperature: 0.0

wake_word:
  name: null  # Custom wake word (null for default)
  sensitivity: 0.5  # Wake word sensitivity
```

### Speech Recognition Providers

The system supports multiple speech recognition providers with configurable selection (no fallback - single provider operation):

#### Quick Comparison

| Provider | Type | Accuracy | Speed | Languages | Best Use Case |
|----------|------|----------|--------|-----------|---------------|
| **Vosk** | Offline | 85-95% | Fast | 25+ | Raspberry Pi, Privacy |
| **Google** | Online | 95%+ | Very Fast | 125+ | High accuracy + Internet |
| **Whisper** | Offline | 95%+ | Slow | 99+ | Best offline accuracy |

#### 1. Vosk Offline Recognition (Default) 🥇
**Status:** ✅ Included • Requires model download  
**Strengths:** Lightweight, fast, privacy-friendly, Pi-optimized  
**Weaknesses:** Limited language models compared to cloud services  

**Ideal for:** Raspberry Pi deployments, offline environments, privacy-critical applications

#### 2. Google Speech Recognition (Online) 🌐
**Status:** ✅ Included • No setup required  
**Strengths:** Excellent accuracy, 60min/month free, vast language support  
**Weaknesses:** Internet dependent, usage limits, privacy concerns  

**Ideal for:** Development, testing, applications with reliable internet

#### 3. OpenAI Whisper (Offline) 🎯
**Status:** ✅ Included • Auto-downloads models  
**Strengths:** State-of-the-art accuracy, 99 languages, robust to noise  
**Weaknesses:** Resource intensive, slow on CPU, large models  

**Ideal for:** Desktop/server deployments, multilingual needs, batch processing

#### Provider Architecture
- **Single provider operation** - no automatic fallbacks
- **Factory pattern** - consistent with TTS system  
- **Configuration-driven** - select provider in config.yaml
- **Provider-specific optimizations** - each engine tuned independently

### Text-to-Speech Providers

The system supports multiple TTS providers with automatic availability detection and graceful fallback:

#### 1. Piper Neural TTS (Default)
**Description:** High-quality neural text-to-speech  
**Status:** ✅ Included in requirements.txt, requires model download  
**Quality:** Excellent, human-like  
**Requirements:** Neural voice models (see System Dependencies section above)

**Installation:**
```bash
# Install with specific requirements file
pip install -r requirements-tts-piper.txt
```

**Popular Models:**
- `en_US-lessac-medium` - Female US English (recommended, included)
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

#### 2. Pyttsx (System TTS)
**Description:** Uses pyttsx3 library with system TTS engines  
**Status:** ✅ Available on all platforms, no setup required  
**Quality:** Good, uses system voices  
**Requirements:** No additional installation

**Installation:**
```bash
# Install with specific requirements file
pip install -r requirements-tts-pyttsx.txt
```

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

#### 3. eSpeak-NG (Direct)
**Description:** Direct subprocess calls to eSpeak-NG  
**Status:** ⚠️ Requires system installation  
**Quality:** Basic, robotic but clear  
**Requirements:** Install eSpeak-NG system package (see System Dependencies section above)

**Installation:**
```bash
# Install with specific requirements file  
pip install -r requirements-tts-espeak.txt

# System installation required (see System Dependencies section)
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

#### Provider Selection Priority
1. **Piper Neural TTS** (default, highest quality)
2. **Automatic fallback** to pyttsx if Piper fails or models unavailable
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

#### Testing Speech Recognition Providers
```bash
# Test all available speech recognition providers
python tests/integration/test_recognizer.py

# Check provider availability
python -c "
from home_assistant.speech.recognizer import SpeechRecognizer
recognizer = SpeechRecognizer()
print('Available providers:', recognizer.get_available_providers())
"

# Test specific provider
python -c "
from home_assistant.speech.recognizer import SpeechRecognizer
recognizer = SpeechRecognizer('vosk')  # or 'google', 'whisper'
print('Testing provider:', recognizer.provider_name)
print('Provider info:', recognizer.get_provider_info())
success, text = recognizer.listen_for_speech(timeout=2)
print('Recognition result:', success, text)
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

# Test speech recognition (new provider-based system)
python tests/integration/test_recognizer.py

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
- Provider availability testing

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

#### General Speech Recognition Issues
- **"Could not find PyAudio"**: Install PortAudio first, then PyAudio
- **Microphone not working**: Check system permissions and microphone settings
- **Speech not recognized**: Ensure good microphone quality and clear speech
- **Provider not available**: Check system dependencies and model installations

#### Vosk Issues
- **"Unable to find model" error**: Download and extract Vosk language model
  1. Visit [Vosk Models](https://alphacephei.com/vosk/models)
  2. Download appropriate model for your language
  3. Extract to project directory
  4. Update `model_path` in config.yaml
- **Model loading slow**: Large models take time to load initially
- **Low recognition accuracy**: Try adjusting confidence_threshold or using larger model
- **Memory usage high**: Use smaller models (vosk-model-small-* variants)

#### Google Speech Issues
- **"No internet connection"**: Google Speech requires internet connectivity
- **Recognition quota exceeded**: Google's free tier has usage limits
- **Recognition timeout**: Short audio clips work better with free tier
- **API errors**: Check internet connection and Google services status

#### Whisper Issues
- **Model download slow**: Whisper downloads models automatically on first use
- **High CPU usage**: Whisper is computationally intensive
  - Use smaller models ('tiny', 'base') on slower hardware
  - Consider CPU vs GPU settings in config
- **Recognition too slow**: Try 'tiny' model for faster processing
- **Out of memory**: Use smaller models or increase system RAM
- **CUDA errors**: Set device to 'cpu' if GPU acceleration fails

#### Debugging Speech Recognition Issues
```bash
# Check provider availability
python -c "
from home_assistant.speech.recognizer import SpeechRecognizer
recognizer = SpeechRecognizer()
print('Available providers:', recognizer.get_available_providers())
for name, available in recognizer.get_available_providers().items():
    if available:
        provider_recognizer = SpeechRecognizer(name)
        print(f'{name} info:', provider_recognizer.get_provider_info())
"

# Test specific provider with verbose logging
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from home_assistant.speech.recognizer import SpeechRecognizer
recognizer = SpeechRecognizer('vosk')  # or 'google', 'whisper'
print('Testing provider:', recognizer.provider_name)
print('Is available:', recognizer.is_available())
success, text = recognizer.listen_for_speech(timeout=5)
print('Result:', success, text)
"
```

### Wake Word Detection Issues

#### General Wake Word Detection Issues
- **"Wake word detector not available"**: Check system dependencies and model installations
- **Wake word not detected**: Check microphone permissions, audio levels, and background noise
- **False wake word detections**: Adjust detection threshold or try different model
- **High CPU usage**: Use more efficient models or adjust processing parameters

#### OpenWakeWord Issues
- **"OpenWakeWord library not available"**: Install with `pip install openwakeword`
- **"No .onnx model files found"**: Download models from [OpenWakeWord Releases](https://github.com/dscripka/openWakeWord/releases)
  1. Create `openwakeword_models` directory
  2. Download `.onnx` model files
  3. Update `model_path` in config.yaml
- **Model loading slow**: Large models take time to load initially
- **Detection accuracy low**: Try adjusting threshold or using different model
- **Memory usage high**: Use smaller/optimized models for your platform

#### Porcupine Issues
- **"Invalid access key"**: Get valid key from [Picovoice Console](https://console.picovoice.ai/)
- **"Porcupine library not available"**: Install with `pip install pvporcupine`
- **Wake word not supported**: Check [built-in keywords](https://picovoice.ai/docs/porcupine/#built-in-keywords) or create custom .ppn file
- **Usage limit exceeded**: Check your Picovoice account usage and plan limits
- **Commercial license required**: Upgrade plan for commercial use

#### PocketSphinx Issues
- **"PocketSphinx library not available"**: Install with `pip install pocketsphinx`
- **Poor detection accuracy**: 
  - Adjust `keyphrase_threshold` (try 1e-15 to 1e-25)
  - Use shorter, clearer wake phrases
  - Improve microphone quality and reduce background noise
- **High false positive rate**: Increase threshold value (less sensitive)
- **High false negative rate**: Decrease threshold value (more sensitive)
- **Model loading errors**: Check HMM and dictionary paths, use defaults if custom paths fail

#### Debugging Wake Word Detection Issues
```bash
# Check wake word provider availability
source venv/bin/activate
python -c "
from home_assistant.wake_word.detector import WakeWordDetector
detector = WakeWordDetector()
print('Available providers:', detector.get_available_providers())
for name, available in detector.get_available_providers().items():
    if available:
        provider_detector = WakeWordDetector(name)
        print(f'{name} info:', provider_detector.get_provider_info())
"

# Test specific provider with verbose logging
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from home_assistant.wake_word.detector import WakeWordDetector
detector = WakeWordDetector('openwakeword')  # or 'porcupine', 'pocketsphinx'
print('Testing provider:', detector.provider_name)
print('Is available:', detector.is_available())
detected, confidence = detector.listen_for_wake_word('test wake word', timeout=5)
print('Result:', detected, confidence)
"

# Check microphone and audio permissions
python -c "
import pyaudio
audio = pyaudio.PyAudio()
print('Audio devices:')
for i in range(audio.get_device_count()):
    info = audio.get_device_info_by_index(i)
    if info['maxInputChannels'] > 0:
        print(f'  {i}: {info[\"name\"]} (inputs: {info[\"maxInputChannels\"]})')
audio.terminate()
"
```

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