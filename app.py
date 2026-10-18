
import re
import os
import tempfile
import sqlite3
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
from gnani.stt import GnaniSTTClient
from gnani.tts import GnaniTTSClient


DB_PATH = "disaster_reports.db"


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                language TEXT NOT NULL,
                transcript TEXT NOT NULL,
                incident_type TEXT NOT NULL,
                affected_families TEXT NOT NULL,
                required_supplies TEXT NOT NULL,
                suggested_priority TEXT NOT NULL,
                location TEXT NOT NULL,
                verification_status TEXT NOT NULL
                    DEFAULT 'Pending Verification'
            )
        """)


def save_report(language, transcript, report):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("""
            INSERT INTO reports (
                created_at, language, transcript,
                incident_type, affected_families,
                required_supplies, suggested_priority,
                location, verification_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().astimezone().isoformat(timespec="seconds"),
            language,
            transcript,
            str(report["Incident Type"]),
            str(report["Affected Families"]),
            str(report["Required Supplies"]),
            str(report["Suggested Priority"]),
            str(report["Location"]),
            "Pending Verification"
        ))

        return cursor.lastrowid


def get_saved_reports():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute("""
            SELECT id, created_at, language, transcript,
                   incident_type, affected_families,
                   required_supplies, suggested_priority,
                   location, verification_status
            FROM reports
            ORDER BY id DESC
        """).fetchall()

        return [dict(row) for row in rows]


def update_verification_status(report_id, new_status):
    allowed_statuses = ["Verified", "Rejected"]

    if new_status not in allowed_statuses:
        raise ValueError("Invalid verification status")

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("""
            UPDATE reports
            SET verification_status = ?
            WHERE id = ?
        """, (new_status, report_id))

        return cursor.rowcount > 0



init_db()




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

    # Identify the incident type.
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

    # Recognize numbers written as words.
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

            if value.isdigit():
                affected_families = int(value)
            else:
                affected_families = number_words.get(
                    value, "Not specified"
                )

            break

    # Identify required supplies.
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

    # Suggest a priority for human verification.
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


# # STEP 2 TEST
# test_transcript = (
#     "There is a flood near the main road. "
#     "Three families are affected. "
#     "They need drinking water and food urgently."
# )

# test_result = analyze_report(test_transcript)
# st.write("Extraction Test:", test_result)


# --------------------------------------------------
# 4. LANGUAGE SELECTION
# --------------------------------------------------

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


# --------------------------------------------------
# 5. AUDIO UPLOAD AND GNANI AI TRANSCRIPTION
# --------------------------------------------------

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
            
            # Extract disaster information.
            report = analyze_report(transcript)

            # Store results across Streamlit reruns.
            st.session_state["last_transcript"] = transcript
            st.session_state["last_report"] = report
            st.session_state["last_language"] = selected_language
            st.session_state["saved_report_id"] = None

            st.success("Voice transcription completed!")

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


# --------------------------------------------------
# 6. DISPLAY TRANSCRIPTION AND EXTRACTED REPORT
# --------------------------------------------------

if (
    st.session_state.get("last_transcript")
    and st.session_state.get("last_report")
):
    transcript = st.session_state["last_transcript"]
    report = st.session_state["last_report"]

    st.divider()
    st.subheader("🗣️ Transcribed Report")
    st.write(transcript)

    st.subheader("📋 Extracted Disaster Report")

    st.write("**Incident Type:**", report["Incident Type"])
    st.write("**Affected Families:**", report["Affected Families"])
    st.write("**Required Supplies:**", report["Required Supplies"])
    st.write("**Suggested Priority:**", report["Suggested Priority"])
    st.write("**Location:**", report["Location"])

    st.warning(
        "This is an automatically generated draft. Verify the "
        "details and location with a human before treating it "
        "as a confirmed incident."
    )

    # --------------------------------------------------
    # 7. SAVE REPORT TO SQLITE
    # --------------------------------------------------

    st.divider()
    st.subheader("💾 Save Disaster Report")

    st.write("Review the extracted details before saving.")

    st.caption(
        "Saving creates a local draft only. It does not notify "
        "emergency services."
    )

    if st.session_state.get("saved_report_id") is None:
        if st.button("Save Report to Database", type="primary"):
            try:
                report_id = save_report(
                    st.session_state["last_language"],
                    transcript,
                    report
                )

                st.session_state["saved_report_id"] = report_id

                st.success(
                    f"Report #{report_id} saved successfully!"
                )

                st.rerun()

            except Exception as error:
                st.error("Could not save the report.")
                st.caption(f"Error details: {error}")

    else:
        st.success(
            f"Report #{st.session_state['saved_report_id']} "
            "has already been saved."
        )


