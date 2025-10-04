# Wyoming Protocol Integration Plan

## Overview
Integration plan for Wyoming protocol with your Home Assistant/Jarvis system. Building on the proven Pi→Mac voice pipeline foundation.

## System Architecture
```
🛰️ Pi Satellite (alicegreen - 192.168.86.20:10700)
├── 🎤 Microphone: Logitech USB headset (hw:2,0)
├── 🔊 Speakers: Same headset for TTS output
├── 👂 Wyoming-OpenWakeWord: Local "Jarvis" detection
└── 📡 Wyoming Satellite: Audio streaming to Mac

💻 Mac Server (192.168.86.26)
├── 🧠 STT: Whisper speech recognition
├── 🤖 AI: Your existing Jarvis system
├── 🗣️ TTS: macOS Samantha voice
└── 📡 Wyoming Server: Receives Pi audio streams
```

## Pipeline Flow
```
🗣️ "Jarvis" → 👂 OpenWakeWord (Pi) → 📡 Stream to Mac → 🧠 STT → 🤖 AI → 🗣️ TTS → 📡 Back to Pi → 🔊 Speakers
```

---

## Step 1: Pi Voice Command → Home Assistant Processing → TTS Playback

### Goal
Connect Wyoming satellite directly to your existing Jarvis components for end-to-end voice processing.

### Implementation
1. **Wyoming Event Bridge** (`home_assistant/wyoming/jarvis_bridge.py`)
   - Handle `AudioChunk` events from Pi satellite
   - Convert to your existing speech recognition format
   - Route AI responses back as TTS audio streams

2. **Jarvis Integration** (`home_assistant/wyoming/jarvis_integration.py`)
   - Connect Wyoming server to existing Jarvis components
   - Manage audio format conversion (16kHz in, 22kHz out)
   - Handle async audio streaming

3. **Configuration** (`config/wyoming_jarvis.yaml`)
   - Pi satellite connection settings
   - Audio format specifications
   - Jarvis component configuration

### Test Script: `test_wyoming_jarvis_step1.py`
```python
# Test manual voice command through Wyoming protocol
# 1. Connect to Pi satellite
# 2. Send test audio
# 3. Verify Jarvis processing
# 4. Confirm TTS response on Pi speakers
```

### Success Criteria
- ✅ Speak into Pi microphone (manual activation)
- ✅ Mac processes with Jarvis STT → AI → TTS
- ✅ Response plays on Pi speakers
- ✅ Clear audio quality both directions

---

## Step 2: Wake Word "Jarvis" Detection

### Goal
Add local wake word detection so system activates only when "Jarvis" is spoken.

### Implementation
1. **Install Wyoming-OpenWakeWord on Pi**
   ```bash
   ssh lizard@alicegreen.local
   pip install wyoming-openwakeword
   ```

2. **Wake Word Configuration**
   - Download "jarvis" wake word model
   - Configure OpenWakeWord to listen for "Jarvis"
   - Set sensitivity and timeout parameters

3. **Pipeline State Management**
   - IDLE: Listening for wake word only
   - WAKE_DETECTED: Wake word heard, start streaming
   - LISTENING: Capturing voice command
   - PROCESSING: STT → AI processing
   - RESPONDING: Playing TTS response
   - Return to IDLE

4. **Wyoming Integration**
   - Handle `Detection` events from OpenWakeWord
   - Trigger `RunPipeline` on wake word detection
   - Manage state transitions

### Test Script: `test_wyoming_wakeword_step2.py`
```python
# Test wake word detection and activation
# 1. Verify OpenWakeWord is listening
# 2. Say "Jarvis" and confirm detection
# 3. Issue voice command
# 4. Verify complete pipeline execution
```

### Success Criteria
- ✅ Pi listens continuously for "Jarvis"
- ✅ No audio sent to Mac until wake word detected
- ✅ "Jarvis" triggers voice command capture
- ✅ Complete pipeline: wake → command → AI → response
- ✅ Returns to wake word listening after response

---

## Step 3: Interruption Handling System

### Goal
Allow interrupting long TTS responses with immediate "Yes" acknowledgment and return to listening.

### Implementation
1. **Interrupt Detection**
   - Monitor for voice activity during TTS playback
   - Use VAD (Voice Activity Detection) or simple audio level detection
   - Trigger interruption on voice input

