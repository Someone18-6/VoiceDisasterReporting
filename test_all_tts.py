
import os
from pathlib import Path
from dotenv import load_dotenv
from gnani.tts import GnaniTTSClient

load_dotenv()

api_key = os.getenv("GNANI_API_KEY")

if not api_key:
    raise ValueError("GNANI_API_KEY not found in .env")

client = GnaniTTSClient(api_key=api_key)

tests = [
    ("Hindi", "hi-IN", "आपकी आपदा रिपोर्ट प्राप्त हो गई है।"),
    ("Telugu", "te-IN", "మీ విపత్తు నివేదిక అందింది."),
    ("Kannada", "kn-IN", "ನಿಮ್ಮ ವಿಪತ್ತು ವರದಿಯನ್ನು ಸ್ವೀಕರಿಸಲಾಗಿದೆ."),
    ("Tamil", "ta-IN", "உங்கள் பேரிடர் அறிக்கை பெறப்பட்டது."),
    ("Malayalam", "ml-IN", "നിങ്ങളുടെ ദുരന്ത റിപ്പോർട്ട് ലഭിച്ചു."),
    ("Marathi", "mr-IN", "तुमचा आपत्ती अहवाल प्राप्त झाला आहे."),
    ("Bengali", "bn-IN", "আপনার দুর্যোগের প্রতিবেদনটি পাওয়া গেছে।"),
    ("Gujarati", "gu-IN", "તમારો આપત્તિ અહેવાલ પ્રાપ્ત થયો છે."),
    ("Punjabi", "pa-IN", "ਤੁਹਾਡੀ ਆਫ਼ਤ ਰਿਪੋਰਟ ਪ੍ਰਾਪਤ ਹੋ ਗਈ ਹੈ।"),
    ("English", "en-IN", "Your disaster report has been received."),
]

output_dir = Path("tts_tests")
output_dir.mkdir(exist_ok=True)

for name, language, message in tests:
    output_file = output_dir / f"{name.lower()}_confirmation.wav"

    print(f"\nTesting {name} ({language})...")

    try:
        audio = client.synthesize(
            text=message,
            voice="Kaveri",
            model="timbre-v2.5",
            language=language,
            speed=0.85,
            output_file=str(output_file),
        )

        if audio:
            print(f"SUCCESS: {output_file}")
        else:
            print("FAILED: Empty audio response")

    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")
