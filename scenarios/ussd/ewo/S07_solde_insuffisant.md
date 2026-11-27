# S07 — Solde insuffisant · USSD · Ewondo (ewo)

**Interface :** USSD  
**Langue :** Ewondo  
**Ce que le jury teste :** l'erreur INSUFFICIENT_FUNDS est expliquée en Ewondo, avec le solde actuel et les options.

---

## Déroulement

### Tour 1 — Initier un transfert avec montant trop élevé

Saisir (transfert > solde) :
```
2
```
Bénéficiaire :
```
677000002
```
Montant supérieur au solde (~253 177 FCFA) :
```
500000
```

**Réponse attendue :**
```
Mòni wom a kpé a : 253 177 FCFA
Fëb 500 000 FCFA a kpé a nà.
1. Zal montant  0. Fôl
```
> *Explication :*  
> "Mòni wom a kpé a" = "Votre solde est de"  
> "Fëb ... a kpé a nà" = "Le transfert de ... n'est pas possible"  
> L'utilisateur peut choisir un autre montant (option 1) ou annuler (option 0).

---

## Vérifications jury

| Critère | Attendu |
|---------|---------|
| `intent` | `TRANSFER` |
| `transaction.status` | `none` (rien n'a été débité) |
| Erreur traduite | ✅ en Ewondo |
| Solde affiché | ✅ 253 177 FCFA |
| Options proposées | ✅ changer montant ou annuler |
| Appel bancaire | `POST /transactions` → retourne INSUFFICIENT_FUNDS (422) |

---

## Conseil

Ne jamais afficher "INSUFFICIENT_FUNDS" en clair devant l'utilisateur. C'est le code d'erreur interne → il doit être traduit dans la langue.
