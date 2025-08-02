# Home Assistant Test Suite

This directory contains the complete test suite for the Home Assistant project, organized into unit tests and integration tests.

## Test Organization

### 📁 `unit/` - Unit Tests
**Fast tests with no external dependencies**

- `test_config.py` - ConfigManager functionality
- `test_name_collector.py` - Name collection logic (with mocked TTS/speech)
- `test_weather_api_scenario.py` - API decorator system and registration

**Characteristics:**
- ✅ Run quickly (< 1 second)
- ✅ No network calls
- ✅ No hardware dependencies (microphone, speakers)
- ✅ No AI API calls
- ✅ Use mocks for external dependencies

### 📁 `integration/` - Integration Tests
**Tests requiring external services and hardware**

- `test_ai_provider.py` - Real AI provider calls (Claude, ChatGPT)
- `test_orchestrator_weather_api_scenario.py` - AI orchestrator with real API calls
- `test_recognizer.py` - Speech recognition using microphone
- `test_tts.py` - Text-to-speech using speakers
- `test_recognizer_tts_integration.py` - Full speech workflow
- `*_scenarios.py` - Real-world usage scenarios

**Requirements:**
- 🎤 Microphone access
- 🔊 Speaker/audio output
- 🌐 Internet connection
- 🔑 AI API keys (in `ai_config.yaml`)
- 📦 All dependencies installed

## Running Tests

### Quick Commands

```bash
# Run unit tests only (fast, no external dependencies)
python3 tests/run_tests.py --unit

# Run integration tests only (requires hardware/services)
python3 tests/run_tests.py --integration

# Run all tests
python3 tests/run_tests.py

# Check dependencies
python3 tests/run_tests.py --deps

# Verbose output
python3 tests/run_tests.py --unit -v
```

### Alternative Commands

```bash
# Using unittest directly
python3 -m unittest discover tests/unit/ -v      # Unit tests
python3 -m unittest discover tests/integration/ -v  # Integration tests

# Run specific test file
python3 -m unittest tests.unit.test_weather_api_scenario -v
```

### Legacy Scenario Runner

```bash
# Run integration scenarios (legacy)
python3 tests/run_scenarios.py
```

## Dependencies

### Required for Unit Tests
- `PyYAML` - Configuration file parsing
- Standard library modules

### Additional for Integration Tests
- `pyttsx3` - Text-to-speech
- `SpeechRecognition` - Speech recognition
- `anthropic` - Claude AI provider
- `openai` - ChatGPT provider
- `pyaudio` - Audio input/output

### Installation
```bash
# Install basic dependencies
pip install PyYAML pyttsx3 SpeechRecognition

# Install AI providers
pip install anthropic openai

# Install audio dependencies (may require system packages)
pip install pyaudio
```

## Test Categories

| Test Type | Speed | Dependencies | When to Run |
|-----------|-------|--------------|-------------|
| **Unit** | ⚡ Fast | Minimal | Every commit, CI/CD |
| **Integration** | 🐌 Slow | External services | Before releases, manual testing |

## CI/CD Recommendations

```yaml
# Example GitHub Actions
- name: Run Unit Tests
  run: python3 tests/run_tests.py --unit

# Only run integration tests with secrets
- name: Run Integration Tests  
  run: python3 tests/run_tests.py --integration
  if: ${{ secrets.ANTHROPIC_API_KEY }}
```

## Troubleshooting

### Unit Tests Failing
- Check Python path imports
- Install missing dependencies: `pip install PyYAML`
- Ensure project structure is correct

### Integration Tests Failing
- Check microphone permissions
- Verify speakers are working
- Confirm AI API keys in `ai_config.yaml`
- Test individual components first

### No Tests Found
- Run from project root directory
- Check `__init__.py` files exist in test directories
- Verify Python can import test modules

## Adding New Tests

### Unit Test Guidelines
- Place in `tests/unit/`
- Mock all external dependencies
- Test logic, not integrations
- Name files `test_*.py`

### Integration Test Guidelines  
- Place in `tests/integration/`
- Test real system interactions
- Include error handling
- Document required setup

## Example Test Run

```bash
$ python3 tests/run_tests.py --unit
🧪 Running Unit Tests
========================================
These tests run quickly and don't require external services

......
----------------------------------------------------------------------
Ran 6 tests in 0.001s

OK
✅ Unit tests passed!
```