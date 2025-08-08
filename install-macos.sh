#!/bin/bash
set -e

# Home Assistant Installation Script for macOS
# This script installs the voice-controlled home automation system

echo "🏠 Home Assistant Installation Script for macOS"
echo "=============================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "\n${BLUE}[STEP]${NC} $1"
}

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "This script is for macOS only. Use install-linux.sh for Linux/Raspberry Pi."
    exit 1
fi

# Step 1: Check Python version
print_step "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [[ $PYTHON_MAJOR -ge 3 && $PYTHON_MINOR -ge 8 ]]; then
        print_status "Python $PYTHON_VERSION found ✅"
    else
        print_error "Python 3.8+ required. Found: $PYTHON_VERSION"
        print_status "Please install Python 3.8+ from https://www.python.org/downloads/"
        exit 1
    fi
else
    print_error "Python 3 not found. Please install from https://www.python.org/downloads/"
    exit 1
fi

# Step 2: Check for Homebrew and install system dependencies
print_step "Checking system dependencies..."
if command -v brew &> /dev/null; then
    print_status "Homebrew found ✅"
    
    print_status "Installing PortAudio (required for speech recognition)..."
    brew install portaudio || print_warning "PortAudio installation failed or already installed"
    
else
    print_warning "Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    print_status "Installing PortAudio..."
    brew install portaudio
fi

# Step 3: Clone repository (if not already cloned)
print_step "Setting up Home Assistant repository..."
if [[ ! -d "home_assistant" ]]; then
    if [[ -f "main.py" && -f "config.yaml" ]]; then
        print_status "Already in Home Assistant directory ✅"
    else
        print_status "Cloning Home Assistant repository..."
        git clone https://github.com/szelenin/home_assistant.git
        cd home_assistant
        print_status "Repository cloned ✅"
    fi
else
    cd home_assistant
    print_status "Using existing Home Assistant directory ✅"
fi

# Step 4: Create virtual environment
print_step "Setting up Python virtual environment..."
if [[ ! -d "venv" ]]; then
    print_status "Creating virtual environment..."
    python3 -m venv venv
    print_status "Virtual environment created ✅"
else
    print_status "Virtual environment already exists ✅"
fi

# Step 5: Activate virtual environment and install dependencies
print_step "Installing Python dependencies..."
source venv/bin/activate
print_status "Virtual environment activated ✅"

pip install --upgrade pip
pip install -r requirements.txt
print_status "Python dependencies installed ✅"

# Step 6: Download Vosk model
print_step "Downloading Vosk speech recognition model..."
VOSK_MODEL="vosk-model-small-en-us-0.15"
if [[ ! -d "$VOSK_MODEL" ]]; then
    print_status "Downloading Vosk model (40MB, optimized for Raspberry Pi)..."
    curl -LO "https://alphacephei.com/vosk/models/${VOSK_MODEL}.zip"
    
    if [[ -f "${VOSK_MODEL}.zip" ]]; then
        print_status "Extracting Vosk model..."
        unzip "${VOSK_MODEL}.zip"
        rm "${VOSK_MODEL}.zip"
        print_status "Vosk model installed ✅"
    else
        print_error "Failed to download Vosk model"
        print_status "You can manually download from: https://alphacephei.com/vosk/models/"
    fi
else
    print_status "Vosk model already exists ✅"
fi

