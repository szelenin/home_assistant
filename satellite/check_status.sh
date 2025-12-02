#!/bin/bash
# Check Jarvis Satellite Status

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/config/satellite.conf"

echo -e "${BLUE}=== Jarvis Satellite Status ===${NC}"
echo ""

# Load config
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
fi

# =============================================================================
# Check Python
# =============================================================================
echo -e "${YELLOW}[Python]${NC}"
if command -v python3 &> /dev/null; then
    VERSION=$(python3 --version 2>&1)
    echo -e "  ${GREEN}✓${NC} $VERSION"
else
    echo -e "  ${RED}✗ Python not found${NC}"
fi

# =============================================================================
# Check Component Installations (separate venvs)
# =============================================================================
echo ""
echo -e "${YELLOW}[Wyoming Satellite]${NC}"
SATELLITE_DIR="${SCRIPT_DIR}/wyoming-satellite"
if [ -d "${SATELLITE_DIR}/.venv" ]; then
    echo -e "  ${GREEN}✓${NC} venv exists"
    if "${SATELLITE_DIR}/.venv/bin/pip" show wyoming-satellite &> /dev/null; then
        VERSION=$("${SATELLITE_DIR}/.venv/bin/pip" show wyoming-satellite | grep Version | cut -d' ' -f2)
        WYOMING_VER=$("${SATELLITE_DIR}/.venv/bin/pip" show wyoming | grep Version | cut -d' ' -f2)
        echo -e "  ${GREEN}✓${NC} wyoming-satellite $VERSION (wyoming $WYOMING_VER)"
    else
        echo -e "  ${RED}✗${NC} wyoming-satellite not installed"
    fi
else
    echo -e "  ${RED}✗ Not installed - run ./install.sh${NC}"
fi

echo ""
echo -e "${YELLOW}[Wyoming OpenWakeWord]${NC}"
OPENWAKEWORD_DIR="${SCRIPT_DIR}/wyoming-openwakeword"
if [ -d "${OPENWAKEWORD_DIR}/.venv" ]; then
    echo -e "  ${GREEN}✓${NC} venv exists"
    if "${OPENWAKEWORD_DIR}/.venv/bin/pip" show wyoming-openwakeword &> /dev/null; then
        VERSION=$("${OPENWAKEWORD_DIR}/.venv/bin/pip" show wyoming-openwakeword | grep Version | cut -d' ' -f2)
        WYOMING_VER=$("${OPENWAKEWORD_DIR}/.venv/bin/pip" show wyoming | grep Version | cut -d' ' -f2)
        echo -e "  ${GREEN}✓${NC} wyoming-openwakeword $VERSION (wyoming $WYOMING_VER)"
    else
        echo -e "  ${RED}✗${NC} wyoming-openwakeword not installed"
    fi
else
    echo -e "  ${RED}✗ Not installed - run ./install.sh${NC}"
fi

# =============================================================================
# Check Audio Devices
# =============================================================================
echo ""
echo -e "${YELLOW}[Audio Devices]${NC}"

# Recording
if arecord -l &> /dev/null; then
    DEVICES=$(arecord -l 2>/dev/null | grep -c "card")
    echo -e "  ${GREEN}✓${NC} $DEVICES recording device(s) found"

    if [ -n "$MIC_DEVICE" ]; then
        echo -e "  ${GREEN}✓${NC} Configured mic: $MIC_DEVICE"
    fi
else
    echo -e "  ${RED}✗ No recording devices${NC}"
fi

# Playback
if aplay -l &> /dev/null; then
    DEVICES=$(aplay -l 2>/dev/null | grep -c "card")
    echo -e "  ${GREEN}✓${NC} $DEVICES playback device(s) found"

    if [ -n "$SPEAKER_DEVICE" ]; then
        echo -e "  ${GREEN}✓${NC} Configured speaker: $SPEAKER_DEVICE"
    fi
else
    echo -e "  ${RED}✗ No playback devices${NC}"
fi

# =============================================================================
# Check Network
# =============================================================================
echo ""
echo -e "${YELLOW}[Network]${NC}"

# Check Mac server connectivity
if [ -n "$MAC_SERVER_IP" ] && [ "$MAC_SERVER_IP" != "192.168.x.x" ]; then
    if ping -c 1 -W 2 "$MAC_SERVER_IP" &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} Mac reachable: $MAC_SERVER_IP"

        # Check Wyoming port
        if nc -z -w 2 "$MAC_SERVER_IP" "${MAC_SERVER_PORT:-10700}" 2>/dev/null; then
            echo -e "  ${GREEN}✓${NC} Wyoming server responding on port ${MAC_SERVER_PORT:-10700}"
        else
            echo -e "  ${RED}✗${NC} Wyoming server not responding on port ${MAC_SERVER_PORT:-10700}"
            echo "    Make sure the server is running on Mac"
        fi
    else
        echo -e "  ${RED}✗${NC} Cannot reach Mac: $MAC_SERVER_IP"
    fi
else
    echo -e "  ${YELLOW}⚠${NC} MAC_SERVER_IP not configured"
fi

# =============================================================================
# Check Running Processes
# =============================================================================
echo ""
echo -e "${YELLOW}[Running Processes]${NC}"

# OpenWakeWord
if pgrep -f "wyoming_openwakeword" > /dev/null; then
    PID=$(pgrep -f "wyoming_openwakeword" | head -1)
    echo -e "  ${GREEN}✓${NC} OpenWakeWord running (PID: $PID)"
else
    echo -e "  ${YELLOW}○${NC} OpenWakeWord not running"
fi

# Satellite
if pgrep -f "wyoming_satellite" > /dev/null; then
    PID=$(pgrep -f "wyoming_satellite" | head -1)
    echo -e "  ${GREEN}✓${NC} Satellite running (PID: $PID)"
else
    echo -e "  ${YELLOW}○${NC} Satellite not running"
fi

# =============================================================================
# Check Systemd Services (if installed)
# =============================================================================
echo ""
echo -e "${YELLOW}[Systemd Services]${NC}"

if systemctl list-unit-files wyoming-satellite.service &> /dev/null; then
    STATUS=$(systemctl is-active wyoming-satellite 2>/dev/null || echo "inactive")
    if [ "$STATUS" = "active" ]; then
        echo -e "  ${GREEN}✓${NC} wyoming-satellite: $STATUS"
    else
        echo -e "  ${YELLOW}○${NC} wyoming-satellite: $STATUS"
    fi

    STATUS=$(systemctl is-active wyoming-openwakeword 2>/dev/null || echo "inactive")
    if [ "$STATUS" = "active" ]; then
        echo -e "  ${GREEN}✓${NC} wyoming-openwakeword: $STATUS"
    else
        echo -e "  ${YELLOW}○${NC} wyoming-openwakeword: $STATUS"
    fi
else
    echo -e "  ${YELLOW}○${NC} Systemd services not installed"
fi

# =============================================================================
# Summary
# =============================================================================
echo ""
echo -e "${BLUE}=== Configuration ===${NC}"
echo "  Server: ${MAC_SERVER_IP:-not set}:${MAC_SERVER_PORT:-10700}"
echo "  Wake word: ${WAKE_WORD_NAME:-hey_jarvis}"
echo "  Mic: ${MIC_DEVICE:-not set}"
echo "  Speaker: ${SPEAKER_DEVICE:-not set}"
echo ""
