# S09 — Parcours multicanal · USSD → SMS · Ewondo (ewo)

**Interface :** USSD puis SMS (même numéro 237651841190)  
**Langue :** Ewondo  
**Ce que le jury teste :** un parcours démarré sur un canal se poursuit sur un autre avec le même numéro.

---

## Étape 1 — Initier sur USSD

**Sur `/sandbox/ussd`** — saisir :
```
2
```
Bénéficiaire :
```
677000002
```
Montant :
```
3000
```

La réponse USSD donne la relecture :
```
Fëb 3 000 FCFA a 677000002
Mintuma : 50 FCFA
1. Confirm  0. Fôl
```

**Ne pas confirmer encore.** Fermer le simulateur USSD (fin de session ou timeout).

---

## Étape 2 — Continuer sur SMS

**Sur `/sandbox/sms`** — saisir :
```
confirm 677000002 3000
```
ou
```
confirme le transfert
```

**Réponse SMS attendue :**
```
Fëb mòni a kes !
3 000 FCFA → 677000002
Mòni wom : 250 127 FCFA
```
> *Explication :* Le middleware stocke la session par numéro de téléphone (`session_store.py`). Le numéro 237651841190 retrouve sa transaction pending et peut la confirmer depuis le SMS.

---

## Vérifications jury

| Critère | Attendu |
|---------|---------|
| Même `phone` sur les 2 canaux | ✅ 237651841190 |
| Transaction confirmée | ✅ depuis SMS |
| `X-Trace-Id` différent du tour USSD | ✅ obligatoire |
| `intent` SMS | `CONFIRM` |

---

## ⚠️ Note importante

La session USSD a un timeout de 180s. Si la confirmation SMS arrive après, le middleware doit chercher la transaction `pending` via `GET /accounts/{phone}/transactions` et retrouver l'ID.
