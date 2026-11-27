# Traduction d'écrans Mobile/Web · Français

**Interface :** `/sandbox/mobile` et `/sandbox/web`  
**Langue :** Français (`fr`)

---

## Clés principales

| Clé | Texte FR | Traduction Français |
|-----|----------|-------------------|
| `nav.home` | Accueil | Accueil |
| `nav.send` | Envoyer | Envoyer |
| `nav.history` | Historique | Historique |
| `home.balance_label` | Solde disponible | Solde disponible |
| `transfer.recipient` | Bénéficiaire | Bénéficiaire |
| `review.confirm` | Confirmer | Confirmer |
| `review.cancel` | Annuler | Annuler |
| `error.INSUFFICIENT_FUNDS` | Solde insuffisant : il vous manque {missing} | Solde insuffisant : il vous manque {missing} |

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
  "language": "fr",
  "strings": {
    "nav.home": "Accueil",
    "nav.send": "Envoyer",
    "nav.history": "Historique",
    "home.balance_label": "Solde disponible",
    "transfer.recipient": "Bénéficiaire",
    "review.confirm": "Confirmer",
    "review.cancel": "Annuler",
    "error.INSUFFICIENT_FUNDS": "Solde insuffisant : il vous manque {missing}"
  }
}
```
