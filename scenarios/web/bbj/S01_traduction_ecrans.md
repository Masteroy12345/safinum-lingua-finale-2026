# Traduction d'écrans Mobile/Web · Ghɔmálá'

**Interface :** `/sandbox/mobile` et `/sandbox/web`  
**Langue :** Ghɔmálá' (`bbj`)

---

## Clés principales

| Clé | Texte FR | Traduction Ghɔmálá' |
|-----|----------|-------------------|
| `nav.home` | Accueil | Tsʼɔ |
| `nav.send` | Envoyer | Mela |
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
  "language": "bbj",
  "strings": {
    "nav.home": "Tsʼɔ",
    "nav.send": "Mela",
    "nav.history": "Mvog",
    "home.balance_label": "Nkap gwɛl",
    "transfer.recipient": "Nnom",
    "review.confirm": "Confirm",
    "review.cancel": "Yée",
    "error.INSUFFICIENT_FUNDS": "Nkap a kpe nà : {missing} a kpe"
  }
}
```
