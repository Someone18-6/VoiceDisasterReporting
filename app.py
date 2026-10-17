
import re
import os
import tempfile

import streamlit as st
from dotenv import load_dotenv
from gnani.stt import GnaniSTTClient



load_dotenv()

st.set_page_config(
    page_title="Voice Disaster Reporting",
    page_icon="🚨",
    layout="centered"
)

st.title("🚨 Voice-Based Disaster Reporting")
st.write(
    "Report a disaster using your voice in your preferred language."
)

api_key = os.getenv("GNANI_API_KEY")

if not api_key:
    st.error("API key not found. Check your .env file.")
    st.stop()



def analyze_report(transcript):
    text = transcript.lower().strip()

    incident_keywords = {
        "Flood": [
            "flood", "flooding", "baadh", "badh", "pravaah",
            "ಪ್ರವಾಹ", "ಪ್ರವಾಹ ಬಂದಿದೆ", "ನೀರು ತುಂಬಿದೆ",
            "बाढ़", "बाढ"
        ],
        "Fire": [
            "fire", "burning", "smoke", "ಬೆಂಕಿ", "आग"
        ],
        "Earthquake": [
            "earthquake", "tremor", "ಭೂಕಂಪ", "भूकंप"
        ],
        "Landslide": [
            "landslide", "ಮಣ್ಣು ಕುಸಿತ", "भूस्खलन"
        ]
    }

    incident_type = "Other / Needs review"

    for incident, keywords in incident_keywords.items():
        if any(keyword in text for keyword in keywords):
            incident_type = incident
            break


    number_words = {
        "one": 1, "two": 2, "three": 3, "four": 4,
        "five": 5, "six": 6, "seven": 7, "eight": 8,
        "nine": 9, "ten": 10,
        "ಒಂದು": 1, "ಎರಡು": 2, "ಮೂರು": 3,
        "ನಾಲ್ಕು": 4, "ಐದು": 5, "ಆರು": 6,
        "ಏಳು": 7, "ಎಂಟು": 8, "ಒಂಬತ್ತು": 9, "ಹತ್ತು": 10,
        "teen": 3, "do": 2, "char": 4, "paanch": 5,
        "एक": 1, "दो": 2, "तीन": 3, "चार": 4,
        "पांच": 5, "पाँच": 5, "छह": 6
    }

    family_patterns = [
        r"(\d+)\s*(?:famil(?:y|ies)|ಕುಟುಂಬಗಳು|परिवार|परिवारों)",
        r"\b(one|two|three|four|five|six|seven|eight|nine|ten)\s+famil(?:y|ies)\b",
        r"\b(ಒಂದು|ಎರಡು|ಮೂರು|ನಾಲ್ಕು|ಐದು|ಆರು|ಏಳು|ಎಂಟು|ಒಂಬತ್ತು|ಹತ್ತು)\s*ಕುಟುಂಬಗಳು",
        r"\b(teen|do|char|paanch)\s+parivar\b",
        r"\b(एक|दो|तीन|चार|पांच|पाँच|छह)\s+परिवार"
    ]

    affected_families = "Not specified"

    for pattern in family_patterns:
        match = re.search(pattern, text)
        if match:
            value = match.group(1)
            affected_families = int(value) if value.isdigit() else number_words.get(value, "Not specified")
            break

    
    supply_keywords = {
        "Food": [
            "food", "meal", "meals", "ration",
            "ಊಟ", "ಆಹಾರ", "ತಿನ್ನಲು", "खाना", "भोजन",
            "khaana", "khana", "oota"
        ],
        "Drinking water": [
            "water", "drinking water", "ಪಾನಿ",
            "ನೀರು", "ಕುಡಿಯೋ ನೀರು", "ಕುಡಿಯುವ ನೀರು",
            "पानी", "पीने का पानी", "paani", "neer"
        ],
        "Rescue assistance": [
            "rescue", "trapped", "stranded", "help immediately",
            "ರಕ್ಷಣೆ", "ಬೇಗ", "ತಕ್ಷಣ", "ಸಹಾಯ",
            "बचाव", "फंसे", "मदद", "bachav", "turant"
        ],
        "Medical supplies": [
            "medical", "medicine", "injured", "doctor",
            "ಔಷಧಿ", "ವೈದ್ಯ", "दवा", "डॉक्टर"
        ]
    }

    required_supplies = []

    for supply, keywords in supply_keywords.items():
        if any(keyword in text for keyword in keywords):
            required_supplies.append(supply)

    if not required_supplies:
        required_supplies = ["Not specified"]

    urgent_keywords = [
        "urgent", "immediately", "immediate", "emergency",
        "trapped", "severe", "critical",
        "ತಕ್ಷಣ", "ಬೇಗ", "ತುರ್ತು", "ಸಿಕ್ಕಿಕೊಂಡಿದ್ದಾರೆ",
        "ಅಪಾಯ", "बहुत ज्यादा", "तुरंत", "आपातकाल",
        "फंसे", "turant", "bahut jyaada", "sikkikondiddare"
    ]

    if any(keyword in text for keyword in urgent_keywords):
        priority = "High — requires verification"
    elif incident_type != "Other / Needs review":
        priority = "Medium — requires verification"
    else:
        priority = "Needs human review"

    return {
        "Incident Type": incident_type,
        "Affected Families": affected_families,
        "Required Supplies": ", ".join(required_supplies),
        "Suggested Priority": priority,
        "Location": "Not provided — ask reporter"
    }



