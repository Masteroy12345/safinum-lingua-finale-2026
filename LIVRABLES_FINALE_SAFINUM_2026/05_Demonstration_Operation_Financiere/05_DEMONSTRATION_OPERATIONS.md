# 5. Démonstration d'Opération Financière Complète & 10 Scénarios du Jury

Cette section présente les **traces d'exécution réelles** générées par notre suite de tests automatisés contre le contrat officiel de la passerelle `Safinum Gateway`, incluant un transfert complet en **2 tours stricts** (initiation `pending` puis confirmation avec un `X-Trace-Id` différent) ainsi que la couverture des **10 scénarios standardisés du jury**.

### 1. Consultation du solde (USSD Ewondo)
- **Requête (`POST /middleware`) :** `{"trace_id": "demo-01", "channel": "ussd", "phone": "237677000001", "language": "ewo", "input": {"type": "menu", "text": "1"}}`
- **Statut HTTP :** `200`
- **Réponse retournée :**
```json
{
  "response": {
    "text": "Mone Amina: 250 000 FCFA. 1.Lom 2.Fre 0.Menu",
    "end_session": true,
    "options": []
  },
  "interpretation": {
    "intent": "BALANCE_INQUIRY",
    "parameters": {
      "balance": 250000,
      "currency": "XAF"
    },
    "language": "ewo"
  },
  "transaction": {
    "id": null,
    "status": "none"
  }
}
```

### 2a. Initiation transfert (USSD Fulfulde)
- **Requête (`POST /middleware`) :** `{"trace_id": "demo-02a", "channel": "ussd", "phone": "237677000001", "language": "fub", "input": {"type": "text", "text": "nel 5000 FCFA e 677000002"}}`
- **Statut HTTP :** `200`
- **Réponse retournée :**
```json
{
  "response": {
    "text": "Nel 5 000 FCFA e 237677000002. Njobdi 50, Fuu 5 050 FCFA.\n1.Tabbitin\n2.Habbit",
    "end_session": false,
    "options": [
      "Confirmer",
      "Annuler"
    ]
  },
  "interpretation": {
    "intent": "TRANSFER",
    "parameters": {
      "amount": 5000,
      "beneficiary": "237677000002",
      "to": "237677000002",
      "fee": 50,
      "total": 5050,
      "currency": "XAF"
    },
    "language": "fub"
  },
  "transaction": {
    "id": "TRX-9001",
    "status": "pending"
  }
}
```

### 5. Correction montant avant confirmation (Mobile)
- **Requête (`POST /middleware`) :** `{"trace_id": "demo-05", "channel": "mobile", "phone": "237677000001", "language": "fr", "input": {"type": "text", "text": "modifier le montant à 10000"}}`
- **Statut HTTP :** `200`
- **Réponse retournée :**
```json
{
  "response": {
    "text": "Recapitulatif : transfert de 10 000 FCFA vers 237677000002 (237677000002). Frais : 150 FCFA. Total : 10 150 FCFA. Repondez 1 (Confirmer) ou 2 (Annuler).",
    "end_session": false,
    "options": [
      "Confirmer",
      "Annuler"
    ]
  },
  "interpretation": {
    "intent": "CORRECTION",
    "parameters": {
      "amount": 10000,
      "beneficiary": "237677000002",
      "fee": 150,
      "total": 10150,
      "currency": "XAF"
    },
    "language": "fr"
  },
  "transaction": {
    "id": "TRX-9001",
    "status": "pending"
  }
}
```

### 2b. Confirmation Tour 2 distinct (USSD Fulfulde)
- **Requête (`POST /middleware`) :** `{"trace_id": "demo-02b", "channel": "ussd", "phone": "237677000001", "language": "fub", "input": {"type": "text", "text": "tabbitin"}}`
- **Statut HTTP :** `200`
- **Réponse retournée :**
```json
{
  "response": {
    "text": "Gasii! Ref:TRX-9001. 10 000 FCFA. 0.Menu",
    "end_session": true,
    "options": []
  },
  "interpretation": {
    "intent": "CONFIRM",
    "parameters": {
      "transaction_id": "TRX-9001",
      "amount": 10000,
      "currency": "XAF"
    },
    "language": "fub"
  },
  "transaction": {
    "id": "TRX-9001",
    "status": "confirmed"
  }
}
```

### 3. Demande de frais (USSD Français)
- **Requête (`POST /middleware`) :** `{"trace_id": "demo-03", "channel": "ussd", "phone": "237677000001", "language": "fr", "input": {"type": "text", "text": "quels sont les frais pour 5000"}}`
- **Statut HTTP :** `200`
- **Réponse retournée :**
```json
{
  "response": {
    "text": "Frais 5 000 FCFA: 50 FCFA. Total: 5 050 FCFA. 0.Menu",
    "end_session": false,
    "options": []
  },
  "interpretation": {
    "intent": "FEE_INQUIRY",
    "parameters": {
      "amount": 5000,
      "type": "transfer",
      "fee": 50,
      "total": 5050,
      "currency": "XAF"
    },
    "language": "fr"
  },
  "transaction": {
    "id": null,
    "status": "none"
  }
}
```

