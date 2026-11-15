# 🤖 Jarvis — Python Voice Assistant
### Oasis Infobyte Internship | Task 1

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> A fully-featured, beginner-friendly Python voice assistant built for the Oasis Infobyte
> internship programme. Listens through your microphone, understands natural language,
> and responds with text-to-speech — no paid APIs required for core features.

---

## 📋 Table of Contents
1. [Features](#features)
2. [Project Structure](#project-structure)
3. [Installation (Windows)](#installation-windows)
4. [Configuration](#configuration)
5. [Running the Assistant](#running-the-assistant)
6. [Sample Voice Commands](#sample-voice-commands)
7. [Running Tests](#running-tests)
8. [Advanced Features Setup](#advanced-features-setup)
9. [Privacy & Security](#privacy--security)
10. [Troubleshooting](#troubleshooting)

---

## ✅ Features

### Beginner Tier (always works out-of-the-box)
| Feature | Voice Command Example |
|---------|----------------------|
| Greeting | "Hello", "Hi", "Good morning" |
| Current Time | "What time is it?" |
| Current Date | "What's today's date?" |
| Google Search | "Search for Python tutorials" |
| Graceful error handling | (says something unclear → asked to repeat) |
| pyttsx3 TTS | All responses spoken aloud |

### Advanced Tier
| Feature | Voice Command Example |
|---------|----------------------|
| NLP intent recognition | (all commands processed automatically) |
| Wikipedia lookup | "Tell me about Albert Einstein" |
| Weather report | "What's the weather in Mumbai?" |
| Timed reminders | "Remind me to drink water in 5 minutes" |
| Email via voice | "Send an email" |
| General knowledge Q&A | "What is machine learning?" |
| Calculator | "What is 25 times 4?" |
| Open websites | "Open YouTube", "Open GitHub" |
| Custom commands | Configured via `config/commands.json` |

---

## 🗂️ Project Structure

```
VoiceAssistant/
├── main.py                     # Entry point
├── test_assistant.py           # Test suite (unittest)
├── requirements.txt            # Python dependencies
├── README.md                   # This file
│
├── modules/
│   ├── __init__.py
│   ├── speech_engine.py        # Microphone input + TTS output
│   ├── intent_recognition.py   # NLP keyword classifier
│   ├── command_handler.py      # Action handlers for each intent
│   └── logger_setup.py         # Rotating log file setup
│
├── config/
│   ├── settings.json           # TTS, SR, weather, email settings
│   └── commands.json           # Custom voice commands + wake word
│
└── logs/
    └── assistant.log           # Auto-generated rotating log
```

---

## 🖥️ Installation (Windows)

### Step 1 — Install Python
1. Download Python 3.10+ from [python.org](https://www.python.org/downloads/)
2. During installation, **check "Add Python to PATH"**
3. Verify: open Command Prompt and run:
   ```
   python --version
   ```

### Step 2 — Install PyAudio (Windows-specific)
PyAudio requires a pre-built wheel on Windows. Run:
```
pip install pipwin
pipwin install pyaudio
```
> **If pipwin fails**, download the matching `.whl` file from
> https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
> and install with `pip install <filename>.whl`

### Step 3 — Install remaining dependencies
Open Command Prompt **in the project folder** and run:
```
pip install -r requirements.txt
```

### Step 4 — Verify installation
```
python -c "import speech_recognition, pyttsx3, pyaudio; print('All OK!')"
```

---

## ⚙️ Configuration

### `config/settings.json`

| Key | Description |
|-----|-------------|
| `tts.rate` | Speech speed (words per minute). Default: `175` |
| `tts.volume` | Volume 0.0–1.0. Default: `1.0` |
| `tts.voice_index` | 0 = first voice, 1 = second (try both on Windows) |
| `speech_recognition.energy_threshold` | Microphone sensitivity (100–4000) |
| `weather.api_key` | OpenWeatherMap API key (see Advanced setup) |
| `weather.default_city` | City for weather if none spoken |
| `email.sender_email` | Your Gmail address |
| `email.sender_password` | Gmail App Password (NOT your login password) |

### `config/commands.json` — Custom Commands
Add your own commands to the `custom_commands` object:
```json
"open my project": {
    "action": "open_url",
    "url": "https://github.com/YourUsername/YourRepo",
    "response": "Opening your project on GitHub!"
}
```

---

## ▶️ Running the Assistant

### Voice Mode (requires microphone)
```
python main.py
```

### Text Mode (no microphone needed — great for testing)
```
python main.py --text
```

### Show version
```
python main.py --version
```

### Show help
```
python main.py --help
```

---

## 🎤 Sample Voice Commands

| Category | Say This |
|----------|----------|
| **Greeting** | "Hello Jarvis" |
| | "Good morning" |
| **Time** | "What time is it?" |
| | "Tell me the current time" |
| **Date** | "What's today's date?" |
| | "What day is it?" |
| **Search** | "Search for the best Python projects on GitHub" |
| | "Google how to learn machine learning" |
| | "Find the latest news about AI" |
| **Wikipedia** | "Tell me about Python programming language" |
| | "Who is Elon Musk?" |
| | "What is quantum computing?" |
| **Weather** | "What's the weather in New Delhi?" |
| | "Weather today" |
| **Reminder** | "Remind me to drink water in 5 minutes" |
| | "Set a reminder for 2 hours" |
| **Email** | "Send an email" |
| **Joke** | "Tell me a joke" |
| | "Say something funny" |
| **Calculate** | "What is 25 times 4?" |
| | "Calculate 100 divided by 5" |
| **Open site** | "Open YouTube" |
| | "Open GitHub" |
| | "Open Gmail" |
| **Custom** | "Open my project" (if configured) |
| **Exit** | "Goodbye", "Bye", "Exit", "Quit" |

---

## 🧪 Running Tests

Run the full test suite (no microphone required):
```
python test_assistant.py
```

Run with pytest for coloured output:
```
pip install pytest
pytest test_assistant.py -v
```

### What is tested
- Intent recognition for all 15+ command categories
- Slot extraction (search query, city, reminder time, math operands)
- Command handler responses (time format, date format, joke length, etc.)
- Calculator (addition, multiplication, division by zero)
- Browser opening (mocked — no actual browser opened)
- Reminder threading (mocked)
- End-to-end integration flows

---

## 🔧 Advanced Features Setup

### 🌦️ Live Weather (OpenWeatherMap)
1. Sign up free at [openweathermap.org](https://openweathermap.org/api)
2. Copy your API key
3. Paste it into `config/settings.json`:
   ```json
   "weather": {
       "api_key": "PASTE_YOUR_KEY_HERE",
       "default_city": "New Delhi"
   }
   ```
4. Say: *"What's the weather in Mumbai?"*

### 📧 Email via Voice (Gmail)
1. Enable **2-Step Verification** on your Google account
2. Go to: Google Account → Security → App Passwords
3. Generate a password for "Mail" / "Windows Computer"
4. Add to `config/settings.json`:
   ```json
   "email": {
       "sender_email": "your.email@gmail.com",
       "sender_password": "xxxx xxxx xxxx xxxx"
   }
   ```
5. Say: *"Send an email"*

> ⚠️ Never commit `settings.json` with real credentials to a public repository.
> Add it to `.gitignore`.

---

## 🔒 Privacy & Security

| Topic | Details |
|-------|---------|
| **Voice data** | Your voice is sent to Google's Speech Recognition API over HTTPS for transcription. No audio is stored locally. |
| **API keys** | Stored locally in `config/settings.json`. Never shared. |
| **Email credentials** | Stored locally. Use Gmail App Passwords, never your main password. |
| **Logs** | Stored in `logs/assistant.log`. Contains command text, no audio. Rotates at 1 MB. |
| **Internet access** | Required only for: speech recognition, weather API, Wikipedia, news, and Google search. All other features (time, date, calculator, TTS, reminders) work offline. |
| **Data retention** | No data is retained beyond the current session. Log files remain on your machine only. |

### Recommendations
- Do not use this assistant on shared/public computers with email configured.
- Regularly clear `logs/assistant.log` if you are privacy-conscious.
- Use Gmail App Passwords (not your main password) for email.
- Keep `config/settings.json` out of version control (add to `.gitignore`).

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: pyaudio` | Run `pipwin install pyaudio` or install the `.whl` manually |
| `OSError: [Errno -9999]` | Check that your microphone is connected and not muted in Windows Sound settings |
| "Could not understand audio" | Speak clearly, reduce background noise, or lower `energy_threshold` in settings.json |
| `RequestError` from Google SR | Check your internet connection; Google SR requires the internet |
| pyttsx3 no sound | Ensure Windows audio is not muted; try `voice_index: 1` in settings |
| Slow response | Speech recognition sends audio to Google — internet speed matters |
| `--text` mode works, voice doesn't | The issue is microphone/PyAudio specific — reinstall PyAudio |

---

## 📄 License
MIT — free to use, modify, and distribute.

---

*Built for Oasis Infobyte Internship | Task 1 — Python Voice Assistant*
