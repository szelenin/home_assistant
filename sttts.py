#!/usr/bin/env python3.6

import deep_translator.google
import pyttsx3
from RealtimeSTT import AudioToTextRecorder
import sounddevice as sd
import deep_translator
from deep_translator import GoogleTranslator
import warnings
import threading
import os
import sys

os.environ["CT2_VERBOSE"] = "0"
sys.stderr = open(os.devnull, "w")

# Use any translator you like, in this example GoogleTranslator

def set_input_device(name):
    devices = sd.query_devices()
    for i, d in enumerate(devices):
        if name.lower() in d['name'].lower() and d['max_input_channels'] > 0:
            sd.default.device = (i, None)
            return i
    raise ValueError(f"Audio device '{name}' not found")

set_input_device("MacBook Air Microphone")

def print_positive(text):
    print(f"\033[32m[+] {text}\033[0m")

def print_negative(text):
    print(f"\033[31m[-] {text}\033[0m")

def print_neutral(text):
    print(f"\033[35m[*] {text}\033[0m")

def speak(text):
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    text = text.replace(",", "")
    engine.say(text)
    engine.runAndWait()
    engine.stop()

def listen():
    print_neutral("Wait until it says 'speak now'")
    recorder = AudioToTextRecorder()
    result = []

    def process_text(text):
        if print_output:
            print_neutral(text)
        result.append(text)

    recorder.text(process_text)
    return result[0] if result else ""


if __name__ == "__main__":
    try:
        translator = GoogleTranslator(source="auto", target="en")
        print(translator.get_supported_languages())
        while True:
            try:
                spoken = listen()
                translated = translator.translate(spoken)
                speak(translated)
            except Exception as e:
                print_negative(f"An error occured: {e}")
    except KeyboardInterrupt:
        print_neutral("Exitting...")
        exit()