# --------------------------------------------------
# 8. SAVED DISASTER REPORTS DASHBOARD
# --------------------------------------------------

st.divider()
st.header("📊 Saved Disaster Reports")


try:
    saved_reports = get_saved_reports()

    if saved_reports:
        total_reports = len(saved_reports)

        pending_reports = sum(
            report["verification_status"] == "Pending Verification"
            for report in saved_reports
        )

        # Dashboard metrics
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Total Reports", total_reports)

        with col2:
            st.metric("Pending Verification", pending_reports)

        # Display saved reports in a table
        dashboard_rows = [
            {
                "Report ID": row["id"],
                "Created At": row["created_at"],
                "Language": row["language"],
                "Incident Type": row["incident_type"],
                "Affected Families": row["affected_families"],
                "Required Supplies": row["required_supplies"],
                "Suggested Priority": row["suggested_priority"],
                "Location": row["location"],
                "Status": row["verification_status"],
            }
            for row in saved_reports
        ]

        st.dataframe(
            dashboard_rows,
            use_container_width=True,
            hide_index=True,
        )

        # View individual report details
        st.subheader("🔎 View Report Details")

        report_ids = [row["id"] for row in saved_reports]

        selected_report_id = st.selectbox(
            "Select a report",
            options=report_ids,
            format_func=lambda report_id: f"Report #{report_id}",
        )

        selected_report = next(
            row for row in saved_reports
            if row["id"] == selected_report_id
        )

        # Display report information
        st.write("**Original Transcript:**")
        st.write(selected_report["transcript"])

        st.write("**Language:**", selected_report["language"])
        st.write("**Incident Type:**", selected_report["incident_type"])

        st.write(
            "**Affected Families:**",
            selected_report["affected_families"],
        )

        st.write(
            "**Required Supplies:**",
            selected_report["required_supplies"],
        )

        st.write(
            "**Suggested Priority:**",
            selected_report["suggested_priority"],
        )

        st.write("**Location:**", selected_report["location"])

        st.write(
            "**Verification Status:**",
            selected_report["verification_status"],
        )

        st.write("**Created At:**", selected_report["created_at"])

        # Human verification section
        st.divider()
        st.subheader("🛡️ Human Verification")

        current_status = selected_report["verification_status"]

        if current_status == "Pending Verification":
            col1, col2 = st.columns(2)

            with col1:
                if st.button(
                    "✅ Mark as Verified",
                    key=f"verify_{selected_report_id}",
                ):
                    updated = update_verification_status(
                        selected_report_id, "Verified"
                    )

                    if updated:
                        st.success("Report marked as Verified.")
                        st.rerun()
                    else:
                        st.error("Could not update this report.")

            with col2:
                if st.button(
                    "❌ Reject Report",
                    key=f"reject_{selected_report_id}",
                ):
                    updated = update_verification_status(
                        selected_report_id, "Rejected"
                    )

                    if updated:
                        st.success("Report marked as Rejected.")
                        st.rerun()
                    else:
                        st.error("Could not update this report.")

        else:
            st.info(
                f"This report has already been marked as: {current_status}"
            )

    else:
        st.info("No disaster reports have been saved yet.")

except Exception as error:
    st.error("Could not load the saved reports dashboard.")
    st.caption(f"Error details: {error}")
