# Wyoming Integration Implementation Plan

## Overview

This plan implements distributed voice assistant with **incrementally testable phases**. Each phase delivers real user value with verifiable end-to-end acceptance criteria.

**End Goal:** Say "Jarvis" on Raspberry Pi → AI responds with weather/time/etc → Audio plays on Pi speakers

**This is a living document.** Progress is tracked here and committed with each change.

---

## Progress Tracking

| Phase | Status | Started | Completed | Notes |
|-------|--------|---------|-----------|-------|
| 1 | 🔄 In Progress | 2025-11-30 | - | Pi satellite + full voice pipeline |
| 2 | 🔲 Not Started | - | - | Unified entry point + core refactor |
| 3 | 🔲 Not Started | - | - | Dual mode (Mac + Pi wake word) |
| 4 | 🔲 Not Started | - | - | Pi interruption during TTS |

**Status Legend:** 🔲 Not Started | 🔄 In Progress | ✅ Complete | ⏸️ Blocked

### Phase 1 Progress
- [x] Create satellite/ folder structure
- [x] Create satellite/README.md with installation guide
- [x] Create satellite/install.sh installer script
- [x] Create satellite/run.sh start script
- [x] Create satellite/stop.sh and check_status.sh
- [x] Create satellite/config/satellite.conf template
- [x] Create satellite/systemd/ service files
- [x] Wire up event_bridge.py with real STT/AI/TTS components (TTS generation implemented)
- [x] Update root README.md with satellite setup section
- [ ] **TESTING** - Run acceptance criteria on real hardware

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                              Mac Server                                    │
│                                                                            │
│  ┌────────────────────┐         ┌──────────────────────────────────────┐  │
│  │  Wyoming Server    │         │       Voice Processing Core          │  │
│  │  (port 10700)      │────────►│       (home_assistant/core/)         │  │
│  │                    │         │                                      │  │
│  │  Receives:         │         │  ┌────────────────────────────────┐  │  │
│  │  - Audio from Pi   │         │  │  VoiceProcessor                │  │  │
│  │                    │         │  │  - STT (Whisper)               │  │  │
│  │  Sends:            │         │  │  - AI (Claude/OpenAI)          │  │  │
│  │  - TTS audio to Pi │         │  │  - TTS (macOS say)             │  │  │
│  └────────────────────┘         │  └────────────────────────────────┘  │  │
│                                 │                                      │  │
│  ┌────────────────────┐         │  ┌────────────────────────────────┐  │  │
│  │  Local Wake Word   │────────►│  │  SessionManager (with mutex)   │  │  │
│  │  (Phase 3)         │         │  │  - Thread-safe state           │  │  │
│  └────────────────────┘         │  └────────────────────────────────┘  │  │
└────────────────────────────────────────────────────────────────────────────┘
          ▲
          │ Wyoming Protocol (TCP:10700)
          ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                          Raspberry Pi Satellite                            │
│                                                                            │
│  ┌────────────────────┐    ┌────────────────────┐    ┌─────────────────┐  │
│  │ wyoming-openwakeword│───►│  wyoming-satellite  │◄──►│ Mic & Speakers │  │
│  │ (local detection)  │    │  (audio streaming) │    │ (USB headset)  │  │
│  └────────────────────┘    └────────────────────┘    └─────────────────┘  │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase Overview

| Phase | Goal | End-to-End Test |
|-------|------|-----------------|
| **1** | Pi satellite works with full voice pipeline | Say "Jarvis" on Pi → AI responds → plays on Pi |
| **2** | Unified entry point + refactored core | Same as Phase 1, via `python -m home_assistant.run` |
| **3** | Mac local wake word (dual mode) | Say "Jarvis" on Mac OR Pi → each responds correctly |
| **4** | Pi interruption during TTS | Say "Jarvis" during response → stops and says "Yes?" |

---

## Phase 1: Pi Satellite + Full Voice Pipeline

### Goal
**Complete end-to-end voice assistant working on Raspberry Pi.**

