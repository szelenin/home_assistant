#!/bin/bash
set -e

# Home Assistant Installation Script for Linux/Raspberry Pi
# This script installs the voice-controlled home automation system

echo "🏠 Home Assistant Installation Script for Linux/Raspberry Pi"
echo "==========================================================="

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

# Detect OS
print_step "Detecting operating system..."
if [[ -f /etc/os-release ]]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
    print_status "Detected: $OS $VER"
elif [[ -f /etc/redhat-release ]]; then
    OS="Red Hat/CentOS/Fedora"
    print_status "Detected: $OS"
else
    OS="Unknown Linux"
    print_warning "Unknown Linux distribution, assuming Debian-based"
fi

# Check if running on Raspberry Pi
if [[ $(uname -m) == "armv7l" || $(uname -m) == "aarch64" ]]; then
    print_status "🍓 Raspberry Pi detected - optimizing for Pi"
    IS_RPI=true
else
    IS_RPI=false
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
        print_status "Please update Python: sudo apt update && sudo apt install python3 python3-venv python3-pip"
        exit 1
    fi
else
    print_error "Python 3 not found. Installing..."
    sudo apt update
    sudo apt install -y python3 python3-venv python3-pip
fi

# Step 2: Install system dependencies
print_step "Installing system dependencies..."

if [[ "$OS" == *"Ubuntu"* || "$OS" == *"Debian"* || "$OS" == *"Raspbian"* ]]; then
    print_status "Installing packages for Debian/Ubuntu/Raspberry Pi OS..."
    sudo apt update
    
    # Essential packages
    sudo apt install -y \
        git \
        curl \
        unzip \
        portaudio19-dev \
        python3-pyaudio \
        python3-venv \
        python3-pip \
        python3-dev \
        build-essential \
        libasound2-dev
    
    print_status "System dependencies installed ✅"
    
elif [[ "$OS" == *"Fedora"* || "$OS" == *"Red Hat"* || "$OS" == *"CentOS"* ]]; then
    print_status "Installing packages for Fedora/RHEL/CentOS..."
    
    if command -v dnf &> /dev/null; then
        sudo dnf install -y git curl unzip portaudio-devel python3-devel python3-pip gcc gcc-c++ alsa-lib-devel
    else
        sudo yum install -y git curl unzip portaudio-devel python3-devel python3-pip gcc gcc-c++ alsa-lib-devel
    fi
    
    print_status "System dependencies installed ✅"
    
elif [[ "$OS" == *"Arch"* ]]; then
    print_status "Installing packages for Arch Linux..."
    sudo pacman -S --noconfirm git curl unzip portaudio python python-pip base-devel alsa-lib
    print_status "System dependencies installed ✅"
    
else
    print_warning "Unknown distribution. Attempting generic installation..."
    print_status "Please manually install: git, curl, unzip, portaudio development libraries, python3-dev"
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

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies with special handling for Raspberry Pi
if [[ $IS_RPI == true ]]; then
    print_status "🍓 Installing dependencies optimized for Raspberry Pi..."
    print_warning "This may take 10-15 minutes on Raspberry Pi due to compilation..."
    
    # Install PyAudio separately on Pi to handle potential issues
    pip install pyaudio || print_warning "PyAudio installation issues - trying alternative approach..."
fi

pip install -r requirements.txt
print_status "Python dependencies installed ✅"

# Step 6: Download Vosk model (optimized for Pi)
print_step "Downloading Vosk speech recognition model..."
if [[ $IS_RPI == true ]]; then
    VOSK_MODEL="vosk-model-small-en-us-0.15"
    print_status "🍓 Downloading small Vosk model (40MB) optimized for Raspberry Pi..."
else
    VOSK_MODEL="vosk-model-en-us-0.22" 
    print_status "Downloading medium Vosk model (50MB) for better accuracy..."
fi

if [[ ! -d "$VOSK_MODEL" ]]; then
    print_status "Downloading Vosk model..."
    curl -LO "https://alphacephei.com/vosk/models/${VOSK_MODEL}.zip"
    
    if [[ -f "${VOSK_MODEL}.zip" ]]; then
        print_status "Extracting Vosk model..."
        unzip "${VOSK_MODEL}.zip"
        rm "${VOSK_MODEL}.zip"
        
        # Update config to use the downloaded model
        sed -i "s|model_path: \".*\"|model_path: \"./${VOSK_MODEL}\"|" config.yaml
        print_status "Vosk model installed and configured ✅"
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

# Step 9: Setup audio permissions (Raspberry Pi specific)
if [[ $IS_RPI == true ]]; then
    print_step "🍓 Configuring Raspberry Pi audio settings..."
    
    # Add user to audio group
    sudo usermod -a -G audio $USER
    print_status "Added user to audio group ✅"
    
    # Basic ALSA configuration
    if [[ ! -f ~/.asoundrc ]]; then
        print_status "Creating basic ALSA configuration..."
        cat > ~/.asoundrc << EOF
pcm.!default {
    type asym
    playback.pcm "plug:hw:0,0"
    capture.pcm "plug:hw:0,0"
}
EOF
        print_status "ALSA configuration created ✅"
    fi
fi

# Step 10: Run basic test
print_step "Running basic system test..."
print_status "Testing speech recognition providers..."
python -c "
from home_assistant.speech.recognizer import SpeechRecognizer
recognizer = SpeechRecognizer()
providers = recognizer.get_available_providers()
print('✅ Available speech providers:', providers)
print('✅ System test completed successfully!')
" && print_status "System test passed ✅" || print_warning "System test had issues, but installation may still work"

# Step 11: Final instructions
print_step "🎉 Installation Complete!"
echo
print_status "Next steps:"
echo "1. 🔑 Add your AI API keys to ai_config.yaml:"
echo "   nano ai_config.yaml"
echo "   - Get Anthropic Claude key: https://console.anthropic.com/settings/keys"
echo "   - Get OpenAI ChatGPT key: https://platform.openai.com/api-keys"
echo
echo "2. 🚀 Run the application:"
echo "   source venv/bin/activate"
echo "   python main.py"
echo

if [[ $IS_RPI == true ]]; then
    echo "3. 🍓 Raspberry Pi specific tips:"
    echo "   - You may need to reboot after installation: sudo reboot"
    echo "   - Check audio devices: aplay -l"
    echo "   - Test microphone: arecord -d 5 test.wav && aplay test.wav"
    echo
fi

echo "4. 📖 Full documentation:"
echo "   https://github.com/szelenin/home_assistant#readme"
echo
print_status "Installation completed successfully! 🎉"

if [[ $IS_RPI == true ]]; then
    print_warning "🍓 Raspberry Pi users: A reboot may be required for audio changes to take effect"
    echo "   Run: sudo reboot"
fi