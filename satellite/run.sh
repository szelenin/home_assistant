#!/bin/bash
# Start Jarvis Satellite Services
# Starts both OpenWakeWord and Wyoming Satellite
# Each component uses its own virtual environment to avoid dependency conflicts

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/config/satellite.conf"
PID_DIR="${SCRIPT_DIR}/run"

# Separate component directories (each has its own .venv)
SATELLITE_DIR="${SCRIPT_DIR}/wyoming-satellite"
OPENWAKEWORD_DIR="${SCRIPT_DIR}/wyoming-openwakeword"

# Create directories
mkdir -p "$PID_DIR"
mkdir -p "${SCRIPT_DIR}/logs"

echo -e "${BLUE}=== Starting Jarvis Satellite ===${NC}"

# Check if components are installed
if [ ! -f "$SATELLITE_DIR/.venv/bin/python" ]; then
    echo -e "${RED}Error: Wyoming satellite not installed. Run ./install.sh first${NC}"
    exit 1
fi

if [ ! -f "$OPENWAKEWORD_DIR/.venv/bin/python" ]; then
    echo -e "${RED}Error: OpenWakeWord not installed. Run ./install.sh first${NC}"
    exit 1
fi

# Load configuration
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
else
    echo -e "${RED}Error: Configuration file not found: ${CONFIG_FILE}${NC}"
    exit 1
fi

# Validate required config
if [ -z "$MAC_SERVER_IP" ] || [ "$MAC_SERVER_IP" = "192.168.x.x" ]; then
    echo -e "${RED}Error: MAC_SERVER_IP not configured in satellite.conf${NC}"
    echo "Edit config/satellite.conf and set your Mac's IP address"
    exit 1
fi

# Stop any existing processes
echo "Stopping any existing processes..."
"${SCRIPT_DIR}/stop.sh" 2>/dev/null || true

# =============================================================================
# Start OpenWakeWord (using its own venv)
# =============================================================================
echo ""
echo -e "${YELLOW}Starting OpenWakeWord service...${NC}"

OPENWAKEWORD_PYTHON="${OPENWAKEWORD_DIR}/.venv/bin/python"

$OPENWAKEWORD_PYTHON -m wyoming_openwakeword \
    --uri tcp://127.0.0.1:10400 \
    --preload-model ${WAKE_WORD_NAME:-hey_jarvis} \
    --threshold ${WAKE_WORD_THRESHOLD:-0.5} \
    > "${SCRIPT_DIR}/logs/openwakeword.log" 2>&1 &

OPENWAKEWORD_PID=$!
echo $OPENWAKEWORD_PID > "${PID_DIR}/openwakeword.pid"

# Wait for it to start
sleep 2

if kill -0 $OPENWAKEWORD_PID 2>/dev/null; then
    echo -e "${GREEN}✓ OpenWakeWord started (PID: ${OPENWAKEWORD_PID})${NC}"
else
    echo -e "${RED}✗ OpenWakeWord failed to start${NC}"
    echo "Check logs/openwakeword.log for details"
    cat "${SCRIPT_DIR}/logs/openwakeword.log" | tail -20
    exit 1
fi

# =============================================================================
# Start Wyoming Satellite (using its own venv)
# =============================================================================
echo ""
echo -e "${YELLOW}Starting Wyoming Satellite...${NC}"

SATELLITE_PYTHON="${SATELLITE_DIR}/.venv/bin/python"

echo ""
echo "Satellite configuration:"
echo "  Server: ${MAC_SERVER_IP}:${MAC_SERVER_PORT:-10700}"
echo "  Wake word: ${WAKE_WORD_NAME:-hey_jarvis}"
echo "  Mic: ${MIC_DEVICE:-plughw:2,0}"
echo "  Speaker: ${SPEAKER_DEVICE:-plughw:2,0}"
echo ""

# Build satellite command arguments
SATELLITE_ARGS=(
    -m wyoming_satellite
    --name "${SATELLITE_NAME:-jarvis-pi}"
    --uri "tcp://${MAC_SERVER_IP}:${MAC_SERVER_PORT:-10700}"
    --mic-command "arecord -D ${MIC_DEVICE:-plughw:2,0} -r 16000 -c 1 -f S16_LE -t raw"
    --snd-command "aplay -D ${SPEAKER_DEVICE:-plughw:2,0} -r 22050 -c 1 -f S16_LE -t raw"
    --wake-uri "${WAKE_WORD_URI:-tcp://127.0.0.1:10400}"
    --wake-word-name "${WAKE_WORD_NAME:-hey_jarvis}"
)

# Add optional parameters
if [ "${VAD_ENABLED:-false}" = "true" ]; then
    SATELLITE_ARGS+=(--vad)
fi

if [ "${NOISE_SUPPRESSION:-0}" != "0" ]; then
    SATELLITE_ARGS+=(--mic-noise-suppression "${NOISE_SUPPRESSION}")
fi

if [ "${AUTO_GAIN:-0}" != "0" ]; then
    SATELLITE_ARGS+=(--mic-auto-gain "${AUTO_GAIN}")
fi

if [ -n "$AWAKE_SOUND" ] && [ -f "$AWAKE_SOUND" ]; then
    SATELLITE_ARGS+=(--awake-wav "${AWAKE_SOUND}")
fi

if [ -n "$DONE_SOUND" ] && [ -f "$DONE_SOUND" ]; then
    SATELLITE_ARGS+=(--done-wav "${DONE_SOUND}")
fi

echo -e "${GREEN}✓ Satellite starting...${NC}"
echo ""
echo -e "${BLUE}Listening for '${WAKE_WORD_NAME:-hey_jarvis}'...${NC}"
echo "Press Ctrl+C to stop"
echo ""

# Run in foreground so user can see output
$SATELLITE_PYTHON "${SATELLITE_ARGS[@]}" 2>&1 | tee "${SCRIPT_DIR}/logs/satellite.log"
