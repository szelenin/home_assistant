# Wyoming Protocol Integration for Home Assistant

## Overview

This integration enables distributed voice assistant satellites using the Wyoming protocol. It allows Raspberry Pi devices to act as voice satellites that connect to your Mac-based Home Assistant server for processing.

## Architecture

```
┌─────────────────────┐         Wyoming Protocol          ┌──────────────────┐
│  Raspberry Pi       │◄────────────────────────────────►│  Mac Server      │
│  Satellite          │         TCP Port 10700           │  (Home Assistant) │
├─────────────────────┤                                  ├──────────────────┤
│ • Wake Word Detection│                                  │ • Jarvis AI      │
│ • Microphone Input  │──────► Audio Stream ────────────►│ • Whisper STT    │
│ • Speaker Output    │◄────── TTS Audio ◄───────────────│ • pyttsx3 TTS    │
└─────────────────────┘                                  └──────────────────┘
```

## Features

- **Distributed Processing**: Wake word on Pi, heavy processing on Mac
- **Multiple Satellites**: Support for multiple Pi devices
- **Bidirectional Audio**: Stream audio from Pi to Mac, TTS from Mac to Pi
- **Local Wake Word**: OpenWakeWord runs locally on each satellite
- **Integration with Jarvis**: Bridges Wyoming protocol to existing Jarvis system

## Installation

### Prerequisites

1. **Mac Server** (Home Assistant):
   - Python 3.7+
   - Wyoming library: `pip install wyoming==1.5.4`
   - pyring_buffer: `pip install pyring_buffer`

2. **Raspberry Pi** (Satellite):
   - Raspberry Pi Zero 2 W or newer
   - Microphone (USB or HAT)
   - Speaker
   - Wyoming-satellite installed

### Server Setup (Mac)

1. **Install Dependencies**:
   ```bash
   ./venv/bin/pip install wyoming==1.5.4 pyring_buffer
   ```

2. **Configure Wyoming**:
   Edit `config/wyoming.yaml` to set:
   - Server host/port
   - Audio settings
   - Integration preferences

3. **Start Wyoming Server**:
   ```bash
   ./venv/bin/python test_wyoming_server.py
   ```

### Satellite Setup (Raspberry Pi)

1. **Install Wyoming-satellite**:
   ```bash
   git clone https://github.com/rhasspy/wyoming-satellite.git
   cd wyoming-satellite
   script/setup
   ```

2. **Configure Audio Devices**:
   ```bash
   # List microphones
   arecord -L

   # List speakers
   aplay -L
   ```

3. **Run Satellite**:
   ```bash
   script/run \
     --name 'my-satellite' \
     --uri 'tcp://YOUR_MAC_IP:10700' \
     --mic-command 'arecord -D plughw:1,0 -r 16000 -c 1 -f S16_LE -t raw' \
     --snd-command 'aplay -D plughw:1,0 -r 22050 -c 1 -f S16_LE -t raw'
   ```

## Configuration

### Wyoming Configuration (`config/wyoming.yaml`)

```yaml
wyoming:
  server:
    enabled: true
    host: "0.0.0.0"
    port: 10700

  audio:
    input:
      rate: 16000
      width: 2
      channels: 1
    output:
      rate: 22050
      width: 2
      channels: 1

  integration:
    use_existing_stt: true
    use_existing_tts: true
    use_existing_ai: true
```

### Key Settings

- **Server Port**: 10700 (default Wyoming port)
- **Audio Input**: 16kHz for speech recognition
- **Audio Output**: 22.05kHz for TTS
- **Wake Words**: "jarvis", "hey jarvis"

## API Components

### Server Components

1. **WyomingServer**: TCP server accepting satellite connections
2. **AudioHandler**: Processes audio streams from satellites
3. **EventBridge**: Maps Wyoming events to Jarvis system
4. **JarvisIntegration**: Connects Wyoming to existing components

### Protocol Events

- `RunSatellite`: Register satellite with server
- `AudioStart/Stop`: Begin/end audio streaming
- `AudioChunk`: Stream audio data
- `Transcript`: Speech-to-text result
- `Synthesize`: Text-to-speech request

## Testing

### Test Server
```bash
./venv/bin/python test_wyoming_server.py
```

### Test Client
```bash
./venv/bin/python test_wyoming_client.py
```

## Troubleshooting

### Connection Issues
- Verify firewall allows port 10700
- Check Mac IP address from Pi: `ping YOUR_MAC_IP`
- Ensure server is running before starting satellites

### Audio Issues
- Test microphone: `arecord -d 5 test.wav`
- Test speaker: `aplay test.wav`
- Adjust volume settings in config

### Integration Issues
- Check logs: Server provides detailed debug output
- Verify Jarvis components are initialized
- Ensure Wyoming library version matches

## Future Enhancements

1. **SSL/TLS Support**: Encrypted communication
2. **Multiple Wake Words**: Per-satellite wake word configuration
3. **VAD Support**: Voice Activity Detection
4. **LED Indicators**: Visual feedback on satellites
5. **Home Assistant UI**: Web interface for satellite management

## Related Documentation

- [Wyoming Protocol](https://github.com/rhasspy/wyoming)
- [Wyoming Satellite](https://github.com/rhasspy/wyoming-satellite)
- [Home Assistant Wyoming Integration](https://www.home-assistant.io/integrations/wyoming/)

## Status

✅ **Successfully Implemented**:
- Wyoming server with TCP listener
- Audio stream handling
- Event bridge to Jarvis
- Test client/server communication
- Configuration system

🔄 **Next Steps**:
- Deploy to Raspberry Pi
- Test with real audio
- Add wake word detection
- Implement full pipeline