import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, Field
import numpy as np
import wave
import io
import math
import time

# --- Morse Code Logic (Adapted from jscwlib) ---

# Character to Morse Code Mapping (from jscwlib)
# Expanded slightly, add more from original JS if needed
MORSE_CODE_DICT = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
    'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
    'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..',
    '1': '.----', '2': '..---', '3': '...--', '4': '....-', '5': '.....',
    '6': '-....', '7': '--...', '8': '---..', '9': '----.', '0': '-----',
    ',': '--..--', '.': '.-.-.-', '?': '..--..', '/': '-..-.', '-': '-....-',
    '(': '-.--.', ')': '-.--.-', "'": '.----.', '!': '-.-.--', '&': '.-...',
    ':': '---...', ';': '-.-.-.', '=': '-...-', '+': '.-.-.', '_': '..--.-',
    '"': '.-..-.', '$': '...-..-', '@': '.--.-.',
    ' ': ' ' # Space represents word gap
}

# --- Audio Generation Parameters ---
SAMPLE_RATE = 44100  # Samples per second (CD quality)
FREQUENCY = 600      # Morse tone frequency in Hz
AMPLITUDE = 0.5      # Volume (0.0 to 1.0)
BASE_WPM = 20        # Default WPM if speed is 1.0 OR if voice not mapped

# --- Voice to WPM Mapping ---
# Map desired "voice" names to specific WPM settings.
# Use lowercase keys for case-insensitive matching.
VOICE_WPM_MAP = {
    "alloy":   15,  # Example: Slower
    "echo":    20,  # Example: Default/Medium
    "fable":   25,  # Example: Faster
    "onyx":    30,  # Example: Very Fast
    "nova":    12,  # Example: Very Slow
    "shimmer": 18,  # Example: Slightly slower than default
    # Add any other custom names and WPM values you want
    "slowpoke": 8,
    "speedy":   35,
}

# --- FastAPI Application ---
app = FastAPI(
    title="Morse Code TTS Server",
    description="A server mimicking OpenAI TTS API to generate Morse code audio. Uses 'voice' to select WPM.",
)

# --- Request Model (Matching OpenAI TTS API structure) ---
class SpeechRequest(BaseModel):
    model: str = Field(default="morse-code", description="Model name (ignored, always morse)")
    input: str = Field(..., description="The text to convert to Morse code speech")
    voice: str = Field(default="echo", description="Selects WPM based on VOICE_WPM_MAP: alloy, echo, fable, onyx, nova, shimmer, or custom")
    response_format: str = Field(default="wav", description="Audio format (only wav supported)")
    speed: float = Field(default=1.0, ge=0.25, le=4.0, description="Speed multiplier (Used ONLY if voice is not mapped in VOICE_WPM_MAP)")

# --- Morse Audio Generation Function ---
def generate_morse_wav(text: str, wpm: float, freq: int, sample_rate: int, amplitude: float) -> bytes:
    """Generates WAV audio bytes for the given text in Morse code."""

    # This function remains the same as before, it just uses the 'wpm' value passed to it.
    if wpm <= 0:
        wpm = BASE_WPM # Prevent division by zero or negative speeds

    # Timing (based on PARIS standard)
    dot_duration_sec = 1.2 / wpm
    dah_duration_sec = 3 * dot_duration_sec
    intra_symbol_gap_sec = dot_duration_sec  # Gap between dits/dahs within a char
    inter_char_gap_sec = 3 * dot_duration_sec # Gap between characters in a word
    word_gap_sec = 7 * dot_duration_sec       # Gap between words

    # Convert durations to samples
    dot_samples = int(sample_rate * dot_duration_sec)
    dah_samples = int(sample_rate * dah_duration_sec)
    intra_symbol_gap_samples = int(sample_rate * intra_symbol_gap_sec)
    # Note: The actual silence added between chars/words below accounts for the
    # intra_symbol_gap already added after the last symbol.
    inter_char_additional_silence_samples = int(sample_rate * (inter_char_gap_sec - intra_symbol_gap_sec))
    word_additional_silence_samples = int(sample_rate * (word_gap_sec - intra_symbol_gap_sec))


    # Generate basic waveforms
    t_dot = np.linspace(0., dot_duration_sec, dot_samples, endpoint=False)
    t_dah = np.linspace(0., dah_duration_sec, dah_samples, endpoint=False)

    dot_wave = (amplitude * np.sin(2 * np.pi * freq * t_dot)).astype(np.float32)
    dah_wave = (amplitude * np.sin(2 * np.pi * freq * t_dah)).astype(np.float32)

    # Silence waveforms
    intra_symbol_silence = np.zeros(intra_symbol_gap_samples, dtype=np.float32)
    # Pre-calculate additional silence needed beyond the intra-symbol gap
    inter_char_additional_silence = np.zeros(inter_char_additional_silence_samples, dtype=np.float32)
    word_additional_silence = np.zeros(word_additional_silence_samples, dtype=np.float32)


    audio_segments = []
    first_char = True

    for char in text.upper():
        morse_pattern = MORSE_CODE_DICT.get(char)

        if morse_pattern is None:
            print(f"Warning: Character '{char}' not found in Morse dictionary. Skipping.")
            continue # Skip characters not in the dictionary

        # Add inter-character or word gap *before* the next character/word
        # This gap is the *additional* silence needed after the previous char's intra-symbol gap
        if not first_char:
            if char == ' ':
                # Add word gap (additional silence)
                if word_additional_silence.size > 0:
                     audio_segments.append(word_additional_silence)
            else:
                 # Add inter-character gap (additional silence)
                 if inter_char_additional_silence.size > 0:
                      audio_segments.append(inter_char_additional_silence)
        else:
            first_char = False


        if char == ' ':
            continue # Already handled gap before the *next* word

        # Generate audio for the character's Morse pattern
        first_symbol = True
        for symbol in morse_pattern:
            # Add intra-symbol gap before the next symbol within the char
            if not first_symbol:
                if intra_symbol_silence.size > 0:
                     audio_segments.append(intra_symbol_silence)
            else:
                first_symbol = False

            if symbol == '.':
                audio_segments.append(dot_wave)
            elif symbol == '-':
                audio_segments.append(dah_wave)

        # Add the final intra-symbol gap after the last symbol of the character
        if intra_symbol_silence.size > 0:
             audio_segments.append(intra_symbol_silence)


    if not audio_segments:
        # Handle empty input or input with only unknown chars
         return b''

    # Combine all segments
    full_audio = np.concatenate(audio_segments)

    # Convert to 16-bit PCM WAV format
    scaled_audio = (full_audio * 32767).astype(np.int16)

    # Write to in-memory WAV file
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wf:
        wf.setnchannels(1)  # Mono
        wf.setsampwidth(2)  # 16 bits per sample (2 bytes)
        wf.setframerate(sample_rate)
        wf.writeframes(scaled_audio.tobytes())

    buffer.seek(0)
    return buffer.read()

