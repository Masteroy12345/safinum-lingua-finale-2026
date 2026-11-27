# S01 — Consultation de solde · USSD · Duálá (dua)

**Interface :** USSD · **Langue :** Duálá

---

## Saisies à copier-coller

**Tour 1 — menu :**  *(automatique, rien à saisir)*

**Tour 2 — solde :**
```
1
```
ou
```
mòni wam
```

**Réponse attendue :**
```
Mòni wam : 253 177 FCFA
```
> "Mòni wam" = votre solde. Intent : `BALANCE_INQUIRY`, langue : `dua`.

---

## Mots-clés Duálá reconnus

| Intention | Mots-clés |
|-----------|-----------|
| Solde | mòni wam, solde, balance |
| Transfert | njem, envoyer, fëb |
| Frais | mintuma njem, frais |
| Historique | mvog njem, historique |