Say "Jarvis" on Pi → "Yes?" → "What's the weather in Tampa?" → AI responds → plays on Pi speakers.

### What We Build

1. **`satellite/` folder** - Complete Pi setup module
   - `README.md` - Installation guide
   - `install.sh` - One-command installer
   - `run.sh` - Start services
   - `stop.sh` - Stop services
   - `check_status.sh` - Health check
   - `config/satellite.conf` - Configuration
   - `systemd/` services

2. **Wire up Wyoming server** - Connect existing components
   - `event_bridge.py` already has STT→AI→TTS structure
   - Need to properly wire up speech_recognizer, tts_engine, ai_orchestrator
   - Implement `_generate_tts_sync()` to actually generate audio
   - **Note:** Keep processing logic clean - it will be extracted to `VoiceProcessor` in Phase 2

3. **Update root README.md** - Add satellite setup section

### Architecture Note: event_bridge.py Evolution

**Phase 1 (this phase):**
```
server.py → event_bridge.py
            ├── on_audio_complete() ← has STT→AI→TTS logic
            └── _generate_tts_sync() ← generates audio
```
We wire up components minimally to get end-to-end working.

**Phase 2 (refactor):**
```
server.py → VoiceProcessor (extracted from event_bridge)
            ├── process_audio() ← STT→AI→TTS
            └── generate_tts() ← audio generation

event_bridge.py (simplified)
            ├── on_satellite_connected()
            └── on_satellite_disconnected()
            (just event routing, no processing)
```
The processing logic moves to `VoiceProcessor`. `event_bridge.py` becomes a thin event router or merges into `server.py`.

### Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `satellite/README.md` | CREATE | Pi installation guide |
| `satellite/install.sh` | CREATE | Installer script |
| `satellite/run.sh` | CREATE | Start script |
| `satellite/stop.sh` | CREATE | Stop script |
| `satellite/check_status.sh` | CREATE | Health check |
| `satellite/config/satellite.conf` | CREATE | Config template |
| `satellite/systemd/*.service` | CREATE | Auto-start services |
| `home_assistant/wyoming/event_bridge.py` | MODIFY | Wire up components |
| `test_wyoming_server.py` | MODIFY | Add component initialization |
| `README.md` | MODIFY | Add satellite setup section |

### Acceptance Criteria

**All criteria must pass on real hardware.**

| # | Test Case | Expected Result | Verification | Pass/Fail |
|---|-----------|-----------------|--------------|-----------|
| 1.1 | Run `./install.sh` on fresh Raspberry Pi | Completes without errors, all dependencies installed | **Check:** Script output shows green ✓ for each step. Final message says "Installation Complete". **No pip dependency conflict errors.** Component versions shown at end with separate wyoming versions (satellite: 1.4.1, openwakeword: 1.8+). **Save output:** `./install.sh 2>&1 \| tee install_output.log` | ☐ |
| 1.1b | Run `./install.sh` on already-installed environment | Updates to latest version, no errors | **Check:** Script detects existing installation, pulls latest from git, shows "Already up to date" or commit hash of update. All ✓ marks. Run `git log -1 --oneline` matches expected version. **Save output:** `./install.sh 2>&1 \| tee install_update_output.log` | ☐ |
| 1.2 | Run `./check_status.sh` | All checks green (Python, venv, audio devices, network) | **Check:** Script output shows ✓ for Python, venv, mic device, speaker device, and network. No ✗ marks. | ☐ |
| 1.3 | Run `./run.sh` on Pi while Mac server running | Pi connects to Mac, logs show "Satellite connected" | **Check on Mac:** Terminal running Wyoming server shows log line containing "Satellite connected" or "client_X connected". **Check on Pi:** run.sh output shows "Connecting to MAC_SERVER_IP:10700". | ☐ |
| 1.4 | Say "Jarvis" clearly | Pi detects wake word, Mac receives audio stream | **Check on Pi:** Logs show "Wake word detected" or similar. **Check on Mac:** Logs show "Audio streaming started" or "AudioStart received". | ☐ |
| 1.5 | After "Jarvis", hear "Yes?" | "Yes?" plays on Pi speakers within 1 second | **Check:** Audibly hear "Yes?" from Pi speakers. **Check on Mac:** Logs show "Generated TTS audio" and "Sending TTS audio to satellite". | ☐ |
| 1.6 | Say "What time is it?" | AI responds with current time, plays on Pi speakers | **Check:** Audibly hear spoken time from Pi speakers. Time is reasonably accurate. **Check on Mac:** Logs show transcript "what time is it" and AI response containing time. | ☐ |
| 1.7 | Say "What's the weather in Tampa?" | AI orchestrator calls weather API, response plays on Pi | **Check:** Audibly hear weather info from Pi speakers (temperature, conditions). **Check on Mac:** Logs show "AI Response" containing weather data. | ☐ |
| 1.8 | Run `./stop.sh` | Services stop cleanly, no orphan processes | **Check:** Run `ps aux \| grep -E "wyoming\|openwakeword"` on Pi - no processes found. Run `./check_status.sh` shows services stopped. | ☐ |
| 1.9 | Reboot Pi (with systemd services enabled) | Satellite auto-starts and connects to Mac | **Check:** After reboot, run `systemctl status wyoming-satellite` shows "active (running)". Mac logs show satellite reconnected. | ☐ |

