# S02 — Transfert avec confirmation · USSD · Ewondo (ewo)

**Interface :** USSD  
**Langue :** Ewondo  
**Règle critique :** le débit n'a lieu qu'au **tour 3** (tour de confirmation), jamais au tour d'initiation.

---

## Déroulement

### Tour 1 — Menu

Saisir :
```
2
```
ou
```
fëb mòni
```

**Réponse attendue :**
```
A zal nnom mòni ne bé ye nté ?
(Numéro du bénéficiaire)
```
> *Explication :* "À qui envoyer de l'argent ?" Le middleware attend le numéro.

---

### Tour 2 — Montant et bénéficiaire

Saisir un numéro de bénéficiaire valide :
```
677000002
```

**Réponse attendue :**
```
Fëb mòni : 677000002
Montant (FCFA) ?
```

Saisir :
```
5000
```

**Réponse attendue (relecture) :**
```
Fëb 5 000 FCFA a 677000002
Fëb : 5 000 FCFA
Mintuma : 50 FCFA
Fëb yam : 5 050 FCFA
1. Confirm  0. Fôl
```
> *Explication :* Le middleware crée une transaction `pending` via `POST /transactions` mais **ne confirme pas encore**. Il relit les détails à l'utilisateur.  
> `Mintuma` = frais (50 FCFA pour 5 000 FCFA selon la grille officielle)

---

### Tour 3 — Confirmation ⚠️

**Saisir :**
```
1
```
ou
```
confirm
```

**Réponse attendue :**
```
Fëb mòni a kes !
TRX-XXXXXXXX : 5 000 FCFA → 677000002
Mòni wom mà : 248 127 FCFA
```
> *Explication :* Le middleware appelle `POST /transactions/{id}/confirm` avec un **nouveau X-Trace-Id** (différent de celui du tour 2). L'argent bouge ici.

---

## Vérifications jury

| Tour | Intent | Appel bancaire |
|------|--------|----------------|
| Tour 1 | `TRANSFER` | Aucun (attente saisie) |
| Tour 2 | `TRANSFER` | `GET /fees`, `POST /transactions` (pending) |
| Tour 3 | `CONFIRM` | `POST /transactions/{id}/confirm` avec **X-Trace-Id différent** |

**Erreur fatale :** confirmer au même tour que l'initiation → marqué ÉCHEC automatiquement.

---

## Problèmes fréquents

- Oublier de relire avant confirmation
- Envoyer le même `X-Trace-Id` au tour de confirmation
- Ne pas inclure les frais dans la relecture
