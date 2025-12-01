#!/bin/bash
# Jarvis Satellite Installer for Raspberry Pi
# This script installs all dependencies for running the Wyoming satellite
# Supports both fresh install and updates
#
# IMPORTANT: wyoming-satellite and wyoming-openwakeword use SEPARATE virtual
# environments to avoid dependency conflicts (they require different wyoming versions)

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"  # Parent directory (home_assistant repo)
CONFIG_FILE="${SCRIPT_DIR}/config/satellite.conf"

# Separate directories for each component (to avoid dependency conflicts)
SATELLITE_DIR="${SCRIPT_DIR}/wyoming-satellite"
OPENWAKEWORD_DIR="${SCRIPT_DIR}/wyoming-openwakeword"

# =============================================================================
# Detect install mode (fresh vs update)
# =============================================================================
IS_UPDATE=false
if [ -d "$SATELLITE_DIR/.venv" ] && [ -f "$SATELLITE_DIR/.venv/bin/python" ]; then
    IS_UPDATE=true
fi

if [ "$IS_UPDATE" = true ]; then
    echo -e "${BLUE}=== Jarvis Satellite Updater ===${NC}"
    echo -e "${YELLOW}Existing installation detected - running in UPDATE mode${NC}"
else
    echo -e "${BLUE}=== Jarvis Satellite Installer ===${NC}"
    echo -e "${YELLOW}Fresh installation${NC}"
fi
echo ""

# =============================================================================
# Show current version (for updates)
# =============================================================================
if [ "$IS_UPDATE" = true ]; then
    echo -e "${YELLOW}[0/8] Checking versions...${NC}"
    echo "Current version before update:"
    cd "$REPO_DIR"
    BEFORE_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    BEFORE_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
    echo "  Branch: $BEFORE_BRANCH"
    echo "  Commit: $BEFORE_COMMIT"
    echo ""

    # Pull latest changes
    echo "Pulling latest changes from git..."
    GIT_PULL_OUTPUT=$(git pull 2>&1) || true
    echo "$GIT_PULL_OUTPUT"

    AFTER_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    if [ "$BEFORE_COMMIT" = "$AFTER_COMMIT" ]; then
        echo -e "${GREEN}✓ Already up to date (commit: $AFTER_COMMIT)${NC}"
    else
        echo -e "${GREEN}✓ Updated from $BEFORE_COMMIT to $AFTER_COMMIT${NC}"
    fi
    cd "$SCRIPT_DIR"
    echo ""
fi

# =============================================================================
# STEP 1: Check Python version
# =============================================================================
echo -e "${YELLOW}[1/8] Checking Python version...${NC}"

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
    echo -e "${RED}Error: Python 3.9+ required (found $PYTHON_VERSION)${NC}"
    echo "Install newer Python with: sudo apt-get install python3.11"
    exit 1
fi

echo -e "${GREEN}✓ Python $PYTHON_VERSION${NC}"

# =============================================================================
# STEP 2: Install system dependencies
# =============================================================================
echo ""
echo -e "${YELLOW}[2/8] Installing system dependencies...${NC}"

sudo apt-get update
sudo apt-get install -y \
    python3-venv \
    python3-pip \
    portaudio19-dev \
    alsa-utils \
    git

echo -e "${GREEN}✓ System dependencies installed${NC}"

# =============================================================================
# STEP 3: Clone/update wyoming-satellite (separate venv)
# =============================================================================
echo ""
echo -e "${YELLOW}[3/8] Installing Wyoming satellite...${NC}"
echo -e "${BLUE}Note: Using separate venv to avoid dependency conflicts${NC}"

if [ -d "$SATELLITE_DIR" ]; then
    echo "Wyoming-satellite directory exists, updating..."
    cd "$SATELLITE_DIR"
    git fetch origin
    git pull || true
else
    echo "Cloning wyoming-satellite..."
    git clone https://github.com/rhasspy/wyoming-satellite.git "$SATELLITE_DIR"
    cd "$SATELLITE_DIR"
fi

# Create/update venv for satellite
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment for wyoming-satellite..."
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip wheel
pip install -e .
deactivate

cd "$SCRIPT_DIR"
echo -e "${GREEN}✓ Wyoming satellite installed (venv: wyoming-satellite/.venv)${NC}"

