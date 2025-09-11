
"""
policy.py — Règles métiers pour compléter les infos manquantes
Mono-tenant (pas de multi-tenant)

- Définit les champs requis par type d’intention
- Définit les phrases par défaut pour demander les infos
"""

from typing import List, Dict, Any

REQUIRED = {
    "RESERVATION": ["party_size","date","time","name","contact"],
    "ORDER": ["items","mode","customer","time_preference"],
    "APPOINTMENT": ["service","date","time","customer"],
}

PROMPTS_DEFAULT = {
    "party_size":"Pour combien de personnes ?",
    "date":"Quel jour souhaitez-vous ? (ex: 14/09 ou samedi prochain)",
    "time":"À quelle heure ? (ex: 20:00)",
    "name":"À quel nom dois-je réserver ?",
    "contact":"Un téléphone ou un e-mail pour vous joindre ?",
    "items":"Que souhaitez-vous commander ? (ex: 2 margherita, 1 tiramisu)",
    "mode":"Préférez-vous la livraison ou à emporter ?",
    "address":"Quelle est l’adresse de livraison ?",
    "postal_code":"Quel est le code postal ?",
    "city":"Dans quelle ville ?",
    "time_preference":"Plutôt au plus vite ou à une heure précise ?",
    "service":"Quel service souhaitez-vous ?",
    "customer":"À quel nom dois-je noter votre demande ? (nom + téléphone ou e-mail)",
    "location_preference":"Préférez-vous sur place ou à distance ?",
}

def normalize_incoming_state(state: Dict[str,Any]) -> Dict[str,Any]:
    if not isinstance(state, dict):
        state = {}
    state.setdefault("slots", {})
    return state

def next_missing_slots(intent: str, slots: Dict[str,Any]) -> List[str]:
    """
    Retourne la liste des champs encore manquants pour un intent donné.
    """
    req = REQUIRED.get(intent, [])
    missing = []
    for k in req:
        v = slots.get(k)
        if not v:
            missing.append(k)
        elif k in ("contact","customer"):
            phone = v.get("phone") if isinstance(v, dict) else None
            email = v.get("email") if isinstance(v, dict) else None
            if not phone and not email:
                missing.append(k)
    return missing

def ask_for(slot: str, intent: str) -> str:
    """
    Retourne la question à poser pour compléter un champ manquant.
    """
    return PROMPTS_DEFAULT.get(slot, "Pouvez-vous préciser ?")

def recap(intent: str, slots: Dict[str,Any]) -> str:
    """
    Génère un récapitulatif simple selon l’intention.
    """
    if intent == "RESERVATION":
        contact_disp = (slots.get("contact",{}) or {}).get("phone") or (slots.get("contact",{}) or {}).get("email") or "—"
        return (
            f"Récapitulatif :\n"
            f"• {slots.get('party_size','?')} couverts — {slots.get('date','?')} à {slots.get('time','?')}\n"
            f"• Nom : {slots.get('name','?')}, Contact : {contact_disp}\n"
            f"• Notes : {slots.get('special_requests','—')}\n"
            f"Je confirme et j’envoie au restaurant ?"
        )

    if intent == "ORDER":
        items = slots.get("items", [])
        items_str = "\n".join([f"- {it['quantity']}× {it['product_name']}" for it in items]) or "—"
        contact = slots.get("customer", {})
        return (
            f"Récapitulatif :\n"
            f"{items_str}\n"
            f"• Mode : {slots.get('mode','?')}\n"
            f"• Pour : {slots.get('time_preference','au plus vite')}\n"
            f"• Client : {contact.get('name','?')} ({contact.get('phone') or contact.get('email') or '?'})\n"
            f"Je valide et j’envoie ?"
        )

    if intent == "APPOINTMENT":
        contact = slots.get("customer", {})
        return (
            f"Récapitulatif :\n"
            f"• Service : {slots.get('service','?')}\n"
            f"• Quand : {slots.get('date','?')} à {slots.get('time','?')}\n"
            f"• Client : {contact.get('name','?')} ({contact.get('phone') or contact.get('email') or '?'})\n"
            f"• Préférence : {slots.get('location_preference','—')}\n"
            f"Je confirme et j’envoie ?"
        )

    return "Je n'ai pas assez d'informations."

