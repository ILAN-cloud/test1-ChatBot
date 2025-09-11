import os, io, tempfile, subprocess
from pydub import AudioSegment
import httpx

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

async def webm_to_wav(bytes_in: bytes, target_rate=16000) -> bytes:
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f_in:
        f_in.write(bytes_in)
        in_path = f_in.name
    out_path = in_path.replace(".webm", ".wav")
    subprocess.check_call([
        "ffmpeg", "-y", "-i", in_path, "-ac", "1", "-ar", str(target_rate), out_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    with open(out_path, "rb") as f:
        return f.read()

async def ogg_to_wav(bytes_in: bytes, target_rate=16000) -> bytes:
    audio = AudioSegment.from_file(io.BytesIO(bytes_in), format="ogg")
    audio = audio.set_channels(1).set_frame_rate(target_rate)
    out = io.BytesIO()
    audio.export(out, format="wav")
    return out.getvalue()

async def mp3_to_wav(bytes_in: bytes, target_rate=16000) -> bytes:
    audio = AudioSegment.from_file(io.BytesIO(bytes_in), format="mp3")
    audio = audio.set_channels(1).set_frame_rate(target_rate)
    out = io.BytesIO()
    audio.export(out, format="wav")
    return out.getvalue()

async def transcribe_wav(wav_bytes: bytes, language: str | None = None) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY manquant pour Whisper.")
    files = {"file": ("audio.wav", wav_bytes, "audio/wav")}
    data = {"model": "whisper-1"}
    if language:
        data["language"] = language
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    async with httpx.AsyncClient(timeout=180) as client:
        r = await client.post("https://api.openai.com/v1/audio/transcriptions",
                              headers=headers, data=data, files=files)
        r.raise_for_status()
        return r.json()["text"].strip()
