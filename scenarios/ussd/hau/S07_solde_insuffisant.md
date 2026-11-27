# S07 — Solde insuffisant · USSD · Haoussa

## Saisies

**Initier un transfert avec montant trop élevé :**
```
2
ou
aika
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
Ba kuɗi ba
Solde : 253 177 FCFA
1. Changer montant  0. Annuler
```

**Intent :** `TRANSFER` · `transaction.status` : `none` · Code API : `INSUFFICIENT_FUNDS (422)`
