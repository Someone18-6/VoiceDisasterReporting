
import os
from dotenv import load_dotenv
from gnani.tts import GnaniTTSClient

load_dotenv()

api_key = os.getenv("GNANI_API_KEY")

if not api_key:
    raise ValueError("GNANI_API_KEY not found in .env")

client = GnaniTTSClient(api_key=api_key)

text = "ನಿಮ್ಮ ವಿಪತ್ತು ವರದಿಯನ್ನು ಸ್ವೀಕರಿಸಲಾಗಿದೆ. ದಯವಿಟ್ಟು ವಿವರಗಳನ್ನು ಪರಿಶೀಲಿಸಿ."

try:
    audio = client.synthesize(
        text=text,
        voice="Kaveri",
        model="timbre-v2.5",
        language="kn-IN",
        speed=1.0,
        output_file="kannada_confirmation.wav",
    )

    print("Success! Audio generated.")
    print("Audio size:", len(audio), "bytes")
    print("Saved to: kannada_confirmation.wav")

except Exception as e:
    print("TTS test failed:", e)
