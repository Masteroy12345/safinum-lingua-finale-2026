# Scénarios IVR · Bulu (`bum`)

**Interface :** `/sandbox/ivr` — cliquer le bouton micro 🎤 et parler  
**Langue :** Bulu  
**Moteur STT :** Gemini 3.1 Flash Lite

---

## Tour 1 — Décroché (automatique, rien à dire)

Le simulateur envoie `input.type: "dtmf"` vide.  
Réponse du middleware : menu d'accueil vocal en Bulu.

---

## Phrases à prononcer

| Intention | Dire en Bulu | Fallback français |
|-----------|---------------|-------------------|
| Solde | *nkap* | *quel est mon solde* |
| Transfert | *tuk 5000 677000002* | *envoyer 5000 à 677000002* |
| Confirmer | *confirm* | *confirmer* |
| Annuler | *fol* | *annuler* |

---

## Ce que le jury entend

Le sandbox lit ta réponse texte avec sa propre synthèse.  
Envoie du texte clair, ≤ 400 chars, sans markdown.

---

## Contraintes

- Budget : **8 secondes** par tour (Gemini STT inclus)
- Max : **400 caractères** de réponse texte
- Si Gemini ne transcrit pas : menu vocal DTMF de reprise
