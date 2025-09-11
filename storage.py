import os, uuid

PUBLIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "public"))
os.makedirs(PUBLIC_DIR, exist_ok=True)

def save_public_bytes(data: bytes, suffix: str = ".mp3") -> str:
    name = f"{uuid.uuid4().hex}{suffix}"
    path = os.path.join(PUBLIC_DIR, name)
    with open(path, "wb") as f:
        f.write(data)
    base = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")
    return f"{base}/public/{name}"
