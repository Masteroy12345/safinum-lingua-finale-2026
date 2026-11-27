# S07 — Solde insuffisant · USSD · Français

## Saisies

**Initier un transfert avec montant trop élevé :**
```
2
ou
envoyer
```
Bénéficiaire :
```
677000002
```
Montant supérieur au solde :
```
500000
```

**Réponse attendue :**
```
Solde insuffisant
Solde : 253 177 FCFA
1. Changer montant  0. Annuler
```

**Intent :** `TRANSFER` · `transaction.status` : `none` · Code API : `INSUFFICIENT_FUNDS (422)`
