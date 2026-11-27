# S02 — Transfert avec confirmation · USSD · Mə̀dûmbà

## Saisies

**Tour 1 :**
```
2
ou
yeel nkap
```
**Tour 2 :** saisir `677000002` puis `5000`

**Tour 2 — relecture attendue :**
```
Yeel nkap : 5 000 FCFA → 677000002
Mintuma / frais : 50 FCFA
1. Confirm  0. Annuler
```

**Tour 3 — confirmation :**
```
1
```

**Réponse :**
```
Yeel a yuu !
5 000 FCFA → 677000002
```
> ⚠️ X-Trace-Id **différent** au tour 3.

**Intent tour 3 :** `CONFIRM`