# =============================================================================
# STEP 4: Clone/update wyoming-openwakeword (separate venv)
# =============================================================================
echo ""
echo -e "${YELLOW}[4/8] Installing Wyoming OpenWakeWord...${NC}"
echo -e "${BLUE}Note: Using separate venv to avoid dependency conflicts${NC}"

if [ -d "$OPENWAKEWORD_DIR" ]; then
    echo "OpenWakeWord directory exists, updating..."
    cd "$OPENWAKEWORD_DIR"
    git fetch origin
    git pull || true
else
    echo "Cloning wyoming-openwakeword..."
    git clone https://github.com/rhasspy/wyoming-openwakeword.git "$OPENWAKEWORD_DIR"
    cd "$OPENWAKEWORD_DIR"
fi

# Create venv and install (the official script/setup is Python, we do it manually)
echo "Setting up OpenWakeWord..."
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment for wyoming-openwakeword..."
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip wheel
pip install -e .
deactivate

cd "$SCRIPT_DIR"
echo -e "${GREEN}✓ Wyoming OpenWakeWord installed (venv: wyoming-openwakeword/.venv)${NC}"

# =============================================================================
# STEP 5: Download wake word models
# =============================================================================
echo ""
echo -e "${YELLOW}[5/8] Downloading wake word models...${NC}"

# Use openwakeword's venv to download models
source "$OPENWAKEWORD_DIR/.venv/bin/activate"
pip install openwakeword 2>/dev/null || true
deactivate

echo -e "${GREEN}✓ Wake word models available${NC}"

# =============================================================================
# STEP 6: Detect audio devices
# =============================================================================
echo ""
echo -e "${YELLOW}[6/8] Detecting audio devices...${NC}"

echo ""
echo "Recording devices (microphones):"
arecord -l 2>/dev/null || echo "No recording devices found"

echo ""
echo "Playback devices (speakers):"
aplay -l 2>/dev/null || echo "No playback devices found"

# Try to auto-detect USB audio device
USB_CARD=$(arecord -l 2>/dev/null | grep -i "usb\|headset" | head -1 | sed -n 's/card \([0-9]*\).*/\1/p')

if [ -n "$USB_CARD" ]; then
    DETECTED_DEVICE="plughw:${USB_CARD},0"
    echo ""
    echo -e "${GREEN}✓ Detected USB audio device: ${DETECTED_DEVICE}${NC}"

    # Update config file
    sed -i "s|MIC_DEVICE=.*|MIC_DEVICE=\"${DETECTED_DEVICE}\"|" "$CONFIG_FILE"
    sed -i "s|SPEAKER_DEVICE=.*|SPEAKER_DEVICE=\"${DETECTED_DEVICE}\"|" "$CONFIG_FILE"
else
    echo ""
    echo -e "${YELLOW}⚠ Could not auto-detect USB audio device${NC}"
    echo "Please edit config/satellite.conf manually"
fi

# =============================================================================
# STEP 7: Test audio (optional)
# =============================================================================
echo ""
echo -e "${YELLOW}[7/8] Testing audio...${NC}"

if [ -n "$USB_CARD" ]; then
    echo "Testing recording (2 seconds)..."
    TEST_FILE="/tmp/satellite_test.wav"

    if timeout 3 arecord -D "$DETECTED_DEVICE" -r 16000 -c 1 -f S16_LE -t wav -d 2 "$TEST_FILE" 2>/dev/null; then
        FILE_SIZE=$(stat -f%z "$TEST_FILE" 2>/dev/null || stat -c%s "$TEST_FILE" 2>/dev/null)
        if [ "$FILE_SIZE" -gt 1000 ]; then
            echo -e "${GREEN}✓ Recording works (${FILE_SIZE} bytes)${NC}"

            echo "Testing playback..."
            if aplay -D "$DETECTED_DEVICE" "$TEST_FILE" 2>/dev/null; then
                echo -e "${GREEN}✓ Playback works${NC}"
            else
                echo -e "${YELLOW}⚠ Playback test failed - check speaker${NC}"
            fi
        else
            echo -e "${YELLOW}⚠ Recording file too small - check microphone${NC}"
        fi
        rm -f "$TEST_FILE"
    else
        echo -e "${YELLOW}⚠ Recording test failed - check audio device${NC}"
    fi
