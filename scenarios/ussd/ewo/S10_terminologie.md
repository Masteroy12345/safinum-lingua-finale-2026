# S10 — Terminologie financière · USSD · Ewondo (ewo)

**Interface :** USSD  
**Langue :** Ewondo  
**Ce que le jury teste :** l'utilisateur demande l'explication d'un terme financier → réponse claire en Ewondo.

---

## Déroulement

### Tour 1 — Demande d'explication

Saisir :
```
c'est quoi les frais
```
ou
```
mintuma nge a ne tân
```
ou
```
explique beneficiaire
```
ou
```
c'est quoi le plafond
```

**Réponse attendue (pour "frais") :**
```
Mintuma : nkap ye bâ bé dépenser a fëb mòni.
Ex : fëb 5 000 FCFA → mintuma 50 FCFA.
```
> *Explication :* "Mintuma" = frais. La définition est en Ewondo simple, accessible à quelqu'un qui n'a jamais eu de compte bancaire (c'est une exigence du jury pour les bulles `help.*`).

---

## Termes à expliquer (liste complète)

| Terme FR | Terme Ewondo | Explication attendue |
|----------|-------------|----------------------|
| Frais | Mintuma | Nkap ye bâ bé dépenser a fëb mòni |
| Plafond | Montant maximum | Mòni zôt a fëb yam (500 000 FCFA) |
| Bénéficiaire | Nnom a fëb mòni | Mfan ye a zal mòni |
| Solde | Mòni wom | Nkap ye wom a kpé a |
| Transaction | Fëb mòni | Fëb be bé mòni |
| Confirmation | Confirm | Zal a fëb mòni a kes |

---

## Variantes à tester

```
kesquoi frais          → TERM_EXPLANATION (frais)
explique moi plafond   → TERM_EXPLANATION (plafond)
benef c'est quoi       → TERM_EXPLANATION (bénéficiaire)
c koi solde            → TERM_EXPLANATION (solde)
```

---

## Vérifications jury

| Critère | Attendu |
|---------|---------|
| `intent` | `TERM_EXPLANATION` |
| Appel bancaire | Aucun (pas nécessaire) |
| Explication en Ewondo | ✅ simple, sans jargon |
| `end_session` | `false` (l'utilisateur peut continuer) |
