"""
tenants.py — version mono-tenant
⚠️ Toute la logique multi-tenant a été supprimée.
- On ne charge plus de fichiers YAML par client.
- Toute la config se fait via .env
"""

import os

def get_tenant() -> dict:
    """
    Version mono-tenant : retourne une configuration unique
    basée sur les variables d'environnement (.env).
    """
    return {
        "OPENAI_CHAT_MODEL": os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
        "PUBLIC_BASE_URL": os.getenv("PUBLIC_BASE_URL", "http://localhost:8000"),
        "CLIENT_NOTIFICATION_EMAIL": os.getenv("CLIENT_NOTIFICATION_EMAIL", ""),
        "TTS_PROVIDER": os.getenv("TTS_PROVIDER", "azure"),
    }
