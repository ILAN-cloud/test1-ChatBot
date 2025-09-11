import os, json
from typing import Optional, Literal

from fastapi import FastAPI, UploadFile, File, Form, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx
from dotenv import load_dotenv

# Local services (fichiers Python fournis dans ton projet)
import stt, tts
from storage import save_public_bytes
from email import send_email  # ton email.py (⚠️ garde le fichier à la racine du backend)

# Charger .env
load_dotenv()

# === App & CORS ===
app = FastAPI(title="ChatIA — Mono-tenant (sans Stripe / sans plans)")
origins_env = os.getenv("ALLOW_ORIGINS", "*")
allow_origins = [o.strip() for o in origins_env.split(",")] if origins_env else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static pour MP3 publics
PUBLIC_DIR = os.path.join(os.path.dirname(__file__), "public")
os.makedirs(PUBLIC_DIR, exist_ok=True)
app.mount("/public", StaticFiles(directory=PUBLIC_DIR), name="public")

PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")

# === OpenAI ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")

# === Prompt de spécialisation (mono-tenant) ===
SPECIAL_PROMPT = os.getenv(
    "SPECIAL_PROMPT",
    "Tu es un assistant utile, clair et concis."
)

async def openai_chat(messages, temperature: float = 0.3) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY manquant")
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": OPENAI_CHAT_MODEL, "messages": messages, "temperature": temperature}
    async with httpx.AsyncClient(timeout=180) as client:
        r = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()

# === Santé
@app.get("/health")
async def health():
    return {"ok": True}

# === Schémas commande / résa / intent ===
class OrderItem(BaseModel):
    name: str
    quantity: int = Field(gt=0)
    notes: Optional[str] = None

class OrderIn(BaseModel):
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    items: list[OrderItem]
    delivery: Literal["pickup","delivery"] = "pickup"
    address: Optional[str] = None
    desired_time: Optional[str] = None  # ex: "2025-09-10 19:30"
    notes: Optional[str] = None

class ReservationIn(BaseModel):
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    people: int = Field(gt=0)
    date: str           # "2025-09-10"
    time: str           # "19:30"
    notes: Optional[str] = None

class ChatIn(BaseModel):
    message: str

class ChatOut(BaseModel):
    reply: str

class IntentOut(BaseModel):
    intent: Literal["info","order","reservation","unknown"]
    missing_fields: list[str] = []
    suggestion: Optional[str] = None

# === Email destinataire (mono-tenant)
CLIENT_NOTIFICATION_EMAIL = os.getenv("CLIENT_NOTIFICATION_EMAIL", "").strip()

def _order_email_body(o: OrderIn) -> str:
    lines = []
    lines.append("Nouvelle commande :")
    lines.append(f"Client : {o.customer_name or '-'}")
    lines.append(f"Téléphone : {o.customer_phone or '-'}")
    lines.append(f"Email : {o.customer_email or '-'}")
    lines.append("")
    lines.append("Articles :")
    for it in o.items:
        lines.append(f" - {it.quantity} x {it.name}" + (f" (notes: {it.notes})" if it.notes else ""))
    lines.append("")
    lines.append(f"Mode : {o.delivery}")
    if o.address: lines.append(f"Adresse : {o.address}")
    if o.desired_time: lines.append(f"Heure souhaitée : {o.desired_time}")
    if o.notes: lines.append(f"Notes : {o.notes}")
    return "\n".join(lines)

def _reservation_email_body(r: ReservationIn) -> str:
    lines = []
    lines.append("Nouvelle réservation :")
    lines.append(f"Client : {r.customer_name or '-'}")
    lines.append(f"Téléphone : {r.customer_phone or '-'}")
    lines.append(f"Email : {r.customer_email or '-'}")
    lines.append("")
    lines.append(f"Personnes : {r.people}")
    lines.append(f"Date : {r.date}")
    lines.append(f"Heure : {r.time}")
    if r.notes: lines.append(f"Notes : {r.notes}")
    return "\n".join(lines)

# === /chat (réponse libre)
@app.post("/chat", response_model=ChatOut)
async def chat(inp: ChatIn):
    msgs = [
        {"role": "system", "content": SPECIAL_PROMPT},
        {"role": "user", "content": inp.message}
    ]
    reply = await openai_chat(msgs, temperature=0.3)
    return {"reply": reply}

