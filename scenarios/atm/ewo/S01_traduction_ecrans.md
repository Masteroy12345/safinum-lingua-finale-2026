# Traduction d'écrans Mobile/Web · Ewondo

**Interface :** `/sandbox/mobile` et `/sandbox/web`  
**Langue :** Ewondo (`ewo`)

---

## Clés principales

| Clé | Texte FR | Traduction Ewondo |
|-----|----------|-------------------|
| `nav.home` | Accueil | Nda |
| `nav.send` | Envoyer | Fëb |
| `nav.history` | Historique | Mvog |
| `home.balance_label` | Solde disponible | Mòni wom |
| `transfer.recipient` | Bénéficiaire | Nnom |
| `review.confirm` | Confirmer | Confirm |
| `review.cancel` | Annuler | Fôl |
| `error.INSUFFICIENT_FUNDS` | Solde insuffisant : il vous manque {missing} | Mòni wom a kpé a : {missing} a kpé a nà |

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
  "language": "ewo",
  "strings": {
    "nav.home": "Nda",
    "nav.send": "Fëb",
    "nav.history": "Mvog",
    "home.balance_label": "Mòni wom",
    "transfer.recipient": "Nnom",
    "review.confirm": "Confirm",
    "review.cancel": "Fôl",
    "error.INSUFFICIENT_FUNDS": "Mòni wom a kpé a : {missing} a kpé a nà"
  }
}
```
