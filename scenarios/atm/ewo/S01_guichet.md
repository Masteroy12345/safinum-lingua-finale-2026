# Guichet Automatique (GAB) · Ewondo (ewo)

**Interface :** `/sandbox/atm`  
**Langue :** Ewondo  
**Contrat :** `ui_translation` (identique à mobile/web) avec écrans spécifiques ATM.

---

## Parcours GAB

1. **Insérer la carte** → clic sur la fente
2. **Saisir le code PIN** (4 chiffres quelconques) → touche verte
3. **Menu principal** → les touches grises latérales choisissent l'option en face
4. **Retrait** → choisir montant (multiple de 5 000 FCFA, max 200 000 FCFA)
5. **Confirmation** → touche verte
6. **Reçu**

---

## Clés d'écran ATM à traduire

| Clé | Texte FR | Traduction Ewondo |
|-----|----------|-------------------|
| `atm.welcome` | Bienvenue | Mòni wom a lig |
| `atm.insert_card` | Insérez votre carte | Tëg kard yom |
| `atm.pin_prompt` | Code secret | Nkamba |
| `atm.menu_balance` | Consulter solde | Mòni wom |
| `atm.menu_withdraw` | Retrait | Zal nkap |
| `atm.menu_history` | Historique | Mvog |
| `atm.amount_prompt` | Montant du retrait | Nkap ye zal |
| `atm.confirm_text` | Confirmer le retrait de {amount} ? | Confirm zal {amount} ? |
| `atm.cash_ready` | Veuillez prendre vos billets | Zal nkap yom |
| `atm.receipt_title` | Reçu de retrait | Reçu zal nkap |
| `atm.error_limit` | Montant non disponible | Nkap a kpé a |
| `atm.error_multiple` | Choisir un multiple de 5 000 FCFA | Zal nkap ye 5 000 FCFA |

---

## Contraintes GAB

| Critère | Valeur |
|---------|--------|
| Écran | 40 colonnes (texte coupé si trop long) |
| Touches latérales | 18 caractères max |
| Retraits | Multiples de 5 000 FCFA uniquement |
| Plafond retrait | 200 000 FCFA par opération |
| Charset | UTF-8 |
| Timeout | 10s par écran |

---

## Montants de test (multiples de 5 000)

```
5000
10000
20000
50000
100000
200000   ← plafond maximum
```

---

## Réponse JSON minimale

```json
{
  "language": "ewo",
  "strings": {
    "atm.welcome": "Mòni wom a lig",
    "atm.pin_prompt": "Nkamba",
    "atm.menu_balance": "Mòni wom",
    "atm.menu_withdraw": "Zal nkap",
    "atm.amount_prompt": "Nkap ye zal",
    "atm.confirm_text": "Confirm zal {amount} ?",
    "atm.cash_ready": "Zal nkap yom"
  }
}
```
