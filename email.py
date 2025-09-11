"""
email.py — Service d'envoi d'e-mails (mono-tenant)

- Utilise un serveur SMTP (par défaut Gmail) pour envoyer des mails.
- Pas de Stripe, pas de plans, pas de multi-tenant.
- Configurable via variables d'environnement.
"""

import os, asyncio, smtplib
from email.mime.text import MIMEText

# === Configuration SMTP (définie dans .env) ===
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")

async def send_email(to_addr: str, subject: str, body: str):
    """
    Envoie un email en texte brut.

    Args:
        to_addr (str): Adresse du destinataire (ex: CLIENT_NOTIFICATION_EMAIL depuis .env)
        subject (str): Objet de l'email
        body (str): Contenu texte de l'email
    """
    if not to_addr:
        return  # pas de destinataire = pas d'envoi

    # Création du message
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER or "noreply@chatia.app"
    msg["To"] = to_addr

    # Fonction interne pour exécuter le send dans un thread
    def _send():
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            if SMTP_USER and SMTP_PASS:
                server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(msg["From"], [to_addr], msg.as_string())

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _send)
