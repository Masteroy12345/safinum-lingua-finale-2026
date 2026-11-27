# Scénarios de Test — Safinum Innovate Challenge 2026

**Équipe : Dev space ICT**

Chaque dossier = une interface. Dedans, un dossier par langue. Dedans, un fichier MD par scénario.  
Les textes sont prêts à copier-coller dans le simulateur. Les réponses attendues sont expliquées en français.

## Structure

```
scenarios/
├── ussd/       ← simulateur USSD (*123# / menu)
├── mobile/     ← simulateur application mobile
├── web/        ← simulateur interface web
├── sms/        ← simulateur SMS (8123)
├── atm/        ← simulateur guichet automatique
└── ivr/        ← simulateur serveur vocal (micro)
    ├── fr/     ← Français
    ├── ewo/    ← Ewondo
    ├── dua/    ← Duálá
    ├── bas/    ← Ɓasaá
    ├── bbj/    ← Ghɔmálá'
    ├── byv/    ← Mə̀dûmbà
    ├── fub/    ← Fulfulde
    ├── hau/    ← Haoussa
    ├── bum/    ← Bulu
    └── wes/    ← Pidgin Camerounais
```

## Les 10 scénarios officiels

| # | Nom | Ce que le jury vérifie |
|---|-----|------------------------|
| S01 | Consultation de solde | Réponse dans la langue, montant correct |
| S02 | Transfert avec confirmation | 2 tours, argent bouge au 2e tour seulement |
| S03 | Demande de frais | Calcul correct, réponse traduite |
| S04 | Historique des opérations | Liste traduite |
| S05 | Correction avant confirmation | CORRECTION capturé, opération modifiée |
| S06 | Demande ambiguë | CLARIFICATION_NEEDED, pas de débit |
| S07 | Solde insuffisant | Erreur expliquée dans la langue |
| S08 | Changement de langue | LANGUAGE_SWITCH, suite dans la nouvelle langue |
| S09 | Parcours multicanal | Même numéro, session différente |
| S10 | Terminologie financière | TERM_EXPLANATION, explication en langue nationale |

## Compte de test

- **Numéro :** 237651841190 (Achille Abega)
- **Solde :** ~253 177 FCFA
- **PASS simulateur :** 4BZ (ou vérifie avec `GET /api/v1/sandbox/endpoint`)
