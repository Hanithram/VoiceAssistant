"""
==============================================================================
  Voice Assistant — Intent Recognition Module
  Oasis Infobyte Internship | Task 1
==============================================================================
  Provides lightweight NLP-based intent detection without requiring large
  model downloads (no NLTK corpus, no transformers).  Uses keyword matching
  with confidence scoring so the assistant degrades gracefully offline.
==============================================================================
"""

import re
import json
import os
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Intent definitions — keyword groups and their intent labels
# ---------------------------------------------------------------------------
INTENT_PATTERNS: dict[str, list[str]] = {
    # Greetings
    "greeting": [
        r"\bhello\b", r"\bhi\b", r"\bhey\b", r"\bgreetings?\b",
        r"\bgood\s*(morning|afternoon|evening|night)\b",
        r"\bwhat'?s\s*up\b", r"\bhowdy\b",
    ],
    # Time queries
    "time": [
        r"\btime\b", r"\bwhat\s*time\b", r"\bcurrent\s*time\b",
        r"\btell\s*me\s*the\s*time\b",
    ],
    # Date queries
    "date": [
        r"\bdate\b", r"\btoday\b", r"\bwhat\s*day\b", r"\bwhich\s*day\b",
        r"\bcurrent\s*date\b", r"\bday\s*is\s*it\b", r"\bday\s*today\b",
    ],
    # Google search
    "search": [
        r"\bsearch\b", r"\bgoogle\b", r"\blook\s*up\b", r"\bfind\b",
        r"\bsearch\s*for\b", r"\bsearch\s*google\b",
    ],
    # Wikipedia
    "wikipedia": [
        r"\bwikipedia\b", r"\bwiki\b", r"\btell\s*me\s*about\b",
        r"\bwhat\s*is\b", r"\bwho\s*is\b", r"\bwhat\s*are\b",
        r"\bexplain\b", r"\bdefinition\s*of\b",
    ],
    # Weather
    "weather": [
        r"\bweather\b", r"\btemperature\b", r"\bforecast\b",
        r"\bhumidity\b", r"\brain\b", r"\bsunny\b", r"\bcloudy\b",
        r"\bwind\b", r"\bclimate\b",
    ],
    # Reminder / alarm
    "reminder": [
        r"\bremind(er)?\b", r"\bset\s*a\s*reminder\b", r"\balarm\b",
        r"\bremind\s*me\b", r"\bschedul(e|ing)\b",
        r"\bnotif(y|ication)\b",
    ],
    # Email
    "email": [
        r"\bemail\b", r"\bsend\s*(an?\s*)?mail\b", r"\bcompose\b",
        r"\bwrite\s*(an?\s*)?email\b", r"\bsend\s*(an?\s*)?message\b",
    ],
    # Jokes
    "joke": [
        r"\bjoke\b", r"\bfunny\b", r"\bmake\s*me\s*laugh\b",
        r"\btell\s*(me\s*)?a\s*joke\b", r"\bhumou?r\b",
    ],
    # News
    "news": [
        r"\bnews\b", r"\bheadlines?\b", r"\blatest\b",
        r"\bwhat\s*('?s\s*|is\s*)happening\b",
    ],
    # Calculator / math
    "calculate": [
        r"\bcalculat(e|or)\b", r"\bmath\b", r"\bcompute\b",
        r"\bwhat\s*is\s*\d", r"\bhow\s*much\s*is\b",
        r"\d+\s*[\+\-\*\/]\s*\d+",
    ],
    # Open URL / website
    "open_url": [
        r"\bopen\b", r"\blaunch\b", r"\bgo\s*to\b", r"\bvisit\b",
        r"\bnavigate\s*to\b",
    ],
    # Goodbye / exit
    "goodbye": [
        r"\bbye\b", r"\bgoodbye\b", r"\bsee\s*you\b", r"\bquit\b",
        r"\bexit\b", r"\bstop\b", r"\bshutdown\b", r"\bclose\b",
    ],
}


@dataclass
class Intent:
    """Container for a recognized intent and its metadata."""
    name:       str
    confidence: float              # 0.0 – 1.0
    slots:      dict = field(default_factory=dict)   # named entities / params
    raw_text:   str  = ""


# ---------------------------------------------------------------------------
# Custom-command loader
# ---------------------------------------------------------------------------
def _load_custom_commands() -> dict:
    path = os.path.join(
        os.path.dirname(__file__), "..", "config", "commands.json"
    )
    try:
        with open(path) as f:
            data = json.load(f)
            return data.get("custom_commands", {})
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning("Could not load commands.json: %s", e)
        return {}


CUSTOM_COMMANDS: dict = _load_custom_commands()


