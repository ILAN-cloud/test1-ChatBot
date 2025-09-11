# Voice IA — Web + Premium Téléphone (Azure TTS, Whisper, Stripe, Twilio)

Fonctionnalités :
- Widget web bulle (champ unique + 🎙️) — `/chat`, `/voice-chat`, `/speak`
- Lecture vocale via **Azure TTS**
- Transcription vocale via **Whisper (OpenAI)**
- **Stripe** : Checkout + Webhook, gating **Basic** vs **Premium**
- **Twilio** (option Premium) : appels entrants vers le chatbot (`/twilio/voice`, `/twilio/handle-recording`)
- Fichiers audio servis via `/public/...`

# Voice IA — Web + Téléphone (Azure TTS, Whisper, Twilio)

Fonctionnalités :
- Widget web bulle (champ unique + 🎙️) — `/chat`, `/voice-chat`, `/speak`
- Lecture vocale via **Azure TTS** (ou ElevenLabs si configuré)
- Transcription vocale via **Whisper (OpenAI)**
- **Twilio** : appels entrants vers le chatbot (`/twilio/voice`, `/twilio/handle-recording`)
- Fichiers audio servis via `/public/...`
- **Mono-tenant** : toute la config dans `.env` (pas de Stripe, pas de multi-client)

## Lancer en local
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # puis édite .env
uvicorn main:app --reload

# Frontend (autre terminal)
cd frontend
python -m http.server 5500
# Ouvre http://localhost:5500
