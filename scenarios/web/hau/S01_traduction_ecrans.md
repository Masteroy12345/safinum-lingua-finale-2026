# Traduction d'écrans Mobile/Web · Haoussa

**Interface :** `/sandbox/mobile` et `/sandbox/web`  
**Langue :** Haoussa (`hau`)

---

## Clés principales

| Clé | Texte FR | Traduction Haoussa |
|-----|----------|-------------------|
| `nav.home` | Accueil | Gida |
| `nav.send` | Envoyer | Aika |
| `nav.history` | Historique | Tarihi |
| `home.balance_label` | Solde disponible | Kuɗinka |
| `transfer.recipient` | Bénéficiaire | Wanda |
| `review.confirm` | Confirmer | Tabbatar |
| `review.cancel` | Annuler | Soke |
| `error.INSUFFICIENT_FUNDS` | Solde insuffisant : il vous manque {missing} | Ba kuɗi ba : {missing} ya ɓaci |

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
  "language": "hau",
  "strings": {
    "nav.home": "Gida",
    "nav.send": "Aika",
    "nav.history": "Tarihi",
    "home.balance_label": "Kuɗinka",
    "transfer.recipient": "Wanda",
    "review.confirm": "Tabbatar",
    "review.cancel": "Soke",
    "error.INSUFFICIENT_FUNDS": "Ba kuɗi ba : {missing} ya ɓaci"
  }
}
```
