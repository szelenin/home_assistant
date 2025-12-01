# Jarvis Satellite Setup for Raspberry Pi

This folder contains everything needed to set up a Raspberry Pi as a voice satellite for the Jarvis home assistant system.

## Overview

The satellite runs on Raspberry Pi and handles:
- **Wake word detection** ("Jarvis") using OpenWakeWord
- **Audio capture** from USB microphone
- **Audio playback** of AI responses on speakers
- **Wyoming protocol** communication with Mac server

All heavy processing (STT, AI, TTS generation) happens on the Mac server.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Raspberry Pi Satellite                    │
│                                                             │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │ wyoming-        │    │      wyoming-satellite          │ │
│  │ openwakeword    │───►│                                 │ │
│  │ (localhost:     │    │  - Listens for wake word        │ │
│  │  10400)         │    │  - Streams audio to Mac         │ │
│  └─────────────────┘    │  - Plays TTS responses          │ │
│                         │  - Connects to Mac:10700        │ │
│                         └─────────────────────────────────┘ │
│                                      │                      │
│                         ┌────────────┴────────────┐         │
│                         │   USB Headset/Mic       │         │
│                         │   (hw:2,0 or similar)   │         │
│                         └─────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Wyoming Protocol (TCP)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Mac Server (:10700)                       │
│                                                             │
│  Wyoming Server → STT (Whisper) → AI (Claude) → TTS (say)   │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

### Hardware
- Raspberry Pi Zero 2 W (or better: Pi 3, Pi 4, Pi 5)
- USB audio device with microphone and speaker (e.g., USB headset)
- MicroSD card (8GB+)
- Power supply
- Network connection (WiFi or Ethernet)

### Software
- Raspberry Pi OS (Bookworm or newer recommended)
- Python 3.9 or newer
- Network access to Mac server

## Quick Start

### 1. Copy satellite folder to Pi

From your Mac:
```bash
scp -r satellite/ pi@your-pi-hostname:~/
```

### 2. Run the installer

SSH to your Pi and run:
```bash
ssh pi@your-pi-hostname
cd ~/satellite
./install.sh
```

### 3. Configure

Edit the configuration file:
```bash
nano config/satellite.conf
```

Set your Mac's IP address:
```bash
MAC_SERVER_IP="192.168.x.x"  # Your Mac's IP address
```

### 4. Start the satellite

```bash
./run.sh
```

### 5. Test

Say "Jarvis" followed by a command like "What time is it?"

## Installation Details

### What install.sh Does

1. **Checks Python version** (requires 3.9+)
2. **Installs system dependencies** (portaudio, etc.)
3. **Creates Python virtual environment**
4. **Installs wyoming-satellite**
5. **Installs wyoming-openwakeword**
6. **Downloads wake word models**
7. **Detects audio devices**
8. **Generates configuration**
9. **Optionally installs systemd services**

### Manual Installation

If you prefer manual installation:

```bash
# System dependencies
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip portaudio19-dev

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Wyoming satellite
pip install wyoming wyoming-satellite

# Install OpenWakeWord
pip install wyoming-openwakeword

# Or clone for latest version:
git clone https://github.com/rhasspy/wyoming-openwakeword.git
cd wyoming-openwakeword
script/setup
cd ..
```

## Configuration

### satellite.conf

```bash
# Mac server connection
MAC_SERVER_IP="192.168.1.100"    # Your Mac's IP address
MAC_SERVER_PORT="10700"          # Wyoming server port

# Audio devices (auto-detected by install.sh)
MIC_DEVICE="plughw:2,0"          # Microphone device
SPEAKER_DEVICE="plughw:2,0"      # Speaker device

# Wake word settings
WAKE_WORD_NAME="hey_jarvis"      # Wake word model name
WAKE_WORD_URI="tcp://127.0.0.1:10400"  # Local openwakeword service

# Audio processing (optional)
MIC_VOLUME="1.0"                 # Microphone volume multiplier
NOISE_SUPPRESSION="0"            # 0-4, higher = more suppression
AUTO_GAIN="0"                    # 0-31 dBFS, 0 = disabled
```

