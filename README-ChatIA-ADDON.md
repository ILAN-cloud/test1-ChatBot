
# ChatIA – Add-on multi-tenant (réservation, commande, rendez-vous)

## Lancer en local
```bash
pip install -r requirements.txt
uvicorn chatia.main:app --reload --port 8000
```

## Utilisation
Envoyez un POST sur `/chatia/incoming` :
```json
{
  "message": "Je voudrais réserver samedi à 20h pour 4 personnes",
  "state": {},
  "confirm": false
}
```
Le bot posera les questions manquantes puis proposera un **récap**.
Envoyez ensuite `{ "confirm": true, "state": { ... } }` pour déclencher l'envoi webhook/email.

## Multi-client sans changer le code
- Ajoutez un fichier dans `chatia/data/tenants/<slug>.yaml` (copie de `default.yaml`).
- Appelez l’API avec un header `X-Tenant-Id: <slug>`.
- Tout le style et les prompts, webhooks, horaires, etc. se configurent dans le YAML.

## Secrets
Créez un `.env` à la racine (copie de `.env.example`) pour SMTP, etc.

Bon dev !