### Implementation Details

#### satellite/install.sh
```bash
#!/bin/bash
set -e

echo "=== Jarvis Satellite Installer ==="

# Check Python
python3 --version || { echo "Python 3 required"; exit 1; }

# System dependencies
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip portaudio19-dev

# Create venv
python3 -m venv venv
source venv/bin/activate

# Install Wyoming components
pip install wyoming wyoming-satellite

# Clone and install openwakeword
git clone https://github.com/rhasspy/wyoming-openwakeword.git
cd wyoming-openwakeword
script/setup
cd ..

# Download wake word model
# ... (hey_jarvis model)

# Detect audio devices
echo "Detecting audio devices..."
arecord -l
aplay -l

# Generate config
echo "Generating satellite.conf..."
# ... (auto-detect and write config)

echo "=== Installation Complete ==="
echo "Edit config/satellite.conf with your Mac's IP address"
echo "Then run: ./run.sh"
```

#### event_bridge.py modifications
```python
# In EventBridge.__init__, properly initialize components:
def set_home_assistant_components(self, speech_recognizer, tts_engine, ai_orchestrator):
    self.speech_recognizer = speech_recognizer
    self.tts_engine = tts_engine
    self.ai_orchestrator = ai_orchestrator

# Implement _generate_tts_sync:
def _generate_tts_sync(self, text: str, target_rate: int) -> bytes:
    """Generate TTS audio using macOS say command."""
    import subprocess
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix='.aiff', delete=False) as f:
        aiff_path = f.name

    wav_path = aiff_path.replace('.aiff', '.wav')

    try:
        # Generate with macOS say
        subprocess.run(['say', text, '-o', aiff_path], check=True)

        # Convert to WAV (16-bit, target rate, mono)
        subprocess.run([
            'afconvert', aiff_path, '-o', wav_path,
            '-f', 'WAVE', '-d', f'LEI16@{target_rate}'
        ], check=True)

        # Read raw PCM data (skip WAV header)
        with open(wav_path, 'rb') as f:
            wav_data = f.read()
            # Skip 44-byte WAV header to get raw PCM
            return wav_data[44:]

    finally:
        if os.path.exists(aiff_path):
            os.unlink(aiff_path)
        if os.path.exists(wav_path):
            os.unlink(wav_path)
```

---

## Phase 2: Unified Entry Point + Core Refactoring

### Goal
**Single entry point (`run.py`) driven by configuration, with clean code architecture.**

