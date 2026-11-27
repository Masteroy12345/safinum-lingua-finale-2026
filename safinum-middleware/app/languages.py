"""Moteur multilingue SAFINUM Lingua : 8 langues ISO 639-3 du sandbox + Pidgin (wes).

Inclut les gabarits conversationnels (Web/Mobile) et compacts (USSD <= 182 septets),
les 12 codes d'erreur traduits, et les explications de terminologie financière.
"""
import re
from typing import Any

# 7 Langues Nationales Camerounaises (incl. Pidgin Camerounais) + Langues officielles (FR/EN) pour le pivot/source
CAMEROON_NATIONAL_LANGUAGES = {
    "dua": "Duálá (Cameroun)",
    "ewo": "Ewondo (Cameroun)",
    "bas": "Ɓasaá (Cameroun)",
    "bbj": "Ghɔmálá' (Cameroun)",
    "byv": "Mə̀dûmbà (Cameroun)",
    "fub": "Fulfulde (Cameroun)",
    "hau": "Haoussa (Cameroun)",
    "bum": "Bulu (Cameroun)",
    "wes": "Pidgin Camerounais (Kamtok)",
}

SUPPORTED_LANGUAGES = {
    "dua": "Duálá",
    "ewo": "Ewondo",
    "bas": "Ɓasaá",
    "bbj": "Ghɔmálá'",
    "byv": "Mə̀dûmbà",
    "fub": "Fulfulde",
    "hau": "Haoussa",
    "bum": "Bulu",
    "wes": "Pidgin Camerounais (Kamtok)",
    "fr": "Français",
    "en": "English",
}

LANGUAGE_ALIASES = {
    "fr": "fr", "francais": "fr", "français": "fr", "french": "fr",
    "en": "en", "anglais": "en", "english": "en",
    "ewo": "ewo", "ewondo": "ewo", "beti": "ewo",
    "bum": "bum", "bulu": "bum", "boulou": "bum",
    "fub": "fub", "ff": "fub", "fulfulde": "fub", "fula": "fub", "peul": "fub",
    "hau": "hau", "ha": "hau", "hausa": "hau", "haoussa": "hau",
    "dua": "dua", "duala": "dua", "douala": "dua",
    "bas": "bas", "basaa": "bas", "bassa": "bas",
    "bbj": "bbj", "ghomala": "bbj", "bamileke": "bbj", "bandjoun": "bbj",
    "byv": "byv", "medumba": "byv", "bangangte": "byv",
    "wes": "wes", "pidgin": "wes", "kamtok": "wes", "pcm": "wes",
}


def normalize_language(lang: str | None) -> str | None:
    if not lang:
        return None
    key = lang.strip().lower()
    return LANGUAGE_ALIASES.get(key)


def detect_language(text: str, fallback: str = "fr") -> str:
    """Détecte la langue à partir du texte utilisateur lorsque language=null."""
    t = f" {text.lower().strip()} "
    # Mots-clés discriminants par langue nationale camerounaise
    markers = {
        "wes": ["weh", "moni", "pesin", "comot", "fit", "wetin", "abeg", "na ", "don ", "wan ", "how much", "send moni"],
        "fub": ["ceede", "njoɓdi", "njobdi", "neldude", "nel ", "konte", "sannu", "sannou", "tabbitin", "heɓoowo", "heboowo", "meere", "yonaa", "demgal", "golle", "keeri"],
        "hau": ["kudi", "kuɗi", "aika", "asusu", "barka", "ina kwana", "nawa", "saura", "tabbatar", "soke", "tarihi", "kuɗin aiki"],
        "bum": ["mbôlô", "moné", "tyé", "lôm", "kañese", "jôé", "tañ", "kônte", "nkobô", "li'i"],
        "ewo": ["mone", "mòni", "mɔni", "a lig", "a ne va", "wom", "lôm", "lom ", "mbolo", "yebe", "fre ", "kônte", "mod a kos", "zeze", "zezé", "kele", "sûli", "suli", "bili", "ben ", "alom", "nkobo"],
        "dua": ["bwea", "bwam", "idib", "masoma", "na som", "mboa", "ndutu", "môni", "moni ma", "lóma", "loma", "hee", "kem", "mbale", "diba", "njoa", "bola", "timbis"],
        "bas": ["kɛl i lam", "kel i lam", "mɛ̀ ǹyega", "nyega", "lémèl", "lemel", "lôñ", "moni wem", "moni u nkon", "ni nkon", "basa", "ŋ̀ŋ̂", "tɔ̀", "nsas", "bilon", "hémle", "hemle"],
        "bbj": ["ghomala", "mbúʼ", "mbu", "mbou", "ndèmá", "ndema", "ŋkap", "nkap", "nkàp", "yôô", "yoo", "ka'", "tso", "nyam", "bivul", "tom "],
        "byv": ["medumba", "o zi", "làbtə̌", "labte", "ntúm", "ntum", "ncob", "num ", "tso'", "mba'", "bivul", "bwam"],
        "en": ["balance", "transfer", "send ", "fees", "fee ", "history", "confirm", "cancel", "hello", "help", "airtime", "bill", "what is", "how much", "money"],
        "fr": ["solde", "envoyer", "transfert", "frais", "historique", "confirmer", "annuler", "bonjour", "aide", "credit", "crédit", "facture", "c'est quoi", "combien", "argent", "compte"],
    }
    scores: dict[str, int] = {code: 0 for code in markers}
    for code, words in markers.items():
        for w in words:
            if w in t:
                scores[code] += 1
    best_code = max(scores, key=lambda k: scores[k])
    if scores[best_code] > 0:
        return best_code
    return fallback


def fmt_amount(amount: int | float | None) -> str:
    if amount is None:
        return "0"
    val = int(round(float(amount)))
    return f"{val:,}".replace(",", " ")


