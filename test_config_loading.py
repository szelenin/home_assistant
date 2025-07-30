#!/usr/bin/env python3
"""
Test config loading for TTS
"""

import yaml
import os

def test_config_loading():
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
            print("✅ Config loaded successfully")
            print(f"TTS config: {config.get('tts', {})}")
            
            tts_config = config.get('tts', {})
            print(f"Voice ID: {tts_config.get('voice_id')}")
            print(f"Rate: {tts_config.get('rate')}")
            print(f"Volume: {tts_config.get('volume')}")
            
    except Exception as e:
        print(f"❌ Failed to load config: {e}")

if __name__ == "__main__":
    test_config_loading() 