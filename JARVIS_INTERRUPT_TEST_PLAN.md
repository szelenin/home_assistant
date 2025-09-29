# Jarvis Interruption Test Plan

## Overview
This test plan focuses on validating the interrupt functionality of Jarvis voice assistant, ensuring users can interrupt ongoing responses and receive proper acknowledgments.

## Current System State
- **TTS Mode**: Blocking (fallback mode - interrupts not currently functional)
- **Expected Behavior**: Falls back to blocking TTS with warning
- **Target**: Enable async TTS for true interrupt capability

---

## Test Categories

### 1. Basic Interrupt Functionality

#### Test 1.1: Simple Response Interruption
**Given** Jarvis is speaking a long response (>10 seconds)
**When** I say "jarvis" during the middle of the response
**Then** Jarvis should:
- Stop speaking immediately
- Log `🛑 [INTERRUPT] Wake word detected during TTS! Stopping speech after {X}s`
- Say "Yes?" as acknowledgment
- Transition to `wake_detected` state
- Be ready for a new command

#### Test 1.2: Early Response Interruption
**Given** Jarvis just started speaking a response (<2 seconds)
**When** I say "jarvis" immediately
**Then** Jarvis should:
- Stop speaking immediately
- Log interrupt detection with short duration
- Provide "Yes?" acknowledgment
- Accept new command without delay

#### Test 1.3: Late Response Interruption
**Given** Jarvis is near the end of a long response (>90% complete)
**When** I say "jarvis" just before natural completion
**Then** Jarvis should:
- Stop speaking immediately (not complete naturally)
- Log interrupt detection
- Provide acknowledgment
- Prioritize new interaction over completion

### 2. Interrupt Acknowledgment Testing

#### Test 2.1: Consistent Acknowledgment
**Given** Jarvis has been interrupted multiple times in a session
**When** I interrupt Jarvis with "jarvis"
**Then** Jarvis should:
- Always respond with "Yes?" (not silence)
- Use consistent voice settings (same as initial wake word)
- Acknowledgment should be immediate (<1 second delay)

#### Test 2.2: Acknowledgment After Natural Completion
**Given** Jarvis completes a response naturally (no interrupt)
**When** I say "jarvis" after the response ends
**Then** Jarvis should:
- Respond with "Yes?" as normal wake word detection
- Not show interrupt logging (should be normal wake word flow)
- Accept new command normally

### 3. State Management During Interrupts

#### Test 3.1: State Transition Verification
**Given** Jarvis is in `responding_with_interrupts` state
**When** I interrupt with "jarvis"
**Then** The logs should show:
- `🛑 TTS interrupted by wake word`
- `🔄 STATE CHANGE: responding_with_interrupts → wake_detected`
- Proper state timing and reason logging

#### Test 3.2: Command Context Clearing
**Given** Jarvis is responding to command A and gets interrupted
**When** I give command B after the interrupt
**Then** Jarvis should:
- Process command B completely (not mix with command A)
- Clear previous command context
- Not reference or continue command A

### 4. Multiple Consecutive Interrupts

#### Test 4.1: Rapid Interruption Sequence
**Given** Jarvis is ready and listening
**When** I perform this sequence rapidly:
1. "jarvis" → "tell me a long story" → wait 2s → "jarvis"
2. "what's the weather" → wait 2s → "jarvis"
3. "what time is it"
**Then** Each interrupt should:
- Work consistently
- Provide "Yes?" acknowledgment each time
- Accept the new command properly
- Not show degraded performance

#### Test 4.2: Interrupt During Acknowledgment
**Given** Jarvis is saying "Yes?" after an interrupt
**When** I say "jarvis" again during the "Yes?" acknowledgment
**Then** Jarvis should:
- Handle gracefully (either complete "Yes?" or interrupt it)
- Not get stuck or confused
- Be ready for new command

### 5. Failure Modes and Edge Cases

#### Test 5.1: Async TTS Availability Check
**Given** The system starts up
**When** Jarvis processes the first command requiring TTS with interrupts
**Then** The logs should show either:
- Successful async TTS initialization, OR
- `WARNING - TTS provider doesn't support async mode, falling back to blocking`

#### Test 5.2: Fallback Mode Behavior
**Given** System is in blocking TTS fallback mode
**When** I attempt to interrupt during TTS
**Then** The system should:
- Complete the response without interruption (expected behavior)
- Still accept "jarvis" wake word after completion
- Log that fallback mode is active

#### Test 5.3: Thread Safety During Interrupts
**Given** Multiple rapid interactions are happening
**When** I interrupt and immediately give new commands
**Then** The system should:
- Not crash or hang
- Handle threading properly
- Not show threading errors in logs

### 6. Performance and Timing Tests

#### Test 6.1: Interrupt Response Time
**Given** Jarvis is speaking and async TTS is working
**When** I say "jarvis" to interrupt
**Then** The interrupt should:
- Be detected within 100ms (0.1s timeout)
- Stop TTS within 500ms
- Start acknowledgment within 1 second

#### Test 6.2: Wake Word Sensitivity During TTS
**Given** Jarvis is speaking at normal volume
**When** I say "jarvis" at various volumes (whisper to normal)
**Then** The wake word should:
- Be detected consistently
- Not be affected by ongoing TTS audio
- Work with same sensitivity as when silent

---

## Test Execution Priority

### Phase 1: Current State Validation
1. Test 5.1 - Verify current async TTS status
2. Test 5.2 - Confirm fallback behavior
3. Test 2.2 - Basic wake word after natural completion

### Phase 2: Async TTS Enablement
1. Fix async TTS hanging issue
2. Test 1.1 - Basic interrupt functionality
3. Test 3.1 - State transition verification

### Phase 3: Comprehensive Testing
1. All remaining tests in order
2. Performance validation
3. Edge case verification

---

## Success Criteria

### Minimum Viable Interrupt System
- [ ] Async TTS works without hanging
- [ ] Basic interruption works (Test 1.1)
- [ ] Consistent acknowledgments (Test 2.1)
- [ ] Proper state management (Test 3.1)

### Full Interrupt System
- [ ] All interrupt scenarios work reliably
- [ ] Performance meets timing requirements
- [ ] No thread safety issues
- [ ] Graceful fallback behavior

---

## Test Environment Setup

### Prerequisites
- macOS system with working Jarvis
- pyttsx + whisper + pocketsphinx configuration
- Anthropic API key configured
- Audio input/output devices working

### Test Data
- **Short response**: "The weather is sunny today."
- **Medium response**: Weather report with 3-day forecast
- **Long response**: "Tell me a detailed story about space exploration"
- **Very long response**: Ask for explanation of complex technical topic

### Logging
- Ensure all interrupt-related log levels are enabled
- Monitor for specific log patterns mentioned in tests
- Capture timing information for performance validation