Same functionality as Phase 1, but with:
- `python -m home_assistant.run` as the only entry point
- Shared `VoiceProcessor` in `home_assistant/core/`
- Thread-safe `SessionManager`
- Config-driven behavior

### What We Build

1. **`home_assistant/core/`** - Shared processing module
   - `voice_processor.py` - STT → AI → TTS pipeline (extracted from `event_bridge.py`)
   - `session_manager.py` - Thread-safe session handling

2. **`home_assistant/run.py`** - Unified entry point
   - Reads config to determine mode
   - Starts Wyoming server if enabled
   - (Local wake word prepared but disabled for Phase 3)

3. **Refactor `event_bridge.py`**
   - Remove processing logic (moved to VoiceProcessor)
   - Keep only event routing (satellite connected/disconnected)
   - Or merge into `server.py` if too thin

4. **Update configs and README**

### Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `home_assistant/core/__init__.py` | CREATE | Package init |
| `home_assistant/core/voice_processor.py` | CREATE | Shared STT→AI→TTS (extracted from event_bridge) |
| `home_assistant/core/session_manager.py` | CREATE | Thread-safe sessions |
| `home_assistant/run.py` | CREATE | Unified entry point |
| `home_assistant/wyoming/server.py` | MODIFY | Use VoiceProcessor |
| `home_assistant/wyoming/event_bridge.py` | MODIFY | Remove processing, keep event routing only |
| `home_assistant/main.py` | MODIFY | Add deprecation notice |
| `config/wyoming.yaml` | MODIFY | Add config options |
| `README.md` | MODIFY | Update run instructions |

### Acceptance Criteria

| # | Test Case | Expected Result | Pass/Fail |
|---|-----------|-----------------|-----------|
| 2.1 | Run `python -m home_assistant.run` | Server starts, logs show "Wyoming server listening on 0.0.0.0:10700" | ☐ |
| 2.2 | Pi satellite connects | Logs show "Satellite connected: jarvis-pi" | ☐ |
| 2.3 | Say "Jarvis" → "What time is it?" | Full pipeline works, response plays on Pi (same as 1.6) | ☐ |
| 2.4 | Say "Jarvis" → "What's the weather in Tampa?" | Full pipeline works with AI API call (same as 1.7) | ☐ |
| 2.5 | Check logs | Logs show VoiceProcessor and SessionManager activity | ☐ |
| 2.6 | Ctrl+C to stop server | Clean shutdown, logs show "Home Assistant stopped" | ☐ |
| 2.7 | Run `python -m home_assistant.main` | Shows deprecation warning, still works for backward compat | ☐ |

### Implementation Details

#### home_assistant/run.py
```python
#!/usr/bin/env python3
"""Unified entry point for Home Assistant voice control."""

import sys
import asyncio
import signal

from home_assistant.utils.config import ConfigManager
from home_assistant.utils.logger import setup_logging
from home_assistant.core.voice_processor import VoiceProcessor
from home_assistant.core.session_manager import SessionManager


async def main():
    logger = setup_logging("home_assistant.run")
    logger.info("🚀 Starting Home Assistant...")

    config = ConfigManager()

    # Initialize shared voice processor
    processor = VoiceProcessor(config)
    if not processor.initialize_components():
        logger.error("Failed to initialize voice processor")
        return 1

    session_manager = SessionManager()

    tasks = []

    # Wyoming server (enabled by default)
    if config.get('wyoming.server.enabled', True):
        from home_assistant.wyoming.server import WyomingServer

        host = config.get('wyoming.server.host', '0.0.0.0')
        port = config.get('wyoming.server.port', 10700)

        server = WyomingServer(processor, session_manager, host, port)
        tasks.append(server.start())
        logger.info(f"📡 Wyoming server will listen on {host}:{port}")

    # Local wake word (for Phase 3)
    if config.get('local_wake_word.enabled', False):
        from home_assistant.wyoming.local_loop import LocalWakeWordLoop
        # ... Phase 3 implementation

    if not tasks:
        logger.error("No modes enabled!")
        return 1

    # Handle shutdown
    def signal_handler(sig, frame):
        logger.info("🛑 Shutdown requested...")
        for task in tasks:
            task.cancel()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        pass

    logger.info("👋 Home Assistant stopped")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
```