else
    echo "Skipping audio test (no device detected)"
fi

# =============================================================================
# STEP 8: Setup systemd services (optional)
# =============================================================================
echo ""
echo -e "${YELLOW}[8/8] Systemd services...${NC}"

if [ "$1" = "--systemd" ]; then
    echo "Installing systemd services..."

    # Update service files with correct paths
    SYSTEMD_DIR="${SCRIPT_DIR}/systemd"

    # Create updated service files
    cat > "${SYSTEMD_DIR}/wyoming-openwakeword.service" << EOF
[Unit]
Description=Wyoming OpenWakeWord
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=${OPENWAKEWORD_DIR}
ExecStart=${OPENWAKEWORD_DIR}/.venv/bin/python -m wyoming_openwakeword --uri tcp://127.0.0.1:10400 --preload-model hey_jarvis
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    cat > "${SYSTEMD_DIR}/wyoming-satellite.service" << EOF
[Unit]
Description=Wyoming Satellite
After=network.target wyoming-openwakeword.service
Requires=wyoming-openwakeword.service

[Service]
Type=simple
User=$(whoami)
EnvironmentFile=${CONFIG_FILE}
WorkingDirectory=${SATELLITE_DIR}
ExecStart=${SATELLITE_DIR}/.venv/bin/python -m wyoming_satellite \\
    --name \${SATELLITE_NAME} \\
    --uri tcp://0.0.0.0:10700 \\
    --mic-command "arecord -D \${MIC_DEVICE} -r 16000 -c 1 -f S16_LE -t raw" \\
    --snd-command "aplay -D \${SPEAKER_DEVICE} -r 22050 -c 1 -f S16_LE -t raw" \\
    --wake-uri \${WAKE_WORD_URI} \\
    --wake-word-name \${WAKE_WORD_NAME}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    sudo cp "${SYSTEMD_DIR}/"*.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable wyoming-openwakeword
    sudo systemctl enable wyoming-satellite

    echo -e "${GREEN}✓ Systemd services installed and enabled${NC}"
else
    echo "Skipping systemd setup (run with --systemd to install)"
fi

# =============================================================================
# COMPLETE
# =============================================================================
echo ""
if [ "$IS_UPDATE" = true ]; then
    echo -e "${GREEN}=== Update Complete ===${NC}"
else
    echo -e "${GREEN}=== Installation Complete ===${NC}"
fi
echo ""

# Show final version info
cd "$REPO_DIR"
FINAL_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
FINAL_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
echo "Installed version:"
echo "  Branch: $FINAL_BRANCH"
echo "  Commit: $FINAL_COMMIT"
echo "  Date:   $(git log -1 --format='%ci' 2>/dev/null || echo 'unknown')"
cd "$SCRIPT_DIR"
echo ""

# Show component versions
echo "Component versions:"
echo "  wyoming-satellite: $($SATELLITE_DIR/.venv/bin/pip show wyoming-satellite 2>/dev/null | grep Version | cut -d' ' -f2 || echo 'unknown')"
echo "  wyoming (satellite): $($SATELLITE_DIR/.venv/bin/pip show wyoming 2>/dev/null | grep Version | cut -d' ' -f2 || echo 'unknown')"
echo "  wyoming-openwakeword: $($OPENWAKEWORD_DIR/.venv/bin/pip show wyoming-openwakeword 2>/dev/null | grep Version | cut -d' ' -f2 || echo 'unknown')"
echo "  wyoming (openwakeword): $($OPENWAKEWORD_DIR/.venv/bin/pip show wyoming 2>/dev/null | grep Version | cut -d' ' -f2 || echo 'unknown')"
echo ""

echo "Next steps:"
echo "  1. Edit config/satellite.conf with your Mac's IP address:"
echo "     nano config/satellite.conf"
echo ""
echo "  2. Make sure Wyoming server is running on Mac"
echo ""
echo "  3. Start the satellite:"
echo "     ./run.sh"
echo ""
echo "  4. Say 'Jarvis' followed by a command!"
echo ""

if [ -z "$USB_CARD" ]; then
    echo -e "${YELLOW}⚠ Remember to configure audio devices in satellite.conf${NC}"
    echo ""
fi