# --- API Endpoint ---
@app.post("/v1/audio/speech")
async def create_speech(request: Request, body: SpeechRequest):
    """
    Generates Morse code audio based on the input text.
    Uses 'voice' to select WPM from VOICE_WPM_MAP, otherwise uses 'speed' multiplier.
    Mimics the OpenAI TTS API endpoint.
    """
    print(f"Received request: Model={body.model}, Voice={body.voice}, Speed={body.speed}, Input='{body.input[:50]}...'")

    requested_voice = body.voice.lower() # Use lowercase for map lookup

    # --- WPM Calculation Logic ---
    if requested_voice in VOICE_WPM_MAP:
        # Voice found in map: Use the mapped WPM directly, ignore the 'speed' parameter
        effective_wpm = VOICE_WPM_MAP[requested_voice]
        print(f"Using WPM {effective_wpm} based on mapped voice '{body.voice}'. Ignoring speed parameter.")
    else:
        # Voice not found in map: Use the default BASE_WPM multiplied by the 'speed' parameter
        effective_wpm = BASE_WPM * body.speed
        print(f"Voice '{body.voice}' not mapped. Using default BASE_WPM ({BASE_WPM}) * speed ({body.speed}) = {effective_wpm:.2f} WPM.")
    # --- End WPM Calculation Logic ---


    # Ensure WPM is valid before passing to generation function
    if effective_wpm <= 0:
        print(f"Warning: Calculated WPM ({effective_wpm:.2f}) is invalid. Falling back to BASE_WPM ({BASE_WPM}).")
        effective_wpm = BASE_WPM # Fallback to prevent errors

    try:
        start_time = time.time()
        wav_bytes = generate_morse_wav(
            text=body.input,
            wpm=effective_wpm, # Pass the determined WPM
            freq=FREQUENCY,
            sample_rate=SAMPLE_RATE,
            amplitude=AMPLITUDE
        )
        end_time = time.time()
        print(f"Generated {len(wav_bytes)} bytes of WAV audio in {end_time - start_time:.3f} seconds at {effective_wpm:.2f} WPM.")

        if not wav_bytes:
             raise HTTPException(status_code=400, detail="Could not generate audio. Input might be empty or contain only unsupported characters.")

        # Return WAV audio
        return Response(content=wav_bytes, media_type="audio/wav")

    except Exception as e:
        print(f"Error generating Morse code audio: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

# --- Root Endpoint (Optional: for testing if the server is running) ---
@app.get("/")
async def read_root():
    return {"message": "Morse Code TTS Server is running. POST to /v1/audio/speech"}

# --- Main Execution ---
if __name__ == "__main__":
    print("Starting Morse Code TTS Server...")
    # NOTE: The host and port specified here in uvicorn.run() are ONLY used
    # if you run the script directly using: python morse_tts_server.py
    # If you run using `uvicorn morse_tts_server:app --port XXXX`,
    # the command-line arguments take precedence.
    uvicorn.run(app, host="0.0.0.0", port=8081) # Example port, ignored if using command-line args
