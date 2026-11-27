# Scénarios IVR · Haoussa (`hau`)

**Interface :** `/sandbox/ivr` — cliquer le bouton micro 🎤 et parler  
**Langue :** Haoussa  
**Moteur STT :** Gemini 3.1 Flash Lite

---

## Tour 1 — Décroché (automatique, rien à dire)

Le simulateur envoie `input.type: "dtmf"` vide.  
Réponse du middleware : menu d'accueil vocal en Haoussa.

---

## Phrases à prononcer

| Intention | Dire en Haoussa | Fallback français |
|-----------|---------------|-------------------|
| Solde | *kudi na* | *quel est mon solde* |
| Transfert | *aika 5000 677000002* | *envoyer 5000 à 677000002* |
| Confirmer | *tabbatar* | *confirmer* |
| Annuler | *soke* | *annuler* |

---

## Ce que le jury entend

Le sandbox lit ta réponse texte avec sa propre synthèse.  
Envoie du texte clair, ≤ 400 chars, sans markdown.

---

## Contraintes

- Budget : **8 secondes** par tour (Gemini STT inclus)
- Max : **400 caractères** de réponse texte
- Si Gemini ne transcrit pas : menu vocal DTMF de reprise
