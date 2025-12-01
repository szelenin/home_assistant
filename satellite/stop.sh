#!/bin/bash
# Stop Jarvis Satellite Services

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="${SCRIPT_DIR}/run"

echo -e "${YELLOW}Stopping Jarvis Satellite services...${NC}"

# Stop satellite
if [ -f "${PID_DIR}/satellite.pid" ]; then
    PID=$(cat "${PID_DIR}/satellite.pid")
    if kill -0 $PID 2>/dev/null; then
        kill $PID 2>/dev/null
        echo -e "${GREEN}✓ Satellite stopped (PID: ${PID})${NC}"
    fi
    rm -f "${PID_DIR}/satellite.pid"
fi

# Stop openwakeword
if [ -f "${PID_DIR}/openwakeword.pid" ]; then
    PID=$(cat "${PID_DIR}/openwakeword.pid")
    if kill -0 $PID 2>/dev/null; then
        kill $PID 2>/dev/null
        echo -e "${GREEN}✓ OpenWakeWord stopped (PID: ${PID})${NC}"
    fi
    rm -f "${PID_DIR}/openwakeword.pid"
fi

# Kill any remaining processes
pkill -f "wyoming_satellite" 2>/dev/null || true
pkill -f "wyoming_openwakeword" 2>/dev/null || true

# Also kill any arecord/aplay that might be hanging
pkill -f "arecord.*plughw" 2>/dev/null || true
pkill -f "aplay.*plughw" 2>/dev/null || true

echo -e "${GREEN}All services stopped${NC}"