# Step 7: Download OpenWakeWord models
print_step "Downloading OpenWakeWord models..."
if [[ ! -d "openwakeword_models" ]] || [[ $(ls -1 openwakeword_models/*.onnx 2>/dev/null | wc -l) -eq 0 ]]; then
    print_status "Downloading OpenWakeWord models using Python utility..."
    
    # Use the official OpenWakeWord download utility (most reliable method)
    python -c "
import openwakeword.utils
print('Downloading models to ./openwakeword_models directory...')
try:
    openwakeword.utils.download_models(target_directory='./openwakeword_models')
    print('✅ Models downloaded successfully')
except Exception as e:
    print(f'❌ Error downloading to custom directory: {e}')
    print('Trying default download location...')
    openwakeword.utils.download_models()
    print('✅ Models downloaded to default location')

# Copy core models to OpenWakeWord package directory
import os
import shutil
import openwakeword

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
" && print_status "OpenWakeWord models installed ✅" || {
        print_warning "Python download failed, trying manual download..."
        
        # Fallback: manual download with correct URLs (v0.5.1)
        mkdir -p openwakeword_models
        cd openwakeword_models
        
        print_status "Downloading core models..."
        curl -LO "https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/embedding_model.onnx" || print_warning "Failed to download embedding model"
        curl -LO "https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/melspectrogram.onnx" || print_warning "Failed to download melspectrogram model"
        curl -LO "https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/alexa_v0.1.onnx" || print_warning "Failed to download Alexa model"
        curl -LO "https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/hey_jarvis_v0.1.onnx" || print_warning "Failed to download Hey Jarvis model"
        
        cd ..
        
        # Check if core models were downloaded
        if [[ -f "openwakeword_models/embedding_model.onnx" ]] && [[ -f "openwakeword_models/melspectrogram.onnx" ]]; then
            print_status "OpenWakeWord core models installed ✅"
        else
            print_error "OpenWakeWord model download failed - wake word detection will not work"
            print_status "Please install manually: pip install openwakeword && python -c 'import openwakeword.utils; openwakeword.utils.download_models()'"
        fi
    }
else
    print_status "OpenWakeWord models already exist ✅"
fi

# Step 8: Setup AI configuration
print_step "Setting up AI configuration..."
if [[ ! -f "ai_config.yaml" ]]; then
    if [[ -f "ai_config.example.yaml" ]]; then
        cp ai_config.example.yaml ai_config.yaml
        print_status "AI config template created ✅"
    else
        print_status "Creating basic AI config template..."
        cat > ai_config.yaml << EOF
# API Keys for AI providers
# Get your keys from:
# - Anthropic Claude: https://console.anthropic.com/settings/keys
# - OpenAI ChatGPT: https://platform.openai.com/api-keys

# Anthropic Claude (Recommended)
anthropic_api_key: "your-anthropic-key-here"

# OpenAI ChatGPT (Alternative)
openai_api_key: "your-openai-key-here"

# Provider settings
default_provider: "anthropic"
model_settings:
  anthropic:
    model: "claude-3-5-sonnet-20241022"
    max_tokens: 1000
  openai:
    model: "gpt-4"
    max_tokens: 1000
EOF
        print_status "AI config template created ✅"
    fi
else
    print_status "AI config already exists ✅"
fi

# Step 9: Run basic test
print_step "Running basic system test..."
print_status "Testing speech recognition providers..."
python -c "
from home_assistant.speech.recognizer import SpeechRecognizer
recognizer = SpeechRecognizer()
providers = recognizer.get_available_providers()
print('✅ Available speech providers:', providers)
print('✅ System test completed successfully!')
" && print_status "System test passed ✅" || print_warning "System test had issues, but installation may still work"

# Step 10: Final instructions
print_step "🎉 Installation Complete!"
echo
print_status "Next steps:"
echo "1. 🔑 Add your AI API keys to ai_config.yaml:"
echo "   - Get Anthropic Claude key: https://console.anthropic.com/settings/keys"  
echo "   - Get OpenAI ChatGPT key: https://platform.openai.com/api-keys"
echo
echo "2. 🎤 Grant microphone permissions:"
echo "   - System Preferences → Security & Privacy → Privacy → Microphone"
echo "   - Enable access for Terminal/your IDE"
echo
echo "3. 🚀 Run the application:"
echo "   source venv/bin/activate"
echo "   python main.py"
echo
echo "4. 📖 Full documentation:"
echo "   https://github.com/szelenin/home_assistant#readme"
echo
print_status "Installation completed successfully! 🎉"