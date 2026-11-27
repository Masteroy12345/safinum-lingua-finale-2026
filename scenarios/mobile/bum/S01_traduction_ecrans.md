# Traduction d'écrans Mobile/Web · Bulu

**Interface :** `/sandbox/mobile` et `/sandbox/web`  
**Langue :** Bulu (`bum`)

---

## Clés principales

| Clé | Texte FR | Traduction Bulu |
|-----|----------|-------------------|
| `nav.home` | Accueil | Nda |
| `nav.send` | Envoyer | Tuk |
| `nav.history` | Historique | Mvog |
| `home.balance_label` | Solde disponible | Nkap gwɛl |
| `transfer.recipient` | Bénéficiaire | Nnom |
| `review.confirm` | Confirmer | Confirm |
| `review.cancel` | Annuler | Fôl |
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
  "language": "bum",
  "strings": {
    "nav.home": "Nda",
    "nav.send": "Tuk",
    "nav.history": "Mvog",
    "home.balance_label": "Nkap gwɛl",
    "transfer.recipient": "Nnom",
    "review.confirm": "Confirm",
    "review.cancel": "Fôl",
    "error.INSUFFICIENT_FUNDS": "Nkap a kpe nà : {missing} a kpe"
  }
}
```
