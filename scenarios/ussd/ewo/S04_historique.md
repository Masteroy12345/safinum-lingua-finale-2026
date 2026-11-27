# S04 — Historique des opérations · USSD · Ewondo (ewo)

**Interface :** USSD  
**Langue :** Ewondo

---

## Déroulement

### Tour 1

Saisir :
```
3
```
ou
```
historique
```
ou
```
mvog bé mòni
```

**Réponse attendue (exemple) :**
```
Mvog bé mòni (3 mbu) :
1. +10 000 FCFA (dépôt)
2. -5 050 FCFA → 677000002
3. -1 200 FCFA (crédit)
```
> *Explication :* "Mvog bé mòni" = historique des transactions. Le middleware appelle `GET /accounts/237651841190/transactions?limit=10`.  
> Les montants sont précédés de `+` (entrée) ou `-` (sortie).

---

## Vérifications jury

| Critère | Attendu |
|---------|---------|
| `intent` | `TRANSACTION_HISTORY` |
| Appel bancaire | `GET /accounts/{phone}/transactions` avec X-Trace-Id |
| Nombre de transactions | ≤ 50 (limite API) |
| Format lisible en USSD | ≤ 182 septets par réponse |

---

## Conseil

Si la liste est longue, tronquer à 3–5 entrées et proposer `1. Plus` pour paginer. Le jury apprécie l'UX claire.