### 4. Historique des transactions (USSD Anglais)
- **Requête (`POST /middleware`) :** `{"trace_id": "demo-04", "channel": "ussd", "phone": "237677000001", "language": "en", "input": {"type": "text", "text": "show my transaction history"}}`
- **Statut HTTP :** `200`
- **Réponse retournée :**
```json
{
  "response": {
    "text": "Your last 1 transactions:\n- transfer: 10 000 FCFA 237677000002",
    "end_session": false,
    "options": []
  },
  "interpretation": {
    "intent": "TRANSACTION_HISTORY",
    "parameters": {
      "count": 1
    },
    "language": "en"
  },
  "transaction": {
    "id": null,
    "status": "none"
  }
}
```

### 6. Demande ambiguë sans destinataire (USSD)
- **Requête (`POST /middleware`) :** `{"trace_id": "demo-06", "channel": "ussd", "phone": "237677000001", "language": "fr", "input": {"type": "text", "text": "envoyer 5000 FCFA"}}`
- **Statut HTTP :** `200`
- **Réponse retournée :**
```json
{
  "response": {
    "text": "A quel beneficiaire (nom ou numero) souhaitez-vous envoyer 5 000 FCFA ?",
    "end_session": false,
    "options": []
  },
  "interpretation": {
    "intent": "CLARIFICATION_NEEDED",
    "parameters": {
      "amount": 5000
    },
    "language": "fr"
  },
  "transaction": {
    "id": null,
    "status": "none"
  }
}
```

### 7. Solde insuffisant traduit en Duálá (USSD)
- **Requête (`POST /middleware`) :** `{"trace_id": "demo-07", "channel": "ussd", "phone": "237677000001", "language": "dua", "input": {"type": "text", "text": "loma 400000 FCFA na 677000002"}}`
- **Statut HTTP :** `200`
- **Réponse retournée :**
```json
{
  "response": {
    "text": "Moni mongo mu si koki onyola loma di (moni + njoa).",
    "end_session": false,
    "options": []
  },
  "interpretation": {
    "intent": "TRANSFER",
    "parameters": {
      "error_code": "INSUFFICIENT_FUNDS"
    },
    "language": "dua"
  },
  "transaction": {
    "id": null,
    "status": "failed"
  }
}
```

### 8. Changement de langue vers Basaa (USSD)
- **Requête (`POST /middleware`) :** `{"trace_id": "demo-08", "channel": "ussd", "phone": "237677000001", "language": "fr", "input": {"type": "text", "text": "passer en basaa"}}`
- **Statut HTTP :** `200`
- **Réponse retournée :**
```json
{
  "response": {
    "text": "Hop u henha i Basaa. Lelaa me nla hola we?",
    "end_session": false,
    "options": []
  },
  "interpretation": {
    "intent": "LANGUAGE_SWITCH",
    "parameters": {
      "language": "bas"
    },
    "language": "bas"
  },
  "transaction": {
    "id": null,
    "status": "none"
  }
}
```

### 9. Traduction interface Web ui_translation (Ghɔmálá)
- **Requête (`POST /middleware`) :** `{"trace_id": "demo-09", "channel": "web", "type": "ui_translation", "phone": "237677000001", "language": "bbj", "source_language": "fr", "screen": "review", "strings": {"nav.home": {"text": "Accueil", "max_chars": 12}, "review.total": {"text": "Total débité", `
- **Statut HTTP :** `200`
- **Réponse retournée :**
```json
{
  "language": "bbj",
  "strings": {
    "nav.home": "Tse",
    "review.total": "Nkap tsem",
    "error.INSUFFICIENT_FUNDS": "Nkap po ka kwet: o tse {missing}.",
    "help.fee": "Frais ba nkap banki e nyon mba tom nkap po."
  }
}
```

### 10. Explication terminologie financière (langue auto-détectée)
- **Requête (`POST /middleware`) :** `{"trace_id": "demo-10", "channel": "ussd", "phone": "237677000001", "language": null, "input": {"type": "text", "text": "c'est quoi les frais ?"}}`
- **Statut HTTP :** `200`
- **Réponse retournée :**
```json
{
  "response": {
    "text": "Les frais sont la commission prelevee pour traiter votre operation (ex: 50 FCFA jusqu'a 5 000 FCFA, 150 FCFA jusqu'a 25 000 FCFA).",
    "end_session": false,
    "options": []
  },
  "interpretation": {
    "intent": "TERM_EXPLANATION",
    "parameters": {
      "term": "frais"
    },
    "language": "fr"
  },
  "transaction": {
    "id": null,
    "status": "none"
  }
}
```
