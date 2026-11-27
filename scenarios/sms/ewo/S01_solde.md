# S01 — Consultation de solde · SMS · Ewondo (ewo)

**Interface :** `/sandbox/sms` · Numéro court **8123**  
**Langue :** Ewondo  
**Différence avec USSD :** pas de session (`session_id: null`), chaque SMS est autonome, réponse ≤ 160 chars GSM-7.

---

## SMS à envoyer (copier-coller dans le simulateur)

```
mòni wom
```
ou
```
1
```
ou
```
solde
```
ou
```
balance
```

---

## Réponse attendue

```
Mòni wom : 253 177 FCFA
```

> Longueur : 32 chars — bien sous la limite de 160.  
> Le `ò` est en GSM-7 étendu (1,5 septet). Vérifier que la longueur réelle ≤ 160 septets.

---

## Points de vigilance SMS

| Contrainte | Valeur |
|------------|--------|
| Alphabet | GSM-7 (160 chars) ou UCS-2 si caractère hors GSM-7 (70 chars) |
| Session | Aucune — le middleware doit retenir le contexte par numéro |
| Réponse différée | Possible : 202 + POST `/api/v1/sms/send` avec même X-Trace-Id |
| Max segments | 3 (au-delà : TOO_MANY_SEGMENTS) |

---

## Caractères Ewondo en GSM-7

| Symbole AGLC | Équivalent GSM-7 | Coût |
|---|---|---|
| `ɔ` | `o` | 1 septet |
| `ɛ` | `e` | 1 septet |
| `ŋ` | `ng` | 2 septets |
| `ë` (tréma) | Hors GSM-7 → passe en UCS-2 | 70 chars max |

> Notre middleware translittère automatiquement pour le SMS.
