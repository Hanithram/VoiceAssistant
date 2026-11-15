"""
==============================================================================
  Voice Assistant — Command Handler Module
  Oasis Infobyte Internship | Task 1
==============================================================================
  Maps recognized intents to concrete actions (search, weather, email,
  reminders, Wikipedia, jokes, calculator, etc.) and returns response text.
==============================================================================
"""

import datetime
import webbrowser
import logging
import json
import os
import re
import math
import threading
import time as _time
import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config helper
# ---------------------------------------------------------------------------
_CFG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "settings.json")

def _load_settings() -> dict:
    try:
        with open(_CFG_PATH) as f:
            return json.load(f)
    except Exception as e:
        logger.warning("settings.json load error: %s", e)
        return {}


# ---------------------------------------------------------------------------
# Joke bank (offline)
# ---------------------------------------------------------------------------
JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs!",
    "Why did the computer go to the doctor? Because it had a virus!",
    "How many programmers does it take to change a light bulb? None — that's a hardware problem.",
    "I told my computer I needed a break. Now it won't stop sending me Kit-Kat ads.",
    "Why do Java developers wear glasses? Because they can't C sharp!",
    "A SQL query walks into a bar, walks up to two tables and asks: 'Can I join you?'",
    "Real programmers count from 0.",
    "To understand recursion, you must first understand recursion.",
    "There are 10 types of people in the world: those who understand binary and those who don't.",
    "Why was the JavaScript developer sad? Because he didn't Node how to Express himself.",
]

# ---------------------------------------------------------------------------
# General knowledge Q&A (offline fallback)
# ---------------------------------------------------------------------------
GENERAL_KNOWLEDGE = {
    "capital of india":    "The capital of India is New Delhi.",
    "capital of usa":      "The capital of the USA is Washington, D.C.",
    "capital of uk":       "The capital of the UK is London.",
    "capital of france":   "The capital of France is Paris.",
    "who is the president of usa": "As of 2025, the President of the USA is Joe Biden.",
    "speed of light":      "The speed of light is approximately 299,792 kilometres per second.",
    "what is python":      "Python is a high-level, interpreted programming language known for its clear syntax and versatility.",
    "what is ai":          "Artificial Intelligence is the simulation of human intelligence in machines.",
    "what is machine learning": "Machine Learning is a subset of AI where systems learn patterns from data.",
    "distance to the moon": "The average distance from Earth to the Moon is about 384,400 kilometres.",
    "distance to the sun":  "The average distance from Earth to the Sun is about 150 million kilometres.",
    "who invented python":  "Python was created by Guido van Rossum and first released in 1991.",
    "who invented the internet": "The internet was developed by ARPA in the late 1960s and popularised through the work of Tim Berners-Lee, who invented the World Wide Web in 1989.",
    "what is oasis infobyte": "Oasis Infobyte is an online internship platform that offers hands-on project-based learning in technology domains.",
}


# ---------------------------------------------------------------------------
# Active reminders tracker (in-memory)
# ---------------------------------------------------------------------------
_active_reminders: list[dict] = []


