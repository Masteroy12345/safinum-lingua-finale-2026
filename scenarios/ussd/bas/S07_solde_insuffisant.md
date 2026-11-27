# S07 — Solde insuffisant · USSD · Ɓasaá

## Saisies

**Initier un transfert avec montant trop élevé :**
```
2
ou
tondl
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
Nkap a hii nà
Solde : 253 177 FCFA
1. Changer montant  0. Annuler
```

**Intent :** `TRANSFER` · `transaction.status` : `none` · Code API : `INSUFFICIENT_FUNDS (422)`
