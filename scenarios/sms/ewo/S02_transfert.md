# S02 — Transfert · SMS · Ewondo (ewo)

**Interface :** `/sandbox/sms`  
**Langue :** Ewondo  
**Particularité :** pas de session, le contexte est gardé par numéro dans le middleware.

---

## SMS 1 — Initier

Envoyer :
```
fëb 5000 a 677000002
```
ou
```
envoye 5000 677000002
```

**Réponse SMS 1 :**
```
Fëb 5000 FCFA a 677000002
Mintuma: 50 FCFA. Total: 5050 FCFA
Repond 1 pou confirm, 0 pou fol
```
> Longueur : ~75 chars. La translittération `ë` → `e` garde le SMS en GSM-7.

---

## SMS 2 — Confirmer (SMS suivant)

Envoyer :
```
1
```
ou
```
confirm
```
ou
```
oui
```

**Réponse SMS 2 :**
```
Fëb kes! 5000 FCFA → 677000002
Moni wom: 248127 FCFA
```

---

## Points importants

- Le X-Trace-Id du SMS 2 est **différent** du SMS 1 (deux requêtes séparées)
- Le middleware retrouve la transaction pending via la session en mémoire (clé = numéro de téléphone)
- Si la session expire (middleware redémarré), le middleware doit chercher dans `GET /accounts/{phone}/transactions`
