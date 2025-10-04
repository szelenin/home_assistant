# Wyoming Satellite Testing Guide

## System Overview

Your Wyoming satellite system is now operational with:
- **Raspberry Pi "alicegreen"**: Wyoming satellite server on 192.168.86.20:10700
- **Mac**: Wyoming client that connects to Pi for voice processing
- **Protocol**: Wyoming protocol for distributed voice assistant

## Current Status ✅

- ✅ Pi satellite is running and listening on port 10700
- ✅ Mac can connect to Pi satellite
- ✅ Audio devices configured (microphone active, speaker ready)
- ✅ Wyoming protocol communication working

## Testing Methods

### 1. **Check Pi Satellite Status**
```bash
ssh lizard@alicegreen.local "ps aux | grep wyoming | grep -v grep"
ssh lizard@alicegreen.local "netstat -tlnp | grep :10700"
```

### 2. **Test Network Connection**
```bash
# From Mac, test connection to Pi
./venv/bin/python -c "
import asyncio
async def test():
    try:
        reader, writer = await asyncio.open_connection('192.168.86.20', 10700)
        print('✅ Connected to Pi satellite successfully!')
        writer.close()
        await writer.wait_closed()
    except Exception as e:
        print(f'❌ Connection failed: {e}')
asyncio.run(test())
"
```

### 3. **Monitor Pi Satellite Logs**
```bash
# Check what Wyoming satellite is currently doing
ssh lizard@alicegreen.local "journalctl -f | grep wyoming"
```

### 4. **Test Audio System**
```bash
# Check if microphone is active (should show "Device busy")
ssh lizard@alicegreen.local "arecord -D hw:2,0 -r 16000 -c 1 -f S16_LE -t wav -d 1 /tmp/test.wav"
# ☝️ Should fail with "Device busy" - that's GOOD! It means Wyoming is using it.

# Test speaker (when Wyoming is not using it)
ssh lizard@alicegreen.local "speaker-test -D hw:2,0 -c 2 -t wav -l 1"
```

### 5. **Monitor System Resources**
```bash
ssh lizard@alicegreen.local "
echo '🖥️  System Status:'
echo '📊 Load:' && uptime
echo '💾 Memory:' && free -h
echo '🔊 Audio processes:' && ps aux | grep -E '(arecord|aplay)' | grep -v grep
"
```

## Real-time Monitoring

### Watch Pi Satellite Activity
```bash
# Terminal 1: Monitor satellite logs
ssh lizard@alicegreen.local "tail -f /var/log/syslog | grep wyoming"

# Terminal 2: Monitor network connections
watch "ssh lizard@alicegreen.local 'netstat -an | grep :10700'"

# Terminal 3: Monitor processes
watch "ssh lizard@alicegreen.local 'ps aux | grep wyoming'"
```

## Current Configuration

### Pi Satellite (Server)
- **IP**: 192.168.86.20
- **Port**: 10700
- **Microphone**: hw:2,0 (Logitech USB Headset, 16kHz mono)
- **Speaker**: hw:2,0 (Logitech USB Headset, 22kHz stereo)
- **Status**: ✅ Running and listening for connections

### Mac (Client)
- **Role**: Connects to Pi to process voice
- **STT**: Whisper (loaded and ready)
- **TTS**: Samantha voice (configured)
- **Status**: Ready to connect when needed

## What's Working Now

1. **Wyoming Protocol**: ✅ Pi satellite server running
2. **Network**: ✅ Mac can connect to Pi on port 10700
3. **Audio Capture**: ✅ Pi microphone active and streaming
4. **Audio Playback**: ✅ Pi speaker configured for TTS output

## Integration with Home Assistant

The Pi satellite is discoverable and can be added to Home Assistant:

1. In Home Assistant: Settings → Devices & Services → Add Integration
2. Search for "Wyoming Protocol"
3. Enter Pi IP: `192.168.86.20:10700`
4. The satellite will appear as "alicegreen-satellite"

## Voice Pipeline Flow

```
🗣️  User speaks → 🎤 Pi microphone → 📡 Wyoming protocol →
💻 Mac processing (STT + AI + TTS) → 📡 Wyoming protocol → 🔊 Pi speaker
```

## Quick Health Check

Run this command to verify everything is working:

```bash
echo "🔍 Wyoming Satellite Health Check:"
echo "1. Pi satellite listening:" && nc -zv 192.168.86.20 10700
echo "2. Pi microphone active:" && ssh lizard@alicegreen.local "pgrep arecord > /dev/null && echo '✅ Active' || echo '❌ Not running'"
echo "3. Wyoming process running:" && ssh lizard@alicegreen.local "pgrep -f wyoming > /dev/null && echo '✅ Running' || echo '❌ Not running'"
```

The system is ready for voice commands! 🎉