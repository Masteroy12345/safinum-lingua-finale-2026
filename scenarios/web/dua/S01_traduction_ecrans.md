# Traduction d'écrans Mobile/Web · Duálá

**Interface :** `/sandbox/mobile` et `/sandbox/web`  
**Langue :** Duálá (`dua`)

---

## Clés principales

| Clé | Texte FR | Traduction Duálá |
|-----|----------|-------------------|
| `nav.home` | Accueil | Mboka |
| `nav.send` | Envoyer | Njem |
| `nav.history` | Historique | Mvog njem |
| `home.balance_label` | Solde disponible | Mòni wam |
| `transfer.recipient` | Bénéficiaire | Mfumu |
| `review.confirm` | Confirmer | Confirm |
| `review.cancel` | Annuler | Fôl |
| `error.INSUFFICIENT_FUNDS` | Solde insuffisant : il vous manque {missing} | Mòni a kpé a : {missing} a wɛl nà |

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
  "language": "dua",
  "strings": {
    "nav.home": "Mboka",
    "nav.send": "Njem",
    "nav.history": "Mvog njem",
    "home.balance_label": "Mòni wam",
    "transfer.recipient": "Mfumu",
    "review.confirm": "Confirm",
    "review.cancel": "Fôl",
    "error.INSUFFICIENT_FUNDS": "Mòni a kpé a : {missing} a wɛl nà"
  }
}
```
