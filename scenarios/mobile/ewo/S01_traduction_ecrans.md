# Traduction d'écrans Mobile · Ewondo (ewo)

**Interface :** `/sandbox/mobile` ou `/sandbox/web`  
**Langue :** Ewondo  
**Contrat :** `ui_translation` — le middleware reçoit les clés FR, retourne les clés traduites.

---

## Comment tester

1. Ouvre `/sandbox/mobile`, choisis l'équipe, entre le PASS, sélectionne la langue **Ewondo**
2. Clique **"Afficher les clés"** pour voir les identifiants à traduire
3. Navigue entre les écrans — le middleware traduit en direct

---

## Clés principales par écran

### Écran `home` (Accueil)

| Clé | Texte FR | Traduction Ewondo |
|-----|----------|-------------------|
| `nav.home` | Accueil | Nda |
| `nav.send` | Envoyer | Fëb |
| `nav.pay` | Payer | Payer |
| `nav.history` | Historique | Mvog |
| `home.balance_label` | Solde disponible | Mòni wom |
| `home.balance_value` | 253 177 FCFA | 253 177 FCFA *(inchangé)* |
| `home.send_button` | Envoyer de l'argent | Fëb mòni |

### Écran `transfer` (Envoi)

| Clé | Texte FR | Traduction Ewondo |
|-----|----------|-------------------|
| `transfer.title` | Envoyer de l'argent | Fëb mòni |
| `transfer.recipient` | Bénéficiaire | Nnom |
| `transfer.amount` | Montant | Nkap |
| `transfer.fee_label` | Frais | Mintuma |
| `transfer.total` | Total débité | Fëb yam |

### Écran `review` (Relecture)

| Clé | Texte FR | Traduction Ewondo |
|-----|----------|-------------------|
| `review.title` | Vérifier l'envoi | Zal fëb |
| `review.confirm` | Confirmer | Confirm |
| `review.cancel` | Annuler | Fôl |
| `review.total` | Total débité | Fëb yam |

### Messages d'erreur

| Clé | Texte FR | Traduction Ewondo |
|-----|----------|-------------------|
| `error.INSUFFICIENT_FUNDS` | Solde insuffisant : il vous manque {missing} | Mòni wom a kpé a : {missing} a kpé a nà |
| `error.UNKNOWN_BENEFICIARY` | Bénéficiaire introuvable | Nnom a ngo a kpé a |
| `error.LIMIT_EXCEEDED` | Montant supérieur au plafond | Nkap a dëp a montant maximum |

---

## Règles critiques

- **Garder les placeholders** `{missing}`, `{amount}`, `{name}` tels quels — l'appli les remplace
- **Respecter `max_chars`** : `nav.*` = 12 chars max (onglets), boutons = 15 max
- **Toutes les clés doivent être présentes** — une clé absente s'affiche en français (MISSING_STRINGS)
- **≥ 25% des clés doivent être différentes du français** sinon marqué UNTRANSLATED

---

## Réponse JSON type

```json
{
  "language": "ewo",
  "strings": {
    "nav.home": "Nda",
    "nav.send": "Fëb",
    "nav.pay": "Payer",
    "nav.history": "Mvog",
    "home.balance_label": "Mòni wom",
    "transfer.title": "Fëb mòni",
    "transfer.recipient": "Nnom",
    "transfer.amount": "Nkap",
    "review.confirm": "Confirm",
    "review.cancel": "Fôl",
    "error.INSUFFICIENT_FUNDS": "Mòni wom a kpé a : {missing} a kpé a nà"
  }
}
```
