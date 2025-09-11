import os, httpx

PROVIDER = os.getenv("TTS_PROVIDER", "azure").lower()

# Azure
AZURE_TTS_KEY = os.getenv("AZURE_TTS_KEY")
AZURE_TTS_REGION = os.getenv("AZURE_TTS_REGION", "westeurope")
AZURE_TTS_VOICE = os.getenv("AZURE_TTS_VOICE", "fr-FR-DeniseNeural")

# ElevenLabs (optionnel)
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
ELEVEN_VOICE_ID = os.getenv("ELEVEN_VOICE_ID", "Rachel")

SSML_TMPL = """<speak version='1.0' xml:lang='fr-FR'>
  <voice name='{voice}'>{text}</voice>
</speak>"""

async def synthesize(text: str) -> bytes:
    if PROVIDER == "azure":
        if not AZURE_TTS_KEY:
            raise RuntimeError("AZURE_TTS_KEY manquant. (TTS_PROVIDER=azure)")
        url = f"https://{AZURE_TTS_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"
        ssml = SSML_TMPL.format(voice=AZURE_TTS_VOICE, text=text)
        headers = {
            "Ocp-Apim-Subscription-Key": AZURE_TTS_KEY,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3",
            "User-Agent": "voice-ia",
        }
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(url, headers=headers, content=ssml.encode("utf-8"))
            r.raise_for_status()
            return r.content

    elif PROVIDER == "elevenlabs":
        if not ELEVEN_API_KEY:
            raise RuntimeError("ELEVEN_API_KEY manquant. (TTS_PROVIDER=elevenlabs)")
        headers = {
            "xi-api-key": ELEVEN_API_KEY,
            "accept": "audio/mpeg",
            "Content-Type": "application/json",
        }
        payload = {"text": text}
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE_ID}"
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            return r.content

    else:
        raise RuntimeError("TTS_PROVIDER doit être 'azure' ou 'elevenlabs'")
