"""
==============================================================================
  Voice Assistant — Test Suite
  Oasis Infobyte Internship | Task 1
==============================================================================
  Run with:  python test_assistant.py
  Or:        python -m pytest test_assistant.py -v
==============================================================================
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.intent_recognition import IntentRecognizer, Intent
from modules.command_handler    import CommandHandler


# ---------------------------------------------------------------------------
# Intent Recognition Tests
# ---------------------------------------------------------------------------
class TestIntentRecognizer(unittest.TestCase):
    """Unit tests for the NLP intent classifier."""

    def setUp(self):
        self.recognizer = IntentRecognizer()

    def _intent(self, text: str) -> str:
        return self.recognizer.recognize(text).name

    # --- Greeting ---
    def test_greeting_hello(self):
        self.assertEqual(self._intent("hello"), "greeting")

    def test_greeting_hi(self):
        self.assertEqual(self._intent("hi there"), "greeting")

    def test_greeting_good_morning(self):
        self.assertEqual(self._intent("good morning"), "greeting")

    # --- Time ---
    def test_time_query(self):
        self.assertEqual(self._intent("what time is it"), "time")

    def test_time_tell(self):
        self.assertEqual(self._intent("tell me the time"), "time")

    # --- Date ---
    def test_date_query(self):
        self.assertEqual(self._intent("what is today's date"), "date")

    def test_date_today(self):
        self.assertEqual(self._intent("what day is today"), "date")

    # --- Search ---
    def test_search_google(self):
        self.assertEqual(self._intent("search for python tutorials"), "search")

    def test_search_query(self):
        self.assertEqual(self._intent("google machine learning"), "search")

    # --- Wikipedia ---
    def test_wikipedia_what_is(self):
        self.assertEqual(self._intent("what is artificial intelligence"), "wikipedia")

    def test_wikipedia_tell_me(self):
        self.assertEqual(self._intent("tell me about Albert Einstein"), "wikipedia")

    # --- Weather ---
    def test_weather_query(self):
        self.assertEqual(self._intent("what's the weather in Delhi"), "weather")

    def test_weather_temperature(self):
        self.assertEqual(self._intent("what is the temperature today"), "weather")

    # --- Reminder ---
    def test_reminder_query(self):
        self.assertEqual(self._intent("remind me to drink water in 5 minutes"), "reminder")

    # --- Email ---
    def test_email_query(self):
        self.assertEqual(self._intent("send an email"), "email")

    # --- Joke ---
    def test_joke_query(self):
        self.assertEqual(self._intent("tell me a joke"), "joke")

    # --- Calculate ---
    def test_calculate_query(self):
        self.assertEqual(self._intent("calculate 25 times 4"), "calculate")

    # --- Open URL ---
    def test_open_url(self):
        self.assertEqual(self._intent("open youtube"), "open_url")

    # --- Goodbye ---
    def test_goodbye_bye(self):
        self.assertEqual(self._intent("bye"), "goodbye")

    def test_goodbye_exit(self):
        self.assertEqual(self._intent("exit"), "goodbye")

    # --- Unknown ---
    def test_unknown_gibberish(self):
        self.assertEqual(self._intent("zzz qqq xyz"), "unknown")

    # --- Slot Extraction ---
    def test_search_slot(self):
        intent = self.recognizer.recognize("search for machine learning")
        self.assertIn("machine learning", intent.slots.get("query", ""))

    def test_weather_city_slot(self):
        intent = self.recognizer.recognize("what's the weather in Mumbai")
        self.assertEqual(intent.slots.get("city", "").lower(), "mumbai")

    def test_reminder_time_slot(self):
        intent = self.recognizer.recognize("remind me to call mom in 10 minutes")
        self.assertEqual(intent.slots.get("amount"), 10)
        self.assertEqual(intent.slots.get("unit"), "minute")

    def test_calculate_slots(self):
        intent = self.recognizer.recognize("what is 25 * 4")
        self.assertEqual(intent.slots.get("a"), 25.0)
        self.assertEqual(intent.slots.get("b"), 4.0)


# ---------------------------------------------------------------------------
# Command Handler Tests
# ---------------------------------------------------------------------------
class TestCommandHandler(unittest.TestCase):
    """Unit tests for command responses (no TTS, no network)."""

    def setUp(self):
        self.handler    = CommandHandler(speaker=None)
        self.recognizer = IntentRecognizer()

    def _run(self, text: str) -> str:
        intent = self.recognizer.recognize(text)
        return self.handler.handle(intent)

    # --- Greeting ---
    def test_greeting_response_contains_greeting_word(self):
        resp = self._run("hello")
        self.assertTrue(
            any(w in resp.lower() for w in ("morning", "afternoon", "evening", "hello", "hey")),
            msg=f"Unexpected greeting response: {resp}",
        )

    # --- Time ---
    def test_time_response_contains_time(self):
        import re
        resp = self._run("what time is it")
        self.assertRegex(resp, r"\d{1,2}:\d{2}\s*(AM|PM)", msg=resp)

    # --- Date ---
    def test_date_response_contains_date(self):
        resp = self._run("what is today's date")
        self.assertIn("today is", resp.lower(), msg=resp)

    # --- Search (mocked browser) ---
    @patch("webbrowser.open")
    def test_search_opens_browser(self, mock_open):
        resp = self._run("search for python tutorials")
        mock_open.assert_called_once()
        self.assertIn("python tutorials", resp.lower())

    # --- Open URL (mocked browser) ---
    @patch("webbrowser.open")
    def test_open_youtube(self, mock_open):
        resp = self._run("open youtube")
        mock_open.assert_called_once()

    # --- Joke ---
    def test_joke_response_not_empty(self):
        resp = self._run("tell me a joke")
        self.assertTrue(len(resp) > 10)

    # --- Calculator ---
    def test_calculate_addition(self):
        intent = self.recognizer.recognize("what is 10 + 5")
        resp   = self.handler.handle(intent)
        self.assertIn("15", resp)

    def test_calculate_multiplication(self):
        intent = self.recognizer.recognize("what is 6 * 7")
        resp   = self.handler.handle(intent)
        self.assertIn("42", resp)

    def test_calculate_division_by_zero(self):
        intent = self.recognizer.recognize("calculate 10 / 0")
        resp   = self.handler.handle(intent)
        self.assertIn("zero", resp.lower())

    # --- Goodbye ---
    def test_goodbye_response(self):
        resp = self._run("goodbye")
        self.assertTrue(
            any(w in resp.lower() for w in ("goodbye", "bye", "see you", "pleasure")),
            msg=resp,
        )

    # --- Unknown ---
    def test_unknown_response_asks_to_repeat(self):
        resp = self._run("zzz qqq xyz")
        self.assertTrue(len(resp) > 5)

    # --- Email not configured ---
    def test_email_unconfigured(self):
        resp = self._run("send an email")
        self.assertIn("not configured", resp.lower())

    # --- Weather no api key ---
    @patch("webbrowser.open")
    def test_weather_no_api_key(self, mock_open):
        resp = self._run("what's the weather today")
        # Should open browser fallback
        self.assertTrue(
            "configured" in resp.lower() or "browser" in resp.lower() or "weather" in resp.lower()
        )

    # --- Reminder ---
    @patch("threading.Thread")
    def test_reminder_sets_timer(self, mock_thread):
        mock_instance = MagicMock()
        mock_thread.return_value = mock_instance
        resp = self._run("remind me to drink water in 5 minutes")
        self.assertIn("5 minute", resp)
        mock_thread.assert_called_once()
        mock_instance.start.assert_called_once()


# ---------------------------------------------------------------------------
# Integration smoke test
# ---------------------------------------------------------------------------
class TestIntegration(unittest.TestCase):
    """
    End-to-end flow tests (no audio I/O).
    Simulates what would happen during a live voice session.
    """

    def setUp(self):
        self.recognizer = IntentRecognizer()
        self.handler    = CommandHandler(speaker=None)

    def _flow(self, utterance: str) -> tuple[str, str]:
        """Returns (intent_name, response_text)."""
        intent   = self.recognizer.recognize(utterance)
        response = self.handler.handle(intent)
        return intent.name, response

    def test_full_greeting_flow(self):
        name, resp = self._flow("hello there")
        self.assertEqual(name, "greeting")
        self.assertTrue(len(resp) > 5)

    def test_full_time_flow(self):
        name, resp = self._flow("what time is it right now")
        self.assertEqual(name, "time")
        self.assertIn("time is", resp.lower())

    @patch("webbrowser.open")
    def test_full_search_flow(self, _):
        name, resp = self._flow("search for the best Python projects")
        self.assertEqual(name, "search")
        self.assertIn("python projects", resp.lower())

    def test_full_joke_flow(self):
        name, resp = self._flow("tell me something funny")
        self.assertEqual(name, "joke")
        self.assertTrue(len(resp) > 15)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("  Running Voice Assistant Test Suite")
    print("=" * 60)
    loader  = unittest.TestLoader()
    suite   = loader.loadTestsFromModule(sys.modules[__name__])
    runner  = unittest.TextTestRunner(verbosity=2)
    result  = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
