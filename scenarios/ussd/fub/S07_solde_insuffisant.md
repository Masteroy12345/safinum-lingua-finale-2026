# S07 — Solde insuffisant · USSD · Fulfulde

## Saisies

**Initier un transfert avec montant trop élevé :**
```
2
ou
haaɓ
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
Céédé alaa ɗo
Solde : 253 177 FCFA
1. Changer montant  0. Annuler
```

**Intent :** `TRANSFER` · `transaction.status` : `none` · Code API : `INSUFFICIENT_FUNDS (422)`
