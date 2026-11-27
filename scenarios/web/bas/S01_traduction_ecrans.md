# Traduction d'écrans Mobile/Web · Ɓasaá

**Interface :** `/sandbox/mobile` et `/sandbox/web`  
**Langue :** Ɓasaá (`bas`)

---

## Clés principales

| Clé | Texte FR | Traduction Ɓasaá |
|-----|----------|-------------------|
| `nav.home` | Accueil | Mba |
| `nav.send` | Envoyer | Tondl |
| `nav.history` | Historique | Mvog |
| `home.balance_label` | Solde disponible | Nkap gwɛl |
| `transfer.recipient` | Bénéficiaire | Yɛ̀ |
| `review.confirm` | Confirmer | Confirm |
| `review.cancel` | Annuler | Fôl |
| `error.INSUFFICIENT_FUNDS` | Solde insuffisant : il vous manque {missing} | Nkap a hii nà : {missing} a hii |

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
  "language": "bas",
  "strings": {
    "nav.home": "Mba",
    "nav.send": "Tondl",
    "nav.history": "Mvog",
    "home.balance_label": "Nkap gwɛl",
    "transfer.recipient": "Yɛ̀",
    "review.confirm": "Confirm",
    "review.cancel": "Fôl",
    "error.INSUFFICIENT_FUNDS": "Nkap a hii nà : {missing} a hii"
  }
}
```
