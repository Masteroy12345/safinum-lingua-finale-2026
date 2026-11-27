# Traduction d'écrans Mobile/Web · Pidgin Camerounais

**Interface :** `/sandbox/mobile` et `/sandbox/web`  
**Langue :** Pidgin Camerounais (`wes`)

---

## Clés principales

| Clé | Texte FR | Traduction Pidgin Camerounais |
|-----|----------|-------------------|
| `nav.home` | Accueil | Home |
| `nav.send` | Envoyer | Send |
| `nav.history` | Historique | History |
| `home.balance_label` | Solde disponible | Yua money |
| `transfer.recipient` | Bénéficiaire | Person |
| `review.confirm` | Confirmer | Confirm |
| `review.cancel` | Annuler | Stop |
| `error.INSUFFICIENT_FUNDS` | Solde insuffisant : il vous manque {missing} | Yua money no reach : {missing} miss |

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
  "language": "wes",
  "strings": {
    "nav.home": "Home",
    "nav.send": "Send",
    "nav.history": "History",
    "home.balance_label": "Yua money",
    "transfer.recipient": "Person",
    "review.confirm": "Confirm",
    "review.cancel": "Stop",
    "error.INSUFFICIENT_FUNDS": "Yua money no reach : {missing} miss"
  }
}
```