# === /chat-intent (détection d'intention + champs manquants)
@app.post("/chat-intent", response_model=IntentOut)
async def chat_intent(inp: ChatIn):
    # Classifieur d'intentions (info / order / reservation / unknown)
    system = (
        "Tu es un classifieur d'intentions pour un commerce local (resto/PME). "
        "Catégories possibles: info, order, reservation, unknown. "
        "Si order: champs potentiels -> customer_name, customer_phone, customer_email, "
        "items (liste), delivery (pickup/delivery), address, desired_time, notes. "
        "Si reservation: customer_name, customer_phone, customer_email, people, date, time, notes. "
        "Réponds en JSON strict avec: intent, missing_fields (array), suggestion (phrase courte)."
    )
    user = f"Message: {inp.message}"
    reply = await openai_chat(
        [{"role":"system","content":system},{"role":"user","content":user}],
        temperature=0
    )
    intent = "unknown"; missing=[]; suggestion=None
    try:
        data = json.loads(reply)
        intent = data.get("intent","unknown")
        missing = data.get("missing_fields",[]) or []
        suggestion = data.get("suggestion")
    except Exception:
        pass
    return IntentOut(intent=intent, missing_fields=missing, suggestion=suggestion)

# === /order (recevoir une commande structurée + e-mail)
@app.post("/order")
async def create_order(order: OrderIn):
    if not CLIENT_NOTIFICATION_EMAIL:
        return {"ok": False, "error": "CLIENT_NOTIFICATION_EMAIL non configuré."}
    subject = "Nouvelle commande"
    body = _order_email_body(order)
    await send_email(CLIENT_NOTIFICATION_EMAIL, subject, body)
    return {"ok": True}

# === /reservation (recevoir une résa structurée + e-mail)
@app.post("/reservation")
async def create_reservation(resa: ReservationIn):
    if not CLIENT_NOTIFICATION_EMAIL:
        return {"ok": False, "error": "CLIENT_NOTIFICATION_EMAIL non configuré."}
    subject = "Nouvelle réservation"
    body = _reservation_email_body(resa)
    await send_email(CLIENT_NOTIFICATION_EMAIL, subject, body)
    return {"ok": True}

# === /voice-chat (vocal web complet)
@app.post("/voice-chat")
async def voice_chat(audio: UploadFile = File(...)):
    raw = await audio.read()
    name = (audio.filename or "").lower()
    if name.endswith(".webm"):
        wav = await stt.webm_to_wav(raw)
    elif name.endswith(".ogg"):
        wav = await stt.ogg_to_wav(raw)
    elif name.endswith(".mp3"):
        wav = await stt.mp3_to_wav(raw)
    else:
        wav = raw  # suppose WAV
    user_text = await stt.transcribe_wav(wav)
    bot_text = await openai_chat([
        {"role": "system", "content": SPECIAL_PROMPT},
        {"role": "user", "content": user_text}
    ])
    mp3 = await tts.synthesize(bot_text)
    url = save_public_bytes(mp3, ".mp3")
    return {"user_text": user_text, "bot_text": bot_text, "audio_url": url}

# === /speak (TTS direct)
class SpeakIn(BaseModel):
    text: str

@app.post("/speak")
async def speak(inp: SpeakIn):
    mp3 = await tts.synthesize(inp.text)
    url = save_public_bytes(mp3, ".mp3")
    return {"audio_url": url}

# === Twilio (gardé)
@app.post("/twilio/voice")
async def twilio_voice(To: str = Form(None), From: str = Form(None)):
    greeting = "Bonjour, vous parlez avec l’assistant. Posez votre question après le bip, puis patientez."
    mp3 = await tts.synthesize(greeting)
    url = save_public_bytes(mp3, ".mp3")
    xml = f'''
<Response>
  <Play>{url}</Play>
  <Record maxLength="30" playBeep="true" timeout="3" action="/twilio/handle-recording" />
</Response>
'''.strip()
    return Response(content=xml, media_type="text/xml")

@app.post("/twilio/handle-recording")
async def twilio_handle_recording(RecordingUrl: str = Form(...), RecordingDuration: str = Form(None)):
    async with httpx.AsyncClient(timeout=180) as c:
        r = await c.get(RecordingUrl + ".mp3")
        r.raise_for_status()
        mp3_bytes = r.content
    wav = await stt.mp3_to_wav(mp3_bytes)
    user_text = await stt.transcribe_wav(wav)
    bot_text = await openai_chat([
        {"role": "system", "content": SPECIAL_PROMPT},
        {"role": "user", "content": user_text}
    ])
    mp3 = await tts.synthesize(bot_text)
    url = save_public_bytes(mp3, ".mp3")
    xml = f'''
<Response>
  <Play>{url}</Play>
  <Say voice="alice">Vous pouvez poser une autre question après le bip, puis patienter.</Say>
  <Record maxLength="30" playBeep="true" timeout="3" action="/twilio/handle-recording" />
</Response>
'''.strip()
    return Response(content=xml, media_type="text/xml")