language_options = {
    "English": "en-IN",
    "Hindi": "hi-IN",
    "Telugu": "te-IN",
    "Tamil": "ta-IN",
    "Kannada": "kn-IN",
    "Malayalam": "ml-IN",
    "Marathi": "mr-IN",
    "Bengali": "bn-IN",
    "Gujarati": "gu-IN",
    "Punjabi": "pa-IN"
}

selected_language = st.selectbox(
    "Select the language of your recording",
    options=list(language_options.keys())
)

language = language_options[selected_language]



audio_file = st.file_uploader(
    "Upload a short voice recording",
    type=["wav", "mp3", "flac", "ogg", "m4a"]
)



if audio_file:
    st.audio(audio_file)

    if st.button("Transcribe Voice", type="primary"):
        temp_path = None

        try:
            client = GnaniSTTClient(api_key=api_key)

            suffix = os.path.splitext(audio_file.name)[1]

            with tempfile.NamedTemporaryFile(
                suffix=suffix,
                delete=False
            ) as temp_file:
                temp_file.write(audio_file.getvalue())
                temp_path = temp_file.name

            with st.spinner(
                f"Transcribing your report in {selected_language}..."
            ):
                result = client.transcribe(
                    temp_path,
                    language_code=language
                )

            transcript = result["transcript"]

            # Display the original transcript
            st.divider()
            st.subheader("🗣️ Transcribed Report")
            st.write(transcript)

            st.success("Voice transcription completed!")

            # Extract disaster information
            report = analyze_report(transcript)

            st.divider()
            st.subheader("📋 Extracted Disaster Report")

            st.write("**Incident Type:**", report["Incident Type"])
            st.write("**Affected Families:**", report["Affected Families"])
            st.write("**Required Supplies:**", report["Required Supplies"])
            st.write("**Suggested Priority:**", report["Suggested Priority"])
            st.write("**Location:**", report["Location"])

            st.warning(
                "This is an automatically generated draft. "
                "Verify the details and location with a human "
                "before treating it as a confirmed incident."
            )

            st.info(
                "This report has not been saved or submitted yet."
            )

        except Exception as error:
            st.error(
                "Processing failed. Check language support, API "
                "credentials, network connection, audio format "
                "and API usage."
            )
            st.caption(f"Error details: {error}")

        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
