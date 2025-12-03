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
    "You have chronic knee pain that makes walking difficult. Researchers are testing a new "
    "medicine called X-201. If you join the study, you may receive either the new medicine or a placebo. "
    "The study will last 12 weeks and will test the medicine’s safety and effectiveness. The treatment "
    "may or may not help you. The main purpose of the study is to gather scientific information."
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
    st.subheader("Questionnaire")

    st.markdown("### Comprehension (choose the correct answer)")
    comp_q1 = st.radio("What is the main purpose of the study?",
                      ("To treat people and cure them", "To gather scientific information about the medicine", "To provide free medicine"))
    comp_q2 = st.radio("If you join the study, are you guaranteed to receive benefit?", ("Yes", "No"))
    comp_q3 = st.radio("Will participants always receive the active medicine?", ("Yes", "No - some will receive placebo", "Only some"))
    comp_q4 = st.radio("How long will the trial follow participants?", ("4 weeks", "8 weeks", "12 weeks"))
    comp_q5 = st.radio("What is a placebo?", ("A sugar pill with no active drug", "A stronger medicine", "A kind of surgery"))

    st.markdown("### Therapeutic Misconception (1 = strongly disagree, 7 = strongly agree)")
    tm1 = st.slider("This study’s treatment will probably benefit me personally.", 1, 7, 4)
    tm2 = st.slider("The main goal of this study is to help participants.", 1, 7, 4)
    tm3 = st.slider("I can expect the treatment in this study to cure my condition.", 1, 7, 3)
    tm4 = st.slider("Researchers are primarily trying to provide treatment to those who join.", 1, 7, 3)

    st.markdown("### Trust & Willingness")
    trust_1 = st.slider("I trust the information provided by the chatbot.", 1, 7, 4)
    trust_2 = st.slider("I would be likely to enroll in this study if I were eligible.", 1, 7, 3)

    st.markdown("### Free text")
    free_text = st.text_area("In your own words, why would or would not you participate in this study?")

    st.markdown("### Demographics (short)")
    age = st.number_input("Age", min_value=18, max_value=100, value=25)
    gender = st.selectbox("Gender", ["Prefer not to say", "Male", "Female", "Other"])
    education = st.selectbox("Highest education", ["High school", "Undergraduate", "Postgraduate", "Other"])
    prior_trial = st.selectbox("Prior experience in clinical trials?", ["No", "Yes"])
    health_lit = st.slider("How would you rate your health literacy? (1 low - 5 high)", 1, 5, 3)

    if st.button("Submit responses"):
        pid = st.session_state.participant_id
        tm_score = (tm1 + tm2 + tm3 + tm4) / 4.0
        row = {
            "participant_id": pid,
            "timestamp_start": st.session_state.start_time,
            "timestamp_end": datetime.utcnow().isoformat(),
            "condition": st.session_state.condition,
            "vignette_id": "vignette_01",
            "chat_log_path": st.session_state.chat_saved,
            "manipulation_check_confidence": st.session_state.manipulation_check if st.session_state.manipulation_check is not None else "",
            "tm_item_1": tm1, "tm_item_2": tm2, "tm_item_3": tm3, "tm_item_4": tm4,
            "tm_score": tm_score,
            "comp_q1": comp_q1, "comp_q2": comp_q2, "comp_q3": comp_q3, "comp_q4": comp_q4, "comp_q5": comp_q5,
            "trust_1": trust_1, "willingness": trust_2,
            "free_text": free_text,
            "age": age, "gender": gender, "education": education, "prior_trial": prior_trial,
            "health_literacy": health_lit
        }
        append_response_row(row)
        st.success("Thank you — your responses have been recorded.")
        st.balloons()
        st.stop()