# Gabarits de réponses par langue (standard + compact USSD)
TEMPLATES: dict[str, dict[str, str]] = {
    "fr": {
        "menu": "Safinum Pay\n1. Solde\n2. Transfert\n3. Frais\n4. Historique\n5. Credit\n6. Facture\n0. Langue",
        "menu_ussd": "Safinum Pay\n1.Solde\n2.Transfert\n3.Frais\n4.Historique\n5.Credit\n6.Facture\n0.Langue",
        "balance": "Bonjour {name}. Votre solde disponible est de {balance} FCFA (compte {phone}).",
        "balance_ussd": "Solde {name}: {balance} FCFA. 1.Transfert 2.Frais 0.Menu",
        "fees": "Pour {amount} FCFA ({op_type}), les frais sont de {fee} FCFA. Total a debiter: {total} FCFA.",
        "fees_ussd": "Frais {amount} FCFA: {fee} FCFA. Total: {total} FCFA. 0.Menu",
        "history_header": "Vos {count} dernieres operations :",
        "history_empty": "Aucune transaction recente trouvee sur votre compte.",
        "confirm_transfer": "Recapitulatif : transfert de {amount} FCFA vers {beneficiary} ({to_phone}). Frais : {fee} FCFA. Total : {total} FCFA. Repondez 1 (Confirmer) ou 2 (Annuler).",
        "confirm_transfer_ussd": "Envoi {amount} FCFA a {beneficiary}. Frais {fee}, Total {total} FCFA.\n1.Confirmer\n2.Annuler",
        "confirm_airtime": "Recapitulatif : achat de credit {operator} de {amount} FCFA pour {to_phone} (frais : {fee} FCFA). Repondez 1 (Confirmer) ou 2 (Annuler).",
        "confirm_bill": "Recapitulatif : paiement facture {biller} de {amount} FCFA (frais : {fee} FCFA, total : {total} FCFA). Repondez 1 (Confirmer) ou 2 (Annuler).",
        "confirmed": "Operation confirmee avec succes ! Ref: {tx_id}. Montant: {amount} FCFA.",
        "confirmed_ussd": "Succes! Ref:{tx_id}. Montant:{amount} FCFA. 0.Menu",
        "cancelled": "Operation annulee. Aucun montant n'a ete debite.",
        "no_pending": "Aucune operation en attente de confirmation.",
        "ask_amount": "Quel montant en FCFA souhaitez-vous envoyer ?",
        "ask_beneficiary": "A quel beneficiaire (nom ou numero) souhaitez-vous envoyer {amount} FCFA ?",
        "ask_transfer_details": "Precisez le montant en FCFA et le nom ou numero du beneficiaire.",
        "ask_clarify_candidates": "Plusieurs beneficiaires correspondent : {candidates}. Lequel choisissez-vous ?",
        "ask_correction": "Que souhaitez-vous modifier (montant ou beneficiaire) ?",
        "lang_switched": "Langue changee en Francais. Comment puis-je vous aider ?",
        "unknown": "Je n'ai pas bien compris. Vous pouvez demander votre solde, les frais, l'historique ou un transfert.",
        "unknown_ussd": "Choix invalide.\n1.Solde 2.Transfert 3.Frais 4.Hist 0.Langue",
        "err_INSUFFICIENT_FUNDS": "Solde insuffisant pour effectuer cette operation (montant + frais).",
        "err_UNKNOWN_BENEFICIARY": "Beneficiaire introuvable. Verifiez le nom ou le numero.",
        "err_LIMIT_EXCEEDED": "Le montant depasse le plafond autorise de {max} par operation.",
        "err_INVALID_AMOUNT": "Montant invalide. Entrez un montant positif en FCFA.",
        "err_UNKNOWN_BILLER": "Facturier ou operateur inconnu. Disponibles : ENEO, CAMWATER, CANAL, CAMTEL, MTN, ORANGE.",
        "err_TX_NOT_FOUND": "Transaction introuvable.",
        "err_TX_NOT_PENDING": "Cette transaction n'est plus en attente.",
        "err_UNAUTHORIZED": "Erreur d'authentification du service (cle equipe).",
        "err_UNKNOWN_ACCOUNT": "Compte introuvable dans le systeme.",
        "err_INVALID_REQUEST": "Requete invalide. Verifiez les informations saisies.",
        "err_CONFIG_LOCKED": "Configuration verrouillee pendant l'evaluation.",
        "err_UNSAFE_ENDPOINT": "URL de service rejetee (adresse publique requise).",
        "err_GENERIC": "Service temporairement indisponible. Reessayez.",
    },
    "en": {
        "menu": "Safinum Pay\n1. Balance\n2. Transfer\n3. Fees\n4. History\n5. Airtime\n6. Bills\n0. Language",
        "menu_ussd": "Safinum Pay\n1.Balance\n2.Transfer\n3.Fees\n4.History\n5.Airtime\n6.Bills\n0.Lang",
        "balance": "Hello {name}. Your available balance is {balance} FCFA (account {phone}).",
        "balance_ussd": "Balance {name}: {balance} FCFA. 1.Transfer 2.Fees 0.Menu",
        "fees": "For {amount} FCFA ({op_type}), the fee is {fee} FCFA. Total to debit: {total} FCFA.",
        "fees_ussd": "Fee {amount} FCFA: {fee} FCFA. Total: {total} FCFA. 0.Menu",
        "history_header": "Your last {count} transactions:",
        "history_empty": "No recent transactions found on your account.",
        "confirm_transfer": "Summary: transfer {amount} FCFA to {beneficiary} ({to_phone}). Fee: {fee} FCFA. Total: {total} FCFA. Reply 1 (Confirm) or 2 (Cancel).",
        "confirm_transfer_ussd": "Send {amount} FCFA to {beneficiary}. Fee {fee}, Total {total} FCFA.\n1.Confirm\n2.Cancel",
        "confirm_airtime": "Summary: {operator} airtime of {amount} FCFA for {to_phone} (fee: {fee} FCFA). Reply 1 (Confirm) or 2 (Cancel).",
        "confirm_bill": "Summary: {biller} bill payment of {amount} FCFA (fee: {fee} FCFA, total: {total} FCFA). Reply 1 (Confirm) or 2 (Cancel).",
        "confirmed": "Operation confirmed successfully! Ref: {tx_id}. Amount: {amount} FCFA.",
        "confirmed_ussd": "Success! Ref:{tx_id}. Amount:{amount} FCFA. 0.Menu",
        "cancelled": "Operation cancelled. No money was debited.",
        "no_pending": "No pending operation to confirm.",
        "ask_amount": "How much in FCFA would you like to send?",
        "ask_beneficiary": "Which beneficiary (name or phone) should receive {amount} FCFA?",
        "ask_transfer_details": "Please specify the amount in FCFA and the beneficiary name or number.",
        "ask_clarify_candidates": "Multiple beneficiaries match: {candidates}. Which one do you choose?",
        "ask_correction": "What would you like to change (amount or beneficiary)?",
        "lang_switched": "Language switched to English. How can I help you?",
        "unknown": "I did not understand. You can ask for your balance, fees, history, or a transfer.",
        "unknown_ussd": "Invalid choice.\n1.Balance 2.Transfer 3.Fees 4.Hist 0.Lang",
        "err_INSUFFICIENT_FUNDS": "Insufficient balance for this operation (amount + fees).",
        "err_UNKNOWN_BENEFICIARY": "Beneficiary not found. Please check the name or phone number.",
        "err_LIMIT_EXCEEDED": "Amount exceeds the {max} per-operation limit.",
        "err_INVALID_AMOUNT": "Invalid amount. Please enter a positive amount in FCFA.",
        "err_UNKNOWN_BILLER": "Unknown biller or operator. Available: ENEO, CAMWATER, CANAL, CAMTEL, MTN, ORANGE.",
        "err_TX_NOT_FOUND": "Transaction not found.",
        "err_TX_NOT_PENDING": "This transaction is no longer pending.",
        "err_UNAUTHORIZED": "Service authentication error (team key).",
        "err_UNKNOWN_ACCOUNT": "Account not found in the system.",
        "err_INVALID_REQUEST": "Invalid request. Please check your input.",
        "err_CONFIG_LOCKED": "Configuration is locked during evaluation.",
        "err_UNSAFE_ENDPOINT": "Endpoint URL rejected (public URL required).",
        "err_GENERIC": "Service temporarily unavailable. Please try again.",
    },
    "wes": {
        "menu": "Safinum Pay\n1. Moni weh remain\n2. Send moni\n3. Charges\n4. History\n5. Credit\n6. Bill\n0. Language",
        "menu_ussd": "Safinum Pay\n1.Moni remain\n2.Send moni\n3.Charges\n4.History\n5.Credit\n6.Bill\n0.Lang",
        "balance": "Hello {name}. Di moni weh remain fo yu account na {balance} FCFA ({phone}).",
        "balance_ussd": "Moni {name}: {balance} FCFA. 1.Send 2.Charges 0.Menu",
        "fees": "Fo {amount} FCFA ({op_type}), charges na {fee} FCFA. All moni weh go comot na {total} FCFA.",
        "fees_ussd": "Charges {amount} FCFA: {fee} FCFA. Total: {total} FCFA. 0.Menu",
        "history_header": "Yu last {count} transaction dem:",
        "history_empty": "No transaction no dey fo yu account.",
        "confirm_transfer": "Check am: yu wan send {amount} FCFA give {beneficiary} ({to_phone}). Charges: {fee} FCFA. Total: {total} FCFA. Press 1 (Confirm) or 2 (Cancel).",
        "confirm_transfer_ussd": "Send {amount} FCFA to {beneficiary}. Charges {fee}, Total {total} FCFA.\n1.Confirm\n2.Cancel",
        "confirm_airtime": "Check am: buy {operator} credit {amount} FCFA fo {to_phone} (charges: {fee} FCFA). Press 1 (Confirm) or 2 (Cancel).",
        "confirm_bill": "Check am: pay {biller} bill {amount} FCFA (charges: {fee} FCFA, total: {total} FCFA). Press 1 (Confirm) or 2 (Cancel).",
        "confirmed": "Moni don go fine! Ref: {tx_id}. Amount: {amount} FCFA.",
        "confirmed_ussd": "Moni don go! Ref:{tx_id}. {amount} FCFA. 0.Menu",
        "cancelled": "We don cancel am. No moni no comot.",
        "no_pending": "No operation no dey weh e wait confirm.",
        "ask_amount": "How much FCFA yu wan send?",
        "ask_beneficiary": "Who go receive dis {amount} FCFA (name or phone number)?",
        "ask_transfer_details": "Talk how much moni yu wan send an di pesin name or number.",
        "ask_clarify_candidates": "Plenty pesin get dis name: {candidates}. Which one yu mean?",
        "ask_correction": "Wetin yu wan change (how much or di pesin)?",
        "lang_switched": "We don change language fo Pidgin. How ah fit help yu?",
        "unknown": "Ah no understand fine. Yu fit ask fo yu moni weh remain, charges, history or send moni.",
        "unknown_ussd": "No correct.\n1.Moni 2.Send 3.Charges 4.Hist 0.Lang",
        "err_INSUFFICIENT_FUNDS": "Yu moni no reach fo dis send (amount + charges).",
        "err_UNKNOWN_BENEFICIARY": "We no see dat pesin. Check di name or phone number.",
        "err_LIMIT_EXCEEDED": "Di moni don pass limit ({max}).",
        "err_INVALID_AMOUNT": "Di moni no correct. Put correct number fo FCFA.",
        "err_UNKNOWN_BILLER": "We no sabi dat biller. Use ENEO, CAMWATER, CANAL, CAMTEL, MTN, ORANGE.",
        "err_TX_NOT_FOUND": "We no see dat transaction.",
        "err_TX_NOT_PENDING": "Dis transaction no dey wait again.",
        "err_UNAUTHORIZED": "Problem fo team key.",
        "err_UNKNOWN_ACCOUNT": "We no see dis account.",
        "err_INVALID_REQUEST": "Problem fo wetin yu send.",
        "err_CONFIG_LOCKED": "Config lock fo evaluation time.",
        "err_UNSAFE_ENDPOINT": "URL no good.",
        "err_GENERIC": "Network problem, try again.",
    },
    "fub": {
        "menu": "Safinum Pay\n1. Ceede keddiide\n2. Nel ceede\n3. Njobdi\n4. Golle ceede\n5. Crédit\n6. Facture\n0. Demgal",
        "menu_ussd": "Safinum Pay\n1.Ceede\n2.Nel ceede\n3.Njobdi\n4.Golle\n5.Crédit\n6.Facture\n0.Demgal",
        "balance": "Sannu {name}. Ceede maa keddiide ko {balance} FCFA (compte {phone}).",
        "balance_ussd": "Ceede {name}: {balance} FCFA. 1.Nel 2.Njobdi 0.Menu",
        "fees": "Ngam {amount} FCFA ({op_type}), njobdi ko {fee} FCFA. Fuu ko ittetee ko {total} FCFA.",
        "fees_ussd": "Njobdi {amount} FCFA: {fee} FCFA. Fuu: {total} FCFA. 0.Menu",
        "history_header": "Golle ceede maa {count} sakkitiide:",
        "history_empty": "Alaa golle ceede kesre e compte maa.",
        "confirm_transfer": "Yeewaa fuu: nelde {amount} FCFA e {beneficiary} ({to_phone}). Njobdi: {fee} FCFA. Fuu: {total} FCFA. Jaabo 1 (Tabbitin) malla 2 (Habbit).",
        "confirm_transfer_ussd": "Nel {amount} FCFA e {beneficiary}. Njobdi {fee}, Fuu {total} FCFA.\n1.Tabbitin\n2.Habbit",
        "confirm_airtime": "Yeewaa fuu: soodude crédit {operator} {amount} FCFA ngam {to_phone} (njobdi: {fee} FCFA). Jaabo 1 (Tabbitin) malla 2 (Habbit).",
        "confirm_bill": "Yeewaa fuu: njobdi facture {biller} {amount} FCFA (njobdi: {fee} FCFA, fuu: {total} FCFA). Jaabo 1 (Tabbitin) malla 2 (Habbit).",
        "confirmed": "Nelde ceede gasii no feewi! Ref: {tx_id}. Limre: {amount} FCFA.",
        "confirmed_ussd": "Gasii! Ref:{tx_id}. {amount} FCFA. 0.Menu",
        "cancelled": "Golle habbitaama. Alaa ceede ittaa.",
        "no_pending": "Alaa golle faddeede tabbitinal.",
        "ask_amount": "Limre ceede noye (FCFA) njid-daa nelde?",
        "ask_beneficiary": "Mo heboowo (innde malla limre) nelataa {amount} FCFA?",
        "ask_transfer_details": "Winndu limre ceede FCFA e innde walla numéro heboowo.",
        "ask_clarify_candidates": "Heboobe heewbe nanndube: {candidates}. Mo cubi-daa?",
        "ask_correction": "Ko njid-daa waylude (limre ceede malla heboowo)?",
        "lang_switched": "Demgal waylaama e Fulfulde. No mballirmi maa?",
        "unknown": "Mi faamaani. A waawi naamnaade ceede maa, njobdi, golle malla nelde ceede.",
        "unknown_ussd": "Famaani.\n1.Ceede 2.Nel 3.Njobdi 4.Golle 0.Demgal",
        "err_INSUFFICIENT_FUNDS": "Ceede maa yonaa ngam nelde ndee (limre + njobdi).",
        "err_UNKNOWN_BENEFICIARY": "Heboowo hebaaka. Yeew innde malla limre téléphone.",
        "err_LIMIT_EXCEEDED": "Limre ceede burii keeri {max}.",
        "err_INVALID_AMOUNT": "Limre ceede moƴƴaa. Winndu limre goonga e FCFA.",
        "err_UNKNOWN_BILLER": "Facture malla rese anndaaka (ENEO, CAMWATER, CANAL, CAMTEL, MTN, ORANGE).",
        "err_TX_NOT_FOUND": "Golle ceede hebaaka.",
        "err_TX_NOT_PENDING": "Golle ndee faddeetaake kadi.",
        "err_UNAUTHORIZED": "Juumre seedantaagal (team key).",
        "err_UNKNOWN_ACCOUNT": "Compte hebaaka.",
        "err_INVALID_REQUEST": "Naamnal moƴƴaa.",
        "err_CONFIG_LOCKED": "Teelte uddataama e waktu ƴeewndo.",
        "err_UNSAFE_ENDPOINT": "URL jaɓaaka.",
        "err_GENERIC": "Juumre réseau: service oo heɓataake jooni. Fuɗɗito kadi.",
    },
    "ewo": {
        "menu": "Safinum Pay\n1. Mòni a lig\n2. Lom mòni\n3. Frais\n4. Alom ya nde\n5. Crédit\n6. Facture\n0. Nkobo",
        "menu_ussd": "Safinum Pay\n1.Moni\n2.Lom moni\n3.Frais\n4.Alom nde\n5.Crédit\n6.Facture\n0.Nkobo",
        "balance": "Mbolo {name}. Mòni wôé a lig a ne {balance} FCFA (compte {phone}).",
        "balance_ussd": "Moni {name}: {balance} FCFA. 1.Lom 2.Frais 0.Menu",
        "fees": "Asu {amount} FCFA ({op_type}), frais a ne {fee} FCFA. Mone mese ba ye nyon: {total} FCFA.",
        "fees_ussd": "Frais {amount} FCFA: {fee} FCFA. Mese: {total} FCFA. 0.Menu",
        "history_header": "Alom mone ya nde {count}:",
        "history_empty": "Alom mone mfe a ne ki.",
        "confirm_transfer": "Yen bise: wa lom {amount} FCFA a {beneficiary} ({to_phone}). Frais: {fee} FCFA. Mese: {total} FCFA. Yebe 1 (Ayebe) nge 2 (Bili/Ben).",
        "confirm_transfer_ussd": "Lom {amount} FCFA a {beneficiary}. Frais {fee}, Mese {total} FCFA.\n1.Ayebe\n2.Bili",
        "confirm_airtime": "Yen bise: kus crédit {operator} {amount} FCFA asu {to_phone} (frais: {fee} FCFA). 1 (Ayebe) nge 2 (Bili).",
        "confirm_bill": "Yen bise: ave facture {biller} {amount} FCFA (frais: {fee} FCFA, mese: {total} FCFA). 1 (Ayebe) nge 2 (Bili).",
        "confirmed": "Alom mone a mana mbembe! Ref: {tx_id}. Mone: {amount} FCFA.",
        "confirmed_ussd": "A mana! Ref:{tx_id}. {amount} FCFA. 0.Menu",
        "cancelled": "Alom mone a bili. Mone a ne ki nyon.",
        "no_pending": "Alom mone a ne ki a yege ayebe.",
        "ask_amount": "Mòni tân ya (FCFA) wa ye lôm?",
        "ask_beneficiary": "Mod mfe (dzoe nge numéro téléphone) a ye kos {amount} FCFA?",
        "ask_transfer_details": "Kal mone FCFA a dzoe ngə numéro mod a kos.",
        "ask_clarify_candidates": "Bod befe be ne dzoe di: {candidates}. Nnye mfe wa fas?",
        "ask_correction": "Jom fe wa ye sûli (mone nge mod a kos)?",
        "lang_switched": "Nkobo a ne Ewondo. Me ne wo vole aya?",
        "unknown": "Me ne ki wog mbembe. Wa ne sili mone woe, frais, alom ya nde nge lom mone.",
        "unknown_ussd": "Me ne ki wog.\n1.Mone 2.Lom 3.Frais 4.Alom 0.Nkobo",
        "err_INSUFFICIENT_FUNDS": "Mone woe ma ne ki tege ase alom nyi (mone + frais).",
        "err_UNKNOWN_BENEFICIARY": "Mod a kos a ne ki yen. Yen mbembe dzoe nge numéro téléphone.",
        "err_LIMIT_EXCEEDED": "Mone ma lot {max}.",
        "err_INVALID_AMOUNT": "Mone ma ne ki mbembe. Tili mone ya benya a FCFA.",
        "err_UNKNOWN_BILLER": "Facture nge opérateur a ne ki yen (ENEO, CAMWATER, CANAL, CAMTEL, MTN, ORANGE).",
        "err_TX_NOT_FOUND": "Alom mone a ne ki yen.",
        "err_TX_NOT_PENDING": "Alom nyi a ne ki fe a yege ayebe.",
        "err_UNAUTHORIZED": "Dzam abe a team key.",
        "err_UNKNOWN_ACCOUNT": "Compte a ne ki yen.",
        "err_INVALID_REQUEST": "Sil abe.",
        "err_CONFIG_LOCKED": "Config a ne dibi.",
        "err_UNSAFE_ENDPOINT": "URL a ne ki yebe.",
        "err_GENERIC": "Réseau a ne ki mbembe: service a ne ki tege. Bulan bo fe.",
    },
    "dua": {
        "menu": "Safinum Pay\n1. Môni ma dia\n2. Lóma môni\n3. Njoa (Frais)\n4. Bola la môni\n5. Crédit\n6. Facture\n0. Bwea",
        "menu_ussd": "Safinum Pay\n1.Moni\n2.Loma moni\n3.Njoa\n4.Bola\n5.Crédit\n6.Facture\n0.Bwea",
        "balance": "Idib'a bwam {name}. Môni mongo ma dia me {balance} FCFA (compte {phone}).",
        "balance_ussd": "Moni {name}: {balance} FCFA. 1.Loma 2.Njoa 0.Menu",
        "fees": "Onyola {amount} FCFA ({op_type}), njoa e ne {fee} FCFA. Môni mese: {total} FCFA.",
        "fees_ussd": "Njoa {amount} FCFA: {fee} FCFA. Mese: {total} FCFA. 0.Menu",
        "history_header": "Bola longo la môni {count} la sukan:",
        "history_empty": "Bola la môni di si ma dia o compte ango.",
        "confirm_transfer": "Kwaléa bwam: o ma lóma {amount} FCFA na {beneficiary} ({to_phone}). Njoa: {fee} FCFA. Mese: {total} FCFA. Alane 1 (Hee / Timbisɛ) to 2 (Kem / Timba).",
        "confirm_transfer_ussd": "Loma {amount} FCFA na {beneficiary}. Njoa {fee}, Mese {total} FCFA.\n1.Hee\n2.Kem",
        "confirm_airtime": "Kwaléa bwam: anda crédit {operator} {amount} FCFA na {to_phone} (njoa: {fee} FCFA). 1 (Timbisɛ) to 2 (Timba).",
        "confirm_bill": "Kwaléa bwam: sawa facture {biller} {amount} FCFA (njoa: {fee} FCFA, mese: {total} FCFA). 1 (Timbisɛ) to 2 (Timba).",
        "confirmed": "Loma la môni di timbisabe bwam! Ref: {tx_id}. Môni: {amount} FCFA.",
        "confirmed_ussd": "Di boli! Ref:{tx_id}. {amount} FCFA. 0.Menu",
        "cancelled": "Loma di timbabe. Môni mu si busi.",
        "no_pending": "Bola di si ma dia o longe timbisɛ.",
        "ask_amount": "Moni nena (FCFA) o ma pula loma?",
        "ask_beneficiary": "Nja (dina to numéro) nu ma kusa {amount} FCFA?",
        "ask_transfer_details": "Langwa moni FCFA na dina to numéro moto nu ma kusa.",
        "ask_clarify_candidates": "Bato bapepe ba bi dina di: {candidates}. Nja o ma posa?",
        "ask_correction": "Nje o ma pula tukwa (moni to moto)?",
        "lang_switched": "Bwea bu tukwabe o Duala. Ne na longwa wa ne?",
        "unknown": "Na si senga bwea. O wele baise moni mongo, njoa, bola to loma moni.",
        "unknown_ussd": "Na si senga.\n1.Moni 2.Loma 3.Njoa 4.Bola 0.Bwea",
        "err_INSUFFICIENT_FUNDS": "Moni mongo mu si koki onyola loma di (moni + njoa).",
        "err_UNKNOWN_BENEFICIARY": "Moto nu ma kusa a si benabe. Ombwa dina to numéro.",
        "err_LIMIT_EXCEEDED": "Moni mu tombi {max}.",
        "err_INVALID_AMOUNT": "Moni mu si tege. Tila moni ma mbale o FCFA.",
        "err_UNKNOWN_BILLER": "Facture to opérateur e si bibe (ENEO, CAMWATER, CANAL, CAMTEL, MTN, ORANGE).",
        "err_TX_NOT_FOUND": "Bola di si benabe.",
        "err_TX_NOT_PENDING": "Bola di si ma longe eme.",
        "err_UNAUTHORIZED": "Ndutu a team key.",
        "err_UNKNOWN_ACCOUNT": "Compte e si benabe.",
        "err_INVALID_REQUEST": "Baise di si tege.",
        "err_CONFIG_LOCKED": "Config e dibabe.",
        "err_UNSAFE_ENDPOINT": "URL e si emebe.",
        "err_GENERIC": "Ndutu a réseau: service e si ma bola tatan. Bola pete.",
    },
    "bas": {
        "menu": "Safinum Pay\n1. Moni u nkon\n2. Lémèl moni\n3. Nsas (Frais)\n4. Bilon bi moni\n5. Crédit\n6. Facture\n0. Hop",
        "menu_ussd": "Safinum Pay\n1.Moni\n2.Lemel moni\n3.Nsas\n4.Bilon\n5.Crédit\n6.Facture\n0.Hop",
        "balance": "Kɛl i lam {name}. Moni won u nkon u yene {balance} FCFA (compte {phone}).",
        "balance_ussd": "Moni {name}: {balance} FCFA. 1.Lemel 2.Nsas 0.Menu",
        "fees": "Inyu {amount} FCFA ({op_type}), nsas u yene {fee} FCFA. Moni mwomede: {total} FCFA.",
        "fees_ussd": "Nsas {amount} FCFA: {fee} FCFA. Mwomede: {total} FCFA. 0.Menu",
        "history_header": "Bilon bion bi moni {count} bi nsukan:",
        "history_empty": "Bilon bi moni bi ta be i compte yon.",
        "confirm_transfer": "Tol longe: u nlémèl {amount} FCFA i {beneficiary} ({to_phone}). Nsas: {fee} FCFA. Mwomede: {total} FCFA. Timbhe 1 (Ŋ̀ŋ̂ / Hémle) to 2 (Tɔ̀ / Bôg).",
        "confirm_transfer_ussd": "Lemel {amount} FCFA i {beneficiary}. Nsas {fee}, Mwomede {total} FCFA.\n1.Nng\n2.To",
        "confirm_airtime": "Tol longe: somb crédit {operator} {amount} FCFA inyu {to_phone} (nsas: {fee} FCFA). 1 (Hémle) to 2 (Bôg).",
        "confirm_bill": "Tol longe: jel facture {biller} {amount} FCFA (nsas: {fee} FCFA, mwomede: {total} FCFA). 1 (Hémle) to 2 (Bôg).",
        "confirmed": "Lémèl u mal longe! Ref: {tx_id}. Moni: {amount} FCFA.",
        "confirmed_ussd": "U mal! Ref:{tx_id}. {amount} FCFA. 0.Menu",
        "cancelled": "Lémèl u bôg. Moni u nyo-be.",
        "no_pending": "Bilon bi ta be i bem hémle.",
        "ask_amount": "Moni nwaa (FCFA) u ngwés lom?",
        "ask_beneficiary": "Njee (jôl to numéro) a nkôs {amount} FCFA?",
        "ask_transfer_details": "Kal moni FCFA ni jôl tole numéro mut a nkôs.",
        "ask_clarify_candidates": "Bôt bape ba gwe jôl lini: {candidates}. Njee u mpohol?",
        "ask_correction": "Kii u ngwés henha (moni to mut)?",
        "lang_switched": "Hop u henha i Basaa. Lelaa me nla hôla we?",
        "unknown": "Me nok-be longe. U nla bat moni won, nsas, bilon to lom moni.",
        "unknown_ussd": "Me nok-be.\n1.Moni 2.Lom 3.Nsas 4.Bilon 0.Hop",
        "err_INSUFFICIENT_FUNDS": "Moni won u nkola ɓé inyu lémèl unu (moni + nsas).",
        "err_UNKNOWN_BENEFICIARY": "Mut a nkôs a nene-be. Benge jôl to numéro.",
        "err_LIMIT_EXCEEDED": "Moni u nloo {max}.",
        "err_INVALID_AMOUNT": "Moni u ta-be longe. Tila moni u mba i FCFA.",
        "err_UNKNOWN_BILLER": "Facture to opérateur i yi-be (ENEO, CAMWATER, CANAL, CAMTEL, MTN, ORANGE).",
        "err_TX_NOT_FOUND": "Lom u nene-be.",
        "err_TX_NOT_PENDING": "Lom unu u mbem-be neebe.",
        "err_UNAUTHORIZED": "Njam i team key.",
        "err_UNKNOWN_ACCOUNT": "Compte i nene-be.",
        "err_INVALID_REQUEST": "Mbat i ta-be longe.",
        "err_CONFIG_LOCKED": "Config i yibha.",
        "err_UNSAFE_ENDPOINT": "URL i neebe-be.",
        "err_GENERIC": "Njam i réseau: service i nsal-be nano. Tigil bôt.",
    },
    "bbj": {
        "menu": "Safinum Pay\n1. Ŋkap ya tse\n2. Tom ŋkap\n3. Frais\n4. Bivul\n5. Crédit\n6. Facture\n0. Ghomala",
        "menu_ussd": "Safinum Pay\n1.Nkap\n2.Tom nkap\n3.Frais\n4.Bivul\n5.Crédit\n6.Facture\n0.Ghom",
        "balance": "Mbúʼ {name}. Ŋkap po ya tse e ba {balance} FCFA (compte {phone}).",
        "balance_ussd": "Nkap {name}: {balance} FCFA. 1.Tom 2.Frais 0.Menu",
        "fees": "Mba {amount} FCFA ({op_type}), frais ba {fee} FCFA. Ŋkap tsem: {total} FCFA.",
        "fees_ussd": "Frais {amount} FCFA: {fee} FCFA. Tsem: {total} FCFA. 0.Menu",
        "history_header": "Bivul bi ŋkap {count} bi tsem:",
        "history_empty": "Bivul bi ŋkap ka po.",
        "confirm_transfer": "Ye bwe: o ko tom {amount} FCFA a {beneficiary} ({to_phone}). Frais: {fee} FCFA. Tsem: {total} FCFA. 1 (Yôô) ka 2 (Ka').",
        "confirm_transfer_ussd": "Tom {amount} FCFA a {beneficiary}. Frais {fee}, Tsem {total} FCFA.\n1.Yoo\n2.Ka'",
        "confirm_airtime": "Ye bwe: yu crédit {operator} {amount} FCFA a {to_phone} (frais: {fee} FCFA). 1 (Yebe) ka 2 (Tebe).",
        "confirm_bill": "Ye bwe: fo facture {biller} {amount} FCFA (frais: {fee} FCFA, tsem: {total} FCFA). 1 (Yebe) ka 2 (Tebe).",
        "confirmed": "Nkap tom bwe! Ref: {tx_id}. Nkap: {amount} FCFA.",
        "confirmed_ussd": "Tom bwe! Ref:{tx_id}. {amount} FCFA. 0.Menu",
        "cancelled": "Tom tebe. Nkap ka nyon.",
        "no_pending": "Bivul ka po e yebe.",
        "ask_amount": "Nkap sa (FCFA) o ko tom?",
        "ask_beneficiary": "We (dzo ka numéro) e ko nyam {amount} FCFA?",
        "ask_transfer_details": "Kwe nkap FCFA na dzo ka numéro we e ko nyam.",
        "ask_clarify_candidates": "Puo puo gwe dzo li: {candidates}. We o ko tso?",
        "ask_correction": "Ka o ko shang (nkap ka we)?",
        "lang_switched": "Ghomala shang bwe. Me ne ko vole o ka?",
        "unknown": "Me ka yu bwe. O ne baa nkap po, frais, bivul ka tom nkap.",
        "unknown_ussd": "Me ka yu.\n1.Nkap 2.Tom 3.Frais 4.Bivul 0.Lang",
        "err_INSUFFICIENT_FUNDS": "Nkap po ka kwet mba tom li (nkap + frais).",
        "err_UNKNOWN_BENEFICIARY": "We e nyam ka yen. Ye dzo ka numéro.",
        "err_LIMIT_EXCEEDED": "Nkap lot {max}.",
        "err_INVALID_AMOUNT": "Nkap ka bwe. Tili nkap bwe a FCFA.",
        "err_UNKNOWN_BILLER": "Facture ka opérateur ka yi (ENEO, CAMWATER, CANAL, CAMTEL, MTN, ORANGE).",
        "err_TX_NOT_FOUND": "Tom ka yen.",
        "err_TX_NOT_PENDING": "Tom li ka tse e yebe.",
        "err_UNAUTHORIZED": "Problem a team key.",
        "err_UNKNOWN_ACCOUNT": "Compte ka yen.",
        "err_INVALID_REQUEST": "Baa ka bwe.",
        "err_CONFIG_LOCKED": "Config dibi.",
        "err_UNSAFE_ENDPOINT": "URL ka yebe.",
        "err_GENERIC": "Réseau ka bwe: service ka tse. Bulen.",
    },
    "byv": {
        "menu": "Safinum Pay\n1. Nkap bwam\n2. Ntúm nkap\n3. Frais\n4. Bivul\n5. Crédit\n6. Facture\n0. Medumba",
        "menu_ussd": "Safinum Pay\n1.Nkap\n2.Ntum nkap\n3.Frais\n4.Bivul\n5.Crédit\n6.Facture\n0.Med",
        "balance": "O zi à {name}. Nkap bu ya tse ne {balance} FCFA (compte {phone}).",
        "balance_ussd": "Nkap {name}: {balance} FCFA. 1.Ntum 2.Frais 0.Menu",
        "fees": "Num {amount} FCFA ({op_type}), frais ne {fee} FCFA. Nkap tsem: {total} FCFA.",
        "fees_ussd": "Frais {amount} FCFA: {fee} FCFA. Tsem: {total} FCFA. 0.Menu",
        "history_header": "Bivul bi nkap {count} bi tsem:",
        "history_empty": "Bivul bi nkap ka po.",
        "confirm_transfer": "Yen bwam: u ko ntúm {amount} FCFA a {beneficiary} ({to_phone}). Frais: {fee} FCFA. Tsem: {total} FCFA. 1 (Ŋ̂ / Yebe) ke 2 (Ŋŋ̀ / Tebe).",
        "confirm_transfer_ussd": "Ntum {amount} FCFA a {beneficiary}. Frais {fee}, Tsem {total} FCFA.\n1.Yebe\n2.Tebe",
        "confirm_airtime": "Yen bwam: yu crédit {operator} {amount} FCFA a {to_phone} (frais: {fee} FCFA). 1 (Yebe) ke 2 (Tebe).",
        "confirm_bill": "Yen bwam: fo facture {biller} {amount} FCFA (frais: {fee} FCFA, tsem: {total} FCFA). 1 (Yebe) ke 2 (Tebe).",
        "confirmed": "Nkap tom bwam! Ref: {tx_id}. Nkap: {amount} FCFA.",
        "confirmed_ussd": "Tom bwam! Ref:{tx_id}. {amount} FCFA. 0.Menu",
        "cancelled": "Tom tebe. Nkap ka nyon.",
        "no_pending": "Bivul ka po e yebe.",
        "ask_amount": "Nkap sa (FCFA) u ko tom?",
        "ask_beneficiary": "Wo (lin ke numéro) e ko nyam {amount} FCFA?",
        "ask_transfer_details": "Kal nkap FCFA na lin ka numéro wo e ko nyam.",
        "ask_clarify_candidates": "Bu bu gwe lin li: {candidates}. Wo u ko tso?",
        "ask_correction": "Ka u ko shang (nkap ke wo)?",
        "lang_switched": "Medumba shang bwam. Me ne ko vole u ka?",
        "unknown": "Me ka yu bwam. U ne baa nkap bu, frais, bivul ke tom nkap.",
        "unknown_ussd": "Me ka yu.\n1.Nkap 2.Tom 3.Frais 4.Bivul 0.Lang",
        "err_INSUFFICIENT_FUNDS": "Nkap bu ka kwet num tom li (nkap + frais).",
        "err_UNKNOWN_BENEFICIARY": "Wo e nyam ka yen. Yen lin ke numéro.",
        "err_LIMIT_EXCEEDED": "Nkap lot {max}.",
        "err_INVALID_AMOUNT": "Nkap ka bwam. Tili nkap bwam a FCFA.",
        "err_UNKNOWN_BILLER": "Facture ke opérateur ka yi (ENEO, CAMWATER, CANAL, CAMTEL, MTN, ORANGE).",
        "err_TX_NOT_FOUND": "Tom ka yen.",
        "err_TX_NOT_PENDING": "Tom li ka tse e yebe.",
        "err_UNAUTHORIZED": "Problem a team key.",
        "err_UNKNOWN_ACCOUNT": "Compte ka yen.",
        "err_INVALID_REQUEST": "Baa ka bwam.",
        "err_CONFIG_LOCKED": "Config dibi.",
        "err_UNSAFE_ENDPOINT": "URL ka yebe.",
        "err_GENERIC": "Réseau ka bwam: service ka tse. Bulen.",
    },
    "hau": {
        "menu": "Safinum Pay\n1. Ragowar kudi\n2. Aika kudi\n3. Kudin aiki\n4. Tarihi\n5. Katin waya\n6. Biyan lissafi\n0. Harshe",
        "menu_ussd": "Safinum Pay\n1.Kudi\n2.Aika kudi\n3.Kudin aiki\n4.Tarihi\n5.Katin waya\n6.Lissafi\n0.Harshe",
        "balance": "Barka {name}. Ragowar kudinka shi ne {balance} FCFA (asusu {phone}).",
        "balance_ussd": "Kudi {name}: {balance} FCFA. 1.Aika 2.Kudin aiki 0.Menu",
        "fees": "Don {amount} FCFA ({op_type}), kudin aiki: {fee} FCFA. Jimilla: {total} FCFA.",
        "fees_ussd": "Kudin aiki {amount} FCFA: {fee} FCFA. Jimilla: {total} FCFA. 0.Menu",
        "history_header": "Ayyuka {count} na karshe:",
        "history_empty": "Babu wani aiki a baya.",
        "confirm_transfer": "Duba: aika {amount} FCFA zuwa {beneficiary} ({to_phone}). Kudin aiki: {fee} FCFA. Jimilla: {total} FCFA. 1 (Tabbatar) ko 2 (Soke).",
        "confirm_transfer_ussd": "Aika {amount} FCFA zuwa {beneficiary}. Aiki {fee}, Jimilla {total} FCFA.\n1.Tabbatar\n2.Soke",
        "confirm_airtime": "Duba: sayen katin {operator} {amount} FCFA don {to_phone} (aiki: {fee} FCFA). 1 (Tabbatar) ko 2 (Soke).",
        "confirm_bill": "Duba: biyan lissafin {biller} {amount} FCFA (aiki: {fee} FCFA, jimilla: {total} FCFA). 1 (Tabbatar) ko 2 (Soke).",
        "confirmed": "An kammala aikawa! Ref: {tx_id}. Kudi: {amount} FCFA.",
        "confirmed_ussd": "An gama! Ref:{tx_id}. {amount} FCFA. 0.Menu",
        "cancelled": "An soke aikin. Ba a cire kudi ba.",
        "no_pending": "Babu aiki mai jiran tabbatarwa.",
        "ask_amount": "Nawa (FCFA) kake so ka aika?",
        "ask_beneficiary": "Wa (suna ko lambar waya) zai karbi {amount} FCFA?",
        "ask_transfer_details": "Fadi adadin kudi FCFA da suna ko lambar mai karba.",
        "ask_clarify_candidates": "Mutane da yawa suna da wannan suna: {candidates}. Wanne kake nufi?",
        "ask_correction": "Me kake so ka gyara (kudi ko mai karba)?",
        "lang_switched": "An koma Hausa. Yaya zan taimaka maka?",
        "unknown": "Ban gane ba. Za ka iya tambayar ragowar kudi, kudin aiki, tarihi ko aika kudi.",
        "unknown_ussd": "Ban gane ba.\n1.Kudi 2.Aika 3.Aiki 4.Tarihi 0.Harshe",
        "err_INSUFFICIENT_FUNDS": "Kudinka bai isa wannan aikin ba (kudi + kudin aiki).",
        "err_UNKNOWN_BENEFICIARY": "Ba a sami mai karba ba. Duba suna ko lambar waya.",
        "err_LIMIT_EXCEEDED": "Adadin ya wuce iyaka na {max}.",
        "err_INVALID_AMOUNT": "Adadin kudi ba daidai ba ne. Rubuta lamba a FCFA.",
        "err_UNKNOWN_BILLER": "Ba a san wannan service ba (ENEO, CAMWATER, CANAL, CAMTEL, MTN, ORANGE).",
        "err_TX_NOT_FOUND": "Ba a sami wannan aikin ba.",
        "err_TX_NOT_PENDING": "Wannan aikin ba ya jiran tabbatarwa.",
        "err_UNAUTHORIZED": "Matsala da team key.",
        "err_UNKNOWN_ACCOUNT": "Ba a sami asusu ba.",
        "err_INVALID_REQUEST": "Bukata ba daidai ba ce.",
        "err_CONFIG_LOCKED": "An kulle saiti.",
        "err_UNSAFE_ENDPOINT": "URL ba amintacce ba ne.",
        "err_GENERIC": "Matsalar hanyar sadarwa: service ba ya samuwa yanzu.",
    },
    "bum": {
        "menu": "Safinum Pay\n1. Moné a li'i\n2. Lôm moné\n3. Tañ alôm\n4. Mam me lôteya\n5. Crédit\n6. Facture\n0. Nkobô",
        "menu_ussd": "Safinum Pay\n1.Mone\n2.Lom mone\n3.Frais\n4.Alom\n5.Crédit\n6.Facture\n0.Nkobo",
        "balance": "Mbôlô {name}. Moné wôé a li'i a ne {balance} FCFA (compte {phone}).",
        "balance_ussd": "Mone {name}: {balance} FCFA. 1.Lom 2.Frais 0.Menu",
        "fees": "Asu {amount} FCFA ({op_type}), frais a ne {fee} FCFA. Moné ase: {total} FCFA.",
        "fees_ussd": "Frais {amount} FCFA: {fee} FCFA. Ase: {total} FCFA. 0.Menu",
        "history_header": "Alôm moné {count} me lôteya:",
        "history_empty": "Alôm moné éfe é ne teke.",
        "confirm_transfer": "Fombô'ô mvaé: wo lôm {amount} FCFA be {beneficiary} ({to_phone}). Frais: {fee} FCFA. Ase: {total} FCFA. 1 (Kañese) nge 2 (Jô'é).",
        "confirm_transfer_ussd": "Lom {amount} FCFA be {beneficiary}. Frais {fee}, Ase {total} FCFA.\n1.Kanese\n2.Joe",
        "confirm_airtime": "Fombô'ô: kus crédit {operator} {amount} FCFA asu {to_phone} (frais: {fee} FCFA). 1 (Kañese) nge 2 (Jô'é).",
        "confirm_bill": "Fombô'ô: ya'an facture {biller} {amount} FCFA (frais: {fee} FCFA, ase: {total} FCFA). 1 (Kañese) nge 2 (Jô'é).",
        "confirmed": "Alôm moné é maneya mvaé! Ref: {tx_id}. Moné: {amount} FCFA.",
        "confirmed_ussd": "E maneya! Ref:{tx_id}. {amount} FCFA. 0.Menu",
        "cancelled": "Alôm moné é jô'éya. Moné a nji nyon.",
        "no_pending": "Alôm moné éfe é ne teke a yange.",
        "ask_amount": "Moné tañ ya (FCFA) wo kômbô lôm?",
        "ask_beneficiary": "Za (jôé nge numéro téléphone) a ye nyoñ {amount} FCFA?",
        "ask_transfer_details": "Kate'e moné FCFA a jôé nge numéro môt a nyoñ.",
        "ask_clarify_candidates": "Bôt abui be bili jôé éte: {candidates}. Za wo fas?",
        "ask_correction": "Jé wo kômbô tyendé (moné nge môt a nyoñ)?",
        "lang_switched": "Nkobô ô ne Bulu. Me ne volô wo aya?",
        "unknown": "Me nji wô'ô mvaé. Ô ne sili moné wôé, frais, mam me lôteya nge lôm moné.",
        "unknown_ussd": "Me nji wo'o.\n1.Mone 2.Lom 3.Frais 4.Alom 0.Nkobo",
        "err_INSUFFICIENT_FUNDS": "Moné wôé a ne tyôtyoé asu alôm éte (moné + frais).",
        "err_UNKNOWN_BENEFICIARY": "Môt a nyoñ a nji yené. Fombô'ô jôé nge numéro.",
        "err_LIMIT_EXCEEDED": "Moné a lôteya {max}.",
        "err_INVALID_AMOUNT": "Moné a nji bo mvaé. Tili'i tañ a FCFA.",
        "err_UNKNOWN_BILLER": "Service ô nji yé'éban (ENEO, CAMWATER, CANAL, CAMTEL, MTN, ORANGE).",
        "err_TX_NOT_FOUND": "Alôm é nji yené.",
        "err_TX_NOT_PENDING": "Alôm éte é nji beta yange.",
        "err_UNAUTHORIZED": "Njuk a team key.",
        "err_UNKNOWN_ACCOUNT": "Compte a nji yené.",
        "err_INVALID_REQUEST": "Nsili ô nji bo mvaé.",
        "err_CONFIG_LOCKED": "Config a fetiya.",
        "err_UNSAFE_ENDPOINT": "URL a nji kañeseban.",
        "err_GENERIC": "Njuk réseau: service a ne teke éyoñ ji.",
    },
}


