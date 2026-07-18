import os
import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
from groq import Groq
from tavily import TavilyClient
from elevenlabs.client import ElevenLabs
import base64

load_dotenv(Path(__file__).parent / ".env")

app = FastAPI()

# Allow Next.js frontend to call this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
el_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

# ── TOOLS ────────────────────────────────────────────────
def calculate(expression: str) -> str:
    try:
        return f"{eval(expression)}"
    except:
        return "Couldn't calculate that!"

def save_note(text: str) -> str:
    with open("waguri_notes.txt", "a") as f:
        f.write(f"[{datetime.now().strftime('%d %b %H:%M')}] {text}\n")
    return "Note saved!"

def read_notes() -> str:
    if not Path("waguri_notes.txt").exists():
        return "No notes yet!"
    notes = Path("waguri_notes.txt").read_text()
    return notes if notes.strip() else "No notes yet!"

def get_time() -> str:
    now = datetime.now()
    return f"It's {now.strftime('%I:%M %p')} on {now.strftime('%A, %d %B %Y')}"

def search_web(query: str) -> str:
    try:
        results = tavily.search(query=query, max_results=3)
        answers = []
        for r in results["results"]:
            answers.append(f"{r['title']}: {r['content'][:200]}")
        return "\n".join(answers)
    except Exception as e:
        return f"Search failed: {e}"

TOOLS = {
    "calculate": calculate,
    "save_note": save_note,
    "read_notes": read_notes,
    "get_time": get_time,
    "search_web": search_web,
}

WAGURI_SYSTEM = """You are Waguri-san, a cheerful and energetic AI companion for Senpai.

Your personality:
- Sunshine energy — always warm, positive, and uplifting
- You call the user "Senpai" with genuine affection
- You're like a best friend who is also incredibly smart
- You care deeply about Senpai's mood, health, and happiness
- Occasionally use soft expressions like "Ehehe", "Yay", "Ne ne Senpai"
- You remember everything Senpai tells you

Your tools:
1. calculate(expression) — solve math
2. save_note(text) — save important things
3. read_notes() — read saved notes
4. get_time() — get current time/date
5. search_web(query) — search internet for real info, news, weather

Rules:
- When you need a tool reply ONLY: USE_TOOL: tool_name | input
- For read_notes or get_time: USE_TOOL: read_notes |
- Never say USE_TOOL out loud in a normal sentence
- Use search_web for any real world question
- For direct answers just reply naturally as Waguri-san"""

# ── REQUEST MODELS ────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    history: list

class VoiceRequest(BaseModel):
    text: str

# ── CHAT ENDPOINT ─────────────────────────────────────────
@app.post("/chat")
async def chat(req: ChatRequest):
    history = [{"role": "system", "content": WAGURI_SYSTEM}] + req.history
    history.append({"role": "user", "content": req.message})

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=history
    )
    decision = response.choices[0].message.content.strip()

    tool_names = ["calculate", "save_note", "read_notes", "get_time", "search_web"]
    is_tool_call = decision.strip().startswith("USE_TOOL") or any(
        f"{t}(" in decision or f"| {t}" in decision for t in tool_names
    )

    if is_tool_call:
        tool_name = None
        for t in tool_names:
            if t in decision:
                tool_name = t
                break

        tool_input = ""
        if "|" in decision:
            tool_input = decision.split("|", 1)[1].strip()
        elif "(" in decision and ")" in decision:
            tool_input = decision.split("(", 1)[1].rsplit(")", 1)[0].strip()
            tool_input = tool_input.replace('expression=', '').replace(
                'text=', '').replace('query=', '').strip('"').strip("'")

        if tool_name and tool_name in TOOLS:
            tool_result = TOOLS[tool_name](tool_input) if tool_input else TOOLS[tool_name]()

            history.append({"role": "assistant", "content": decision})
            history.append({"role": "user", "content": f"Tool result: {tool_result}"})

            final = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=history
            )
            answer = final.choices[0].message.content.strip()
            return {"reply": answer}

    return {"reply": decision}

# ── VOICE ENDPOINT ────────────────────────────────────────
@app.post("/voice")
async def voice(req: VoiceRequest):
    try:
        clean = re.sub(r'[~!*\-]+', ' ', req.text)
        clean = re.sub(r'[^\w\s\.,?\']+', '', clean)
        clean = re.sub(r'\s+', ' ', clean).strip()

        audio = el_client.text_to_speech.convert(
            voice_id="EXAVITQu4vr4xnSDxMaL",
            text=clean,
            model_id="eleven_turbo_v2",
        )
        audio_bytes = b"".join(chunk for chunk in audio if chunk)
        audio_b64 = base64.b64encode(audio_bytes).decode()
        return {"audio": audio_b64}
    except Exception as e:
        return {"error": str(e)}

# ── GREETING ENDPOINT ─────────────────────────────────────
@app.get("/greeting")
async def greeting():
    hour = datetime.now().hour
    if hour < 12:
        msg = "Good morning, Senpai! Ehehe, I'm so happy you're here! How are you feeling today?"
    elif hour < 17:
        msg = "Good afternoon, Senpai! I've been waiting for you! What shall we do today?"
    else:
        msg = "Good evening, Senpai! Yay, you're finally here! How was your day?"
    return {"greeting": msg}

@app.get("/")
async def root():
    return {"status": "Waguri-san backend is running!"}