# ---------------------------------------------------------------------------
# CommandHandler
# ---------------------------------------------------------------------------
class CommandHandler:
    """
    Executes actions based on a recognized Intent and returns a text response.
    The TTS speaker is injected so reminders can speak asynchronously.
    """

    def __init__(self, speaker=None):
        """
        Parameters
        ----------
        speaker : TextToSpeech | None
            If provided, reminder alerts will speak via this instance.
        """
        self.speaker  = speaker
        self.settings = _load_settings()

    # -----------------------------------------------------------------------
    # Public dispatch method
    # -----------------------------------------------------------------------
    def handle(self, intent) -> str:
        """Route an Intent to the appropriate handler and return a response."""
        name = intent.name
        slots = intent.slots

        dispatch = {
            "greeting":       self._handle_greeting,
            "time":           self._handle_time,
            "date":           self._handle_date,
            "search":         self._handle_search,
            "wikipedia":      self._handle_wikipedia,
            "weather":        self._handle_weather,
            "reminder":       self._handle_reminder,
            "email":          self._handle_email,
            "joke":           self._handle_joke,
            "news":           self._handle_news,
            "calculate":      self._handle_calculate,
            "open_url":       self._handle_open_url,
            "custom_command": self._handle_custom_command,
            "goodbye":        self._handle_goodbye,
            "unknown":        self._handle_unknown,
        }

        handler = dispatch.get(name, self._handle_unknown)
        try:
            return handler(slots, intent.raw_text)
        except Exception as e:
            logger.error("Error in handler '%s': %s", name, e)
            return "Sorry, something went wrong while processing your request."

    # -----------------------------------------------------------------------
    # Individual handlers
    # -----------------------------------------------------------------------

    def _handle_greeting(self, slots: dict, text: str) -> str:
        hour = datetime.datetime.now().hour
        if hour < 12:
            greeting = "Good morning"
        elif hour < 17:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
        cfg = _load_settings()
        name = cfg.get("assistant_name", "Jarvis")  # read from commands.json via settings
        responses = [
            f"{greeting}! I'm {name}, your voice assistant. How can I help you today?",
            f"Hello there! {greeting} to you. What can I do for you?",
            f"Hey! {greeting}! I'm here and ready to assist.",
        ]
        return random.choice(responses)

    def _handle_time(self, slots: dict, text: str) -> str:
        now = datetime.datetime.now()
        time_str = now.strftime("%I:%M %p")   # e.g. "03:45 PM"
        return f"The current time is {time_str}."

    def _handle_date(self, slots: dict, text: str) -> str:
        now  = datetime.datetime.now()
        # e.g. "Saturday, 07 November 2026"
        date_str = now.strftime("%A, %d %B %Y")
        return f"Today is {date_str}."

    def _handle_search(self, slots: dict, text: str) -> str:
        query = slots.get("query", text).strip()
        if not query:
            return "What would you like me to search for?"
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        logger.info("Opening search URL: %s", url)
        webbrowser.open(url)
        return f"Searching Google for: {query}"

    def _handle_wikipedia(self, slots: dict, text: str) -> str:
        topic = slots.get("topic", "").strip()

        # 1. Check offline general knowledge bank first
        for key, answer in GENERAL_KNOWLEDGE.items():
            if key in text.lower():
                return answer

        # 2. Try Wikipedia API
        if topic:
            try:
                import urllib.request, urllib.parse
                encoded = urllib.parse.quote(topic)
                api_url = (
                    f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"
                )
                req = urllib.request.Request(api_url, headers={"User-Agent": "VoiceAssistant/1.0"})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode())
                    extract = data.get("extract", "")
                    if extract:
                        # Return first two sentences
                        sentences = re.split(r'(?<=[.!?])\s+', extract)
                        summary = " ".join(sentences[:2])
                        webbrowser.open(f"https://en.wikipedia.org/wiki/{encoded}")
                        return f"According to Wikipedia: {summary}"
            except Exception as e:
                logger.warning("Wikipedia API error: %s", e)

        # 3. Fallback: open Wikipedia search
        query = topic or text
        webbrowser.open(f"https://en.wikipedia.org/wiki/Special:Search?search={query.replace(' ', '+')}")
        return f"I couldn't fetch a summary, but I've opened Wikipedia for '{query}'."

    def _handle_weather(self, slots: dict, text: str) -> str:
        city = slots.get("city") or self.settings.get("weather", {}).get("default_city", "")
        api_key = self.settings.get("weather", {}).get("api_key", "")

        if not api_key or api_key == "YOUR_OPENWEATHERMAP_API_KEY":
            # No key configured — open weather website
            webbrowser.open(f"https://wttr.in/{city.replace(' ', '+')}")
            return (
                f"I don't have a weather API key configured yet. "
                f"I've opened the weather page for {city or 'your location'} in your browser. "
                "To enable live weather, add your OpenWeatherMap API key in config/settings.json."
            )

        try:
            import urllib.request, urllib.parse
            city_enc = urllib.parse.quote(city or "Delhi")
            units = self.settings.get("weather", {}).get("units", "metric")
            url = (
                f"https://api.openweathermap.org/data/2.5/weather"
                f"?q={city_enc}&appid={api_key}&units={units}"
            )
            with urllib.request.urlopen(url, timeout=5) as resp:
                data = json.loads(resp.read().decode())

            temp        = data["main"]["temp"]
            feels_like  = data["main"]["feels_like"]
            humidity    = data["main"]["humidity"]
            description = data["weather"][0]["description"]
            city_name   = data["name"]
            unit_sym    = "°C" if units == "metric" else "°F"

            return (
                f"Weather in {city_name}: {description}. "
                f"Temperature is {temp}{unit_sym}, feels like {feels_like}{unit_sym}. "
                f"Humidity is {humidity}%."
            )
        except Exception as e:
            logger.error("Weather fetch error: %s", e)
            return "Sorry, I couldn't fetch the weather right now. Please check your internet connection."

    def _handle_reminder(self, slots: dict, text: str) -> str:
        message = slots.get("message", "your reminder")
        amount  = slots.get("amount")
        unit    = slots.get("unit", "minute")

        if amount is None:
            # Couldn't parse time — ask user interactively is handled upstream;
            # here we give a helpful response
            return (
                "I'd be happy to set a reminder! Please say something like: "
                "'Remind me to drink water in 5 minutes'."
            )

        # Convert to seconds
        multipliers = {"second": 1, "minute": 60, "hour": 3600}
        delay_sec = amount * multipliers.get(unit, 60)

        # Fire reminder in a background thread
        speaker_ref = self.speaker

        def _remind():
            _time.sleep(delay_sec)
            alert = f"⏰ Reminder: {message}"
            print(f"\n{'='*50}\n{alert}\n{'='*50}\n")
            if speaker_ref:
                speaker_ref.speak(f"Reminder! {message}")

        t = threading.Thread(target=_remind, daemon=True)
        t.start()
        _active_reminders.append({"message": message, "delay": delay_sec})

        unit_label = f"{amount} {unit}{'s' if amount != 1 else ''}"
        return f"Got it! I'll remind you to {message} in {unit_label}."

    def _handle_email(self, slots: dict, text: str) -> str:
        cfg = self.settings.get("email", {})
        sender   = cfg.get("sender_email", "")
        password = cfg.get("sender_password", "")
        smtp_srv = cfg.get("smtp_server", "smtp.gmail.com")
        smtp_prt = cfg.get("smtp_port", 587)

        if not sender or sender == "your_email@gmail.com":
            return (
                "Email is not configured yet. "
                "Please add your Gmail address and App Password to config/settings.json. "
                "See the README for instructions."
            )

        # In a real scenario we'd prompt for recipient/body via voice.
        # Here we return a guided response.
        recipient = slots.get("recipient", "")
        return (
            f"I can send an email for you. "
            f"{'Sending to ' + recipient + '.' if recipient else ''} "
            "Please provide the recipient, subject, and message body."
        )

    def _handle_email_send(self, to: str, subject: str, body: str) -> str:
        """Actually sends an email via SMTP (called after full details collected)."""
        cfg = self.settings.get("email", {})
        sender   = cfg.get("sender_email", "")
        password = cfg.get("sender_password", "")
        smtp_srv = cfg.get("smtp_server", "smtp.gmail.com")
        smtp_prt = int(cfg.get("smtp_port", 587))

        try:
            msg = MIMEMultipart()
            msg["From"]    = sender
            msg["To"]      = to
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(smtp_srv, smtp_prt) as server:
                server.ehlo()
                server.starttls()
                server.login(sender, password)
                server.sendmail(sender, to, msg.as_string())

            logger.info("Email sent to %s", to)
            return f"Email sent successfully to {to}!"
        except smtplib.SMTPAuthenticationError:
            return "Email authentication failed. Please check your credentials in settings.json."
        except Exception as e:
            logger.error("Email send error: %s", e)
            return f"Sorry, I couldn't send the email. Error: {e}"

    def _handle_joke(self, slots: dict, text: str) -> str:
        return random.choice(JOKES)

    def _handle_news(self, slots: dict, text: str) -> str:
        webbrowser.open("https://news.google.com")
        return "Opening Google News in your browser. Stay informed!"

    def _handle_calculate(self, slots: dict, text: str) -> str:
        if "expression" in slots:
            a  = slots["a"]
            op = slots["op"]
            b  = slots["b"]

            if op in ("+",):
                result = a + b
            elif op in ("-",):
                result = a - b
            elif op in ("*", "x"):
                result = a * b
            elif op == "/":
                if b == 0:
                    return "Division by zero is not allowed."
                result = a / b
            else:
                result = None

            if result is not None:
                # Format result cleanly
                result_str = str(int(result)) if result == int(result) else f"{result:.4f}"
                return f"The answer is {result_str}."

        # Fallback: open Google Calculator
        webbrowser.open(f"https://www.google.com/search?q={text.replace(' ', '+')}")
        return "I've opened Google for that calculation."

    def _handle_open_url(self, slots: dict, text: str) -> str:
        site = slots.get("site", "").lower()

        # Map common site names to URLs
        url_map = {
            "youtube":        "https://youtube.com",
            "github":         "https://github.com",
            "google":         "https://google.com",
            "gmail":          "https://mail.google.com",
            "stackoverflow":  "https://stackoverflow.com",
            "twitter":        "https://twitter.com",
            "linkedin":       "https://linkedin.com",
            "wikipedia":      "https://wikipedia.org",
            "reddit":         "https://reddit.com",
            "netflix":        "https://netflix.com",
            "amazon":         "https://amazon.com",
        }

        url = url_map.get(site)
        if not url:
            # Try building a URL from the site name
            if site and "." not in site:
                url = f"https://www.{site}.com"
            elif site:
                url = f"https://{site}" if not site.startswith("http") else site

        if url:
            webbrowser.open(url)
            return f"Opening {site or 'the website'} in your browser."
        else:
            return "Which website would you like me to open?"

    def _handle_custom_command(self, slots: dict, text: str) -> str:
        data   = slots.get("command_data", {})
        action = data.get("action", "")
        resp   = data.get("response", "Done!")

        if action == "open_url":
            url = data.get("url", "")
            if url:
                webbrowser.open(url)

        return resp

    def _handle_goodbye(self, slots: dict, text: str) -> str:
        farewells = [
            "Goodbye! Have a great day!",
            "See you later! Take care!",
            "Bye! It was a pleasure assisting you!",
            "Goodbye! Come back whenever you need help!",
        ]
        return random.choice(farewells)

    def _handle_unknown(self, slots: dict, text: str) -> str:
        fallbacks = [
            "I'm sorry, I didn't quite understand that. Could you please repeat?",
            "Hmm, I'm not sure what you mean. Could you rephrase that?",
            "I didn't catch that. Try saying 'help' for a list of commands.",
            "Sorry, I couldn't process that. Could you say it differently?",
        ]
        return random.choice(fallbacks)

    # -----------------------------------------------------------------------
    # Email conversation flow (multi-turn)
    # -----------------------------------------------------------------------
    def run_email_flow(self, listen_fn) -> str:
        """
        Guides the user through composing and sending an email via voice.
        `listen_fn` is a callable that returns transcribed speech text or None.
        """
        cfg = self.settings.get("email", {})
        if not cfg.get("sender_email") or cfg["sender_email"] == "your_email@gmail.com":
            return "Email is not configured. Please update config/settings.json."

        def ask(prompt: str) -> Optional[str]:
            if self.speaker:
                self.speaker.speak(prompt)
            return listen_fn()

        to      = ask("Please say the recipient's email address.")
        subject = ask("What is the subject of the email?")
        body    = ask("What would you like the email to say?")

        if not all([to, subject, body]):
            return "Email cancelled — I didn't catch all the details."

        if self.speaker:
            self.speaker.speak(
                f"Sending email to {to} with subject {subject}. Shall I proceed? Say yes or no."
            )
        confirm = listen_fn()
        if confirm and "yes" in confirm:
            return self._handle_email_send(to, subject, body)
        return "Email cancelled."