# Explications de terminologie financière (Scénario 10 — claires pour un usager sans compte bancaire, zéro chiffre en dur)
FINANCIAL_TERMS: dict[str, dict[str, str]] = {
    "frais": {
        "fr": "C'est la petite somme retenue par le service pour acheminer votre argent en securite vers le destinataire.",
        "en": "It is the small service amount deducted to safely deliver your money to the recipient.",
        "wes": "Charges na di smol moni weh bank di take fo carry yu moni safe go give di pesin.",
        "fub": "Njobdi ko ceede pamare de banque ittata ngam neldude ceede maa e kisal.",
        "ewo": "Mone banque ya nyon asu na ba lom mone woe mvoe a mod a kos.",
        "dua": "Njoa e ne moni ma busi banque e ma nyoa onyola loma moni mongo na bwam.",
        "bas": "Nsas u yene moni ma titigi banque i nyo inyu lémèl moni won i mvoe.",
        "bbj": "Ba nkap fi banque e nyon mba tom nkap po bwe a we e nyam.",
        "byv": "Ne nkap fi banque a nyon num ntum nkap bu bwam a wo e nyam.",
        "hau": "Kudin aiki shi ne karamin ladar da banki ke cirewa don aika kudinka lafiya.",
        "bum": "Moné banque a nyoñ asu na a lôm moné wôé mvo'é be môt a nyoñ.",
    },
    "solde": {
        "fr": "C'est tout l'argent qui vous reste actuellement et que vous pouvez utiliser.",
        "en": "It is all the money currently left in your account that you can spend or send.",
        "wes": "Balance na all di moni weh e remain inside yu account now.",
        "fub": "Ceede keddiide ko limre ceede gonnde e compte maa jooni.",
        "ewo": "Mòni a lig a ne mòni mese me ne a compte wôé dên.",
        "dua": "Moni ma dia me moni mese me o compte ango tatan.",
        "bas": "Moni u nkon u yene moni mwomede u ye i compte yon nano.",
        "bbj": "Nkap ya tse ba nkap tsem e ba o compte po tatan.",
        "byv": "Nkap bwam ne nkap tsem e ba o compte bu tatan.",
        "hau": "Ragowar kudi shi ne dukkan kudin da ya rage a asusunka a yanzu.",
        "bum": "Moné a li'i a ne moné ase a ne e compte wôé éyoñ ji.",
    },
    "plafond": {
        "fr": "C'est la plus grande somme d'argent que vous avez le droit d'envoyer en une seule fois.",
        "en": "It is the largest amount of money you are allowed to send in a single operation.",
        "wes": "Limit na di biggest moni weh yu get right fo send fo one time.",
        "fub": "Keeri ko limre ceede burnde mawnude nde mbaaw-daa neldude laawol gootol.",
        "ewo": "Ndelo a ne abim mone ya ngul wa ne lom a alom wua.",
        "dua": "Ndelo e ne moni ma ndene mu si wele tomba o bola diwo.",
        "bas": "Ndék u yene moni u nloo u la lémèl i ngéda yada.",
        "bbj": "Ba nkap mbu ya o fit tom a tom mo tse.",
        "byv": "Ne nkap mbu ya o ko ntum a ntum mo tse.",
        "hau": "Iyaka ita ce mafi girman adadin kudi da za ka iya aikawa a aiki daya.",
        "bum": "Ndelo a ne tañ moné ya ngul ô ne lôm a alôm mbôk.",
    },
    "beneficiaire": {
        "fr": "C'est la personne ou l'entreprise qui va recevoir l'argent que vous envoyez.",
        "en": "It is the person or business who will receive the money you send.",
        "wes": "Pesin weh go receive na di man or woman weh yu di send moni give am.",
        "fub": "Heboowo ko neddo keboowo ceede neldaade.",
        "ewo": "Mod a kos a ne mod a ye kos mone wa lom.",
        "dua": "Moto nu ma kusa a ne moto nu ma kusa moni o ma loma.",
        "bas": "Mut a nkôs a yene mut a nkôs moni u nlémèl.",
        "bbj": "We e ko nyam ba moto e ko nyam nkap po.",
        "byv": "Wo e ko nyam ne moto e ko nyam nkap bu.",
        "hau": "Mai karba shi ne mutumin da zai karbi kudin da kake aikawa.",
        "bum": "Môt a nyoñ a ne môt a ye nyoñ moné ô ne lôm.",
    },
    "reference": {
        "fr": "C'est le code secret unique inscrit sur votre recu qui prouve que votre envoi a bien eu lieu.",
        "en": "It is the unique receipt code that proves your transaction took place.",
        "wes": "Reference na di special receipt code weh di show say yu don send moni.",
        "fub": "Ko code keerido e seedee maa hollitoowo golle ceede maa.",
        "ewo": "A ne code kalara wa lere na alom mone woe a boban.",
        "dua": "E ne code kalati e ma lee na bola longo la moni di boli.",
        "bas": "U yene code kaat u nhol le lom won u mbôña.",
        "bbj": "Ba code reçu e ko lee pa' tom nkap po ghə.",
        "byv": "Ne code reçu e ko lee pa' ntum nkap bu ghə.",
        "hau": "Lambar shaida ita ce lamba ta musamman a rasit mai tabbatar da aikinka.",
        "bum": "A ne code kalara a lere na alôm moné wôé a lôteya.",
    },
}


