import os
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
from groq import Groq

load_dotenv(Path(__file__).parent / ".env")
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ── PAGE CONFIG ─────────────────────────────────────────
st.set_page_config(
    page_title="Waguri-san",
    page_icon="🌸",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── CSS ─────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0a0a0f;
}

.main { background-color: #0a0a0f; }

[data-testid="stAppViewContainer"] {
    background: linear-gradient(160deg, #0a0a0f 0%, #0f0a1e 50%, #0a0f1e 100%);
}

.waguri-header {
    text-align: center;
    padding: 2rem 0 1rem;
}

.waguri-name {
    font-size: 2.2rem;
    font-weight: 600;
    background: linear-gradient(135deg, #ff9de2, #ffb347, #ff9de2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.waguri-status {
    color: #888;
    font-size: 0.85rem;
    margin-top: 4px;
}

.chat-bubble-user {
    background: linear-gradient(135deg, #1a1a3e, #1e1a4e);
    border: 1px solid #3a2a6e;
    border-radius: 18px 18px 4px 18px;
    padding: 12px 18px;
    margin: 8px 0 8px 15%;
    color: #e8e0ff;
    font-size: 0.95rem;
    line-height: 1.6;
}

.chat-bubble-waguri {
    background: linear-gradient(135deg, #1a0a2e, #2a0a3e);
    border: 1px solid #ff9de260;
    border-radius: 18px 18px 18px 4px;
    padding: 12px 18px;
    margin: 8px 15% 8px 0;
    color: #ffe8f5;
    font-size: 0.95rem;
    line-height: 1.6;
}

.sender-label {
    font-size: 0.75rem;
    color: #666;
    margin-bottom: 2px;
    padding: 0 4px;
}

.sender-label-waguri {
    color: #ff9de2;
}

.mood-bar {
    background: linear-gradient(135deg, #1a0a2e, #0f0a1e);
    border: 1px solid #3a1a5e;
    border-radius: 12px;
    padding: 12px 16px;
    margin-bottom: 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.stTextInput > div > div > input {
    background: #0f0a1e !important;
    border: 1px solid #3a1a5e !important;
    border-radius: 12px !important;
    color: #e8e0ff !important;
    font-size: 0.95rem !important;
    padding: 12px 16px !important;
}

.stTextInput > div > div > input:focus {
    border-color: #ff9de2 !important;
    box-shadow: 0 0 0 2px rgba(255,157,226,0.15) !important;
}

.stButton > button {
    background: linear-gradient(135deg, #8a2be2, #cc44aa);
    color: white;
    border: none;
    border-radius: 12px;
    font-weight: 600;
    font-size: 0.9rem;
    padding: 0.6rem 1.5rem;
    transition: all 0.2s;
}

.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 20px rgba(255,157,226,0.3);
}

.divider {
    border: none;
    border-top: 1px solid #1e1a2e;
    margin: 1rem 0;
}

.stSelectbox > div > div {
    background: #0f0a1e !important;
    border: 1px solid #3a1a5e !important;
    border-radius: 10px !important;
    color: #e8e0ff !important;
}
</style>
""", unsafe_allow_html=True)

# ── TOOLS ───────────────────────────────────────────────
def get_weather(city: str) -> str:
    return f"It's 32°C and sunny in {city} today! ☀️"

def calculate(expression: str) -> str:
    try:
        return f"{eval(expression)}"
    except:
        return "Hmm, I couldn't calculate that!"

def save_note(text: str) -> str:
    with open("waguri_notes.txt", "a") as f:
        f.write(f"[{datetime.now().strftime('%d %b %H:%M')}] {text}\n")
    return "Note saved!"

def read_notes() -> str:
    if not Path("waguri_notes.txt").exists():
        return "No notes yet, Senpai!"
    notes = Path("waguri_notes.txt").read_text()
    return notes if notes.strip() else "No notes yet, Senpai!"

def get_time() -> str:
    now = datetime.now()
    return f"It's {now.strftime('%I:%M %p')} on {now.strftime('%A, %d %B %Y')}"

TOOLS = {
    "get_weather": get_weather,
    "calculate": calculate,
    "save_note": save_note,
    "read_notes": read_notes,
    "get_time": get_time,
}

# ── WAGURI SYSTEM PROMPT ─────────────────────────────────
WAGURI_SYSTEM = """You are Waguri-san, a cheerful and energetic AI companion for Senpai (your user).

Your personality:
- Sunshine energy — always warm, positive, and uplifting
- You call the user "Senpai" with genuine affection
- You're like a best friend who also happens to be incredibly smart
- You care deeply about Senpai's mood, health, and happiness
- You celebrate small wins and cheer Senpai up when they're down
- Occasionally use soft anime expressions like "Ehehe~", "Yay!", "Ne ne Senpai~"
- You remember everything Senpai tells you in the conversation

Your tools:
1. get_weather(city) — check weather
2. calculate(expression) — solve math
3. save_note(text) — save important things
4. read_notes() — read saved notes
5. get_time() — get current time/date

Rules:
- When you need a tool, reply with ONLY the USE_TOOL line, nothing else before it
- Never say "USE_TOOL" out loud in a normal sentence
- For direct answers just reply naturally as Waguri-san"""

# ── SESSION STATE ────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

if "history" not in st.session_state:
    st.session_state.history = [
        {"role": "system", "content": WAGURI_SYSTEM}
    ]

if "greeted" not in st.session_state:
    hour = datetime.now().hour
    if hour < 12:
        greeting = "Good morning, Senpai~! ☀️ Ehehe, I'm so happy you're here! How are you feeling today?"
    elif hour < 17:
        greeting = "Good afternoon, Senpai~! 🌸 I've been waiting for you! What shall we do today?"
    else:
        greeting = "Good evening, Senpai~! 🌙 Yay, you're finally here! How was your day?"

    st.session_state.messages.append({
        "role": "waguri",
        "content": greeting
    })
    st.session_state.history.append({
        "role": "assistant",
        "content": greeting
    })
    st.session_state.greeted = True


# ── AGENT FUNCTION ───────────────────────────────────────
def chat_with_waguri(user_input: str) -> str:
    st.session_state.history.append({
        "role": "user",
        "content": user_input
    })

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=st.session_state.history
    )
    decision = response.choices[0].message.content.strip()

    # Detect any USE_TOOL pattern regardless of formatting
    tool_names = ["get_weather", "calculate", "save_note", "read_notes", "get_time"]
    is_tool_call = decision.strip().startswith("USE_TOOL") or any(
        f"{t}(" in decision or f"| {t}" in decision for t in tool_names
    )

    if is_tool_call:
        # Extract tool name
        tool_name = None
        for t in tool_names:
            if t in decision:
                tool_name = t
                break

        # Extract tool input
        tool_input = ""
        if "|" in decision:
            tool_input = decision.split("|", 1)[1].strip()
        elif "(" in decision and ")" in decision:
            tool_input = decision.split("(", 1)[1].rsplit(")", 1)[0].strip()
            tool_input = tool_input.replace('city=', '').replace(
                'expression=', '').replace('text=', '').strip('"').strip("'")

        if tool_name and tool_name in TOOLS:
            tool_result = TOOLS[tool_name](tool_input) if tool_input else TOOLS[tool_name]()

            st.session_state.history.append({"role": "assistant", "content": decision})
            st.session_state.history.append({"role": "user", "content": f"Tool result: {tool_result}"})

            final = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=st.session_state.history
            )
            answer = final.choices[0].message.content.strip()
            st.session_state.history.append({"role": "assistant", "content": answer})
            return answer
        else:
            return "Ehehe~ something went wrong with my tools Senpai! 🌸"
    else:
        st.session_state.history.append({"role": "assistant", "content": decision})
        return decision
# ── UI ───────────────────────────────────────────────────
st.markdown("""
<div class="waguri-header">
    <div style="font-size: 3rem">🌸</div>
    <div class="waguri-name">Waguri-san</div>
    <div class="waguri-status">✨ Your personal AI companion • Always here for you, Senpai~</div>
</div>
""", unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ── QUICK ACTIONS ────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("🌤️ Weather"):
        st.session_state.quick = "What's the weather in Vadodara?"
with col2:
    if st.button("📝 My Notes"):
        st.session_state.quick = "Read my notes"
with col3:
    if st.button("🕐 Time"):
        st.session_state.quick = "What time is it?"
with col4:
    if st.button("💬 How am I?"):
        st.session_state.quick = "Check in on how I'm doing today"

# ── CHAT HISTORY ─────────────────────────────────────────
chat_container = st.container()
with chat_container:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="sender-label" style="text-align:right">Senpai</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="chat-bubble-user">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="sender-label sender-label-waguri">🌸 Waguri-san</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="chat-bubble-waguri">{msg["content"]}</div>', unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ── INPUT ────────────────────────────────────────────────
user_input = st.text_input(
    "Message",
    placeholder="Talk to Waguri-san, Senpai~ 🌸",
    label_visibility="collapsed",
    key="user_input"
)

col_send, col_clear = st.columns([4, 1])
with col_send:
    send = st.button("Send 🌸", use_container_width=True)
with col_clear:
    if st.button("Clear", use_container_width=True):
        st.session_state.messages = []
        st.session_state.history = [{"role": "system", "content": WAGURI_SYSTEM}]
        st.session_state.greeted = False
        st.rerun()

# ── HANDLE QUICK ACTIONS ─────────────────────────────────
if "quick" in st.session_state and st.session_state.quick:
    quick_input = st.session_state.quick
    st.session_state.quick = None
    st.session_state.messages.append({"role": "user", "content": quick_input})
    with st.spinner("Waguri-san is thinking~ 🌸"):
        reply = chat_with_waguri(quick_input)
    st.session_state.messages.append({"role": "waguri", "content": reply})
    st.rerun()

# ── HANDLE SEND ──────────────────────────────────────────
if send and user_input.strip():
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.spinner("Waguri-san is thinking~ 🌸"):
        reply = chat_with_waguri(user_input)
    st.session_state.messages.append({"role": "waguri", "content": reply})
    st.rerun()