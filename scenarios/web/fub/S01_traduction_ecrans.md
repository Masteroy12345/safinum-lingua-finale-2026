# Traduction d'écrans Mobile/Web · Fulfulde

**Interface :** `/sandbox/mobile` et `/sandbox/web`  
**Langue :** Fulfulde (`fub`)

---

## Clés principales

| Clé | Texte FR | Traduction Fulfulde |
|-----|----------|-------------------|
| `nav.home` | Accueil | Galle |
| `nav.send` | Envoyer | Haaɓ |
| `nav.history` | Historique | Mvog |
| `home.balance_label` | Solde disponible | Céédé maa |
| `transfer.recipient` | Bénéficiaire | Jom |
| `review.confirm` | Confirmer | Confirm |
| `review.cancel` | Annuler | Haɓɓu |
| `error.INSUFFICIENT_FUNDS` | Solde insuffisant : il vous manque {missing} | Céédé alaa : {missing} alaa |

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
  "language": "fub",
  "strings": {
    "nav.home": "Galle",
    "nav.send": "Haaɓ",
    "nav.history": "Mvog",
    "home.balance_label": "Céédé maa",
    "transfer.recipient": "Jom",
    "review.confirm": "Confirm",
    "review.cancel": "Haɓɓu",
    "error.INSUFFICIENT_FUNDS": "Céédé alaa : {missing} alaa"
  }
}
```
