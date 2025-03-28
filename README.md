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
    *Alternatively, if you create a `requirements.txt` file:*
    ```bash
    pip install -r requirements.txt
    ```

## Running the Server

You can run the server using Uvicorn. Specify the host and port directly on the command line:

```bash
# Example using port 8081, accessible on your local network
uvicorn morse_tts_server:app --host 0.0.0.0 --port 8081
```

* `--host 0.0.0.0`: Listen on all available network interfaces. Use `127.0.0.1` to only allow connections from the same machine.
* `--port 8081`: Specify the port number you want the server to run on. Choose any available port (e.g., 8000, 5000, etc.).

Add `--reload` for automatic reloading during development:

```bash
# Example adding the --reload flag
uvicorn morse_tts_server:app --host 0.0.0.0 --port 8081 --reload
```

**Note:** The `uvicorn.run(...)` call inside the `if __name__ == "__main__":` block in `morse_tts_server.py` is *ignored* when you run the server using the `uvicorn module:app` command format. Use command-line arguments as shown above.

## Client Configuration (Example: Silly Tavern)

1.  Go to TTS Settings in Silly Tavern.
2.  Select **OpenAI** as the provider.
3.  Set the **API Endpoint URL**: `http://<server_ip>:<port>/v1/audio/speech`
    * If running on the same machine: `http://127.0.0.1:8081/v1/audio/speech` (use the port you chose).
    * If running on another machine on your network: `http://<server's_local_ip>:8081/v1/audio/speech`.
4.  Leave the **API Key** field blank.
5.  Select a **Voice**: Choose a name defined in the `VOICE_WPM_MAP` within the script (e.g., "echo", "fable", "onyx", "slowpoke") to get that specific WPM speed.
6.  **Speed Slider**: This slider only takes effect if the selected **Voice** is *not* found in the `VOICE_WPM_MAP` in the script.

## Customization

You can easily customize the server's behavior by editing `morse_tts_server.py`:

* **`VOICE_WPM_MAP`**: Modify this dictionary to add, remove, or change the mapping between voice names (lowercase) and desired WPM speeds.
    ```python
    # Example inside morse_tts_server.py
    VOICE_WPM_MAP = {
        "echo":    20,
        "fable":   25,
        # Add your own
        "custom_slow": 10,
    }
    ```
* **`BASE_WPM`**: Change the default WPM used when a voice is not mapped.
* **`FREQUENCY`**: Change the pitch of the Morse code tone (in Hz).
* **`AMPLITUDE`**: Adjust the volume of the generated audio (0.0 to 1.0).
* **`MORSE_CODE_DICT`**: Add or modify character-to-Morse mappings if needed.

## API Endpoint

### `POST /v1/audio/speech`

* **Request Body (JSON):**
    * `input` (string, required): The text to convert.
    * `voice` (string, optional, default: "echo"): Selects a WPM preset from `VOICE_WPM_MAP`.
    * `speed` (float, optional, default: 1.0): Speed multiplier applied to `BASE_WPM` *only if* `voice` is not found in `VOICE_WPM_MAP`. Range: 0.25 to 4.0.
    * `model` (string, optional): Ignored by this server.
    * `response_format` (string, optional): Ignored, always returns `audio/wav`.
* **Response:**
    * `200 OK`: Returns binary WAV audio data with `Content-Type: audio/wav`.
    * `400 Bad Request`: If audio generation fails (e.g., empty input).
    * `500 Internal Server Error`: If an unexpected error occurs.

## Limitations

* **WAV Only:** The server currently only outputs WAV audio, regardless of the requested `response_format`.
* **Basic Tone:** Audio generation uses a simple sine wave. It does not include advanced audio filtering or shaping found in libraries like `jscwlib`.
* **Simplified Timing:** Primarily based on WPM using the PARIS standard. Does not implement Farnsworth timing (`eff` speed) or explicit extra word spacing (`ews`) control via API parameters.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

* Morse code timing logic based on the PARIS standard.
* API structure designed for compatibility with OpenAI TTS clients.

```