---

## Phase 3: Dual Mode (Mac Local Wake Word)

### Goal
**Mac can listen for wake word simultaneously with Pi satellites.**

- If "Jarvis" detected on Pi → response plays on Pi
- If "Jarvis" detected on Mac → response plays on Mac
- Config option to enable/disable Mac wake word

### What We Build

1. **`home_assistant/wyoming/local_loop.py`** - Mac wake word detection loop
2. **Config options** - `local_wake_word.enabled`, etc.
3. **Update README** - Dual mode configuration

### Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `home_assistant/wyoming/local_loop.py` | CREATE | Mac wake word loop |
| `home_assistant/run.py` | MODIFY | Start local loop if enabled |
| `config/wyoming.yaml` | MODIFY | Add local_wake_word section |
| `README.md` | MODIFY | Document dual mode |

### Acceptance Criteria

| # | Test Case | Expected Result | Pass/Fail |
|---|-----------|-----------------|-----------|
| 3.1 | Set `local_wake_word.enabled: true` in config | No errors on startup | ☐ |
| 3.2 | Run `python -m home_assistant.run` | Logs show both "Wyoming server" and "Local wake word" | ☐ |
| 3.3 | Say "Jarvis" on Mac microphone | Mac responds with "Yes?", plays on Mac speakers | ☐ |
| 3.4 | Say "What time is it?" on Mac | Response plays on Mac speakers | ☐ |
| 3.5 | Say "Jarvis" on Pi microphone | Pi responds with "Yes?", plays on Pi speakers | ☐ |
| 3.6 | Say "What time is it?" on Pi | Response plays on Pi speakers (not Mac) | ☐ |
| 3.7 | Say "Jarvis" on both at same time | One wins (no crash, no deadlock) | ☐ |
| 3.8 | Set `local_wake_word.enabled: false` | Only Wyoming server runs, Mac mic not used | ☐ |

### Configuration

```yaml
# config/wyoming.yaml

wyoming:
  server:
    enabled: true
    host: "0.0.0.0"
    port: 10700

local_wake_word:
  enabled: false          # Set true to enable Mac wake word
  wake_word: "jarvis"
  provider: "pocketsphinx"
  allow_interrupt: true   # Mac can interrupt its own TTS
```

---

## Phase 4: Pi Interruption During TTS (Future)

### Goal
**User can say wake word during TTS playback to interrupt and start new command.**

### Current Limitation

