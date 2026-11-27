# S01 — Accueil vocal · IVR · Ewondo (ewo)

**Interface :** `/sandbox/ivr`  
**Langue :** Ewondo  
**Contrat :** audio WAV PCM 16 bits mono → Gemini 3.1 Flash Lite transcrit → NLU → réponse texte ≤ 400 chars (lue par la synthèse du sandbox).

---

## Comment ça marche

1. Ouvre `/sandbox/ivr`, choisis l'équipe, entre le PASS, sélectionne la langue Ewondo
2. Le simulateur t'affiche un **bouton micro** 🎤 — clique et parle
3. Le sandbox envoie le WAV à ton middleware (`input.type: "audio"`)
4. Gemini 3.1 Flash Lite transcrit → le NLU décode → le middleware répond en texte
5. Le sandbox **lit la réponse texte** avec sa propre synthèse vocale

> Tu n'as pas besoin de gérer la synthèse vocale côté middleware — seulement le texte de réponse.

---

## Tour 1 — Décroché (automatique)

Le simulateur envoie `input.type: "dtmf"`, `input.text: ""` au décroché.

**Réponse attendue :**
```
Mòni wom a lig ma a ne tân ya ?
1. Mòni wom  2. Fëb mòni  3. Crédît  4. Mintuma
```
> Menu d'accueil vocal en Ewondo. Max 400 chars.

---

## Tour 2 — Parler (audio)

**Dire à voix haute (en Ewondo) :**
> *"mòni wom"*

ou en français si Gemini n'entend pas l'Ewondo :
> *"quel est mon solde"*

**Réponse attendue :**
```
Mòni wom mà : 253 177 FCFA
```

---

## Tour 3 — Transfert vocal

**Dire :**
> *"fëb cinq mille à six sept sept zéro zéro zéro zéro zéro deux"*

ou en français :
> *"envoyer 5000 à 677000002"*

**Réponse :**
```
Fëb 5 000 FCFA a 677000002.
Mintuma : 50 FCFA. Total : 5 050 FCFA.
Dis "confirm" pou fëb, "fôl" pou annuler.
```

---

## Phrases à prononcer (prêtes à l'emploi)

| Intention | Dire en Ewondo | Dire en français (fallback) |
|-----------|---------------|--------------------------|
| Solde | *mòni wom* | *quel est mon solde* |
| Transfert | *fëb mòni a [numéro]* | *envoyer [X] FCFA à [numéro]* |
| Frais | *mintuma ye [montant]* | *combien coûte envoyer [X]* |
| Confirmer | *confirm* | *confirmer* |
| Annuler | *fôl* | *annuler* |
| Solde + transfert | *mòni wom, fëb 5000* | *solde puis envoyer 5000* |

---

## Contraintes IVR

| Critère | Valeur |
|---------|--------|
| Max chars réponse | 400 |
| Alphabet | UTF-8 |
| Budget total | 8 secondes (transcription + appel bancaire + réponse) |
| Audio entrant | WAV PCM 16 bits mono, 8 kHz ou 16 kHz, max 30s |

---

## ⚠️ Si la transcription échoue

Gemini retourne vide → le middleware renvoie un **menu vocal de reprise** :
```
Mòni wom a bëk ma a ne tân ya ?
1. Mòni wom  2. Fëb mòni  3. Mintuma  4. Crédît
```
L'utilisateur peut alors choisir avec les touches DTMF (1, 2, 3...).
