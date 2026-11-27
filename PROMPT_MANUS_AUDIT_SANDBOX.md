# Prompt d'Audit Complet — Bac à Sable SAFINUM 2026 (Équipe : Dev space ICT)

Tu es un **auditeur linguistique, technique et UX spécialisé dans les langues camerounaises et les services financiers numériques**.

Ta mission est de **parcourir en vrai avec ton navigateur intégré** les 3 interfaces du bac à sable officiel du concours SAFINUM Innovate Challenge 2026 pour notre équipe **`Dev space ICT`** :
1. **Simulateur USSD** : `https://www.safinum.cm/sandbox/ussd`
2. **Simulateur Mobile** : `https://www.safinum.cm/sandbox/channel/mobile`
3. **Simulateur Web** : `https://www.safinum.cm/sandbox/channel/web`

---

## 1. Configuration initiale obligatoire sur chaque interface
- **Équipe** : sélectionner **`Dev space ICT`**
- **Comptes de test à utiliser** :
  - Compte principal solvable : **Amadou Kamga** (`237657096450`) ou **Serge Tchoupo** (`237696411096`)
  - Compte presque vide (pour `INSUFFICIENT_FUNDS`) : **Achille Kamga** (`237658473555`) ou **Franck Manga** (`237650674271`)
  - Homonymes (pour `CLARIFICATION_NEEDED`) : **Paul Sali** (`237653633039` et `237653159224`)
- **Activer** `GSM-7 strict` sur USSD et inspecter systématiquement le panneau **« Diagnostics »** (code HTTP, durée, violations GSM-7, longueur vs 182 septets, clés manquantes, `PLACEHOLDER_BROKEN`, `OVER_LENGTH`, `UNTRANSLATED`, `realism_flags`).

---

## 2. Langues à tester obligatoirement (toutes nos langues travaillées)
Teste **chacune** des langues suivantes disponibles dans le sélecteur du sandbox :
1. **Duálá (`dua`)**
2. **Ewondo (`ewo`)**
3. **Ɓasaá (`bas`)**
4. **Ghɔmálá' (`bbj`)**
5. **Mə̀dûmbà (`byv`)**
6. **Fulfulde (`fub`)**
7. **Haoussa (`hau`)**
8. **Bulu (`bum`)**
9. **Français (`fr`)** et **Anglais (`en`)** (référence)
10. **Non précisée (`null`)** (vérifier la détection automatique de langue)

---

## 3. Parcours complet à exécuter sur les 3 canaux

### A. Canal USSD (`/sandbox/ussd`) — Tester les 10 scénarios officiels
1. **Consultation de solde** (sans prononcer le mot français « solde » : ex. *« Mbolo, mòni wom a lig ma a ne tan ya ? »* en Ewondo, *« Nawa ne ragowar kudina ? »* en Haoussa, etc.)
2. **Transfert avec confirmation en 2 tours** (Tour 1 : initier + vérifier relecture montant/frais/total + statut `pending` ; Tour 2 : confirmer)
3. **Demande de frais** aux bornes de palier (`5 000 FCFA` et `25 000 FCFA`)
4. **Historique des opérations** (vérifier lisibilité et longueur ≤ 182 septets GSM-7)
5. **Correction avant confirmation** (initier `5 000 FCFA`, corriger à `10 000 FCFA` avant de confirmer, vérifier que les frais sont recalculés)
6. **Demande ambiguë (`CLARIFICATION_NEEDED`)** :
   - Transfert sans bénéficiaire ni montant
   - Transfert vers un homonyme (**Paul Sali**) -> vérifier que la couche demande de choisir sans deviner