wyoming-satellite does **NOT** support interruption during TTS playback:
- [Issue #250](https://github.com/rhasspy/wyoming-satellite/issues/250): Can't interrupt TTS with wake word
- [Issue #301](https://github.com/rhasspy/wyoming-satellite/issues/301): Add Stop Wake Word feature

### Implementation Options

| Option | Description | Effort | Hardware |
|--------|-------------|--------|----------|
| **Option 1** | Wait for upstream implementation | None | None |
| **Option 2** | "Stop" wake word (second openwakeword) | Medium | None |
| **Option 3** | ReSpeaker HAT (hardware echo cancellation) | Low | ~$15 |
| **Option 4** | Software AEC (speexdsp) | High | None |
| **Option 5** | Fork wyoming-satellite | High | None |

### Recommended Approach

**Start with Option 3 (ReSpeaker HAT):**
1. Purchase ReSpeaker 2-Mic Pi HAT (~$15)
2. Hardware DSP provides echo cancellation
3. Mic can "hear" wake word even during speaker playback

### Acceptance Criteria (Future)

| # | Test Case | Expected Result | Pass/Fail |
|---|-----------|-----------------|-----------|
| 4.1 | Say "Jarvis" → get long response | Response starts playing on Pi | ☐ |
| 4.2 | During playback, say "Jarvis" | Playback stops, hear "Yes?" | ☐ |
| 4.3 | Say new command | New response plays | ☐ |
| 4.4 | Rapid interrupts (3x in row) | All work correctly, no crashes | ☐ |

---

## Implementation Order & Timeline

```
Phase 1: Pi Satellite + Full Voice Pipeline
├── Create satellite/ folder
│   ├── README.md
│   ├── install.sh
│   ├── run.sh, stop.sh, check_status.sh
│   ├── config/satellite.conf
│   └── systemd/ services
├── Wire up event_bridge.py with real components
├── Implement _generate_tts_sync() with macOS say
├── Update root README.md
└── TEST: Full end-to-end on real Pi hardware
    ├── 1.1-1.9 acceptance criteria

Phase 2: Unified Entry Point + Core Refactoring
├── Create home_assistant/core/
│   ├── voice_processor.py
│   └── session_manager.py
├── Create home_assistant/run.py
├── Modify server.py to use VoiceProcessor
├── Update config/wyoming.yaml
├── Deprecate main.py
├── Update README.md
└── TEST: Same end-to-end, via new entry point
    ├── 2.1-2.7 acceptance criteria

Phase 3: Dual Mode (Mac Local Wake Word)
├── Create home_assistant/wyoming/local_loop.py
├── Update run.py to start local loop
├── Update config with local_wake_word options
├── Update README.md
└── TEST: Both Mac and Pi wake words work
    ├── 3.1-3.8 acceptance criteria

Phase 4: Pi Interruption (Future)
├── Research: Test ReSpeaker HAT
├── Implement chosen solution
├── Update satellite/ with interruption support
└── TEST: Interrupt works reliably
    ├── 4.1-4.4 acceptance criteria
```

---

## Answer: When Can You Test End-to-End?

**After Phase 1 is complete.**

Phase 1 delivers the complete voice pipeline:
- Pi satellite setup with installer
- Wyoming server receiving audio
- STT (Whisper) transcription
- AI orchestrator processing (Claude/OpenAI)
- TTS generation (macOS say)
- Audio playback on Pi

You can run the full test:
```
"Jarvis" → "Yes?" → "What's the weather in Tampa?" → [AI response plays on Pi]
```

---

## Files Summary

### Phase 1 Files
```
satellite/
├── README.md                    # NEW
├── install.sh                   # NEW
├── run.sh                       # NEW
├── stop.sh                      # NEW
├── check_status.sh              # NEW
├── config/
│   └── satellite.conf           # NEW
└── systemd/
    ├── wyoming-openwakeword.service  # NEW
    └── wyoming-satellite.service      # NEW

home_assistant/wyoming/
└── event_bridge.py              # MODIFY (wire up components)

test_wyoming_server.py           # MODIFY (init components)
README.md                        # MODIFY (add satellite section)
```

### Phase 2 Files
```
home_assistant/
├── core/
│   ├── __init__.py              # NEW
│   ├── voice_processor.py       # NEW
│   └── session_manager.py       # NEW
├── run.py                       # NEW
├── main.py                      # MODIFY (deprecation)
└── wyoming/
    └── server.py                # MODIFY (use VoiceProcessor)

config/wyoming.yaml              # MODIFY
README.md                        # MODIFY
```

### Phase 3 Files
```
home_assistant/wyoming/
└── local_loop.py                # NEW

home_assistant/run.py            # MODIFY
config/wyoming.yaml              # MODIFY
README.md                        # MODIFY
```

---

## Sources

- [wyoming-satellite GitHub](https://github.com/rhasspy/wyoming-satellite)
- [Issue #250: Can't interrupt TTS](https://github.com/rhasspy/wyoming-satellite/issues/250)
- [Issue #301: Add Stop Wake Word](https://github.com/rhasspy/wyoming-satellite/issues/301)
- [Wyoming Protocol - Home Assistant](https://www.home-assistant.io/integrations/wyoming/)
