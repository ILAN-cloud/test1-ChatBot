
"""
intents.py — Détection d'intentions et extraction de slots
Mono-tenant (pas de multi-tenant, pas de Stripe)

- Détecte : RESERVATION, ORDER, APPOINTMENT, INFO
- Extraction rule-based très simple
"""

import re, json
from typing import Dict, Any

INTENT_KEYWORDS = {
    "RESERVATION": ["réserver", "resa", "réservation", "table", "couverts", "book", "booking"],
    "ORDER": ["commande", "commander", "livraison", "à emporter", "takeaway", "deliver"],
    "APPOINTMENT": ["rdv", "rendez-vous", "prise de rendez", "appointment", "booking a slot"],
}

def detect_intent(msg: str) -> str:
    m = msg.lower()
    for intent, keys in INTENT_KEYWORDS.items():
        if any(k in m for k in keys):
            return intent
    if "?" in m or m.startswith(("quand","comment","où","ou","quel","combien","est-ce")):
        return "INFO"
    return "INFO"

def extract_slots_rule_based(msg: str, intent: str) -> Dict[str, Any]:
    slots = {}

    # Nombre de personnes
    m = re.search(r"(\d+)\s*(?:personnes|couverts|pers)", msg, re.I)
    if m:
        slots["party_size"] = int(m.group(1))

    # Date simple
    m = re.search(r"\b(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?\b", msg)
    if m:
        d, mo = m.group(1), m.group(2)
        y = m.group(3) or "2025"
        slots["date"] = f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"

    # Heure
    m = re.search(r"\b(\d{1,2})\s*h(?:\s*(\d{2}))?\b|\b(\d{1,2}):(\d{2})\b", msg, re.I)
    if m:
        if m.group(1):
            hh = int(m.group(1))
            mm = int(m.group(2) or 0)
        else:
            hh = int(m.group(3))
            mm = int(m.group(4))
        slots["time"] = f"{hh:02d}:{mm:02d}"

    # Nom
    m = re.search(r"m'appelle\s+([A-Za-zÀ-ÖØ-öø-ÿ' -]{2,})", msg, re.I)
    if m:
        slots["name"] = m.group(1).strip()

    # Contact
    m = re.search(r"\b(\+?\d[\d\s]{7,}\d)\b", msg)
    if m:
        slots["contact"] = {"phone": re.sub(r"\s+","",m.group(1))}
    m = re.search(r"[\w\.-]+@[\w\.-]+\.\w{2,}", msg)
    if m:
        slots.setdefault("contact", {})
        slots["contact"]["email"] = m.group(0)

    # Items de commande
    if intent == "ORDER":
        items = []
        for qty, name in re.findall(r"(\d+)\s*x?\s*([A-Za-zÀ-ÖØ-öø-ÿ' -]{2,})", msg):
            q = int(qty)
            product = name.strip().strip(",.")
            if q > 0 and len(product) > 1:
                items.append({"product_name": product, "quantity": q, "options": []})
        if items:
            slots["items"] = items

        # Mode commande
        if any(x in msg.lower() for x in ["livraison", "deliver"]):
            slots["mode"] = "delivery"
        elif any(x in msg.lower() for x in ["emporter", "à emporter", "takeaway"]):
            slots["mode"] = "takeaway"

    return slots

async def classify_and_extract(user_msg: str, state: dict) -> dict:
    """
    Détection d’intention + extraction des infos simples.
    """
    intent = state.get("intent") or detect_intent(user_msg)
    if intent == "INFO":
        return {"intent":"INFO","answer":"Je peux vous aider à réserver, commander ou prendre un rendez-vous."}
    slots = extract_slots_rule_based(user_msg, intent)
    return {"intent": intent, "slots": slots}
