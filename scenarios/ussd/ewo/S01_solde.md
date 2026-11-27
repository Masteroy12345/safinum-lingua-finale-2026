# S01 — Consultation de solde · USSD · Ewondo (ewo)

**Interface :** USSD — `/sandbox/ussd`  
**Langue annoncée :** Ewondo  
**Compte :** 237651841190 (Achille Abega, ~253 177 FCFA)

---

## Déroulement

### Tour 1 — L'utilisateur ouvre le menu

Le simulateur envoie automatiquement le menu d'accueil. Rien à saisir.

**Ce que le middleware doit retourner :**
```
Mòni wom a lig ma a ne tân ya?
1. Mòni wom
2. Fëb mòni
3. Crédît téléphonique
4. Fëb be fëb
0. Fôl
```
> *Explication :* Menu principal en Ewondo. "Mòni wom a lig ma a ne tân ya?" = "Comment puis-je vous aider ?"

### Tour 2 — Consultation du solde

**Texte à saisir :**
```
1
```
ou
```
mòni wom
```

**Ce que le middleware doit retourner :**
```
Mòni wom mà : 253 177 FCFA
```
> *Explication :* "Mòni wom mà" = "Votre solde est de". L'intention déclarée doit être `BALANCE_INQUIRY`.

---

## Vérifications jury

| Critère | Attendu |
|---------|---------|
| `interpretation.intent` | `BALANCE_INQUIRY` |
| `interpretation.language` | `ewo` |
| `response.text` contient le montant | ✅ 253 177 |
| Appel bancaire effectué | `GET /accounts/237651841190` avec X-Trace-Id |
| Longueur ≤ 182 septets | ✅ |
| Pas de caractère hors GSM-7 | ✅ (ɔ → o, ŋ → ng translittérés) |

---

## Problèmes fréquents

- **Montant en chiffres arabes** : toujours `253 177` pas `deux cent cinquante-trois mille`
- **X-Trace-Id manquant** sur l'appel bancaire → NO_BANK_CALL côté jury
- **`end_session: true` trop tôt** : laisser `false` pour que l'utilisateur puisse continuer
