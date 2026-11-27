# S08 — Changement de langue · USSD · Ewondo → Duálá (ewo → dua)

**Interface :** USSD  
**Langue initiale :** Ewondo  
**Ce que le jury teste :** en pleine conversation, l'utilisateur change de langue → la suite se fait dans la nouvelle langue.

---

## Déroulement

### Tour 1 — En cours de conversation (solde)

Saisir :
```
1
```
*(sélection solde depuis le menu)*

**Réponse en Ewondo :**
```
Mòni wom mà : 253 177 FCFA
```

---

### Tour 2 — Demande de changement de langue

Saisir :
```
parle duala
```
ou
```
duala
```
ou
```
switch to duala
```
ou (depuis l'option dédiée si affichée) :
```
9
```

**Réponse attendue en Duálá :**
```
Simu ya Duálá !
Ndé bâ nde ngo njé ?
1. Mòni wam
2. Njem
3. Crédit ya waya
0. Fôl
```
> *Explication :* Le middleware détecte `LANGUAGE_SWITCH` vers `dua`, met à jour la session, et répond immédiatement en Duálá. "Ndé bâ nde ngo njé ?" = "Comment puis-je vous aider ?"

---

### Tour 3 — Continuer en Duálá

Saisir :
```
1
```

**Réponse en Duálá :**
```
Mòni wam : 253 177 FCFA
```

---

## Vérifications jury

| Tour | Intent | Langue de réponse |
|------|--------|-------------------|
| Tour 1 | `BALANCE_INQUIRY` | `ewo` |
| Tour 2 | `LANGUAGE_SWITCH` | `dua` (réponse déjà en Duálá) |
| Tour 3 | `BALANCE_INQUIRY` | `dua` |

---

## Mots-clés de déclenchement reconnus

| Saisie | Langue cible |
|--------|-------------|
| `parle ewondo` / `ewondo` | `ewo` |
| `parle duala` / `duala` | `dua` |
| `basaa` / `ɓasaá` | `bas` |
| `fulfulde` / `peul` | `fub` |
| `pidgin` / `pidgin english` | `wes` |
| `français` / `fr` | `fr` |
| `english` / `anglais` | `en` |
