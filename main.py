"""
==============================================================================
  Voice Assistant — Main Entry Point
  Oasis Infobyte Internship | Task 1
  Author: [Your Name] | Organisation: Oasis Infobyte
==============================================================================

DESCRIPTION
-----------
  A Python-based voice assistant that listens through the microphone,
  understands natural language commands using lightweight NLP intent
  recognition, and responds via text-to-speech (pyttsx3).

BEGINNER TIER FEATURES
  ✅  Capture voice input via SpeechRecognition + PyAudio
  ✅  Respond to greetings ("Hello", "Hey", etc.)
  ✅  Tell current time and date
  ✅  Search Google via voice ("Search for Python tutorials")
  ✅  Graceful handling of unrecognized speech
  ✅  pyttsx3 TTS for all responses

ADVANCED TIER FEATURES
  ✅  NLP-based intent recognition (keyword scoring)
  ✅  Send emails via smtplib (config/settings.json)
  ✅  Timed reminders with audible alerts
  ✅  Live weather via OpenWeatherMap API (or browser fallback)
  ✅  General knowledge Q&A (offline + Wikipedia API)
  ✅  Custom commands via config/commands.json
  ✅  Calculator (voice math expressions)
  ✅  Open websites by name ("open YouTube")
  ✅  Rotating log file in logs/assistant.log

USAGE
  python main.py                  # Interactive voice mode
  python main.py --text           # Text-only mode (no microphone required)
  python main.py --help           # Show help
==============================================================================
"""

import sys
import os
import argparse
import logging

# ---------------------------------------------------------------------------
# Make sure project root is on the path so "modules" resolves correctly
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ---------------------------------------------------------------------------
# Internal imports
# ---------------------------------------------------------------------------
from modules.logger_setup     import setup_logger
from modules.speech_engine    import TextToSpeech, SpeechRecognizer
from modules.intent_recognition import IntentRecognizer
from modules.command_handler  import CommandHandler

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ASSISTANT_NAME = "Jarvis"
VERSION        = "2.0.0"
HELP_TEXT = f"""
{'='*60}
  {ASSISTANT_NAME} Voice Assistant — Available Commands
{'='*60}
  GREETINGS   : "Hello", "Hi", "Good morning"
  TIME        : "What time is it?", "Tell me the time"
  DATE        : "What's today's date?", "What day is it?"
  SEARCH      : "Search for Python tutorials"
                "Google machine learning"
  WIKIPEDIA   : "Tell me about Albert Einstein"
                "What is quantum computing?"
  WEATHER     : "What's the weather in Mumbai?"
                "Weather today"
  REMINDER    : "Remind me to drink water in 5 minutes"
                "Set a reminder for 2 hours"
  EMAIL       : "Send an email" (requires config setup)
  JOKE        : "Tell me a joke", "Say something funny"
  NEWS        : "Show me the news", "Latest headlines"
  CALCULATE   : "What is 25 times 4?"
                "Calculate 100 divided by 5"
  OPEN SITE   : "Open YouTube", "Open GitHub"
  GOODBYE     : "Bye", "Exit", "Quit", "Goodbye"
  HELP        : "Help", "What can you do?"
{'='*60}
"""

WAKE_WORDS = {"jarvis", "hey jarvis", "ok jarvis", "assistant"}


# ---------------------------------------------------------------------------
# Assistant Core
# ---------------------------------------------------------------------------
class VoiceAssistant:
    """
    Orchestrates the full voice-assistant pipeline:
      1. Listen (SpeechRecognizer)
      2. Classify (IntentRecognizer)
      3. Act (CommandHandler)
      4. Respond (TextToSpeech)
    """

    def __init__(self, text_mode: bool = False):
        """
        Parameters
        ----------
        text_mode : bool
            If True, reads commands from stdin instead of microphone.
            Useful for testing without a microphone.
        """
        self.text_mode = text_mode
        self.logger    = logging.getLogger(self.__class__.__name__)

        print(self._banner())

        # Initialise components
        self.speaker    = TextToSpeech()
        self.recognizer = None if text_mode else SpeechRecognizer()
        self.classifier = IntentRecognizer()
        self.handler    = CommandHandler(speaker=self.speaker)

        self.running = True

    # ------------------------------------------------------------------
    def run(self) -> None:
        """Main event loop."""
        startup_msg = (
            f"Hello! I'm {ASSISTANT_NAME}, your voice assistant. "
            "I'm ready to help. Say 'help' to see what I can do, "
            "or 'bye' to exit."
        )
        self.speaker.speak(startup_msg)

        while self.running:
            try:
                text = self._get_input()

                if text is None:
                    # Microphone timeout / no speech
                    continue

                if not text.strip():
                    continue

                # Check for help keyword before intent classification
                if any(w in text for w in ("help", "what can you do", "commands")):
                    print(HELP_TEXT)
                    self.speaker.speak(
                        "I can help with greetings, time, date, Google search, "
                        "Wikipedia, weather, reminders, emails, jokes, calculations, "
                        "and opening websites. Check the console for the full list."
                    )
                    continue

                # Classify intent
                intent = self.classifier.recognize(text)
                self.logger.debug("Intent: %s (%.2f)", intent.name, intent.confidence)

                # Special multi-turn flow for email
                if intent.name == "email":
                    response = self.handler.run_email_flow(
                        listen_fn=self._get_input
                    )
                else:
                    response = self.handler.handle(intent)

                # Speak and print the response
                self.speaker.speak(response)

                # Check exit condition
                if intent.name == "goodbye":
                    self.running = False

            except KeyboardInterrupt:
                self.speaker.speak("Shutting down. Goodbye!")
                self.running = False
            except Exception as e:
                self.logger.error("Unexpected error in main loop: %s", e, exc_info=True)
                self.speaker.speak("I encountered an error. Please try again.")

    # ------------------------------------------------------------------
    def _get_input(self) -> str | None:
        """Return transcribed text from microphone or stdin."""
        if self.text_mode:
            try:
                raw = input("⌨️   You (type): ").strip()
                return raw.lower() if raw else None
            except EOFError:
                return None
        else:
            return self.recognizer.listen()

    # ------------------------------------------------------------------
    @staticmethod
    def _banner() -> str:
        return f"""
╔══════════════════════════════════════════════════════╗
║          {ASSISTANT_NAME} — Python Voice Assistant            ║
║          Oasis Infobyte Internship  |          ║
║          Version {VERSION}                              ║
╚══════════════════════════════════════════════════════╝
  Mode    : Voice (microphone) / Text (--text flag)
  Commands: Say "help" or type help for a full list
  Exit    : Say "bye" / "exit" or press Ctrl+C
{'─'*56}
"""


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description=f"{ASSISTANT_NAME} Voice Assistant — Oasis Infobyte Task 1",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--text", "-t",
        action="store_true",
        help="Run in text-input mode (no microphone required).",
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"%(prog)s {VERSION}",
    )
    return parser.parse_args()


def main() -> None:
    # 1. Set up logging before anything else
    setup_logger()

    # 2. Parse CLI arguments
    args = parse_args()

    # 3. Run the assistant
    assistant = VoiceAssistant(text_mode=args.text)
    assistant.run()


if __name__ == "__main__":
    main()
