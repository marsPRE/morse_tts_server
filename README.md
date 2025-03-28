# Morse Code TTS Server (OpenAI API Compatible)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) A simple Python [FastAPI](https://fastapi.tiangolo.com/) server that provides a text-to-speech endpoint mimicking the OpenAI `/v1/audio/speech` API. However, instead of generating human speech, it generates **Morse code audio** in WAV format.

This server is ideal for applications like [Silly Tavern](https://sillytavern.app/) or others that are designed to work with the OpenAI TTS API but where you might want Morse code output instead.

## Features

* **OpenAI API Compatibility:** Exposes a `POST /v1/audio/speech` endpoint accepting standard OpenAI TTS parameters (`input`, `voice`, `speed`, etc.).
* **Text-to-Morse:** Converts input text into corresponding Morse code audio signals.
* **WAV Output:** Generates audio in standard WAV format.
* **Configurable Audio:** Allows setting the base Words Per Minute (WPM), tone frequency (Hz), and amplitude.
* **Voice-Based Speed Selection:** Uses the `voice` parameter (e.g., "alloy", "echo", "fable", "onyx", "nova", "shimmer", or custom names) to select pre-defined WPM speeds (customizable map).
* **Speed Parameter Fallback:** If a selected `voice` is not mapped to a specific WPM, the `speed` parameter acts as a multiplier on the `BASE_WPM`.
* **Simple & Lightweight:** Built with FastAPI and NumPy, minimal dependencies.

## Requirements

* Python 3.7+
* Libraries: `fastapi`, `uvicorn`, `numpy`

## Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git) # Replace with your repo URL
    cd your-repo-name
    ```

2.  **Install dependencies:**
    (It's recommended to use a Python virtual environment)
    ```bash
    pip install fastapi uvicorn numpy
    ```


## Running the Server

You can run the server using Uvicorn. Specify the host and port directly on the command line:

```bash
# Example using port 8081, accessible on your local network
uvicorn morse_tts_server:app --host 0.0.0.0 --port 8081
