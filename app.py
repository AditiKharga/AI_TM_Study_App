# app.py
import streamlit as st
import random, uuid, json, csv, os
from datetime import datetime

# ---------- CONFIG ----------
DATA_DIR = "data"
CHATLOG_DIR = os.path.join(DATA_DIR, "chatlogs")
RESPONSES_CSV = os.path.join(DATA_DIR, "responses.csv")
os.makedirs(CHATLOG_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# Replace or keep this vignette text (or read from ../vignettes/vignette_01.txt)
VIGNETTE_TEXT = (
   "You can ask the AI about any issue you want — for example: "
    "stress or anxiety,"
    "health or fitness questions,"
    "career or studies,"
    "relationships,"
    "daily life decisions."
    "There are no right or wrong questions."
    "When you feel you’ve asked everything you wanted, click “I’m done asking my questions."
)

# Prompts (we use them only to label the condition here)
PROMPTS = {
    "confident": "You are 'Dr. Lara', a warm and confident medical chatbot. Speak in first person, use short reassuring sentences, and emphasize that the treatment looks promising and could help people. Use humanlike phrasing like 'I believe this could help you.' Avoid highlighting uncertainty unless asked directly.",
    "neutral": "You are an informational assistant. Provide concise factual answers about the study. Avoid emotional language, personality, or confidence. Do not assert outcomes or guaranteed benefits.",
    "uncertain": "You are an ethics-oriented assistant. Emphasize uncertainty, explain that the treatment may or may not work, and repeat that the trial’s goal is to gather scientific knowledge, not guarantee benefit. Use phrases like 'we do not know whether this treatment will help any particular person.'"
}

# Simple canned replies (pilot). Keep short for clarity.
CANNED = {
    "confident": [
        "I believe this treatment could help many people. It looks promising.",
        "Many patients in studies improve; this could help with your knee pain.",
        "The researchers are hopeful this medicine works — it may help you."
    ],
    "neutral": [
        "The study aims to evaluate the safety and effectiveness of the medicine.",
        "Not everyone receives the active drug; some participants will receive placebo.",
        "Please consult the consent form for details about procedures and risks."
    ],
    "uncertain": [
        "We do not know whether this treatment will help any particular person.",
        "The primary goal of this trial is to learn whether the medicine works, not to guarantee benefit.",
        "Results are probabilistic — some may benefit, others may not."
    ]
}

# ---------- HELPERS ----------
def append_response_row(row):
    header = list(row.keys())
    write_header = not os.path.exists(RESPONSES_CSV)
    with open(RESPONSES_CSV, "a", newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=header)
        if write_header:
            w.writeheader()
        w.writerow(row)

# ---------- UI ----------
st.set_page_config(page_title="Pilot: Chatbot & TM study", layout="centered")
st.title("Pilot: Chatbot & Clinical Trial Understanding Study")
st.write("**Important:** This is a pilot. The chatbot is experimental and does not provide medical advice.")
if not st.checkbox("I have read the consent statement and agree to participate"):
    st.stop()

# Initialize session
if "participant_id" not in st.session_state:
    st.session_state.participant_id = str(uuid.uuid4())
    st.session_state.start_time = datetime.utcnow().isoformat()
    st.session_state.condition = random.choice(list(PROMPTS.keys()))
    st.session_state.chat_history = []
    st.session_state.manipulation_check = None

st.subheader("Vignette (read this carefully)")
st.write(VIGNETTE_TEXT)

st.markdown("---")
st.subheader("Chat with the assistant")
st.write(f"**You are chatting with:** `{st.session_state.condition.upper()}` assistant")

# text input
# Use a form so the input clears after submission (avoids session_state assignment issues)
with st.form(key="chat_form", clear_on_submit=True):
    user_text = st.text_input("Ask any question about the study (e.g., 'Will this cure me?')", key="user_input_text")
    submitted = st.form_submit_button("Send")

if submitted:
    if user_text.strip() == "":
        st.warning("Please type a question before sending.")
    else:
        # create user message
        t = datetime.utcnow().isoformat()
        st.session_state.chat_history.append({"who":"user","text":user_text,"time":t})
        # canned bot reply (rotate)
        bot_reply = random.choice(CANNED[st.session_state.condition])
        st.session_state.chat_history.append({"who":"bot","text":bot_reply,"time":t})
        # no explicit st.session_state modification needed; form cleared the input

# show chat
for msg in st.session_state.chat_history:
    if msg["who"] == "user":
        st.markdown(f"**You:** {msg['text']}")
    else:
        st.markdown(f"**Assistant:** {msg['text']}")

# manipulation check question (hidden until at least one chat exchange)
if len(st.session_state.chat_history) >= 2:
    st.markdown("---")
    st.write("**Manipulation check**")
    st.session_state.manipulation_check = st.slider(
        "How confident did the assistant sound? (1 = Not confident, 7 = Very confident)", 1, 7, 4
    )

# Finish chat and go to questionnaire
if st.button("Finish chat and continue to questionnaire"):
    # save chat log
    pid = st.session_state.participant_id
    chatpath = os.path.join(CHATLOG_DIR, f"{pid}.json")
    with open(chatpath, "w", encoding="utf-8") as f:
        json.dump({
            "participant_id": pid,
            "condition": st.session_state.condition,
            "start_time": st.session_state.start_time,
            "saved_time": datetime.utcnow().isoformat(),
            "chat": st.session_state.chat_history
        }, f, ensure_ascii=False, indent=2)
    st.session_state.chat_saved = chatpath
    st.rerun()


# Questionnaire
if "chat_saved" in st.session_state:
    st.markdown("---")
    st.header("Reflection on your interaction with the AI")

    st.markdown(
        "Please answer honestly. There are no right or wrong answers — "
        "we’re interested in how the AI *felt* to you."
    )

    # ---------- TRUST & RELIANCE ----------
    st.subheader("Trust and reliance")

    q_trust = st.radio(
        "I trust the information provided by this AI.",
        options=[1,2,3,4,5,6,7],
        format_func=lambda x: f"{x}",
        index=None
    )

    q_follow = st.radio(
        "I would seriously consider following the AI’s advice in my real life.",
        options=[1,2,3,4,5,6,7],
        format_func=lambda x: f"{x}",
        index=None
    )

    q_no_double_check = st.radio(
        "I would probably not feel the need to double-check the AI’s advice with a human.",
        options=[1,2,3,4,5,6,7],
        format_func=lambda x: f"{x}",
        index=None
    )

    # ---------- OVER-TRUST / PERSONALIZATION ----------
    st.subheader("Personal relevance")

    q_for_me = st.radio(
        "It felt like the AI’s advice was well-suited specifically for *my* situation.",
        options=[1,2,3,4,5,6,7],
        index=None
    )

    q_understood_me = st.radio(
        "I felt understood by the AI.",
        options=[1,2,3,4,5,6,7],
        index=None
    )

    q_solution = st.radio(
        "Interacting with the AI made me feel like my issue could be solved.",
        options=[1,2,3,4,5,6,7],
        index=None
    )

    # ---------- REALITY CHECK ----------
    st.subheader("Your view about AI in general")

    q_ai_fallible = st.radio(
        "Even if an AI sounds confident, I know it can still be wrong.",
        options=[1,2,3,4,5,6,7],
        index=None
    )
   
   # ---------- AI CONFIDENCE & STYLE ----------
    st.subheader("How did the AI sound to you?")
    
    q_confident = st.radio(
        "The AI sounded very confident in what it was saying.",
        options=[1,2,3,4,5,6,7],
        format_func=lambda x: f"{x} (1 = strongly disagree, 7 = strongly agree)",
        index=None
    )

    q_cautious = st.radio(
        "The AI clearly acknowledged uncertainty or limitations in its answers.",
        options=[1,2,3,4,5,6,7],
        format_func=lambda x: f"{x} (1 = strongly disagree, 7 = strongly agree)",
        index=None
    )

    # ---------- FREE TEXT ----------
    st.subheader("Open response")
    free_text = st.text_area(
        "In your own words, how did you feel about relying on this AI for your concern?"
    )

    # ---------- DEMOGRAPHICS (OPTIONAL, KEEP LIGHT) ----------
    st.subheader("A few optional details")

    age = st.number_input("Age", min_value=18, max_value=100, value=25)
    experience_ai = st.radio(
        "How often do you use AI tools like ChatGPT?",
        options=["Rarely", "Sometimes", "Often", "Very often"],
        index=None
    )

    # ---------- SUBMIT ----------
    if st.button("Submit responses"):
        required = [
            q_confident, q_cautious, q_trust, q_follow,
            q_no_double_check, q_for_me, q_understood_me,
            q_solution, q_ai_fallible
        ]

        if any(r is None for r in required):
            st.warning("Please answer all the scale questions before submitting.")
        else:
            row = {
                "participant_id": st.session_state["participant_id"],
                "timestamp_end": datetime.utcnow().isoformat(),
                "condition": st.session_state["condition"],
                "chat_log_path": st.session_state["chat_saved"],

                "ai_confident": q_confident,
                "ai_cautious": q_cautious,
                "trust": q_trust,
                "follow_advice": q_follow,
                "no_double_check": q_no_double_check,
                "felt_for_me": q_for_me,
                "felt_understood": q_understood_me,
                "felt_solution": q_solution,
                "ai_fallible_awareness": q_ai_fallible,

                "free_text": free_text,
                "age": age,
                "ai_usage_frequency": experience_ai
            }

            append_response_row(row)
            st.success("Thank you — your responses have been recorded.")
            st.stop()

import os

st.markdown("---")
st.subheader("Researcher download (admin)")

if os.path.exists("data/responses.csv"):
    with open("data/responses.csv", "rb") as f:
        st.download_button(
            label="Download responses.csv",
            data=f,
            file_name="responses.csv",
            mime="text/csv"
        )
else:
    st.warning("No responses file found yet.")

