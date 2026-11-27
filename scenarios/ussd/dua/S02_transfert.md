# S02 — Transfert avec confirmation · USSD · Duálá (dua)

**Interface :** USSD · **Langue :** Duálá

---

## Saisies

| Tour | Saisir | Réponse attendue |
|------|--------|-----------------|
| 1 | `2` ou `njem` | Numéro bénéficiaire ? |
| 2 | `677000002` | Montant ? |
| 2 | `5000` | Relecture : 5 000 FCFA → 677000002 / Mintuma : 50 FCFA / **1.Confirm 0.Fôl** |
| 3 | `1` | Njem a kes ! 5 000 FCFA → 677000002 |

> ⚠️ Tour 3 = X-Trace-Id différent du tour 2.

---

## Mots-clés

```
njem         → TRANSFER
njem 5000 a 677000002 → TRANSFER direct
confirm      → CONFIRM
fôl          → CANCEL
```
