🚀 Jarvis — Local-Language AI Agent Powered by Gemini + Murf AI + Google APIs

Jarvis is a multimodal AI assistant that generates lesson plans, worksheets, presentations, feedback, and more — all in local Indian languages.
It uses Gemini AI, Murf Falcon TTS, Google APIs, and WhatsApp automation to help users automate tasks through simple voice commands.

Demo Link:- https://drive.google.com/file/d/1ItAbr6IzIiWkWEQU5JhBrDSR66WCFAeT/view?usp=sharing

Jarvis can:

🎤 Understand speech (ASR)

🤖 Generate responses, lesson plans, worksheets, & presentations

🗣 Speak naturally using Murf AI Falcon TTS

🧭 Perform system actions (open apps, play music, search online, etc.)

📞 Initiate WhatsApp calls automatically

🇮🇳 Support Indian local languages (Marathi, Hindi, Gujarati, etc.)

📂 Create presentations using Canva / MagicSlides

🎧 Use Spotify + YouTube integration

📝 Automate classroom workflows

👉 Includes README, demo video, and the murf-ai tag in the repository.

🌟 Want to improve your GitHub repo branding?

Here are optional upgrades:

⭐ Add Shields Badges

Add this to the top of your README:

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Gemini AI](https://img.shields.io/badge/Gemini_AI-Powered-brightgreen)
![Murf AI](https://img.shields.io/badge/Murf_AI-Falcon_TTS-orange)
![WhatsApp Automation](https://img.shields.io/badge/WhatsApp-Automation-green)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

⭐ Add a Project Banner

If you want, I can generate a banner image for your GitHub repo (sci-fi JARVIS style).
Just say: “Create a JARVIS GitHub banner”.

⭐ Add Perfect GitHub Topics

Use these tags:

jarvis-ai, gemini-ai, murf-ai, ai-assistant, voice-assistant, asr, tts, whatsapp-automation,
canva-api, magic-slides, python, virtual-assistant, education-ai

🎥 Want a better description for your demo video?

Say: “Write a YouTube-style description for my Jarvis demo”.

📦 Want release notes?

Say: “Generate release notes for the v1.0.0 GitHub release”.

If you'd like, share your GitHub link, and I’ll optimize your README directly for that repository.

You said:
give me redme description as above
ChatGPT said:

Here is the clean, polished, copy-paste-ready README description you asked for — exactly in the style we discussed:

🚀 Jarvis — Local-Language AI Agent Powered by Gemini + Murf AI + Google APIs

Jarvis is an advanced multimodal AI assistant that generates lesson plans, worksheets, presentations, summaries, feedback, and more — all in local Indian languages.
It uses Gemini AI, Murf Falcon TTS, Google APIs, and voice automation to perform tasks hands-free.

Jarvis understands your voice, responds intelligently, speaks naturally, and completes real-world actions on your device.

⭐ Key Features
🎤 Speech Recognition (ASR)

Converts your voice into text in real-time

Supports multilingual input

🤖 AI Generation (Gemini 2.0)

Creates lesson plans

Generates worksheets

Writes presentations

Summarizes documents

Provides educational feedback

Works in local Indian languages (Marathi, Hindi, Gujarati, etc.)

🗣 Natural Voice Output (Murf Falcon TTS)

Uses Murf Falcon ultra-realistic voices

Replies with human-like speech

Fast, low-latency, and API-driven

📞 WhatsApp Automation

Initiates WhatsApp calls using voice commands

Integrates with Google Contacts

Hands-free calling system

🎧 Spotify & YouTube Integration

Play, pause, skip, and search music

Voice-controlled playback

📂 Presentation & Document Automation

Generates presentations using:
✔ Canva API
✔ MagicSlides AI

Auto-creates content using Gemini

Supports text + voice commands

💬 Chat + GUI Mode

Fully interactive GUI frontend

Supports typed input and live voice input

Real-time message bubbles (Jarvis UI)

🔧 Full Setup Guide (After Cloning the Project)

Follow these steps exactly to run Jarvis smoothly.

1️⃣ Clone the Repository
git clone https://github.com/YOUR-USERNAME/JARVIS.git
cd JARVIS

2️⃣ Create .env File (Store All Keys)

Create a file named:

.env


Paste this:

GEMINI_API_KEY=YOUR_GEMINI_API_KEY

MURF_API_KEY=YOUR_MURF_API_KEY

SPOTIFY_CLIENT_ID=YOUR_SPOTIFY_CLIENT_ID

SPOTIFY_CLIENT_SECRET=YOUR_SPOTIFY_CLIENT_SECRET

YT_COOKIE=YOUR_YOUTUBE_COOKIE



⚠️ Never commit .env to GitHub.

3️⃣ Setup Google Gemini Credentials
✅ Step 1 — Create Gemini API Key

Go to Google AI Studio:
https://aistudio.google.com

Open API Keys

Click Create API Key

Copy the key and paste it into .env as GEMINI_API_KEY

✅ Step 2 — Enable Required Google APIs

Go to Google Cloud Console:
https://console.cloud.google.com

Enable these APIs:

Gemini API

Vertex AI API (optional)

Google Text Embeddings API (optional)

Google Contacts API (Required for WhatsApp calling)

Speech-to-Text API (if using Google STT)

To enable:

Console → APIs & Services → Enable APIs → Search → Enable

4️⃣ Install All Dependencies
pip install -r requirements.txt


If using Whisper ASR:

pip install openai-whisper


If using Porcupine for hotword detection:

pip install pvporcupine

5️⃣ Test Gemini Connection

Create a file test_gemini.py:

from google import genai
import os

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

response = client.models.generate_text(
    model="gemini-pro",
    prompt="Hello from Jarvis!"
)

print(response.text)


Run:

python test_gemini.py


If it prints a response → Gemini is working.

6️⃣ Setup Murf Falcon TTS

Create API key at https://murf.ai

Add to .env:

MURF_API_KEY=xxxxx

7️⃣ Spotify & YouTube Music Setup
Spotify

Create Spotify app: https://developer.spotify.com/dashboard/create

Paste credentials in .env.

YouTube

Copy your YouTube cookie and add:

YT_COOKIE="YOUR COOKIE"

8️⃣ Run Jarvis

Simply run:

python run.py