# ---------------------------------------------------------------------------
# Intent Recognizer
# ---------------------------------------------------------------------------
class IntentRecognizer:
    """
    Lightweight keyword-based intent classifier.

    How it works
    ------------
    1. Each intent has a list of regex patterns.
    2. The input text is scanned; each pattern match increments a score.
    3. The intent with the highest score (above a minimum threshold) wins.
    4. Slot extraction pulls specific values (e.g., search query, city name).
    """

    MIN_CONFIDENCE = 0.15   # ignore intents below this threshold

    def __init__(self):
        # Pre-compile all patterns for speed
        self._compiled: dict[str, list[re.Pattern]] = {
            intent: [re.compile(p, re.IGNORECASE) for p in patterns]
            for intent, patterns in INTENT_PATTERNS.items()
        }

    # ------------------------------------------------------------------
    def recognize(self, text: str) -> Intent:
        """
        Classify *text* and return the best-matching Intent.
        Returns an Intent with name='unknown' if nothing matches.
        """
        if not text:
            return Intent(name="unknown", confidence=0.0, raw_text=text)

        # 1. Check custom commands first (exact substring match)
        for cmd_phrase, cmd_data in CUSTOM_COMMANDS.items():
            if cmd_phrase in text.lower():
                return Intent(
                    name="custom_command",
                    confidence=1.0,
                    slots={"command_data": cmd_data, "phrase": cmd_phrase},
                    raw_text=text,
                )

        # 2. Score each built-in intent
        scores: dict[str, float] = {}
        total_patterns = sum(len(v) for v in self._compiled.values())

        for intent_name, patterns in self._compiled.items():
            match_count = sum(1 for p in patterns if p.search(text))
            if match_count:
                # Normalise: more patterns matched → higher confidence
                scores[intent_name] = match_count / len(patterns)

        if not scores:
            return Intent(name="unknown", confidence=0.0, raw_text=text)

        best_intent = max(scores, key=scores.__getitem__)
        best_score  = scores[best_intent]

        if best_score < self.MIN_CONFIDENCE:
            return Intent(name="unknown", confidence=best_score, raw_text=text)

        slots = self._extract_slots(best_intent, text)
        return Intent(
            name=best_intent,
            confidence=round(best_score, 2),
            slots=slots,
            raw_text=text,
        )

    # ------------------------------------------------------------------
    def _extract_slots(self, intent: str, text: str) -> dict:
        """Pull relevant named entities / parameters from the utterance."""
        slots: dict = {}

        if intent == "search":
            # Extract query after trigger keywords
            m = re.search(
                r"(?:search(?:\s+for)?|google|look\s+up|find)\s+(.+)",
                text, re.IGNORECASE,
            )
            slots["query"] = m.group(1).strip() if m else text

        elif intent == "wikipedia":
            # Extract topic after trigger keywords
            m = re.search(
                r"(?:tell\s+me\s+about|what\s+is|who\s+is|what\s+are"
                r"|explain|definition\s+of|wikipedia|wiki)\s+(.+)",
                text, re.IGNORECASE,
            )
            slots["topic"] = m.group(1).strip() if m else text

        elif intent == "weather":
            # Try to find city name (word(s) after "in" or "for")
            m = re.search(
                r"(?:in|for|at|of)\s+([A-Za-z\s]+?)(?:\s+today|\s+now|$)",
                text, re.IGNORECASE,
            )
            slots["city"] = m.group(1).strip() if m else ""

        elif intent == "reminder":
            # Extract reminder text and time
            m_msg = re.search(
                r"remind\s+me\s+(?:to\s+)?(.+?)(?:\s+in\s+|\s+at\s+|$)",
                text, re.IGNORECASE,
            )
            m_time = re.search(
                r"in\s+(\d+)\s*(minute|hour|second)s?",
                text, re.IGNORECASE,
            )
            slots["message"] = m_msg.group(1).strip() if m_msg else text
            if m_time:
                slots["amount"] = int(m_time.group(1))
                slots["unit"]   = m_time.group(2).lower()

        elif intent == "email":
            # Basic slot extraction for email
            m_to = re.search(r"(?:to|send\s+to)\s+(\w+)", text, re.IGNORECASE)
            slots["recipient"] = m_to.group(1).strip() if m_to else ""

        elif intent == "calculate":
            # Try to pull the math expression
            m = re.search(r"(\d+(?:\.\d+)?)\s*([\+\-\*\/x])\s*(\d+(?:\.\d+)?)", text)
            if m:
                slots["expression"] = m.group(0)
                slots["a"]  = float(m.group(1))
                slots["op"] = m.group(2)
                slots["b"]  = float(m.group(3))

        elif intent == "open_url":
            # Look for known site names
            m = re.search(
                r"(?:open|launch|go\s*to|visit)\s+([a-z0-9\.\-]+)",
                text, re.IGNORECASE,
            )
            slots["site"] = m.group(1).strip() if m else ""

        return slots
