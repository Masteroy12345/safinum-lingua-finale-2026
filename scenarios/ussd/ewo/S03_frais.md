# S03 — Demande de frais · USSD · Ewondo (ewo)

**Interface :** USSD  
**Langue :** Ewondo

---

## Déroulement

### Tour 1

Saisir :
```
fëb be fëb
```
ou
```
4
```
ou
```
mintuma ye 10000
```

**Réponse attendue :**
```
Fëb be fëb a 10 000 FCFA :
Mintuma : 150 FCFA
Fëb yam : 10 150 FCFA
```
> *Explication :* "Fëb be fëb" = frais. Grille officielle : 5 001–25 000 FCFA = 150 FCFA de frais.

---

## Grille de frais (à connaître par cœur)

| Montant | Frais |
|---------|-------|
| 1 – 5 000 | 50 FCFA |
| 5 001 – 25 000 | 150 FCFA |
| 25 001 – 100 000 | 400 FCFA |
| ≥ 100 001 | 1 % |

**Cas tests rapides :**

```
mintuma ye 1000     → 50 FCFA
mintuma ye 5000     → 50 FCFA
mintuma ye 5001     → 150 FCFA
mintuma ye 25000    → 150 FCFA
mintuma ye 100000   → 400 FCFA
mintuma ye 500000   → 5 000 FCFA (1%)
```

---

## Vérifications jury

| Critère | Attendu |
|---------|---------|
| `intent` | `FEE_INQUIRY` |
| Appel bancaire | `GET /fees?type=transfer&amount=X` |
| Montant correct | Selon grille ci-dessus |