### Finding Audio Devices

```bash
# List recording devices
arecord -l

# List playback devices
aplay -l

# Test recording (3 seconds)
arecord -D plughw:2,0 -d 3 -f cd test.wav

# Test playback
aplay -D plughw:2,0 test.wav
```

## Scripts

### run.sh
Starts both wyoming-openwakeword and wyoming-satellite services.

```bash
./run.sh
```

### stop.sh
Stops all satellite services.

```bash
./stop.sh
```

### check_status.sh
Checks health of all components.

```bash
./check_status.sh
```

## Auto-Start with systemd

To have the satellite start automatically on boot:

```bash
# Install services (done by install.sh with --systemd flag)
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable wyoming-openwakeword
sudo systemctl enable wyoming-satellite
sudo systemctl start wyoming-openwakeword
sudo systemctl start wyoming-satellite
```

### Managing Services

```bash
# Check status
sudo systemctl status wyoming-satellite
sudo systemctl status wyoming-openwakeword

# View logs
journalctl -u wyoming-satellite -f
journalctl -u wyoming-openwakeword -f

# Restart
sudo systemctl restart wyoming-satellite
```

## Troubleshooting

### Audio Issues

**No sound / microphone not working:**
```bash
# Check if device is detected
arecord -l
aplay -l

# Check if device is busy
fuser -v /dev/snd/*

# Test with different device
arecord -D hw:2,0 -d 3 test.wav  # Try hw: instead of plughw:
```

**Device busy error:**
```bash
# Stop any running audio processes
./stop.sh

# Check what's using the device
fuser -v /dev/snd/*
```

### Network Issues

**Can't connect to Mac server:**
```bash
# Test network connectivity
ping YOUR_MAC_IP

# Test if Wyoming server is running on Mac
nc -zv YOUR_MAC_IP 10700

# Check firewall on Mac
# System Preferences → Security & Privacy → Firewall
```

### Wake Word Issues

**Wake word not detected:**
```bash
# Check if openwakeword is running
./check_status.sh

# Test audio levels
arecord -D plughw:2,0 -d 3 -f cd test.wav
# Play back and check if audio is clear

# Check openwakeword logs
journalctl -u wyoming-openwakeword -f
```

**Wrong wake word triggering:**
- Adjust threshold in satellite.conf
- Try different wake word model
- Reduce background noise

### Common Errors

**"Python 3.9+ required":**
```bash
# Check Python version
python3 --version

# On older Raspberry Pi OS, install newer Python
sudo apt-get install python3.11
```

**"portaudio.h not found":**
```bash
sudo apt-get install portaudio19-dev
```

**"Connection refused to Mac:10700":**
- Ensure Mac Wyoming server is running
- Check Mac IP address in satellite.conf
- Check Mac firewall settings

## Files

```
satellite/
├── README.md              # This file
├── install.sh             # Installation script
├── run.sh                 # Start services
├── stop.sh                # Stop services
├── check_status.sh        # Health check
├── config/
│   └── satellite.conf     # Configuration
└── systemd/
    ├── wyoming-openwakeword.service
    └── wyoming-satellite.service
```

## Next Steps

After satellite is working:

1. **Test basic flow:** "Jarvis" → "Yes?" → "What time is it?" → response
2. **Test weather:** "Jarvis" → "What's the weather in Tampa?"
3. **Adjust audio:** Modify volume/gain settings if needed
4. **Enable auto-start:** Install systemd services for boot startup

## Related Documentation

- [Main README](../README.md) - Project overview
- [Wyoming Protocol](https://github.com/rhasspy/wyoming) - Protocol documentation
- [wyoming-satellite](https://github.com/rhasspy/wyoming-satellite) - Satellite documentation
- [wyoming-openwakeword](https://github.com/rhasspy/wyoming-openwakeword) - Wake word documentation