7. **Solde insuffisant (`INSUFFICIENT_FUNDS`)** sur **Achille Kamga** -> vérifier que le code brut `INSUFFICIENT_FUNDS` n'apparaît jamais et que l'erreur est expliquée dans la langue cible
8. **Changement de langue en cours de conversation** (commencer en Ewondo, basculer en Duálá ou Fulfulde au milieu d'un transfert sans perdre le contexte)
9. **Parcours multicanal** (initier en USSD, puis ouvrir l'historique Web/Mobile avec le même compte)
10. **Terminologie financière** (demander ce que veut dire `frais`, `plafond`, `bénéficiaire` dans la langue nationale -> explication claire pour quelqu'un n'ayant jamais eu de compte bancaire)
11. **Bonus** : Paiement de facture (`ENEO` / `CAMWATER`) et achat de crédit (`MTN` / `ORANGE`)

### B. Canaux Mobile (`/sandbox/channel/mobile`) et Web (`/sandbox/channel/web`)
Pour **chaque langue nationale (`dua`, `ewo`, `bas`, `bbj`, `byv`, `fub`, `hau`, `bum`)**, ouvrir les **6 écrans** :
- `home` (Accueil)
- `transfer` (Envoyer — y compris aperçu des frais + bulles d'aide `(i)`)
- `pay` (Payer facture & crédit)
- `review` (Relecture avant confirmation)
- `receipt` (Reçu)
- `history` (Historique + filtres + statuts)

Cocher aussi **« Afficher les clés à la place des textes »** et **« Comparer source et traduction »** pour relever les clés exactes.

---

## 4. Critères d'audit stricts attendus dans ton rapport

Pour **chaque langue** et **chaque écran / scénario**, vérifie et note :
1. **Exactitude linguistique & authenticité** :
   - Est-ce le **mot exact / expression idiomatique authentique** dans la langue ?
   - Signale tout **faux calque phonétique inventé** (ex. `kredit`, `faktir`, `konte`, `konekson`, `enternet`, `televizion`) ou toute traduction erronée (ex. pronom possessif inversé *mon/ton*, faux ami).
   - Quand un mot technique n'existe pas en langue nationale, vérifie s'il existe un **synonyme / périphrase naturelle** ou s'il vaut mieux conserver le terme intact, et **propose la correction exacte**.
2. **Confidentialité & Variables dynamiques** :
   - Vérifie qu'aucune traduction statique ne contient de montant figé, de nom de client figé ni de numéro de téléphone figé (uniquement des variables dynamiques `{amount}`, `{name}`, `{phone}`, `{fee}`, `{max}`, `{missing}` correctement remplies à l'écran).
3. **Voix, Prononciation & Lecture des numéros de téléphone** :
   - Teste le bouton **haut-parleur / Lecture vocale** sur Mobile et Web (et le studio audio `https://maryellen-parchable-gertude.ngrok-free.dev/studio` si accessible).
   - Évalue :
     - La prononciation de chaque phrase en langue camerounaise (tons, voyelles, fluidité).
     - La lecture dynamique des **montants** (`FCFA`) et des **noms propres** (jamais traduits).
     - La lecture dynamique des **numéros de téléphone variables** (ex. `237657096450`, `237653633039`) : sont-ils bien décomposés en blocs naturels (`237, 6, 57, zéro 9, 64, 50`) sans avaler les zéros ni lire un nombre géant ?
     - Le comportement de la synthèse navigateur (`Aucune voix ... sur ce navigateur`) et les améliorations possibles.
4. **Conformité technique Jury SAFINUM** :
   - Statut HTTP, latence (ms), `gsm7_violations`, `over_limit`, `MISSING_STRINGS`, `PLACEHOLDER_BROKEN`, `OVER_LENGTH`, `UNTRANSLATED`, `NO_BANK_CALL`, `realism_flags`.

---

## 5. Format de sortie exigé (fichier Markdown `.md`)
Retourne l'intégralité de ton audit dans un fichier **`.md`** structuré comme suit :

1. **Synthèse exécutive** (score global `/100`, points forts, anomalies bloquantes vs mineures).
2. **Tableau de conformité technique** (USSD / Mobile / Web × 8 langues camerounaises : HTTP, latence, GSM-7, anomalies).
3. **Audit détaillé des 10 scénarios USSD** (entrée testée, réponse reçue, verdict `PASS/FAIL`, commentaire).
4. **Audit linguistique clé par clé (par langue : `dua`, `ewo`, `bas`, `bbj`, `byv`, `fub`, `hau`, `bum`)** sous forme de tableau Markdown :
   `| Clé / Contexte | Français (source) | Traduction actuelle | Exact ? (Oui/Non) | Correction proposée | Justification linguistique |`
5. **Audit Audio, Voix & Prononciation** (qualité vocale par langue, prononciation des tons, lecture des montants/noms/numéros de téléphone variables, recommandations concrètes).
6. **Plan d'action priorisé** (top corrections immédiates classées par impact Jury).