class _SafeVarDict(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def get_text(lang: str, key: str, channel: str = "web", **kwargs: Any) -> str:
    """Récupère un gabarit dans la langue cible (les variables non fournies restent en {variable})."""
    lang_dict = TEMPLATES.get(lang, TEMPLATES["fr"])
    if channel.lower() == "ussd" and f"{key}_ussd" in lang_dict:
        tpl = lang_dict[f"{key}_ussd"]
    else:
        tpl = lang_dict.get(key) or TEMPLATES["fr"].get(key, "")
    return tpl.format_map(_SafeVarDict(kwargs))


def get_error_text(lang: str, error_code: str, **kwargs: Any) -> str:
    lang_dict = TEMPLATES.get(lang, TEMPLATES["fr"])
    key = f"err_{error_code}"
    tpl = lang_dict.get(key) or lang_dict.get("err_GENERIC") or TEMPLATES["fr"]["err_GENERIC"]
    return tpl.format_map(_SafeVarDict(kwargs))


def get_term_explanation(lang: str, term_key: str, **kwargs: Any) -> str:
    term_dict = FINANCIAL_TERMS.get(term_key, FINANCIAL_TERMS["frais"])
    tpl = term_dict.get(lang) or term_dict["fr"]
    return tpl.format_map(_SafeVarDict(kwargs))


# Lexique mot-à-mot vérifié pour les phrases inédites ou partielles (9 langues)
WORD_GLOSSARY: dict[str, dict[str, str]] = {
    # Salutations, politesse & dialogue courant
    "bonjour": {"fr": "bonjour", "en": "hello", "wes": "hello", "fub": "sannu", "hau": "sannu", "bum": "mbolo", "ewo": "mbolo", "dua": "idib'a bwam", "bas": "kɛl i lam", "bbj": "mbúʼ", "byv": "o zi à"},
    "salut": {"fr": "salut", "en": "hi", "wes": "i salut oh", "fub": "sannu", "hau": "sannu", "bum": "mbolo", "ewo": "masug", "dua": "na nje", "bas": "me yéga", "bbj": "caʼtə", "byv": "mə cà'tə̌"},
    "bonsoir": {"fr": "bonsoir", "en": "good evening", "wes": "good evening", "fub": "jam hiiri", "hau": "barka da yamma", "bum": "mbembe ngô'é", "ewo": "mbembe ngoge", "dua": "ebyamu a bwam", "bas": "kokoa i lam", "bbj": "mbúʼ", "byv": "o zi à"},
    "bienvenue": {"fr": "bienvenue", "en": "welcome", "wes": "welcome", "fub": "jaɓɓama", "hau": "barka da zuwa", "bum": "mbolo", "ewo": "mbolo", "dua": "bwam", "bas": "mɛ̀ ǹyega", "bbj": "mbúʼ", "byv": "o zi à"},
    "merci": {"fr": "merci", "en": "thank you", "wes": "thank yu", "fub": "useko", "hau": "na gode", "bum": "akéva", "ewo": "ma və́ wa akíba", "dua": "na som", "bas": "matue", "bbj": "ndèmá", "byv": "mə̀ làbtə̌"},
    "pardon": {"fr": "pardon", "en": "please", "wes": "abeg", "fub": "accu hakke", "hau": "yi hakuri", "bum": "éngôngôl", "ewo": "engongol", "dua": "ndedi", "bas": "nwéhél", "bbj": "mesə", "byv": "ndə"},
    "svp": {"fr": "s'il vous plaît", "en": "please", "wes": "abeg", "fub": "useni", "hau": "don Allah", "bum": "éngôngôl", "ewo": "engongol", "dua": "na so", "bas": "sôhô", "bbj": "mba", "byv": "mba"},
    "oui": {"fr": "oui", "en": "yes", "wes": "yes", "fub": "ii", "hau": "eh", "bum": "ôwé", "ewo": "yebe", "dua": "hee", "bas": "ŋ̀ŋ̂", "bbj": "yôô", "byv": "ŋ̂"},
    "non": {"fr": "non", "en": "no", "wes": "no", "fub": "alaa", "hau": "a'a", "bum": "momo", "ewo": "bili", "dua": "kem", "bas": "tɔ̀", "bbj": "ka'", "byv": "ŋŋ̀"},
    "daccord": {"fr": "d'accord", "en": "okay", "wes": "na so", "fub": "gasii", "ewo": "yebe", "dua": "hee", "bas": "hémle", "bbj": "yôô", "byv": "yebe"},
    "ok": {"fr": "d'accord", "en": "okay", "wes": "ok", "fub": "gasii", "ewo": "yebe", "dua": "hee", "bas": "hémle", "bbj": "yôô", "byv": "yebe"},
    "aide": {"fr": "aide", "en": "help", "wes": "help", "fub": "ballal", "ewo": "mvolan", "dua": "jongwane", "bas": "mahôla", "bbj": "mvolan", "byv": "mvolan"},
    "aider": {"fr": "aider", "en": "help", "wes": "help", "fub": "wallude", "ewo": "vole", "dua": "ongwane", "bas": "hôla", "bbj": "vole", "byv": "vole"},

    # Questions & pronoms
    "combien": {"fr": "combien", "en": "how much", "wes": "how much", "fub": "noye", "ewo": "tân ya", "dua": "nena", "bas": "nwaa", "bbj": "sa", "byv": "sa"},
    "comment": {"fr": "comment", "en": "how", "wes": "na how", "fub": "no", "ewo": "aya", "dua": "nena", "bas": "lelaa", "bbj": "pa'", "byv": "kə"},
    "quoi": {"fr": "quoi", "en": "what", "wes": "wetin", "fub": "ko", "ewo": "dzé", "dua": "nje", "bas": "kii", "bbj": "ka", "byv": "kə"},
    "qui": {"fr": "qui", "en": "who", "wes": "who", "fub": "mo", "ewo": "zá", "dua": "nja", "bas": "njee", "bbj": "wə", "byv": "wə"},
    "ou": {"fr": "où", "en": "where", "wes": "usai", "fub": "toye", "ewo": "vé", "dua": "owe", "bas": "hee", "bbj": "ha", "byv": "ha"},
    "quand": {"fr": "quand", "en": "when", "wes": "wustem", "fub": "nde", "ewo": "éyong fé", "dua": " njika ponda", "bas": "ngéda", "bbj": "ngə", "byv": "ngə"},
    "pourquoi": {"fr": "pourquoi", "en": "why", "wes": "why", "fub": "ko waɗi", "ewo": "asu dzé", "dua": "onyola nje", "bas": "inyu kii", "bbj": "mba ka", "byv": "num kə"},

    # Nombres en lettres : conservés en français pour éviter toute confusion bancaire
    "zero": {"fr": "zéro", "en": "zero", "wes": "zéro", "fub": "zéro", "ewo": "zéro", "dua": "zéro", "bas": "zéro", "bbj": "zéro", "byv": "zéro"},
    "un": {"fr": "un", "en": "one", "wes": "un", "fub": "un", "ewo": "un", "dua": "un", "bas": "un", "bbj": "un", "byv": "un"},
    "deux": {"fr": "deux", "en": "two", "wes": "deux", "fub": "deux", "ewo": "deux", "dua": "deux", "bas": "deux", "bbj": "deux", "byv": "deux"},
    "trois": {"fr": "trois", "en": "three", "wes": "trois", "fub": "trois", "ewo": "trois", "dua": "trois", "bas": "trois", "bbj": "trois", "byv": "trois"},
    "quatre": {"fr": "quatre", "en": "four", "wes": "quatre", "fub": "quatre", "ewo": "quatre", "dua": "quatre", "bas": "quatre", "bbj": "quatre", "byv": "quatre"},
    "cinq": {"fr": "cinq", "en": "five", "wes": "cinq", "fub": "cinq", "ewo": "cinq", "dua": "cinq", "bas": "cinq", "bbj": "cinq", "byv": "cinq"},
    "dix": {"fr": "dix", "en": "ten", "wes": "dix", "fub": "dix", "ewo": "dix", "dua": "dix", "bas": "dix", "bbj": "dix", "byv": "dix"},
    "cent": {"fr": "cent", "en": "hundred", "wes": "cent", "fub": "cent", "ewo": "cent", "dua": "cent", "bas": "cent", "bbj": "cent", "byv": "cent"},
    "mille": {"fr": "mille", "en": "thousand", "wes": "mille", "fub": "mille", "ewo": "mille", "dua": "mille", "bas": "mille", "bbj": "mille", "byv": "mille"},
    "fcfa": {"fr": "FCFA", "en": "FCFA", "wes": "FCFA", "fub": "FCFA", "ewo": "FCFA", "dua": "FCFA", "bas": "FCFA", "bbj": "FCFA", "byv": "FCFA"},
    "xaf": {"fr": "XAF", "en": "XAF", "wes": "XAF", "fub": "XAF", "ewo": "XAF", "dua": "XAF", "bas": "XAF", "bbj": "XAF", "byv": "XAF"},
    "cfa": {"fr": "CFA", "en": "CFA", "wes": "CFA", "fub": "CFA", "ewo": "CFA", "dua": "CFA", "bas": "CFA", "bbj": "CFA", "byv": "CFA"},

    # Terminologie bancaire, finance numérique & Mobile Money
    "solde": {"fr": "solde", "en": "balance", "wes": "moni weh remain", "fub": "ceede keddiiɗe", "hau": "ragowar kudi", "bum": "moné a li'i", "ewo": "mòni a lig", "dua": "môni ma dia", "bas": "moni u nkon", "bbj": "ŋkap ya tse", "byv": "nkap bwam"},
    "argent": {"fr": "argent", "en": "money", "wes": "moni", "fub": "ceede", "hau": "kudi", "bum": "moné", "ewo": "mòni", "dua": "môni", "bas": "moni", "bbj": "ŋkap", "byv": "nkap"},
    "montant": {"fr": "montant", "en": "amount", "wes": "how much", "fub": "limre ceede", "hau": "adadin kudi", "bum": "tañ moné", "ewo": "mone", "dua": "môni", "bas": "moni", "bbj": "ŋkap", "byv": "nkap"},
    "somme": {"fr": "somme", "en": "amount", "wes": "moni", "fub": "limre ceede", "hau": "adadin kudi", "bum": "tañ moné", "ewo": "mone", "dua": "môni", "bas": "moni", "bbj": "ŋkap", "byv": "nkap"},
    "frais": {"fr": "frais", "en": "fees", "wes": "charges", "fub": "njoɓdi", "hau": "kudin aiki", "bum": "frais", "ewo": "frais", "dua": "njoa", "bas": "nsas", "bbj": "frais", "byv": "frais"},
    "commission": {"fr": "commission", "en": "fee", "wes": "charges", "fub": "njoɓdi", "hau": "kudin aiki", "bum": "frais", "ewo": "frais", "dua": "njoa", "bas": "nsas", "bbj": "frais", "byv": "frais"},
    "tarif": {"fr": "tarif", "en": "rate", "wes": "charges", "fub": "njoɓdi", "hau": "kudin aiki", "bum": "frais", "ewo": "frais", "dua": "njoa", "bas": "nsas", "bbj": "frais", "byv": "frais"},
    "cout": {"fr": "coût", "en": "cost", "wes": "charges", "fub": "njoɓdi", "hau": "kudin aiki", "bum": "tañ", "ewo": "taan", "dua": "njoa", "bas": "nsas", "bbj": "frais", "byv": "frais"},
    "prix": {"fr": "prix", "en": "price", "wes": "price", "fub": "coggu", "hau": "farashi", "bum": "tañ", "ewo": "taan", "dua": "mususedi", "bas": "nsañ", "bbj": "ŋkap", "byv": "nkap"},
    "total": {"fr": "total", "en": "total", "wes": "all moni", "fub": "fuu", "hau": "jimilla", "bum": "ase", "ewo": "mese", "dua": "mese", "bas": "mwomede", "bbj": "tsem", "byv": "tsem"},
    "plafond": {"fr": "plafond", "en": "limit", "wes": "limit", "fub": "keeri", "hau": "iyaka", "bum": "ndelo", "ewo": "ndelo", "dua": "ndelo", "bas": "ndék", "bbj": "plafond", "byv": "plafond"},
    "limite": {"fr": "limite", "en": "limit", "wes": "limit", "fub": "keeri", "hau": "iyaka", "bum": "ndelo", "ewo": "ndelo", "dua": "ndelo", "bas": "ndék", "bbj": "limite", "byv": "limite"},
    "banque": {"fr": "banque", "en": "bank", "wes": "bank", "fub": "banque", "hau": "banki", "bum": "banque", "ewo": "banque", "dua": "banque", "bas": "banque", "bbj": "banque", "byv": "banque"},
    "compte": {"fr": "compte", "en": "account", "wes": "account", "fub": "compte", "hau": "asusu", "bum": "compte", "ewo": "compte", "dua": "compte", "bas": "compte", "bbj": "compte", "byv": "compte"},
    "client": {"fr": "client", "en": "customer", "wes": "customer", "fub": "soodoowo", "hau": "abokin ciniki", "bum": "môt", "ewo": "mod", "dua": "moto", "bas": "mut", "bbj": "moto", "byv": "moto"},
    "beneficiaire": {"fr": "bénéficiaire", "en": "beneficiary", "wes": "pesin weh go receive", "fub": "heɓoowo", "hau": "mai karba", "bum": "môt a nyoñ", "ewo": "mod a kos", "dua": "moto nu ma kusa", "bas": "mut a nkôs", "bbj": "we e nyam", "byv": "wo e nyam"},
    "destinataire": {"fr": "destinataire", "en": "recipient", "wes": "pesin weh go receive", "fub": "heɓoowo", "hau": "mai karba", "bum": "môt a nyoñ", "ewo": "mod a kos", "dua": "moto nu ma kusa", "bas": "mut a nkôs", "bbj": "we e nyam", "byv": "wo e nyam"},
    "nom": {"fr": "nom", "en": "name", "wes": "name", "fub": "innde", "hau": "suna", "bum": "jôé", "ewo": "dzoe", "dua": "dina", "bas": "jôl", "bbj": "dzo", "byv": "lin"},
    "numero": {"fr": "numéro", "en": "number", "wes": "number", "fub": "limre", "hau": "lamba", "bum": "numéro", "ewo": "numéro", "dua": "numéro", "bas": "numéro", "bbj": "numéro", "byv": "numéro"},
    "telephone": {"fr": "téléphone", "en": "phone", "wes": "phone", "fub": "téléphone", "hau": "waya", "bum": "téléphone", "ewo": "téléphone", "dua": "téléphone", "bas": "téléphone", "bbj": "téléphone", "byv": "téléphone"},
    "credit": {"fr": "crédit", "en": "airtime", "wes": "credit", "fub": "crédit", "hau": "katin waya", "bum": "crédit", "ewo": "crédit", "dua": "crédit", "bas": "crédit", "bbj": "crédit", "byv": "crédit"},
    "recharge": {"fr": "recharge", "en": "top up", "wes": "credit", "fub": "crédit", "hau": "katin waya", "bum": "crédit", "ewo": "crédit", "dua": "crédit", "bas": "crédit", "bbj": "crédit", "byv": "crédit"},
    "facture": {"fr": "facture", "en": "bill", "wes": "bill", "fub": "facture", "hau": "lissafi", "bum": "facture", "ewo": "facture", "dua": "facture", "bas": "facture", "bbj": "facture", "byv": "facture"},
    "eau": {"fr": "eau", "en": "water", "wes": "water", "fub": "ndiyam", "hau": "ruwa", "bum": "mendim", "ewo": "mendim", "dua": "madiba", "bas": "malép", "bbj": "shyə", "byv": "ntsi"},
    "electricite": {"fr": "électricité", "en": "electricity", "wes": "electricity", "fub": "électricité", "hau": "wutar lantarki", "bum": "électricité", "ewo": "électricité", "dua": "électricité", "bas": "électricité", "bbj": "électricité", "byv": "électricité"},
    "courant": {"fr": "courant", "en": "power", "wes": "light", "fub": "courant", "hau": "wuta", "bum": "courant", "ewo": "courant", "dua": "courant", "bas": "courant", "bbj": "courant", "byv": "courant"},
    "television": {"fr": "télévision", "en": "television", "wes": "television", "fub": "télévision", "hau": "télévision", "bum": "télévision", "ewo": "télévision", "dua": "télévision", "bas": "télévision", "bbj": "télévision", "byv": "télévision"},
    "internet": {"fr": "internet", "en": "internet", "wes": "internet", "fub": "internet", "hau": "internet", "bum": "internet", "ewo": "internet", "dua": "internet", "bas": "internet", "bbj": "internet", "byv": "internet"},
    "reseau": {"fr": "réseau", "en": "network", "wes": "network", "fub": "réseau", "hau": "hanyar sadarwa", "bum": "réseau", "ewo": "réseau", "dua": "réseau", "bas": "réseau", "bbj": "réseau", "byv": "réseau"},
    "operateur": {"fr": "opérateur", "en": "operator", "wes": "network", "fub": "opérateur", "hau": "kamfanin waya", "bum": "opérateur", "ewo": "opérateur", "dua": "opérateur", "bas": "opérateur", "bbj": "opérateur", "byv": "opérateur"},
    "service": {"fr": "service", "en": "service", "wes": "service", "fub": "service", "hau": "service", "bum": "service", "ewo": "service", "dua": "service", "bas": "service", "bbj": "service", "byv": "service"},
    "historique": {"fr": "historique", "en": "history", "wes": "history", "fub": "golle ceede", "hau": "tarihi", "bum": "mam me lôteya", "ewo": "alom ya nde", "dua": "bola la môni", "bas": "biloñ bi moni", "bbj": "bivul bi ŋkap", "byv": "bivul bi nkap"},
    "operation": {"fr": "opération", "en": "transaction", "wes": "transaction", "fub": "golle", "hau": "aiki", "bum": "alôm", "ewo": "alôm", "dua": "bola", "bas": "biloñ", "bbj": "bivul", "byv": "bivul"},
    "transaction": {"fr": "transaction", "en": "transaction", "wes": "transaction", "fub": "golle ceede", "hau": "aikin kudi", "bum": "alôm moné", "ewo": "alôm mone", "dua": "bola la môni", "bas": "biloñ bi moni", "bbj": "tom ŋkap", "byv": "ntúm nkap"},
    "reference": {"fr": "référence", "en": "reference", "wes": "reference", "fub": "référence", "hau": "lambar shaida", "bum": "référence", "ewo": "référence", "dua": "référence", "bas": "référence", "bbj": "référence", "byv": "référence"},
    "recu": {"fr": "reçu", "en": "receipt", "wes": "receipt", "fub": "seedee", "hau": "rasit", "bum": "kalara", "ewo": "kalara", "dua": "kalati", "bas": "kaat", "bbj": "reçu", "byv": "reçu"},
    "code": {"fr": "code", "en": "code", "wes": "code", "fub": "code", "hau": "code", "bum": "code", "ewo": "code", "dua": "code", "bas": "code", "bbj": "code", "byv": "code"},
    "erreur": {"fr": "erreur", "en": "error", "wes": "wahala", "fub": "juumre", "hau": "kuskure", "bum": "ékop", "ewo": "ékop", "dua": "ndutu", "bas": "hôha", "bbj": "ndutu", "byv": "ndutu"},
    "probleme": {"fr": "problème", "en": "problem", "wes": "wahala", "fub": "caɗeele", "hau": "matsala", "bum": "njuk", "ewo": "ndzúk", "dua": "ndutu", "bas": "ndutu", "bbj": "problème", "byv": "problème"},
    "succes": {"fr": "succès", "en": "success", "wes": "fine", "fub": "gasii", "ewo": "mbembe", "dua": "bwam", "bas": "longe", "bbj": "bwe", "byv": "bwam"},
    "attente": {"fr": "en attente", "en": "pending", "wes": "di wait", "fub": "e fada", "ewo": "a yange", "dua": "o longe", "bas": "u mbem", "bbj": "e yange", "byv": "a yange"},
    "langue": {"fr": "langue", "en": "language", "wes": "language", "fub": "demgal", "ewo": "nkobo", "dua": "bwea", "bas": "hop", "bbj": "ghom", "byv": "medumba"},
    "accueil": {"fr": "accueil", "en": "home", "wes": "home", "fub": "jaɓɓorgo", "ewo": "aba", "dua": "mboa", "bas": "ndap", "bbj": "la'", "byv": "nda"},
    "maison": {"fr": "maison", "en": "house", "wes": "house", "fub": "suudu", "ewo": "nda", "dua": "ndabo", "bas": "ndap", "bbj": "nda", "byv": "nda"},
    "date": {"fr": "date", "en": "date", "wes": "date", "fub": "ñalnde", "ewo": "amôs", "dua": "bunya", "bas": "kel", "bbj": "lyɛ̌'", "byv": "lyɛ'"},
    "jour": {"fr": "jour", "en": "day", "wes": "day", "fub": "ñalnde", "ewo": "amôs", "dua": "bunya", "bas": "kel", "bbj": "lyɛ̌'", "byv": "lyɛ'"},
    "aujourd'hui": {"fr": "aujourd'hui", "en": "today", "wes": "today", "fub": "hannde", "ewo": "den", "dua": "wɛŋgɛ", "bas": "len", "bbj": "tatan", "byv": "tatan"},
    "demain": {"fr": "demain", "en": "tomorrow", "wes": "tomorrow", "fub": "jaŋgo", "ewo": "okídí", "dua": "kiele", "bas": "yani", "bbj": "fɔ̂kdzǔ", "byv": "ndǎmnjʉ"},
    "maintenant": {"fr": "maintenant", "en": "now", "wes": "now", "fub": "jooni", "ewo": "éyong nyi", "dua": "tatan", "bas": "nano", "bbj": "tatan", "byv": "tatan"},

    # Verbes d'action bancaires et leurs formes conjuguées courantes
    "envoyer": {"fr": "envoyer", "en": "send", "wes": "send", "fub": "neldude", "hau": "aika", "bum": "lôm", "ewo": "lôm", "dua": "lóma", "bas": "lémèl", "bbj": "tom", "byv": "ntúm"},
    "envoie": {"fr": "envoie", "en": "send", "wes": "send", "fub": "nel", "hau": "aika", "bum": "lôm", "ewo": "lôm", "dua": "lóma", "bas": "lémèl", "bbj": "tom", "byv": "ntúm"},
    "envoye": {"fr": "envoyé", "en": "sent", "wes": "don send", "fub": "neldaama", "hau": "an aika", "bum": "a lômbane", "ewo": "a lômban", "dua": "e lómabe", "bas": "i nlémél", "bbj": "tom", "byv": "ntúm"},
    "transfert": {"fr": "transfert", "en": "transfer", "wes": "send moni", "fub": "nelde ceede", "hau": "aika kudi", "bum": "alôm moné", "ewo": "alôm mone", "dua": "loma la môni", "bas": "lémèl moni", "bbj": "tom ŋkap", "byv": "ntúm nkap"},
    "transferer": {"fr": "transférer", "en": "transfer", "wes": "send", "fub": "neldude", "hau": "aika", "bum": "lôm", "ewo": "lôm", "dua": "lóma", "bas": "lémèl", "bbj": "tom", "byv": "ntúm"},
    "recevoir": {"fr": "recevoir", "en": "receive", "wes": "receive", "fub": "heɓude", "hau": "karba", "bum": "nyoñ", "ewo": "kos", "dua": "kusa", "bas": "kôs", "bbj": "nyam", "byv": "nyam"},
    "retirer": {"fr": "retirer", "en": "withdraw", "wes": "comot moni", "fub": "ittude", "hau": "cire kudi", "bum": "vaa moné", "ewo": "nyon", "dua": "busise", "bas": "pémés", "bbj": "tu'", "byv": "tu'"},
    "retrait": {"fr": "retrait", "en": "withdrawal", "wes": "comot moni", "fub": "ittugo ceede", "hau": "cire kudi", "bum": "avaa moné", "ewo": "nyonan mone", "dua": "busa môni", "bas": "pémés moni", "bbj": "tu' ŋkap", "byv": "tu' nkap"},
    "payer": {"fr": "payer", "en": "pay", "wes": "pay", "fub": "yoɓude", "hau": "biya", "bum": "ya'an", "ewo": "ya", "dua": "sawa", "bas": "jel", "bbj": "fo", "byv": "fo"},
    "paie": {"fr": "paie", "en": "pay", "wes": "pay", "fub": "yoɓ", "hau": "biya", "bum": "ya'an", "ewo": "ya", "dua": "sawa", "bas": "jel", "bbj": "fo", "byv": "fo"},
    "paye": {"fr": "payé", "en": "paid", "wes": "don pay", "fub": "yoɓaama", "hau": "an biya", "bum": "a ya'ane", "ewo": "a yaban", "dua": "e sawabe", "bas": "i njel", "bbj": "fo bwe", "byv": "fo bwam"},
    "acheter": {"fr": "acheter", "en": "buy", "wes": "buy", "fub": "soodude", "hau": "saya", "bum": "kus", "ewo": "kus", "dua": "anda", "bas": "somb", "bbj": "yu", "byv": "yu"},
    "achete": {"fr": "achète", "en": "buy", "wes": "buy", "fub": "sood", "hau": "saya", "bum": "kus", "ewo": "kus", "dua": "anda", "bas": "somb", "bbj": "yu", "byv": "yu"},
    "verifier": {"fr": "vérifier", "en": "verify", "wes": "check", "fub": "ƴeewde", "hau": "duba", "bum": "fombô", "ewo": "yen mbembe", "dua": "kwaléa", "bas": "tol", "bbj": "ye bwe", "byv": "yen bwam"},
    "consulter": {"fr": "consulter", "en": "check", "wes": "check", "fub": "ƴeewde", "hau": "duba", "bum": "yen", "ewo": "yen", "dua": "ombwa", "bas": "béñge", "bbj": "ye", "byv": "yen"},
    "voir": {"fr": "voir", "en": "see", "wes": "see", "fub": "yi'ude", "hau": "duba", "bum": "yen", "ewo": "yen", "dua": "ombwa", "bas": "tehe", "bbj": "ye", "byv": "yen"},
    "confirmer": {"fr": "confirmer", "en": "confirm", "wes": "confirm", "fub": "tabbitinde", "hau": "tabbatar", "bum": "kañese", "ewo": "yebe", "dua": "timbisɛ", "bas": "hémle", "bbj": "yôô", "byv": "yebe"},
    "valider": {"fr": "valider", "en": "confirm", "wes": "confirm", "fub": "tabbitinde", "hau": "tabbatar", "bum": "kañese", "ewo": "yebe", "dua": "timbisɛ", "bas": "hémle", "bbj": "yôô", "byv": "yebe"},
    "annuler": {"fr": "annuler", "en": "cancel", "wes": "cancel", "fub": "haɓɓitde", "hau": "soke", "bum": "jô'ôé", "ewo": "bili", "dua": "timba", "bas": "bôg", "bbj": "ka'", "byv": "tebe"},
    "modifier": {"fr": "modifier", "en": "edit", "wes": "change am", "fub": "waylude", "hau": "gyara", "bum": "tyendé", "ewo": "sûli", "dua": "tukwa", "bas": "henha", "bbj": "shang", "byv": "shang"},
    "changer": {"fr": "changer", "en": "change", "wes": "change am", "fub": "waylude", "hau": "canza", "bum": "tyendé", "ewo": "sûli", "dua": "tukwa", "bas": "henha", "bbj": "shang", "byv": "shang"},
    "corriger": {"fr": "corriger", "en": "correct", "wes": "change am", "fub": "waylude", "hau": "gyara", "bum": "tyendé", "ewo": "sûli", "dua": "tukwa", "bas": "henha", "bbj": "shang", "byv": "shang"},
    "choisir": {"fr": "choisir", "en": "choose", "wes": "pick", "fub": "suɓaade", "hau": "zabi", "bum": "top", "ewo": "tob", "dua": "posa", "bas": "pohol", "bbj": "tso", "byv": "tso"},
    "ecouter": {"fr": "écouter", "en": "listen", "wes": "listen", "fub": "heɗaade", "hau": "saurara", "bum": "vô'ôlô", "ewo": "vogolo", "dua": "senga", "bas": "emble", "bbj": "yu'", "byv": "yu'"},
    "parler": {"fr": "parler", "en": "speak", "wes": "talk", "fub": "haalude", "hau": "magana", "bum": "kobô", "ewo": "kobo", "dua": "bwala", "bas": "pot", "bbj": "ghɔm", "byv": "cɔ"},
    "continuer": {"fr": "continuer", "en": "continue", "wes": "continue", "fub": "jokkude", "hau": "ci gaba", "bum": "kel ôsu", "ewo": "kele osu", "dua": "ala oboso", "bas": "ke bisu", "bbj": "gɔ̌ ntum", "byv": "nə ntum"},
    "retour": {"fr": "retour", "en": "back", "wes": "go back", "fub": "rutto", "hau": "koma", "bum": "bulan", "ewo": "bulan", "dua": "timba", "bas": "témb", "bbj": "le'", "byv": "kə'"},
    "terminer": {"fr": "terminer", "en": "finish", "wes": "finish", "fub": "timminde", "hau": "kammala", "bum": "mane", "ewo": "mana", "dua": "bɔlɛ", "bas": "mal", "bbj": "mɛ", "byv": "mɛ"},
    "securite": {"fr": "sécurité", "en": "security", "wes": "security", "fub": "kisal", "hau": "tsaro", "bum": "mvo'é", "ewo": "mvoé", "dua": "bwam", "bas": "lam", "bbj": "bwe", "byv": "bwam"},
    "insuffisant": {"fr": "insuffisant", "en": "insufficient", "wes": "no reach", "fub": "yonaa", "hau": "bai isa ba", "bum": "a ne tyôtyoé", "ewo": "ne ki tegé", "dua": "si koki", "bas": "nkola-be", "bbj": "ka kwet", "byv": "ka kwet"},
    "disponible": {"fr": "disponible", "en": "available", "wes": "weh remain", "fub": "keddiiɗe", "hau": "da ya rage", "bum": "a li'i", "ewo": "a lig ma", "dua": "ma dia", "bas": "u nkon", "bbj": "ya tse", "byv": "ya tse"},
    "gratuit": {"fr": "gratuit", "en": "free", "wes": "free", "fub": "meere", "ewo": "zezé", "dua": "zeze", "bas": "zeze", "bbj": "zeze", "byv": "zeze"},
    "bon": {"fr": "bon", "en": "good", "wes": "fine", "fub": "moƴƴo", "ewo": "mbembe", "dua": "bwam", "bas": "lam", "bbj": "bwe", "byv": "bwam"},
    "bien": {"fr": "bien", "en": "well", "wes": "fine", "fub": "no feewi", "ewo": "mbembe", "dua": "bwam", "bas": "longe", "bbj": "bwe", "byv": "bwam"},
}

# Alias FR (variantes orthographiques/conjuguées) & EN -> clé canonique du glossaire
_EN_TO_GLOSSARY_KEY = {
    "hello": "bonjour", "hi": "salut", "hey": "salut", "coucou": "salut", "bsr": "bonsoir", "bjr": "bonjour",
    "good morning": "bonjour", "good evening": "bonsoir", "welcome": "bienvenue",
    "thanks": "merci", "thank you": "merci", "please": "svp", "sorry": "pardon",
    "yes": "oui", "no": "non", "okay": "ok", "d'accord": "daccord",
    "help": "aide", "aidez": "aider", "aidez-moi": "aider",
    "how much": "combien", "how": "comment", "what": "quoi", "who": "qui", "where": "ou", "où": "ou", "when": "quand", "why": "pourquoi",
    "balance": "solde", "money": "argent", "cash": "argent", "fonds": "argent",
    "amount": "montant", "sum": "somme", "fee": "frais", "fees": "frais", "charges": "frais", "cost": "cout", "coût": "cout", "price": "prix",
    "limit": "plafond", "maximum": "plafond", "max": "plafond",
    "bank": "banque", "account": "compte", "customer": "client",
    "beneficiary": "beneficiaire", "bénéficiaire": "beneficiaire", "recipient": "destinataire",
    "name": "nom", "number": "numero", "numéro": "numero", "phone": "telephone", "téléphone": "telephone", "tel": "telephone",
    "airtime": "credit", "crédit": "credit", "unites": "credit", "unités": "credit",
    "bill": "facture", "bills": "facture", "factures": "facture",
    "water": "eau", "electricity": "electricite", "électricité": "electricite", "lumiere": "electricite", "lumière": "electricite",
    "network": "reseau", "réseau": "reseau", "operator": "operateur", "opérateur": "operateur",
    "history": "historique", "transactions": "transaction", "operations": "operation", "opérations": "operation", "opération": "operation",
    "receipt": "recu", "reçu": "recu", "référence": "reference",
    "error": "erreur", "problem": "probleme", "problème": "probleme",
    "language": "langue", "home": "accueil", "house": "maison", "today": "aujourd'hui", "tomorrow": "demain", "now": "maintenant",
    "send": "envoyer", "envoies": "envoie", "envoyez": "envoyer", "envoyé": "envoye",
    "transfer": "transfert", "transférer": "transferer", "transfere": "transferer", "transfère": "transferer", "virement": "transfert",
    "receive": "recevoir", "reçois": "recevoir", "recois": "recevoir",
    "withdraw": "retirer", "withdrawal": "retrait",
    "pay": "payer", "payez": "payer", "payé": "paye", "paid": "paye",
    "buy": "acheter", "achète": "achete",
    "verify": "verifier", "vérifier": "verifier", "vérifie": "verifier", "check": "consulter", "consulte": "consulter", "see": "voir", "vois": "voir",
    "confirm": "confirmer", "confirme": "confirmer", "confirmez": "confirmer", "validate": "valider", "valide": "valider",
    "cancel": "annuler", "annule": "annuler", "annulez": "annuler",
    "edit": "modifier", "modifie": "modifier", "change": "changer", "corrige": "corriger",
    "choose": "choisir", "choisis": "choisir", "pick": "choisir",
    "listen": "ecouter", "écouter": "ecouter", "écoute": "ecouter", "speak": "parler", "parle": "parler",
    "back": "retour", "finish": "terminer", "done": "terminer", "terminé": "terminer",
    "security": "securite", "sécurité": "securite", "insufficient": "insuffisant", "available": "disponible", "free": "gratuit", "good": "bon",
}


# Connecteurs et prépositions pour éviter les calques français dans la traduction de phrases
_CONNECTORS: dict[str, dict[str, str]] = {
    "je": {"fr": "je", "en": "I", "wes": "A", "fub": "mi", "hau": "ni", "bum": "me", "ewo": "ma", "dua": "na", "bas": "me", "bbj": "mə", "byv": "mə"},
    "veux": {"fr": "veux", "en": "want", "wes": "wan", "fub": "yiɗi", "hau": "so", "bum": "kômbô", "ewo": "yi", "dua": "pula", "bas": "nyéñ", "bbj": "kôŋ", "byv": "kô"},
    "a": {"fr": "à", "en": "to", "wes": "give", "fub": "e", "hau": "zuwa", "bum": "be", "ewo": "a", "dua": "na", "bas": "í", "bbj": "a", "byv": "a"},
    "à": {"fr": "à", "en": "to", "wes": "give", "fub": "e", "hau": "zuwa", "bum": "be", "ewo": "a", "dua": "na", "bas": "í", "bbj": "a", "byv": "a"},
    "au": {"fr": "au", "en": "at", "wes": "fo", "fub": "e", "hau": "a", "bum": "be", "ewo": "a", "dua": "o", "bas": "i", "bbj": "a", "byv": "a"},
    "vers": {"fr": "vers", "en": "to", "wes": "give", "fub": "e", "hau": "zuwa", "bum": "be", "ewo": "a", "dua": "na", "bas": "i", "bbj": "a", "byv": "a"},
    "pour": {"fr": "pour", "en": "for", "wes": "fo", "fub": "ngam", "hau": "don", "bum": "asu", "ewo": "asu", "dua": "onyola", "bas": "inyu", "bbj": "mba", "byv": "num"},
    "et": {"fr": "et", "en": "and", "wes": "an", "fub": "e", "hau": "da", "bum": "ba", "ewo": "a", "dua": "na", "bas": "ni", "bbj": "na", "byv": "na"},
    "mon": {"fr": "mon", "en": "my", "wes": "ma", "fub": "maa", "hau": "na", "bum": "wom", "ewo": "wom", "dua": "mongo", "bas": "won", "bbj": "po", "byv": "bu"},
    "ma": {"fr": "ma", "en": "my", "wes": "ma", "fub": "am", "hau": "ta", "bum": "wom", "ewo": "wom", "dua": "am", "bas": "wem", "bbj": "yà", "byv": "zà"},
    "ton": {"fr": "ton", "en": "your", "wes": "yu", "fub": "maa", "hau": "ka", "bum": "wôé", "ewo": "wôé", "dua": "ango", "bas": "yon", "bbj": "po", "byv": "bu"},
    "sa": {"fr": "sa", "en": "his", "wes": "yi", "fub": "makko", "hau": "sa", "bum": "é", "ewo": "dzé", "dua": "mao", "bas": "wé", "bbj": "yé", "byv": "zé"},
    "votre": {"fr": "votre", "en": "your", "wes": "yu", "fub": "maa", "hau": "ka", "bum": "wôé", "ewo": "wôé", "dua": "ango", "bas": "yon", "bbj": "po", "byv": "bu"},
    "frere": {"fr": "frère", "en": "brother", "wes": "broda", "fub": "deerɗiraawo", "hau": "dan uwa", "bum": "mônyañ", "ewo": "manyaṅ", "dua": "muna nyango", "bas": "mankéé", "bbj": "sò'", "byv": "mènzwə"},
    "beaucoup": {"fr": "beaucoup", "en": "very much", "wes": "plenty", "fub": "sanu", "hau": "sosai", "bum": "abui", "ewo": "abui", "dua": "jita", "bas": "ngandag", "bbj": "bwe", "byv": "bwam"},
}
_DROP_ARTICLES = {"le", "la", "les", "l", "un", "une", "des", "du", "de", "d", "est", "sont", "quel", "quels", "quelle", "quelles"}


def anonymize_to_variables(text: str) -> tuple[str, dict[str, str]]:
    """Remplace toute donnée confidentielle (sommes, noms de clients, numéros de téléphone, références) par des {variables} changeables."""
    variables: dict[str, str] = {}
    existing_placeholders: list[str] = []
    existing_names = set(re.findall(r"\{([a-z0-9_]+)\}", text))

    def _stash_existing(m: re.Match) -> str:
        letter_id = ""
        n = len(existing_placeholders)
        while True:
            letter_id = chr(ord("A") + (n % 26)) + letter_id
            n = n // 26 - 1
            if n < 0:
                break
        existing_placeholders.append(m.group(0))
        return f"__EXVAR_{letter_id}__"

    out = re.sub(r"\{[a-z0-9_]+\}", _stash_existing, text)

    def _alloc_var(base: str, raw_val: str) -> str:
        # Réutiliser la même variable si la même valeur réapparaît
        for k, v in variables.items():
            if v == raw_val:
                return "{" + k + "}"
        if base not in variables and base not in existing_names:
            variables[base] = raw_val
            return "{" + base + "}"
        idx = 2
        while f"{base}_{idx}" in variables or f"{base}_{idx}" in existing_names:
            idx += 1
        key = f"{base}_{idx}"
        variables[key] = raw_val
        return "{" + key + "}"

    # 1. Références de transaction (TRX-..., SAF-...) -> {reference}
    out = re.sub(
        r"\b(?:TRX|SAF)-[A-Za-z0-9\-]+\b",
        lambda m: _alloc_var("reference", m.group(0)),
        out,
    )
    # 2. Numéros de téléphone camerounais -> {phone}
    out = re.sub(
        r"(?:\+?237[\s\-\.]?)?[26](?:[\s\-\.]?\d){8}\b",
        lambda m: _alloc_var("phone", m.group(0)),
        out,
    )
    # 3. Sommes / montants avec ou sans devise -> {amount} (ne pas capturer les indices de variables déjà créées)
    out = re.sub(
        r"(?<!_)\b\d[\d\s\.,]*\s*(?:FCFA|XAF|CFA)\b|(?<!_)\b\d+(?:[\s\.,]\d+)*\b",
        lambda m: _alloc_var("amount", m.group(0).strip()),
        out,
        flags=re.IGNORECASE,
    )
    # 4. Noms de clients après salutations -> {name}
    def _greeting_name(m: re.Match) -> str:
        greet, person = m.group(1), m.group(2)
        if person.lower() in WORD_GLOSSARY or person.lower() in _EN_TO_GLOSSARY_KEY or person.lower() in _CONNECTORS or person.lower() in _DROP_ARTICLES:
            return m.group(0)
        return f"{greet}{_alloc_var('name', person)}"

    out = re.sub(
        r"(\b(?:[Bb]onjour|[Bb]onjor|[Bb]jr|[Bb]onsoir|[Bb]sr|[Ss]alut|[Hh]ello|[Mm]bolo|[Ss]annu|[Bb]arka)\s+)([A-ZÀ-Ÿ][a-zà-ÿ'\-]+(?:\s+[A-ZÀ-Ÿ][a-zà-ÿ'\-]+)*)",
        _greeting_name,
        out,
    )
    # 5. Noms de bénéficiaires après prépositions -> {beneficiary} (ou {name} après de/from si pas déjà pris)
    _PUBLIC_BRANDS = {"eneo", "camwater", "canal", "canal+", "camtel", "mtn", "orange", "safinum", "safinum pay", "fcfa", "xaf", "cfa"}

    def _prep_name(m: re.Match) -> str:
        prep, person = m.group(1), m.group(2)
        if person.lower() in _PUBLIC_BRANDS or person.lower() in WORD_GLOSSARY or person.lower() in _EN_TO_GLOSSARY_KEY or person.lower() in _CONNECTORS or person.lower() in _DROP_ARTICLES:
            return m.group(0)
        prep_clean = prep.strip().lower()
        var_base = "name" if prep_clean in ("de", "from") else "beneficiary"
        return f"{prep}{_alloc_var(var_base, person)}"

    out = re.sub(
        r"(\b(?:[àa]|pour|de|vers|chez|give|to|from)\s+)([A-ZÀ-Ÿ][a-zà-ÿ'\-]+(?:\s+[A-ZÀ-Ÿ][a-zà-ÿ'\-]+)*)",
        _prep_name,
        out,
    )

    for idx, ph_val in enumerate(existing_placeholders):
        letter_id = ""
        n = idx
        while True:
            letter_id = chr(ord("A") + (n % 26)) + letter_id
            n = n // 26 - 1
            if n < 0:
                break
        out = out.replace(f"__EXVAR_{letter_id}__", ph_val)

    return out, variables


def render_variables(template_text: str, variables: dict[str, str] | None) -> str:
    """Injecte localement des valeurs de variables dans un gabarit traduit (côté affichage/audio uniquement)."""
    if not variables:
        return template_text
    rendered = template_text
    for k, v in variables.items():
        clean_k = k.strip("{}")
        rendered = rendered.replace("{" + clean_k + "}", str(v))
    return rendered


def translate_phrase(text: str, target_lang: str) -> dict[str, Any]:
    """Traduit uniquement un gabarit anonymisé : AUCUNE somme, AUCUN nom de client ni numéro de téléphone dans la traduction (remplacés par des {variables})."""
    lang = normalize_language(target_lang) or "fr"
    clean = text.strip()
    low = clean.lower()

    # 0. Extraction automatique des données confidentielles en {variables} dynamiques
    template_clean, extracted_vars = anonymize_to_variables(clean)
    t_low = template_clean.lower()

    # 1. Correspondance directe sur un mot ou terme exact du glossaire (uniquement s'il n'y a aucune donnée confidentielle)
    if not extracted_vars:
        key_exact = _EN_TO_GLOSSARY_KEY.get(low, low.replace("é", "e").replace("è", "e"))
        if key_exact in WORD_GLOSSARY:
            return {"mode": "exact_word", "translated": WORD_GLOSSARY[key_exact].get(lang, clean), "source_template": template_clean, "variables": {}}

    # 2. Protection des {variables} dynamiques et des sigles publics (FCFA, ENEO, MTN, ORANGE...)
    protected: list[str] = []

    def _stash(match: re.Match) -> str:
        idx = len(protected)
        protected.append(match.group(0))
        return f"__PROT_{idx}__"

    masked = re.sub(
        r"\{[a-z0-9_]+\}|"
        r"\b(?:FCFA|XAF|CFA)\b|"
        r"\b(?:ENEO|CAMWATER|CANAL\+?|CAMTEL|MTN|ORANGE|Safinum(?:\s+Pay)?)\b",
        _stash,
        template_clean,
        flags=re.IGNORECASE,
    )

    # 3. Patrons de phrases naturelles complètes (avant repli mot-à-mot)
    m_low = masked.lower()
    natural_out: str | None = None
    if re.search(r"\b(quel est mon solde|mon solde|votre solde|check my balance)\b", m_low):
        natural_out = {
            "fr": "Quel est votre solde disponible ?",
            "en": "What is your available balance?",
            "wes": "How much moni remain fo yu account?",
            "fub": "Ceede maa keddiiɗe ko noye?",
            "hau": "Nawa ne ragowar kudina a asusu?",
            "bum": "Moné wom a li'i a ne tañ ya?",
            "ewo": "Mòni wom a lig ma a ne tân ya?",
            "dua": "Môni mongo ma dia me nena?",
            "bas": "Moni won u nkon u yene nwaa?",
            "bbj": "Ŋkap po ya tse ba sa?",
            "byv": "Nkap bu ya tse ne sa?",
        }.get(lang)
    elif re.match(r"^\s*(solde insuffisant|pas assez d'argent|insufficient balance)[\s\.\!\?]*$", m_low):
        natural_out = get_error_text(lang, "INSUFFICIENT_FUNDS")
    elif re.match(r"^\s*(merci beaucoup|thank you very much)[\s\.\!\?]*$", m_low):
        natural_out = {
            "fr": "Merci beaucoup.",
            "en": "Thank you very much.",
            "wes": "Thank yu plenty.",
            "fub": "Useko sanu.",
            "hau": "Na gode sosai.",
            "bum": "Akéva abui.",
            "ewo": "Ma və́ wa akíba abui.",
            "dua": "Na som jita.",
            "bas": "Matue ngandag.",
            "bbj": "Ndèmá bwe.",
            "byv": "Mə̀ làbtə̌ bwam.",
        }.get(lang)

    if natural_out:
        for idx, val in enumerate(protected):
            natural_out = natural_out.replace(f"__PROT_{idx}__", val)
        return {"mode": "natural_sentence", "translated": natural_out, "source_template": template_clean, "variables": extracted_vars, "words_translated": len(natural_out.split())}

    # 3b. Correspondance dans le corpus parallèle Soreva (150 phrases courantes en 7 langues camerounaises)
    try:
        import json
        from pathlib import Path

        corpus_path = Path(__file__).resolve().parent / "data" / "cameroon_corpus_extract.json"
        if corpus_path.is_file():
            raw_c = json.loads(corpus_path.read_text(encoding="utf-8"))
            for row in raw_c.get("soreva_parallel", []):
                for _, vals in row.items():
                    if m_low in (vals.get("aglc", "").strip().lower(), vals.get("ascii", "").strip().lower()):
                        if lang in row and row[lang].get("aglc"):
                            soreva_tr = row[lang]["aglc"]
                            for idx, val in enumerate(protected):
                                soreva_tr = soreva_tr.replace(f"__PROT_{idx}__", val)
                            return {"mode": "soreva_corpus", "translated": soreva_tr, "source_template": template_clean, "variables": extracted_vars, "words_translated": len(soreva_tr.split())}
    except Exception:
        pass

    # 4. Traduction mot-à-mot / syntagmes avec connecteurs grammaticaux et suppression des articles français
    tokens = re.findall(r"__PROT_\d+__|[A-Za-zÀ-ÿ0-9'ʼ]+|[^\w\s]+|\s+", masked)
    out: list[str] = []
    replaced = 0
    for tok in tokens:
        if tok.startswith("__PROT_") or tok.isspace() or not re.match(r"^[A-Za-zÀ-ÿ'ʼ]+$", tok):
            out.append(tok)
            continue
        norm_tok = tok.lower().replace("é", "e").replace("è", "e").replace("ê", "e")
        if lang != "fr" and norm_tok in _DROP_ARTICLES:
            continue
        if norm_tok in _CONNECTORS:
            out.append(_CONNECTORS[norm_tok].get(lang, tok))
            replaced += 1
            continue
        g_key = _EN_TO_GLOSSARY_KEY.get(norm_tok, norm_tok)
        if g_key in WORD_GLOSSARY:
            out.append(WORD_GLOSSARY[g_key].get(lang, tok))
            replaced += 1
        else:
            out.append(tok)

    result = re.sub(r"\s{2,}", " ", "".join(out)).strip()

    # 5. Si aucun mot n'a pu être traduit par le lexique (replaced == 0), utiliser le moteur neuronal CTranslate2 / OPUS-MT local
    if replaced == 0 and lang != "fr" and re.search(r"[A-Za-zÀ-ÿ]", masked):
        try:
            import sys
            from pathlib import Path

            nmt_dir = str(Path(__file__).resolve().parents[2] / "traduction_service_google")
            if nmt_dir not in sys.path:
                sys.path.insert(0, nmt_dir)
            from local_nmt import translate_neural_local

            # Remplacer temporairement __PROT_i__ par un sentinelle numérique 88010i
            nmt_in = masked
            for idx in range(len(protected)):
                nmt_in = nmt_in.replace(f"__PROT_{idx}__", f"88010{idx}")
            src_guess = detect_language(template_clean, fallback="fr")
            nmt_out, nmt_eng = translate_neural_local(nmt_in, src_guess, lang)
            if nmt_out:
                valid_restored = True
                for idx, val in enumerate(protected):
                    if f"88010{idx}" not in nmt_out:
                        valid_restored = False
                        break
                    nmt_out = nmt_out.replace(f"88010{idx}", val)
                if valid_restored:
                    return {"mode": f"neural_{nmt_eng}", "translated": nmt_out, "source_template": template_clean, "variables": extracted_vars, "words_translated": len(nmt_out.split())}
        except Exception:
            pass

    for idx, val in enumerate(protected):
        result = result.replace(f"__PROT_{idx}__", val)

    return {"mode": "word_by_word" if replaced > 0 else "passthrough", "translated": result, "source_template": template_clean, "variables": extracted_vars, "words_translated": replaced}