2. **PauseSatellite Event Handling**
   - Send `PauseSatellite` event to stop current TTS
   - Clear audio buffers on Pi
   - Stop Mac TTS generation

3. **"Yes" Acknowledgment**
   - Generate quick "Yes" TTS response
   - Play immediately on Pi speakers
   - Clear acknowledgment, not part of conversation

4. **State Reset**
   - Return to IDLE (wake word listening) state
   - Clear any pending audio or pipeline state
   - Ready for next "Jarvis" activation

### Test Script: `test_wyoming_interruption_step3.py`
```python
# Test interruption during long responses
# 1. Say "Jarvis, tell me a long story"
# 2. Interrupt mid-response by speaking
# 3. Verify "Yes" acknowledgment
# 4. Confirm return to wake word listening
```

### Success Criteria
- ✅ Can interrupt any TTS response by speaking
- ✅ Immediate "Yes" acknowledgment plays
- ✅ TTS stops cleanly without audio artifacts
- ✅ System returns to wake word listening
- ✅ Next "Jarvis" works normally

---

## Technical Implementation Details

### Wyoming Event Types Used
- `AudioChunk`: Audio data streaming
- `Detection`: Wake word detected
- `RunPipeline`: Start voice processing pipeline
- `PauseSatellite`: Interrupt/stop current operation
- `AudioStart`/`AudioStop`: Stream control
- `Transcript`: STT results
- `Synthesize`: TTS requests

### Audio Format Specifications
- **Input**: 16kHz, 16-bit, mono (Pi microphone)
- **Processing**: Your existing Jarvis format
- **Output**: 22kHz, 16-bit, stereo (Pi speakers)

### Integration Points
- `home_assistant/speech/recognizer.py`: STT integration
- `home_assistant/speech/tts.py`: TTS integration
- `home_assistant/assistant/jarvis.py`: AI processing
- Wyoming protocol: Network communication

### State Management
```python
IDLE = "idle"              # Listening for wake word
WAKE_DETECTED = "wake"     # Wake word heard
LISTENING = "listening"    # Capturing command
PROCESSING = "processing"  # STT + AI
RESPONDING = "responding"  # Playing TTS
INTERRUPTED = "interrupt"  # User interrupted
```

---

## Testing Strategy

### Individual Component Tests
1. **Wyoming Connection**: `nc -zv 192.168.86.20 10700`
2. **Wake Word**: Monitor OpenWakeWord logs
3. **Audio Pipeline**: Pi mic → Mac → Pi speakers
4. **State Transitions**: Log state changes

### End-to-End Tests
1. **Happy Path**: "Jarvis" → command → response → ready
2. **Interruption**: Long response → interrupt → "Yes" → ready
3. **Multiple Commands**: Rapid "Jarvis" activations
4. **Error Recovery**: Network issues, audio problems

### Performance Metrics
- Wake word detection latency: <500ms
- STT processing time: <2s for typical commands
- TTS generation: <1s for short responses
- Audio streaming: Real-time with minimal buffering

---

## File Structure

```
home_assistant/
├── wyoming/
│   ├── __init__.py
│   ├── server.py              # Wyoming protocol server
│   ├── jarvis_bridge.py       # Event bridge to Jarvis
│   ├── jarvis_integration.py  # Main integration class
│   └── state_manager.py       # Pipeline state management
├── config/
│   └── wyoming_jarvis.yaml    # Configuration
└── tests/
    ├── test_wyoming_jarvis_step1.py
    ├── test_wyoming_wakeword_step2.py
    └── test_wyoming_interruption_step3.py
```

## Next Steps After Implementation

1. **Multiple Satellites**: Add more Pi devices for whole-house voice
2. **Custom Wake Words**: Train models for personalized activation
3. **Home Assistant Integration**: Full smart home control
4. **Voice Profiles**: Multiple user recognition
5. **Advanced Interruption**: Context-aware pause/resume

---

## Current Status
- ✅ Pi satellite hardware working (192.168.86.20:10700)
- ✅ Audio pipeline proven (Pi mic → Mac processing → Pi speakers)
- ✅ Wyoming protocol foundation established
- 🟡 Step 1: Wyoming → Jarvis integration (in progress)
- ⏳ Step 2: Wake word detection (pending)
- ⏳ Step 3: Interruption handling (pending)

Your Wyoming satellite system foundation is solid - time to build the intelligence layer! 🚀