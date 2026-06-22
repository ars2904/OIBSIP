# Nova: Python-Based Voice Assistant

Nova is a feature-rich, high-performance, and visually elegant offline/online desktop voice assistant. Built with Python and modern tkinter, it features natural language intent understanding, live weather updates, email dispatching, reminders, general Q&A, and custom command configurations.

This project is created as part of the **Oasis Infobyte Internship Program (OIBSIP)** under the folder structure: `OIBSIP/Python-Task1-VoiceAssistant/`.

---

## Features

### Beginner Tier
*   **Voice Capture:** Listen to user queries via the computer's microphone.
*   **Vocal Greetings:** Friendly response to "Hello" and standard greeting phrases.
*   **Time & Date:** Responds to requests for the current time and date.
*   **Web Search:** Launches a browser window to search Google for your queries.
*   **Graceful Fallbacks:** Friendly request to repeat if the voice isn't recognized.
*   **Text-to-Speech:** Vocalized responses using offline speech synthesis.

### Advanced Tier
*   **Natural Language Understanding (NLU):** Intent mapping using lightweight parsing instead of rigid keyword matching.
*   **Voice Email:** Send emails using SMTP securely via vocal prompts.
*   **Audible Reminders:** Set countdown timers in background threads that alert you via Windows sound signals (`winsound.Beep`) and voice readouts.
*   **Live Weather:** Read out current weather information dynamically using coordinates and conditions from geolocations.
*   **General Knowledge Q&A:** Instantly answer general knowledge questions using DuckDuckGo Instant Answers and Wikipedia search.
*   **Custom Commands:** Configure shortcuts (URL launching, text-to-speech triggers) using the settings pane or via voice prompts.
*   **Clean Dark-Mode GUI:** Dashboard showing status updates, conversation logs, text-input fallback, and a beautiful pulsing visual microphone.

---

## Tech Stack
*   **Speech Recognition:** `SpeechRecognition` (Google Web Speech API)
*   **Text-to-Speech:** `pyttsx3`
*   **Networking / APIs:** `requests`
*   **NLU & Tokenization:** `nltk`
*   **Background Threads:** `threading`
*   **User Interface:** `tkinter`
*   **Email Protocol:** `smtplib`, `email`

---

## Installation & Setup

> [!IMPORTANT]
> Since Python 3.14 lacks precompiled wheels for `PyAudio`, it is highly recommended to run this application using **Python 3.12** or compile/install PyAudio separately.

1. Navigate to the project directory:
   ```bash
   cd C:\Users\aryan\oasis\OIBSIP\Python-Task1-VoiceAssistant
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: If installing PyAudio fails on Windows, install it using a precompiled wheel from standard binary distributions or use the text-input box fallback inside the GUI.*

3. Start the application:
   ```bash
   python main.py
   ```

---

## Privacy Considerations

### 1. Voice Data & Transcription
*   **What is processed:** When you click the microphone to speak, your voice is captured.
*   **How it is processed:** The audio fragment is sent securely to the Google Web Speech API to be translated into text. The raw audio is never recorded, saved, or reused.
*   **Local Processing Fallback:** If you prefer offline usage or do not have internet connection, you can type your commands directly in the GUI text box. All typed inputs are parsed 100% locally on your machine.

### 2. Personal Information & Email
*   **What is processed:** The SMTP settings, email addresses, and message contents.
*   **How it is processed:** All details are processed purely on your machine. SMTP configuration details (such as server, port, and password credentials) are saved in your local `config.json` file. The email is transmitted directly from your computer to your SMTP mail provider (e.g. Gmail) over a secure, encrypted TLS/SSL connection. No external databases, servers, or third parties collect this data.

### 3. Weather Location Information
*   **What is processed:** The city name you request.
*   **How it is processed:** The city name is sent to geocoding services (Open-Meteo or OpenWeatherMap) to fetch weather forecasts. No identifying details, IP addresses, or location trackers are collected or sent.
