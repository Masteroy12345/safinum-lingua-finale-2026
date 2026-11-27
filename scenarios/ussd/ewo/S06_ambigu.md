# S06 — Demande ambiguë · USSD · Ewondo (ewo)

**Interface :** USSD  
**Langue :** Ewondo  
**Ce que le jury teste :** une formulation incomplète → le middleware demande une précision, ne devine pas, ne débite pas.

---

## Déroulement

### Tour 1 — Formulation ambiguë

Saisir (phrases à intention floue) :
```
fëb
```
ou
```
mòni
```
ou
```
aide moi
```
ou
```
677000002
```
*(numéro seul, sans montant)*

**Réponse attendue :**
```
Mòni wom a bëk ma a ne tân ya ?
1. Mòni wom
2. Fëb mòni
3. Mintuma
0. Fôl
```
> *Explication :* "Je n'ai pas bien compris, que voulez-vous faire ?" Le middleware retourne `CLARIFICATION_NEEDED` et propose des options claires. Aucun appel bancaire.

---

### Tour 2 — Clarification apportée

Saisir :
```
2
```

**Réponse attendue :** le flow de transfert démarre normalement (voir S02).

---

## Vérifications jury

| Critère | Attendu |
|---------|---------|
| `intent` tour 1 | `CLARIFICATION_NEEDED` |
| Appel bancaire tour 1 | **Aucun** |
| `end_session` | `false` |
| Menu proposé | ✅ options numérotées |

---

## Variantes à tester

| Saisie | Comportement attendu |
|--------|----------------------|
| `envoyer` | CLARIFICATION_NEEDED (montant manquant) |
| `10000` | CLARIFICATION_NEEDED (destinataire manquant) |
| `` (vide) | Menu d'accueil |
