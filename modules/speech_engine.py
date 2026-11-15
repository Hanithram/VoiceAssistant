"""
==============================================================================
  Voice Assistant — Speech Engine Module
  Oasis Infobyte Internship | Task 1
==============================================================================
  Handles all Text-to-Speech (TTS) output via pyttsx3 and voice input
  capture via SpeechRecognition + PyAudio.
==============================================================================
"""

import pyttsx3
import speech_recognition as sr
import logging
import json
import os

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Load TTS / SR settings from config
# ---------------------------------------------------------------------------
_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "settings.json")

def _load_config() -> dict:
    """Return the parsed settings.json, or sensible defaults on failure."""
    try:
        with open(_CONFIG_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning("Could not load settings.json: %s — using defaults.", e)
        return {}


# ---------------------------------------------------------------------------
# Text-to-Speech Engine
# ---------------------------------------------------------------------------
class TextToSpeech:
    """Wraps pyttsx3 for robust, configurable speech output."""

    def __init__(self):
        cfg = _load_config().get("tts", {})
        self.engine = pyttsx3.init()

        # Apply rate, volume, and voice from config
        self.engine.setProperty("rate",   cfg.get("rate",   175))
        self.engine.setProperty("volume", cfg.get("volume", 1.0))

        # Choose voice by index (0 = first available, usually male on Windows)
        voices = self.engine.getProperty("voices")
        voice_idx = cfg.get("voice_index", 0)
        if voices and 0 <= voice_idx < len(voices):
            self.engine.setProperty("voice", voices[voice_idx].id)
            logger.debug("TTS voice set to: %s", voices[voice_idx].name)

    def speak(self, text: str) -> None:
        """Convert *text* to audible speech and block until playback ends."""
        if not text:
            return
        logger.info("Speaking: %s", text)
        print(f"\n🔊  Assistant: {text}\n")
        self.engine.say(text)
        self.engine.runAndWait()

    def speak_async(self, text: str) -> None:
        """Non-blocking variant — fires and returns immediately.
        
        Note: pyttsx3 is not truly async; this just avoids runAndWait blocking
        callers who don't need to wait for speech to finish.
        """
        if not text:
            return
        logger.info("Speaking (async): %s", text)
        print(f"\n🔊  Assistant: {text}\n")
        self.engine.say(text)
        self.engine.startLoop(False)
        self.engine.iterate()
        self.engine.endLoop()


# ---------------------------------------------------------------------------
# Speech Recognition (Microphone → Text)
# ---------------------------------------------------------------------------
class SpeechRecognizer:
    """Wraps speech_recognition.Recognizer for microphone-based input."""

    def __init__(self):
        cfg = _load_config().get("speech_recognition", {})
        self.recognizer = sr.Recognizer()
        self.language   = _load_config().get("default_language", "en-US")

        # Tunable thresholds from settings.json
        self.recognizer.energy_threshold  = cfg.get("energy_threshold",  300)
        self.recognizer.pause_threshold   = cfg.get("pause_threshold",    0.8)
        self.timeout          = cfg.get("timeout",          5)
        self.phrase_time_limit = cfg.get("phrase_time_limit", 10)

    def listen(self) -> str | None:
        """
        Listen on the default microphone and return the recognized text.

        Returns:
            Lowercase transcribed string on success, or None on failure.
        """
        with sr.Microphone() as source:
            print("\n🎤  Listening … (speak now)\n")
            # Calibrate for ambient noise every call
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)

            try:
                audio = self.recognizer.listen(
                    source,
                    timeout=self.timeout,
                    phrase_time_limit=self.phrase_time_limit,
                )
            except sr.WaitTimeoutError:
                logger.debug("Microphone listen timed out — no speech detected.")
                return None

        return self._transcribe(audio)

    def _transcribe(self, audio: sr.AudioData) -> str | None:
        """Send AudioData to Google Speech Recognition and return text."""
        try:
            text = self.recognizer.recognize_google(audio, language=self.language)
            logger.info("Recognized: %s", text)
            print(f"👤  You said: {text}")
            return text.lower()
        except sr.UnknownValueError:
            logger.debug("Google SR could not understand audio.")
            return None
        except sr.RequestError as e:
            logger.error("Google SR service error: %s", e)
            return None
