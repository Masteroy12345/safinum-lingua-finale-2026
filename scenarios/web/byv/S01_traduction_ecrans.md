# Traduction d'écrans Mobile/Web · Mə̀dûmbà

**Interface :** `/sandbox/mobile` et `/sandbox/web`  
**Langue :** Mə̀dûmbà (`byv`)

---

## Clés principales

| Clé | Texte FR | Traduction Mə̀dûmbà |
|-----|----------|-------------------|
| `nav.home` | Accueil | Tsʼɔ |
| `nav.send` | Envoyer | Yeel |
| `nav.history` | Historique | Mvog |
| `home.balance_label` | Solde disponible | Nkap gwɛl |
| `transfer.recipient` | Bénéficiaire | Nnom |
| `review.confirm` | Confirmer | Confirm |
| `review.cancel` | Annuler | Yée |
| `error.INSUFFICIENT_FUNDS` | Solde insuffisant : il vous manque {missing} | Nkap a kpe nà : {missing} a kpe |

---

## Règles à ne pas oublier

- Garder `{missing}`, `{amount}`, `{name}` tels quels dans les traductions
- `nav.*` ≤ 12 caractères
- Toutes les clés renvoyées, sinon MISSING_STRINGS
- ≥ 25 % différentes du français sinon UNTRANSLATED

---

## Réponse JSON minimale valide

```json
{
  "language": "byv",
  "strings": {
    "nav.home": "Tsʼɔ",
    "nav.send": "Yeel",
    "nav.history": "Mvog",
    "home.balance_label": "Nkap gwɛl",
    "transfer.recipient": "Nnom",
    "review.confirm": "Confirm",
    "review.cancel": "Yée",
    "error.INSUFFICIENT_FUNDS": "Nkap a kpe nà : {missing} a kpe"
  }
}
```
