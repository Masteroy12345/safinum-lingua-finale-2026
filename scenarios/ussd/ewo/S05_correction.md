# S05 — Correction avant confirmation · USSD · Ewondo (ewo)

**Interface :** USSD  
**Langue :** Ewondo  
**Ce que le jury teste :** l'utilisateur se trompe, corrige, et la correction est prise en compte AVANT la confirmation.

---

## Déroulement

### Tour 1 — Initier un transfert

Saisir :
```
2
```
Puis bénéficiaire :
```
677000002
```
Puis montant (intentionnellement faux) :
```
50000
```

**Réponse (relecture avec l'erreur) :**
```
Fëb 50 000 FCFA a 677000002
Mintuma : 400 FCFA
Fëb yam : 50 400 FCFA
1. Confirm  2. Zal  0. Fôl
```

---

### Tour 2 — Correction du montant

Saisir :
```
2
```
ou
```
zal montant
```
ou
```
non, 5000
```

**Réponse attendue :**
```
Montant corrigé. Fëb :
5 000 FCFA a 677000002
Mintuma : 50 FCFA
Fëb yam : 5 050 FCFA
1. Confirm  0. Fôl
```
> *Explication :* Le middleware appelle `POST /transactions/{id}/update` avec le nouveau montant. La transaction pending est modifiée, pas recréée.

---

### Tour 3 — Confirmation

Saisir :
```
1
```

**Réponse attendue :**
```
Fëb mòni a kes !
5 000 FCFA → 677000002
```

---

## Vérifications jury

| Tour | Intent | Appel bancaire |
|------|--------|----------------|
| Tour 1-2 | `TRANSFER` | `POST /transactions` (pending) |
| Tour 2-correction | `CORRECTION` | `POST /transactions/{id}/update` |
| Tour 3 | `CONFIRM` | `POST /transactions/{id}/confirm` (X-Trace-Id différent) |

---

## Conseil

Le NLU doit reconnaître `CORRECTION` sur des saisies comme "non", "zal", "changer", "2" (si option correction dans le menu).
