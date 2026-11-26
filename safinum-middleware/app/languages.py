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
    "wes": "Pidgin Camerounais (Kamtok)",
}

SUPPORTED_LANGUAGES = {
    "dua": "Duálá",
    "ewo": "Ewondo",
    "bas": "Ɓasaá",
    "bbj": "Ghɔmálá'",
    "byv": "Mə̀dûmbà",
    "fub": "Fulfulde",
    "wes": "Pidgin Camerounais (Kamtok)",
    "fr": "Français",
    "en": "English",
}

LANGUAGE_ALIASES = {
    "fr": "fr", "francais": "fr", "français": "fr", "french": "fr",
    "en": "en", "anglais": "en", "english": "en",
    "ewo": "ewo", "ewondo": "ewo", "beti": "ewo",
    "fub": "fub", "ff": "fub", "fulfulde": "fub", "fula": "fub", "peul": "fub",
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
        "ask_transfer_details": "Precisez le montant et le beneficiaire (ex: envoyer 5000 FCFA a 677000001).",
        "ask_clarify_candidates": "Plusieurs beneficiaires correspondent : {candidates}. Lequel choisissez-vous ?",
        "ask_correction": "Que souhaitez-vous modifier (montant ou beneficiaire) ?",
        "lang_switched": "Langue changee en Francais. Comment puis-je vous aider ?",
        "unknown": "Je n'ai pas bien compris. Vous pouvez demander votre solde, les frais, l'historique ou un transfert.",
        "unknown_ussd": "Choix invalide.\n1.Solde 2.Transfert 3.Frais 4.Hist 0.Langue",
        "err_INSUFFICIENT_FUNDS": "Solde insuffisant pour effectuer cette operation (montant + frais).",
        "err_UNKNOWN_BENEFICIARY": "Beneficiaire introuvable. Verifiez le nom ou le numero.",
        "err_LIMIT_EXCEEDED": "Le montant depasse le plafond autorise de 500 000 FCFA par operation.",
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
        "ask_transfer_details": "Please specify the amount and beneficiary (e.g. send 5000 FCFA to 677000001).",
        "ask_clarify_candidates": "Multiple beneficiaries match: {candidates}. Which one do you choose?",
        "ask_correction": "What would you like to change (amount or beneficiary)?",
        "lang_switched": "Language switched to English. How can I help you?",
        "unknown": "I did not understand. You can ask for your balance, fees, history, or a transfer.",
        "unknown_ussd": "Invalid choice.\n1.Balance 2.Transfer 3.Fees 4.Hist 0.Lang",
        "err_INSUFFICIENT_FUNDS": "Insufficient balance for this operation (amount + fees).",
        "err_UNKNOWN_BENEFICIARY": "Beneficiary not found. Please check the name or phone number.",
        "err_LIMIT_EXCEEDED": "Amount exceeds the 500,000 FCFA per-operation limit.",
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
        "ask_transfer_details": "Talk how much yu wan send an di pesin (ex: send 5000 FCFA give 677000001).",
        "ask_clarify_candidates": "Plenty pesin get dis name: {candidates}. Which one yu mean?",
        "ask_correction": "Wetin yu wan change (how much or di pesin)?",
        "lang_switched": "We don change language fo Pidgin. How ah fit help yu?",
        "unknown": "Ah no understand fine. Yu fit ask fo yu moni weh remain, charges, history or send moni.",
        "unknown_ussd": "No correct.\n1.Moni 2.Send 3.Charges 4.Hist 0.Lang",
        "err_INSUFFICIENT_FUNDS": "Yu moni no reach fo dis send (amount + charges).",
        "err_UNKNOWN_BENEFICIARY": "We no see dat pesin. Check di name or phone number.",
        "err_LIMIT_EXCEEDED": "Di moni don pass limit (500 000 FCFA).",
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
        "menu": "Safinum Pay\n1. Ceede keddiide\n2. Nel ceede\n3. Njobdi\n4. Golle ceede\n5. Kredit\n6. Faktir\n0. Demgal",
        "menu_ussd": "Safinum Pay\n1.Ceede\n2.Nel ceede\n3.Njobdi\n4.Golle\n5.Kredit\n6.Faktir\n0.Demgal",
        "balance": "Sannu {name}. Ceede maa keddiide ko {balance} FCFA (konte {phone}).",
        "balance_ussd": "Ceede {name}: {balance} FCFA. 1.Nel 2.Njobdi 0.Menu",
        "fees": "Ngam {amount} FCFA ({op_type}), njobdi ko {fee} FCFA. Fuu ko ittetee ko {total} FCFA.",
        "fees_ussd": "Njobdi {amount} FCFA: {fee} FCFA. Fuu: {total} FCFA. 0.Menu",
        "history_header": "Golle ceede maa {count} sakkitiide:",
        "history_empty": "Alaa golle ceede kesre e konte maa.",
        "confirm_transfer": "Yeewaa fuu: nelde {amount} FCFA e {beneficiary} ({to_phone}). Njobdi: {fee} FCFA. Fuu: {total} FCFA. Jaabo 1 (Tabbitin) malla 2 (Habbit).",
        "confirm_transfer_ussd": "Nel {amount} FCFA e {beneficiary}. Njobdi {fee}, Fuu {total} FCFA.\n1.Tabbitin\n2.Habbit",
        "confirm_airtime": "Yeewaa fuu: soodude kredit {operator} {amount} FCFA ngam {to_phone} (njobdi: {fee} FCFA). Jaabo 1 (Tabbitin) malla 2 (Habbit).",
        "confirm_bill": "Yeewaa fuu: njobdi faktir {biller} {amount} FCFA (njobdi: {fee} FCFA, fuu: {total} FCFA). Jaabo 1 (Tabbitin) malla 2 (Habbit).",
        "confirmed": "Nelde ceede gasii no feewi! Ref: {tx_id}. Limre: {amount} FCFA.",
        "confirmed_ussd": "Gasii! Ref:{tx_id}. {amount} FCFA. 0.Menu",
        "cancelled": "Golle habbitaama. Alaa ceede ittaa.",
        "no_pending": "Alaa golle faddeede tabbitinal.",
        "ask_amount": "Limre ceede noye (FCFA) njid-daa nelde?",
        "ask_beneficiary": "Mo heboowo (innde malla limre) nelataa {amount} FCFA?",
        "ask_transfer_details": "Winndu limre ceede e heboowo (misal: nel 5000 FCFA e 677000001).",
        "ask_clarify_candidates": "Heboobe heewbe nanndube: {candidates}. Mo cubi-daa?",
        "ask_correction": "Ko njid-daa waylude (limre ceede malla heboowo)?",
        "lang_switched": "Demgal waylaama e Fulfulde. No mballirmi maa?",
        "unknown": "Mi faamaani. A waawi naamnaade ceede maa, njobdi, golle malla nelde ceede.",
        "unknown_ussd": "Famaani.\n1.Ceede 2.Nel 3.Njobdi 4.Golle 0.Demgal",
        "err_INSUFFICIENT_FUNDS": "Ceede maa yonaa ngam nelde ndee (limre + njobdi).",
        "err_UNKNOWN_BENEFICIARY": "Heboowo hebaaka. Yeew innde malla limre telefon.",
        "err_LIMIT_EXCEEDED": "Limre ceede burii keeri 500 000 FCFA.",
        "err_INVALID_AMOUNT": "Limre ceede moƴƴaa. Winndu limre goonga e FCFA.",
        "err_UNKNOWN_BILLER": "Faktir malla rese anndaaka (ENEO, CAMWATER, CANAL, CAMTEL, MTN, ORANGE).",
        "err_TX_NOT_FOUND": "Golle ceede hebaaka.",
        "err_TX_NOT_PENDING": "Golle ndee faddeetaake kadi.",
        "err_UNAUTHORIZED": "Juumre seedantaagal (team key).",
        "err_UNKNOWN_ACCOUNT": "Konte hebaaka.",
        "err_INVALID_REQUEST": "Naamnal moƴƴaa.",
        "err_CONFIG_LOCKED": "Teelte uddataama e waktu ƴeewndo.",
        "err_UNSAFE_ENDPOINT": "URL jaɓaaka.",
        "err_GENERIC": "Juumre reso: sarwis oo heɓataake jooni. Fuɗɗito kadi.",
    },
    "ewo": {
        "menu": "Safinum Pay\n1. Mòni a lig\n2. Lom mòni\n3. Fre\n4. Alom ya nde\n5. Kredit\n6. Faktir\n0. Nkobo",
        "menu_ussd": "Safinum Pay\n1.Moni\n2.Lom moni\n3.Fre\n4.Alom nde\n5.Kredit\n6.Faktir\n0.Nkobo",
        "balance": "Mbolo {name}. Mòni wôé a lig a ne {balance} FCFA (konte {phone}).",
        "balance_ussd": "Moni {name}: {balance} FCFA. 1.Lom 2.Fre 0.Menu",
        "fees": "Asu {amount} FCFA ({op_type}), fre a ne {fee} FCFA. Mone mese ba ye nyon: {total} FCFA.",
        "fees_ussd": "Fre {amount} FCFA: {fee} FCFA. Mese: {total} FCFA. 0.Menu",
        "history_header": "Alom mone ya nde {count}:",
        "history_empty": "Alom mone mfe a ne ki.",
        "confirm_transfer": "Yen bise: wa lom {amount} FCFA a {beneficiary} ({to_phone}). Fre: {fee} FCFA. Mese: {total} FCFA. Yebe 1 (Ayebe) nge 2 (Bili/Ben).",
        "confirm_transfer_ussd": "Lom {amount} FCFA a {beneficiary}. Fre {fee}, Mese {total} FCFA.\n1.Ayebe\n2.Bili",
        "confirm_airtime": "Yen bise: kus kredit {operator} {amount} FCFA asu {to_phone} (fre: {fee} FCFA). 1 (Ayebe) nge 2 (Bili).",
        "confirm_bill": "Yen bise: ave faktir {biller} {amount} FCFA (fre: {fee} FCFA, mese: {total} FCFA). 1 (Ayebe) nge 2 (Bili).",
        "confirmed": "Alom mone a mana mbembe! Ref: {tx_id}. Mone: {amount} FCFA.",
        "confirmed_ussd": "A mana! Ref:{tx_id}. {amount} FCFA. 0.Menu",
        "cancelled": "Alom mone a bili. Mone a ne ki nyon.",
        "no_pending": "Alom mone a ne ki a yege ayebe.",
        "ask_amount": "Mòni tân ya (FCFA) wa ye lôm?",
        "ask_beneficiary": "Mod mfe (dzoe nge nombre fon) a ye kos {amount} FCFA?",
        "ask_transfer_details": "Kal mone a mod a kos (ex: lom 5000 FCFA a 677000001).",
        "ask_clarify_candidates": "Bod befe be ne dzoe di: {candidates}. Nnye mfe wa fas?",
        "ask_correction": "Jom fe wa ye sûli (mone nge mod a kos)?",
        "lang_switched": "Nkobo a ne Ewondo. Me ne wo vole aya?",
        "unknown": "Me ne ki wog mbembe. Wa ne sili mone woe, fre, alom ya nde nge lom mone.",
        "unknown_ussd": "Me ne ki wog.\n1.Mone 2.Lom 3.Fre 4.Alom 0.Nkobo",
        "err_INSUFFICIENT_FUNDS": "Mone woe ma ne ki tege ase alom nyi (mone + fre).",
        "err_UNKNOWN_BENEFICIARY": "Mod a kos a ne ki yen. Yen mbembe dzoe nge nombre fon.",
        "err_LIMIT_EXCEEDED": "Mone ma lot 500 000 FCFA.",
        "err_INVALID_AMOUNT": "Mone ma ne ki mbembe. Tili mone ya benya a FCFA.",
        "err_UNKNOWN_BILLER": "Faktir nge operater a ne ki yen (ENEO, CAMWATER, CANAL, CAMTEL, MTN, ORANGE).",
        "err_TX_NOT_FOUND": "Alom mone a ne ki yen.",
        "err_TX_NOT_PENDING": "Alom nyi a ne ki fe a yege ayebe.",
        "err_UNAUTHORIZED": "Dzam abe a team key.",
        "err_UNKNOWN_ACCOUNT": "Konte a ne ki yen.",
        "err_INVALID_REQUEST": "Sil abe.",
        "err_CONFIG_LOCKED": "Config a ne dibi.",
        "err_UNSAFE_ENDPOINT": "URL a ne ki yebe.",
        "err_GENERIC": "Reso a ne ki mbembe: sarvis a ne ki tege. Bulan bo fe.",
    },
    "dua": {
        "menu": "Safinum Pay\n1. Môni ma dia\n2. Lóma môni\n3. Njoa (Frais)\n4. Bola la môni\n5. Kredit\n6. Faktir\n0. Bwea",
        "menu_ussd": "Safinum Pay\n1.Moni\n2.Loma moni\n3.Njoa\n4.Bola\n5.Kredit\n6.Faktir\n0.Bwea",
        "balance": "Idib'a bwam {name}. Môni mongo ma dia me {balance} FCFA (konte {phone}).",
        "balance_ussd": "Moni {name}: {balance} FCFA. 1.Loma 2.Njoa 0.Menu",
        "fees": "Onyola {amount} FCFA ({op_type}), njoa e ne {fee} FCFA. Môni mese: {total} FCFA.",
        "fees_ussd": "Njoa {amount} FCFA: {fee} FCFA. Mese: {total} FCFA. 0.Menu",
        "history_header": "Bola longo la môni {count} la sukan:",
        "history_empty": "Bola la môni di si ma dia o konte ango.",
        "confirm_transfer": "Kwaléa bwam: o ma lóma {amount} FCFA na {beneficiary} ({to_phone}). Njoa: {fee} FCFA. Mese: {total} FCFA. Alane 1 (Hee / Timbisɛ) to 2 (Kem / Timba).",
        "confirm_transfer_ussd": "Loma {amount} FCFA na {beneficiary}. Njoa {fee}, Mese {total} FCFA.\n1.Hee\n2.Kem",
        "confirm_airtime": "Kwaléa bwam: anda kredit {operator} {amount} FCFA na {to_phone} (njoa: {fee} FCFA). 1 (Timbisɛ) to 2 (Timba).",
        "confirm_bill": "Kwaléa bwam: sawa faktir {biller} {amount} FCFA (njoa: {fee} FCFA, mese: {total} FCFA). 1 (Timbisɛ) to 2 (Timba).",
        "confirmed": "Loma la môni di timbisabe bwam! Ref: {tx_id}. Môni: {amount} FCFA.",
        "confirmed_ussd": "Di boli! Ref:{tx_id}. {amount} FCFA. 0.Menu",
        "cancelled": "Loma di timbabe. Môni mu si busi.",
        "no_pending": "Bola di si ma dia o longe timbisɛ.",
        "ask_amount": "Moni nena (FCFA) o ma pula loma?",
        "ask_beneficiary": "Nja (dina to numba) nu ma kusa {amount} FCFA?",
        "ask_transfer_details": "Langwa moni na moto nu ma kusa (ex: loma 5000 FCFA na 677000001).",
        "ask_clarify_candidates": "Bato bapepe ba bi dina di: {candidates}. Nja o ma posa?",
        "ask_correction": "Nje o ma pula tukwa (moni to moto)?",
        "lang_switched": "Bwea bu tukwabe o Duala. Ne na longwa wa ne?",
        "unknown": "Na si senga bwea. O wele baise moni mongo, njoa, bola to loma moni.",
        "unknown_ussd": "Na si senga.\n1.Moni 2.Loma 3.Njoa 4.Bola 0.Bwea",
        "err_INSUFFICIENT_FUNDS": "Moni mongo mu si koki onyola loma di (moni + njoa).",
        "err_UNKNOWN_BENEFICIARY": "Moto nu ma kusa a si benabe. Ombwa dina to numba.",
        "err_LIMIT_EXCEEDED": "Moni mu tombi 500 000 FCFA.",
        "err_INVALID_AMOUNT": "Moni mu si tege. Tila moni ma mbale o FCFA.",
        "err_UNKNOWN_BILLER": "Faktir to operater e si bibe (ENEO, CAMWATER, CANAL, CAMTEL, MTN, ORANGE).",
        "err_TX_NOT_FOUND": "Bola di si benabe.",
        "err_TX_NOT_PENDING": "Bola di si ma longe eme.",
        "err_UNAUTHORIZED": "Ndutu a team key.",
        "err_UNKNOWN_ACCOUNT": "Konte e si benabe.",
        "err_INVALID_REQUEST": "Baise di si tege.",
        "err_CONFIG_LOCKED": "Config e dibabe.",
        "err_UNSAFE_ENDPOINT": "URL e si emebe.",
        "err_GENERIC": "Ndutu a reso: sarvis e si ma bola tatan. Bola pete.",
    },
    "bas": {
        "menu": "Safinum Pay\n1. Moni u nkon\n2. Lémèl moni\n3. Nsas (Frais)\n4. Bilon bi moni\n5. Kredit\n6. Faktir\n0. Hop",
        "menu_ussd": "Safinum Pay\n1.Moni\n2.Lemel moni\n3.Nsas\n4.Bilon\n5.Kredit\n6.Faktir\n0.Hop",
        "balance": "Kɛl i lam {name}. Moni won u nkon u yene {balance} FCFA (konte {phone}).",
        "balance_ussd": "Moni {name}: {balance} FCFA. 1.Lemel 2.Nsas 0.Menu",
        "fees": "Inyu {amount} FCFA ({op_type}), nsas u yene {fee} FCFA. Moni mwomede: {total} FCFA.",
        "fees_ussd": "Nsas {amount} FCFA: {fee} FCFA. Mwomede: {total} FCFA. 0.Menu",
        "history_header": "Bilon bion bi moni {count} bi nsukan:",
        "history_empty": "Bilon bi moni bi ta be i konte yon.",
        "confirm_transfer": "Tol longe: u nlémèl {amount} FCFA i {beneficiary} ({to_phone}). Nsas: {fee} FCFA. Mwomede: {total} FCFA. Timbhe 1 (Ŋ̀ŋ̂ / Hémle) to 2 (Tɔ̀ / Bôg).",
        "confirm_transfer_ussd": "Lemel {amount} FCFA i {beneficiary}. Nsas {fee}, Mwomede {total} FCFA.\n1.Nng\n2.To",
        "confirm_airtime": "Tol longe: somb kredit {operator} {amount} FCFA inyu {to_phone} (nsas: {fee} FCFA). 1 (Hémle) to 2 (Bôg).",
        "confirm_bill": "Tol longe: jel faktir {biller} {amount} FCFA (nsas: {fee} FCFA, mwomede: {total} FCFA). 1 (Hémle) to 2 (Bôg).",
        "confirmed": "Lémèl u mal longe! Ref: {tx_id}. Moni: {amount} FCFA.",
        "confirmed_ussd": "U mal! Ref:{tx_id}. {amount} FCFA. 0.Menu",
        "cancelled": "Lémèl u bôg. Moni u nyo-be.",
        "no_pending": "Bilon bi ta be i bem hémle.",
        "ask_amount": "Moni nwaa (FCFA) u ngwés lom?",
        "ask_beneficiary": "Njee (jôl to nombo) a nkôs {amount} FCFA?",
        "ask_transfer_details": "Kal moni ni mut a nkôs (ex: lom 5000 FCFA i 677000001).",
        "ask_clarify_candidates": "Bôt bape ba gwe jôl lini: {candidates}. Njee u mpohol?",
        "ask_correction": "Kii u ngwés henha (moni to mut)?",
        "lang_switched": "Hop u henha i Basaa. Lelaa me nla hôla we?",
        "unknown": "Me nok-be longe. U nla bat moni won, nsas, bilon to lom moni.",
        "unknown_ussd": "Me nok-be.\n1.Moni 2.Lom 3.Nsas 4.Bilon 0.Hop",
        "err_INSUFFICIENT_FUNDS": "Moni won u nkola ɓé inyu lémèl unu (moni + nsas).",
        "err_UNKNOWN_BENEFICIARY": "Mut a nkôs a nene-be. Benge jôl to nombo.",
        "err_LIMIT_EXCEEDED": "Moni u nloo 500 000 FCFA.",
        "err_INVALID_AMOUNT": "Moni u ta-be longe. Tila moni u mba i FCFA.",
        "err_UNKNOWN_BILLER": "Faktir to operater i yi-be (ENEO, CAMWATER, CANAL, CAMTEL, MTN, ORANGE).",
        "err_TX_NOT_FOUND": "Lom u nene-be.",
        "err_TX_NOT_PENDING": "Lom unu u mbem-be neebe.",
        "err_UNAUTHORIZED": "Njam i team key.",
        "err_UNKNOWN_ACCOUNT": "Konte i nene-be.",
        "err_INVALID_REQUEST": "Mbat i ta-be longe.",
        "err_CONFIG_LOCKED": "Config i yibha.",
        "err_UNSAFE_ENDPOINT": "URL i neebe-be.",
        "err_GENERIC": "Njam i reso: sarvis i nsal-be nano. Tigil bôt.",
    },
    "bbj": {
        "menu": "Safinum Pay\n1. Ŋkap ya tse\n2. Tom ŋkap\n3. Frais\n4. Bivul\n5. Kredit\n6. Faktir\n0. Ghomala",
        "menu_ussd": "Safinum Pay\n1.Nkap\n2.Tom nkap\n3.Frais\n4.Bivul\n5.Kredit\n6.Faktir\n0.Ghom",
        "balance": "Mbúʼ {name}. Ŋkap po ya tse e ba {balance} FCFA (konte {phone}).",
        "balance_ussd": "Nkap {name}: {balance} FCFA. 1.Tom 2.Frais 0.Menu",
        "fees": "Mba {amount} FCFA ({op_type}), frais ba {fee} FCFA. Ŋkap tsem: {total} FCFA.",
        "fees_ussd": "Frais {amount} FCFA: {fee} FCFA. Tsem: {total} FCFA. 0.Menu",
        "history_header": "Bivul bi ŋkap {count} bi tsem:",
        "history_empty": "Bivul bi ŋkap ka po.",
        "confirm_transfer": "Ye bwe: o ko tom {amount} FCFA a {beneficiary} ({to_phone}). Frais: {fee} FCFA. Tsem: {total} FCFA. 1 (Yôô) ka 2 (Ka').",
        "confirm_transfer_ussd": "Tom {amount} FCFA a {beneficiary}. Frais {fee}, Tsem {total} FCFA.\n1.Yoo\n2.Ka'",
        "confirm_airtime": "Ye bwe: yu kredit {operator} {amount} FCFA a {to_phone} (frais: {fee} FCFA). 1 (Yebe) ka 2 (Tebe).",
        "confirm_bill": "Ye bwe: fo faktir {biller} {amount} FCFA (frais: {fee} FCFA, tsem: {total} FCFA). 1 (Yebe) ka 2 (Tebe).",
        "confirmed": "Nkap tom bwe! Ref: {tx_id}. Nkap: {amount} FCFA.",
        "confirmed_ussd": "Tom bwe! Ref:{tx_id}. {amount} FCFA. 0.Menu",
        "cancelled": "Tom tebe. Nkap ka nyon.",
        "no_pending": "Bivul ka po e yebe.",
        "ask_amount": "Nkap sa (FCFA) o ko tom?",
        "ask_beneficiary": "We (dzo ka nombo) e ko nyam {amount} FCFA?",
        "ask_transfer_details": "Kwe nkap na we e ko nyam (ex: tom 5000 FCFA a 677000001).",
        "ask_clarify_candidates": "Puo puo gwe dzo li: {candidates}. We o ko tso?",
        "ask_correction": "Ka o ko shang (nkap ka we)?",
        "lang_switched": "Ghomala shang bwe. Me ne ko vole o ka?",
        "unknown": "Me ka yu bwe. O ne baa nkap po, frais, bivul ka tom nkap.",
        "unknown_ussd": "Me ka yu.\n1.Nkap 2.Tom 3.Frais 4.Bivul 0.Lang",
        "err_INSUFFICIENT_FUNDS": "Nkap po ka kwet mba tom li (nkap + frais).",
        "err_UNKNOWN_BENEFICIARY": "We e nyam ka yen. Ye dzo ka nombo.",
        "err_LIMIT_EXCEEDED": "Nkap lot 500 000 FCFA.",
        "err_INVALID_AMOUNT": "Nkap ka bwe. Tili nkap bwe a FCFA.",
        "err_UNKNOWN_BILLER": "Faktir ka operater ka yi (ENEO, CAMWATER, CANAL, CAMTEL, MTN, ORANGE).",
        "err_TX_NOT_FOUND": "Tom ka yen.",
        "err_TX_NOT_PENDING": "Tom li ka tse e yebe.",
        "err_UNAUTHORIZED": "Problem a team key.",
        "err_UNKNOWN_ACCOUNT": "Konte ka yen.",
        "err_INVALID_REQUEST": "Baa ka bwe.",
        "err_CONFIG_LOCKED": "Config dibi.",
        "err_UNSAFE_ENDPOINT": "URL ka yebe.",
        "err_GENERIC": "Reso ka bwe: sarvis ka tse. Bulen.",
    },
    "byv": {
        "menu": "Safinum Pay\n1. Nkap bwam\n2. Ntúm nkap\n3. Frais\n4. Bivul\n5. Kredit\n6. Faktir\n0. Medumba",
        "menu_ussd": "Safinum Pay\n1.Nkap\n2.Ntum nkap\n3.Frais\n4.Bivul\n5.Kredit\n6.Faktir\n0.Med",
        "balance": "O zi à {name}. Nkap bu ya tse ne {balance} FCFA (konte {phone}).",
        "balance_ussd": "Nkap {name}: {balance} FCFA. 1.Ntum 2.Frais 0.Menu",
        "fees": "Num {amount} FCFA ({op_type}), frais ne {fee} FCFA. Nkap tsem: {total} FCFA.",
        "fees_ussd": "Frais {amount} FCFA: {fee} FCFA. Tsem: {total} FCFA. 0.Menu",
        "history_header": "Bivul bi nkap {count} bi tsem:",
        "history_empty": "Bivul bi nkap ka po.",
        "confirm_transfer": "Yen bwam: u ko ntúm {amount} FCFA a {beneficiary} ({to_phone}). Frais: {fee} FCFA. Tsem: {total} FCFA. 1 (Ŋ̂ / Yebe) ke 2 (Ŋŋ̀ / Tebe).",
        "confirm_transfer_ussd": "Ntum {amount} FCFA a {beneficiary}. Frais {fee}, Tsem {total} FCFA.\n1.Yebe\n2.Tebe",
        "confirm_airtime": "Yen bwam: yu kredit {operator} {amount} FCFA a {to_phone} (frais: {fee} FCFA). 1 (Yebe) ke 2 (Tebe).",
        "confirm_bill": "Yen bwam: fo faktir {biller} {amount} FCFA (frais: {fee} FCFA, tsem: {total} FCFA). 1 (Yebe) ke 2 (Tebe).",
        "confirmed": "Nkap tom bwam! Ref: {tx_id}. Nkap: {amount} FCFA.",
        "confirmed_ussd": "Tom bwam! Ref:{tx_id}. {amount} FCFA. 0.Menu",
        "cancelled": "Tom tebe. Nkap ka nyon.",
        "no_pending": "Bivul ka po e yebe.",
        "ask_amount": "Nkap sa (FCFA) u ko tom?",
        "ask_beneficiary": "Wo (lin ke nombo) e ko nyam {amount} FCFA?",
        "ask_transfer_details": "Kal nkap na wo e ko nyam (ex: tom 5000 FCFA a 677000001).",
        "ask_clarify_candidates": "Bu bu gwe lin li: {candidates}. Wo u ko tso?",
        "ask_correction": "Ka u ko shang (nkap ke wo)?",
        "lang_switched": "Medumba shang bwam. Me ne ko vole u ka?",
        "unknown": "Me ka yu bwam. U ne baa nkap bu, frais, bivul ke tom nkap.",
        "unknown_ussd": "Me ka yu.\n1.Nkap 2.Tom 3.Frais 4.Bivul 0.Lang",
        "err_INSUFFICIENT_FUNDS": "Nkap bu ka kwet num tom li (nkap + frais).",
        "err_UNKNOWN_BENEFICIARY": "Wo e nyam ka yen. Yen lin ke nombo.",
        "err_LIMIT_EXCEEDED": "Nkap lot 500 000 FCFA.",
        "err_INVALID_AMOUNT": "Nkap ka bwam. Tili nkap bwam a FCFA.",
        "err_UNKNOWN_BILLER": "Faktir ke operater ka yi (ENEO, CAMWATER, CANAL, CAMTEL, MTN, ORANGE).",
        "err_TX_NOT_FOUND": "Tom ka yen.",
        "err_TX_NOT_PENDING": "Tom li ka tse e yebe.",
        "err_UNAUTHORIZED": "Problem a team key.",
        "err_UNKNOWN_ACCOUNT": "Konte ka yen.",
        "err_INVALID_REQUEST": "Baa ka bwam.",
        "err_CONFIG_LOCKED": "Config dibi.",
        "err_UNSAFE_ENDPOINT": "URL ka yebe.",
        "err_GENERIC": "Reso ka bwam: sarvis ka tse. Bulen.",
    },
}


# Explications de terminologie financière (Scénario 10)
FINANCIAL_TERMS: dict[str, dict[str, str]] = {
    "frais": {
        "fr": "Les frais sont la commission prelevee pour traiter votre operation (ex: 50 FCFA jusqu'a 5 000 FCFA, 150 FCFA jusqu'a 25 000 FCFA).",
        "en": "Fees are the service charge for processing your transaction (e.g. 50 FCFA up to 5,000 FCFA, 150 FCFA up to 25,000 FCFA).",
        "wes": "Charges na di smol moni weh bank di comot fo send yu moni (ex: 50 FCFA reach 5 000 FCFA).",
        "fub": "Njobdi ko ceede ittetee ngam golle nelde ceede maa (misal: 50 FCFA haa 5 000 FCFA).",
        "ewo": "Fre a ne mone ba nyon asu alom mone woe (ex: 50 FCFA akui 5 000 FCFA).",
        "dua": "Njoa e ne moni ma busi onyola loma moni mongo (ex: 50 FCFA na 5 000 FCFA).",
        "bas": "Nsas u yene moni ba nyo inyu lom moni won (ex: 50 FCFA tee 5 000 FCFA).",
        "bbj": "Frais ba nkap ba nyon mba tom nkap po (ex: 50 FCFA na 5 000 FCFA).",
        "byv": "Frais ne nkap ba nyon num tom nkap bu (ex: 50 FCFA na 5 000 FCFA).",
    },
    "solde": {
        "fr": "Le solde est le montant total d'argent actuellement disponible sur votre compte.",
        "en": "The balance is the total amount of money currently available in your account.",
        "wes": "Balance na all di moni weh e remain inside yu account now.",
        "fub": "Ceede keddiide ko limre ceede gonnde e konte maa jooni.",
        "ewo": "Mòni a lig a ne mòni mese me ne a kônte wôé dên.",
        "dua": "Moni ma dia me moni mese me o konte ango tatan.",
        "bas": "Moni u nkon u yene moni mwomede u ye i konte yon nano.",
        "bbj": "Nkap ya tse ba nkap tsem e ba o konte po tatan.",
        "byv": "Nkap bwam ne nkap tsem e ba o konte bu tatan.",
    },
    "plafond": {
        "fr": "Le plafond est le montant maximum autorise par operation, soit 500 000 FCFA sur Safinum Pay.",
        "en": "The limit is the maximum amount allowed per operation: 500,000 FCFA on Safinum Pay.",
        "wes": "Limit na di big moni weh yu no fit pass fo one send: 500 000 FCFA.",
        "fub": "Keeri ko limre ceede burnde mawnude e golle gootel: 500 000 FCFA.",
        "ewo": "Plafon a ne mone ya ngul wa ne ki lot a alom wua: 500 000 FCFA.",
        "dua": "Plafon e ne moni ma ndene mu si wele tomba o bola diwo: 500 000 FCFA.",
        "bas": "Plafon u yene moni u nloo u la be loo i lom wada: 500 000 FCFA.",
        "bbj": "Plafon ba nkap mbu ko lot a tom mo: 500 000 FCFA.",
        "byv": "Plafon ne nkap mbu ko lot a tom mo: 500 000 FCFA.",
    },
    "beneficiaire": {
        "fr": "Le beneficiaire est la personne ou l'entreprise qui recoit l'argent de votre transfert.",
        "en": "The beneficiary is the person or business receiving the money from your transfer.",
        "wes": "Beneficiary na di pesin weh go receive di moni weh yu send.",
        "fub": "Heboowo ko neddo keboowo ceede neldaade.",
        "ewo": "Mod a kos a ne mod a ye kos mone woe.",
        "dua": "Moto nu ma kusa a ne moto nu ma kusa moni mongo.",
        "bas": "Mut a nkôs a yene mut a nkôs moni won.",
        "bbj": "We e ko nyam ba moto e ko nyam nkap po.",
        "byv": "Wo e ko nyam ne moto e ko nyam nkap bu.",
    },
    "reference": {
        "fr": "La reference est le code unique (ex: TRX-XXXX) qui prouve et identifie votre transaction.",
        "en": "The reference is the unique code (e.g. TRX-XXXX) that identifies and proves your transaction.",
        "wes": "Reference na di special code (ex: TRX-XXXX) weh di show say yu send moni.",
        "fub": "Referaans ko kod keerido (misal: TRX-XXXX) hollitoowo golle ceede maa.",
        "ewo": "Referans a ne kod (ex: TRX-XXXX) wa lere alom mone woe.",
        "dua": "Referans e ne kod (ex: TRX-XXXX) e ma lee bola longo la moni.",
        "bas": "Referans u yene kod (ex: TRX-XXXX) u nhol lom won.",
        "bbj": "Referans ba kod (ex: TRX-XXXX) e ko lee tom nkap po.",
        "byv": "Referans ne kod (ex: TRX-XXXX) e ko lee tom nkap bu.",
    },
}


def get_text(lang: str, key: str, channel: str = "web", **kwargs: Any) -> str:
    """Récupère un gabarit dans la langue cible (avec repli USSD compact puis FR)."""
    lang_dict = TEMPLATES.get(lang, TEMPLATES["fr"])
    if channel.lower() == "ussd" and f"{key}_ussd" in lang_dict:
        tpl = lang_dict[f"{key}_ussd"]
    else:
        tpl = lang_dict.get(key) or TEMPLATES["fr"].get(key, "")
    return tpl.format(**kwargs) if kwargs else tpl


def get_error_text(lang: str, error_code: str) -> str:
    lang_dict = TEMPLATES.get(lang, TEMPLATES["fr"])
    key = f"err_{error_code}"
    return lang_dict.get(key) or lang_dict.get("err_GENERIC") or TEMPLATES["fr"]["err_GENERIC"]


def get_term_explanation(lang: str, term_key: str) -> str:
    term_dict = FINANCIAL_TERMS.get(term_key, FINANCIAL_TERMS["frais"])
    return term_dict.get(lang) or term_dict["fr"]


# Lexique mot-à-mot vérifié pour les phrases inédites ou partielles (9 langues)
WORD_GLOSSARY: dict[str, dict[str, str]] = {
    # Salutations, politesse & dialogue courant
    "bonjour": {"fr": "bonjour", "en": "hello", "wes": "hello", "fub": "sannu", "ewo": "mbolo", "dua": "idib'a bwam", "bas": "kɛl i lam", "bbj": "mbúʼ", "byv": "o zi à"},
    "salut": {"fr": "salut", "en": "hi", "wes": "i salut oh", "fub": "sannu", "ewo": "masug", "dua": "na nje", "bas": "me yéga", "bbj": "caʼtə", "byv": "mə cà'tə̌"},
    "bonsoir": {"fr": "bonsoir", "en": "good evening", "wes": "good evening", "fub": "jam hiiri", "ewo": "mbembe ngoge", "dua": "ebyamu a bwam", "bas": "kokoa i lam", "bbj": "mbúʼ", "byv": "o zi à"},
    "bienvenue": {"fr": "bienvenue", "en": "welcome", "wes": "welcome", "fub": "jaɓɓama", "ewo": "mbolo", "dua": "bwam", "bas": "mɛ̀ ǹyega", "bbj": "mbúʼ", "byv": "o zi à"},
    "merci": {"fr": "merci", "en": "thank you", "wes": "thank yu", "fub": "useko", "ewo": "ma və́ wa akíba", "dua": "na som", "bas": "matue", "bbj": "ndèmá", "byv": "mə̀ làbtə̌"},
    "pardon": {"fr": "pardon", "en": "please", "wes": "abeg", "fub": "accu hakke", "ewo": "engongol", "dua": "ndedi", "bas": "nwéhél", "bbj": "mesə", "byv": "ndə"},
    "svp": {"fr": "s'il vous plaît", "en": "please", "wes": "abeg", "fub": "useni", "ewo": "engongol", "dua": "na so", "bas": "sôhô", "bbj": "mba", "byv": "mba"},
    "oui": {"fr": "oui", "en": "yes", "wes": "yes", "fub": "ii", "ewo": "yebe", "dua": "hee", "bas": "ŋ̀ŋ̂", "bbj": "yôô", "byv": "ŋ̂"},
    "non": {"fr": "non", "en": "no", "wes": "no", "fub": "alaa", "ewo": "bili", "dua": "kem", "bas": "tɔ̀", "bbj": "ka'", "byv": "ŋŋ̀"},
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
    "solde": {"fr": "solde", "en": "balance", "wes": "moni weh remain", "fub": "ceede keddiiɗe", "ewo": "mòni a lig", "dua": "môni ma dia", "bas": "moni u nkon", "bbj": "ŋkap ya tse", "byv": "nkap bwam"},
    "argent": {"fr": "argent", "en": "money", "wes": "moni", "fub": "ceede", "ewo": "mòni", "dua": "môni", "bas": "moni", "bbj": "ŋkap", "byv": "nkap"},
    "montant": {"fr": "montant", "en": "amount", "wes": "how much", "fub": "limre ceede", "ewo": "mone", "dua": "môni", "bas": "moni", "bbj": "ŋkap", "byv": "nkap"},
    "somme": {"fr": "somme", "en": "amount", "wes": "moni", "fub": "limre ceede", "ewo": "mone", "dua": "môni", "bas": "moni", "bbj": "ŋkap", "byv": "nkap"},
    "frais": {"fr": "frais", "en": "fees", "wes": "charges", "fub": "njoɓdi", "ewo": "fre", "dua": "njoa", "bas": "nsas", "bbj": "frais", "byv": "frais"},
    "commission": {"fr": "commission", "en": "fee", "wes": "charges", "fub": "njoɓdi", "ewo": "fre", "dua": "njoa", "bas": "nsas", "bbj": "frais", "byv": "frais"},
    "tarif": {"fr": "tarif", "en": "rate", "wes": "charges", "fub": "njoɓdi", "ewo": "fre", "dua": "njoa", "bas": "nsas", "bbj": "frais", "byv": "frais"},
    "cout": {"fr": "coût", "en": "cost", "wes": "charges", "fub": "njoɓdi", "ewo": "fre", "dua": "njoa", "bas": "nsas", "bbj": "frais", "byv": "frais"},
    "prix": {"fr": "prix", "en": "price", "wes": "price", "fub": "coggu", "ewo": "taan", "dua": "mususedi", "bas": "nsañ", "bbj": "ŋkap", "byv": "nkap"},
    "total": {"fr": "total", "en": "total", "wes": "all moni", "fub": "fuu", "ewo": "mese", "dua": "mese", "bas": "mwomede", "bbj": "tsem", "byv": "tsem"},
    "plafond": {"fr": "plafond", "en": "limit", "wes": "limit", "fub": "keeri", "ewo": "plafon", "dua": "ndelo", "bas": "ndék", "bbj": "plafon", "byv": "plafon"},
    "limite": {"fr": "limite", "en": "limit", "wes": "limit", "fub": "keeri", "ewo": "ndelo", "dua": "ndelo", "bas": "ndék", "bbj": "plafon", "byv": "plafon"},
    "banque": {"fr": "banque", "en": "bank", "wes": "bank", "fub": "banki", "ewo": "banki", "dua": "banki", "bas": "banki", "bbj": "banki", "byv": "banki"},
    "compte": {"fr": "compte", "en": "account", "wes": "account", "fub": "konte", "ewo": "kônte", "dua": "konte", "bas": "konte", "bbj": "konte", "byv": "konte"},
    "client": {"fr": "client", "en": "customer", "wes": "customer", "fub": "soodoowo", "ewo": "mod", "dua": "moto", "bas": "mut", "bbj": "moto", "byv": "moto"},
    "beneficiaire": {"fr": "bénéficiaire", "en": "beneficiary", "wes": "pesin weh go receive", "fub": "heɓoowo", "ewo": "mod a kos", "dua": "moto nu ma kusa", "bas": "mut a nkôs", "bbj": "we e nyam", "byv": "wo e nyam"},
    "destinataire": {"fr": "destinataire", "en": "recipient", "wes": "pesin weh go receive", "fub": "heɓoowo", "ewo": "mod a kos", "dua": "moto nu ma kusa", "bas": "mut a nkôs", "bbj": "we e nyam", "byv": "wo e nyam"},
    "nom": {"fr": "nom", "en": "name", "wes": "name", "fub": "innde", "ewo": "dzoe", "dua": "dina", "bas": "jôl", "bbj": "dzo", "byv": "lin"},
    "numero": {"fr": "numéro", "en": "number", "wes": "number", "fub": "limre", "ewo": "nombre", "dua": "numba", "bas": "nombo", "bbj": "nombo", "byv": "nombo"},
    "telephone": {"fr": "téléphone", "en": "phone", "wes": "phone", "fub": "telefon", "ewo": "telefon", "dua": "telefon", "bas": "telefon", "bbj": "telefon", "byv": "telefon"},
    "credit": {"fr": "crédit", "en": "airtime", "wes": "credit", "fub": "kredit", "ewo": "kredit", "dua": "kredit", "bas": "kredit", "bbj": "kredit", "byv": "kredit"},
    "recharge": {"fr": "recharge", "en": "top up", "wes": "credit", "fub": "kredit", "ewo": "kredit", "dua": "kredit", "bas": "kredit", "bbj": "kredit", "byv": "kredit"},
    "facture": {"fr": "facture", "en": "bill", "wes": "bill", "fub": "faktir", "ewo": "faktir", "dua": "faktir", "bas": "faktir", "bbj": "faktir", "byv": "faktir"},
    "eau": {"fr": "eau", "en": "water", "wes": "wata", "fub": "ndiyam", "ewo": "mendim", "dua": "madiba", "bas": "malép", "bbj": "shyə", "byv": "ntsi"},
    "electricite": {"fr": "électricité", "en": "electricity", "wes": "light", "fub": "kuuraŋ", "ewo": "kuran", "dua": "kuran", "bas": "kuran", "bbj": "kuran", "byv": "kuran"},
    "courant": {"fr": "courant", "en": "power", "wes": "light", "fub": "kuuraŋ", "ewo": "kuran", "dua": "kuran", "bas": "kuran", "bbj": "kuran", "byv": "kuran"},
    "television": {"fr": "télévision", "en": "television", "wes": "TV", "fub": "televizion", "ewo": "televizion", "dua": "televizion", "bas": "televizion", "bbj": "televizion", "byv": "televizion"},
    "internet": {"fr": "internet", "en": "internet", "wes": "intanet", "fub": "enternet", "ewo": "enternet", "dua": "intanet", "bas": "enternet", "bbj": "enternet", "byv": "enternet"},
    "reseau": {"fr": "réseau", "en": "network", "wes": "network", "fub": "reso", "ewo": "reso", "dua": "reso", "bas": "reso", "bbj": "reso", "byv": "reso"},
    "operateur": {"fr": "opérateur", "en": "operator", "wes": "network", "fub": "operater", "ewo": "operater", "dua": "operater", "bas": "operater", "bbj": "operater", "byv": "operater"},
    "service": {"fr": "service", "en": "service", "wes": "service", "fub": "sarwis", "ewo": "sarvis", "dua": "sarvis", "bas": "sarvis", "bbj": "sarvis", "byv": "sarvis"},
    "historique": {"fr": "historique", "en": "history", "wes": "history", "fub": "golle ceede", "ewo": "alom ya nde", "dua": "bola la môni", "bas": "biloñ bi moni", "bbj": "bivul bi ŋkap", "byv": "bivul bi nkap"},
    "operation": {"fr": "opération", "en": "transaction", "wes": "transaction", "fub": "golle", "ewo": "alôm", "dua": "bola", "bas": "biloñ", "bbj": "bivul", "byv": "bivul"},
    "transaction": {"fr": "transaction", "en": "transaction", "wes": "transaction", "fub": "golle ceede", "ewo": "alôm mone", "dua": "bola la môni", "bas": "biloñ bi moni", "bbj": "tom ŋkap", "byv": "ntúm nkap"},
    "reference": {"fr": "référence", "en": "reference", "wes": "reference", "fub": "referaans", "ewo": "referans", "dua": "referans", "bas": "referans", "bbj": "referans", "byv": "referans"},
    "recu": {"fr": "reçu", "en": "receipt", "wes": "receipt", "fub": "seedee", "ewo": "kalara", "dua": "kalati", "bas": "kaat", "bbj": "referans", "byv": "referans"},
    "code": {"fr": "code", "en": "code", "wes": "code", "fub": "kod", "ewo": "kod", "dua": "kod", "bas": "kod", "bbj": "kod", "byv": "kod"},
    "erreur": {"fr": "erreur", "en": "error", "wes": "wahala", "fub": "juumre", "ewo": "ékop", "dua": "ndutu", "bas": "hôha", "bbj": "ndutu", "byv": "ndutu"},
    "probleme": {"fr": "problème", "en": "problem", "wes": "wahala", "fub": "caɗeele", "ewo": "ndzúk", "dua": "ndutu", "bas": "ndutu", "bbj": "problem", "byv": "problem"},
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
    "envoyer": {"fr": "envoyer", "en": "send", "wes": "send", "fub": "neldude", "ewo": "lôm", "dua": "lóma", "bas": "lémèl", "bbj": "tom", "byv": "ntúm"},
    "envoie": {"fr": "envoie", "en": "send", "wes": "send", "fub": "nel", "ewo": "lôm", "dua": "lóma", "bas": "lémèl", "bbj": "tom", "byv": "ntúm"},
    "envoye": {"fr": "envoyé", "en": "sent", "wes": "don send", "fub": "neldaama", "ewo": "a lômban", "dua": "e lómabe", "bas": "i nlémél", "bbj": "tom", "byv": "ntúm"},
    "transfert": {"fr": "transfert", "en": "transfer", "wes": "send moni", "fub": "nelde ceede", "ewo": "alôm mone", "dua": "loma la môni", "bas": "lémèl moni", "bbj": "tom ŋkap", "byv": "ntúm nkap"},
    "transferer": {"fr": "transférer", "en": "transfer", "wes": "send", "fub": "neldude", "ewo": "lôm", "dua": "lóma", "bas": "lémèl", "bbj": "tom", "byv": "ntúm"},
    "recevoir": {"fr": "recevoir", "en": "receive", "wes": "receive", "fub": "heɓude", "ewo": "kos", "dua": "kusa", "bas": "kôs", "bbj": "nyam", "byv": "nyam"},
    "retirer": {"fr": "retirer", "en": "withdraw", "wes": "comot moni", "fub": "ittude", "ewo": "nyon", "dua": "busise", "bas": "pémés", "bbj": "tu'", "byv": "tu'"},
    "retrait": {"fr": "retrait", "en": "withdrawal", "wes": "comot moni", "fub": "ittugo ceede", "ewo": "nyonan mone", "dua": "busa môni", "bas": "pémés moni", "bbj": "tu' ŋkap", "byv": "tu' nkap"},
    "payer": {"fr": "payer", "en": "pay", "wes": "pay", "fub": "yoɓude", "ewo": "ya", "dua": "sawa", "bas": "jel", "bbj": "fo", "byv": "fo"},
    "paie": {"fr": "paie", "en": "pay", "wes": "pay", "fub": "yoɓ", "ewo": "ya", "dua": "sawa", "bas": "jel", "bbj": "fo", "byv": "fo"},
    "paye": {"fr": "payé", "en": "paid", "wes": "don pay", "fub": "yoɓaama", "ewo": "a yaban", "dua": "e sawabe", "bas": "i njel", "bbj": "fo bwe", "byv": "fo bwam"},
    "acheter": {"fr": "acheter", "en": "buy", "wes": "buy", "fub": "soodude", "ewo": "kus", "dua": "anda", "bas": "somb", "bbj": "yu", "byv": "yu"},
    "achete": {"fr": "achète", "en": "buy", "wes": "buy", "fub": "sood", "ewo": "kus", "dua": "anda", "bas": "somb", "bbj": "yu", "byv": "yu"},
    "verifier": {"fr": "vérifier", "en": "verify", "wes": "check", "fub": "ƴeewde", "ewo": "yen mbembe", "dua": "kwaléa", "bas": "tol", "bbj": "ye bwe", "byv": "yen bwam"},
    "consulter": {"fr": "consulter", "en": "check", "wes": "check", "fub": "ƴeewde", "ewo": "yen", "dua": "ombwa", "bas": "béñge", "bbj": "ye", "byv": "yen"},
    "voir": {"fr": "voir", "en": "see", "wes": "see", "fub": "yi'ude", "ewo": "yen", "dua": "ombwa", "bas": "tehe", "bbj": "ye", "byv": "yen"},
    "confirmer": {"fr": "confirmer", "en": "confirm", "wes": "confirm", "fub": "tabbitinde", "ewo": "yebe", "dua": "timbisɛ", "bas": "hémle", "bbj": "yôô", "byv": "yebe"},
    "valider": {"fr": "valider", "en": "confirm", "wes": "confirm", "fub": "tabbitinde", "ewo": "yebe", "dua": "timbisɛ", "bas": "hémle", "bbj": "yôô", "byv": "yebe"},
    "annuler": {"fr": "annuler", "en": "cancel", "wes": "cancel", "fub": "haɓɓitde", "ewo": "bili", "dua": "timba", "bas": "bôg", "bbj": "ka'", "byv": "tebe"},
    "modifier": {"fr": "modifier", "en": "edit", "wes": "change am", "fub": "waylude", "ewo": "sûli", "dua": "tukwa", "bas": "henha", "bbj": "shang", "byv": "shang"},
    "changer": {"fr": "changer", "en": "change", "wes": "change am", "fub": "waylude", "ewo": "sûli", "dua": "tukwa", "bas": "henha", "bbj": "shang", "byv": "shang"},
    "corriger": {"fr": "corriger", "en": "correct", "wes": "change am", "fub": "waylude", "ewo": "sûli", "dua": "tukwa", "bas": "henha", "bbj": "shang", "byv": "shang"},
    "choisir": {"fr": "choisir", "en": "choose", "wes": "pick", "fub": "suɓaade", "ewo": "tob", "dua": "posa", "bas": "pohol", "bbj": "tso", "byv": "tso"},
    "ecouter": {"fr": "écouter", "en": "listen", "wes": "listen", "fub": "heɗaade", "ewo": "vogolo", "dua": "senga", "bas": "emble", "bbj": "yu'", "byv": "yu'"},
    "parler": {"fr": "parler", "en": "speak", "wes": "talk", "fub": "haalude", "ewo": "kobo", "dua": "bwala", "bas": "pot", "bbj": "ghɔm", "byv": "cɔ"},
    "continuer": {"fr": "continuer", "en": "continue", "wes": "continue", "fub": "jokkude", "ewo": "kele osu", "dua": "ala oboso", "bas": "ke bisu", "bbj": "gɔ̌ ntum", "byv": "nə ntum"},
    "retour": {"fr": "retour", "en": "back", "wes": "go back", "fub": "rutto", "ewo": "bulan", "dua": "timba", "bas": "témb", "bbj": "le'", "byv": "kə'"},
    "terminer": {"fr": "terminer", "en": "finish", "wes": "finish", "fub": "timminde", "ewo": "mana", "dua": "bɔlɛ", "bas": "mal", "bbj": "mɛ", "byv": "mɛ"},
    "securite": {"fr": "sécurité", "en": "security", "wes": "security", "fub": "kisal", "ewo": "mvoé", "dua": "bwam", "bas": "lam", "bbj": "bwe", "byv": "bwam"},
    "insuffisant": {"fr": "insuffisant", "en": "insufficient", "wes": "no reach", "fub": "yonaa", "ewo": "ne ki tegé", "dua": "si koki", "bas": "nkola-be", "bbj": "ka kwet", "byv": "ka kwet"},
    "disponible": {"fr": "disponible", "en": "available", "wes": "weh remain", "fub": "keddiiɗe", "ewo": "a lig ma", "dua": "ma dia", "bas": "u nkon", "bbj": "ya tse", "byv": "ya tse"},
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
    "je": {"fr": "je", "en": "I", "wes": "A", "fub": "mi", "ewo": "ma", "dua": "na", "bas": "me", "bbj": "mə", "byv": "mə"},
    "veux": {"fr": "veux", "en": "want", "wes": "wan", "fub": "yiɗi", "ewo": "yi", "dua": "pula", "bas": "nyéñ", "bbj": "kôŋ", "byv": "kô"},
    "a": {"fr": "à", "en": "to", "wes": "give", "fub": "e", "ewo": "a", "dua": "na", "bas": "í", "bbj": "a", "byv": "a"},
    "à": {"fr": "à", "en": "to", "wes": "give", "fub": "e", "ewo": "a", "dua": "na", "bas": "í", "bbj": "a", "byv": "a"},
    "au": {"fr": "au", "en": "at", "wes": "fo", "fub": "e", "ewo": "a", "dua": "o", "bas": "i", "bbj": "a", "byv": "a"},
    "vers": {"fr": "vers", "en": "to", "wes": "give", "fub": "e", "ewo": "a", "dua": "na", "bas": "i", "bbj": "a", "byv": "a"},
    "pour": {"fr": "pour", "en": "for", "wes": "fo", "fub": "ngam", "ewo": "asu", "dua": "onyola", "bas": "inyu", "bbj": "mba", "byv": "num"},
    "et": {"fr": "et", "en": "and", "wes": "an", "fub": "e", "ewo": "a", "dua": "na", "bas": "ni", "bbj": "na", "byv": "na"},
    "mon": {"fr": "mon", "en": "my", "wes": "ma", "fub": "maa", "ewo": "wom", "dua": "mongo", "bas": "won", "bbj": "po", "byv": "bu"},
    "ma": {"fr": "ma", "en": "my", "wes": "ma", "fub": "am", "ewo": "wom", "dua": "am", "bas": "wem", "bbj": "yà", "byv": "zà"},
    "ton": {"fr": "ton", "en": "your", "wes": "yu", "fub": "maa", "ewo": "wôé", "dua": "ango", "bas": "yon", "bbj": "po", "byv": "bu"},
    "sa": {"fr": "sa", "en": "his", "wes": "yi", "fub": "makko", "ewo": "dzé", "dua": "mao", "bas": "wé", "bbj": "yé", "byv": "zé"},
    "votre": {"fr": "votre", "en": "your", "wes": "yu", "fub": "maa", "ewo": "wôé", "dua": "ango", "bas": "yon", "bbj": "po", "byv": "bu"},
    "frere": {"fr": "frère", "en": "brother", "wes": "broda", "fub": "deerɗiraawo", "ewo": "manyaṅ", "dua": "muna nyango", "bas": "mankéé", "bbj": "sò'", "byv": "mènzwə"},
    "beaucoup": {"fr": "beaucoup", "en": "very much", "wes": "plenty", "fub": "sanu", "ewo": "abui", "dua": "jita", "bas": "ngandag", "bbj": "bwe", "byv": "bwam"},
}
_DROP_ARTICLES = {"le", "la", "les", "l", "un", "une", "des", "du", "de", "d", "est", "sont", "quel", "quels", "quelle", "quelles"}


def translate_phrase(text: str, target_lang: str) -> dict[str, Any]:
    """Traduit une phrase entière (syntaxe naturelle) ou mot-à-mot en protégeant montants, numéros et références."""
    lang = normalize_language(target_lang) or "fr"
    clean = text.strip()
    low = clean.lower()

    # 1. Correspondance directe sur un mot ou terme exact du glossaire
    key_exact = _EN_TO_GLOSSARY_KEY.get(low, low.replace("é", "e").replace("è", "e"))
    if key_exact in WORD_GLOSSARY:
        return {"mode": "exact_word", "translated": WORD_GLOSSARY[key_exact].get(lang, clean)}

    # 2. Protection stricte des valeurs bancaires sensibles :
    # - Emplacements {amount}, {name}, {phone}...
    # - Références TRX-XXXX / SAF-XXXX
    # - Numéros de téléphone camerounais (+237 / 6XXXXXXXX)
    # - Montants avec devise (5 000 FCFA / XAF)
    # - Tout nombre ou chiffre isolé (ex: 5000, 15 000, 237...)
    # - Noms de services / facturiers / opérateurs (ENEO, CAMWATER, CANAL, CAMTEL, MTN, ORANGE, Safinum)
    # - Noms propres des clients (mots capitalisés après Bonjour/Hello/Mbolo/Sannu ou à/pour/de/vers/give/na/e)
    protected: list[str] = []

    def _stash(match: re.Match) -> str:
        idx = len(protected)
        protected.append(match.group(0))
        return f"__PROT_{idx}__"

    def _stash_after_prep(match: re.Match) -> str:
        prep = match.group(1)
        name_part = match.group(2)
        if name_part.lower() in WORD_GLOSSARY or name_part.lower() in _EN_TO_GLOSSARY_KEY or name_part.lower() in _CONNECTORS or name_part.lower() in _DROP_ARTICLES:
            return match.group(0)
        idx = len(protected)
        protected.append(name_part)
        return f"{prep}__PROT_{idx}__"

    masked = re.sub(
        r"\{[a-z_]+\}|"
        r"(?:TRX|SAF)-[A-Z0-9\-]+|"
        r"(?:\+?237[\s\-\.]?)?6[\s\-\.]?\d{2}[\s\-\.]?\d{2}[\s\-\.]?\d{2}[\s\-\.]?\d{2}|"
        r"\b\d[\d\s\.,]*\s*(?:FCFA|XAF|CFA)\b|"
        r"\b(?:FCFA|XAF|CFA)\b|"
        r"\b\d+(?:[\s\.,]\d+)*\b|"
        r"\b(?:ENEO|CAMWATER|CANAL\+?|CAMTEL|MTN|ORANGE|Safinum(?:\s+Pay)?)\b",
        _stash,
        clean,
        flags=re.IGNORECASE,
    )
    # Protéger les noms propres de clients après prépositions ou salutations (ex: "à Jean Mbarga", "Bonjour Amina")
    masked = re.sub(
        r"(\b(?:[àa]|pour|de|vers|chez|give|to|from|[Bb]onjour|[Hh]ello|[Mm]bolo|[Ss]annu)\s+)([A-ZÀ-Ÿ][a-zà-ÿ'\-]+(?:\s+[A-ZÀ-Ÿ][a-zà-ÿ'\-]+)*)",
        _stash_after_prep,
        masked,
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
            "ewo": "Mòni wom a lig ma a ne tân ya?",
            "dua": "Môni mongo ma dia me nena?",
            "bas": "Moni won u nkon u yene nwaa?",
            "bbj": "Ŋkap po ya tse ba sa?",
            "byv": "Nkap bu ya tse ne sa?",
        }.get(lang)
    elif re.search(r"\b(solde insuffisant|pas assez d'argent|insufficient balance)\b", m_low):
        natural_out = get_error_text(lang, "INSUFFICIENT_FUNDS")
    elif re.search(r"\b(merci beaucoup|thank you very much)\b", m_low):
        natural_out = {
            "fr": "Merci beaucoup.",
            "en": "Thank you very much.",
            "wes": "Thank yu plenty.",
            "fub": "Useko sanu.",
            "ewo": "Ma və́ wa akíba abui.",
            "dua": "Na som jita.",
            "bas": "Matue ngandag.",
            "bbj": "Ndèmá bwe.",
            "byv": "Mə̀ làbtə̌ bwam.",
        }.get(lang)

    if natural_out:
        for idx, val in enumerate(protected):
            natural_out = natural_out.replace(f"__PROT_{idx}__", val)
        return {"mode": "natural_sentence", "translated": natural_out, "words_translated": len(natural_out.split())}

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
                            return {"mode": "soreva_corpus", "translated": soreva_tr, "words_translated": len(soreva_tr.split())}
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
            src_guess = detect_language(clean, fallback="fr")
            nmt_out, nmt_eng = translate_neural_local(nmt_in, src_guess, lang)
            if nmt_out:
                valid_restored = True
                for idx, val in enumerate(protected):
                    if f"88010{idx}" not in nmt_out:
                        valid_restored = False
                        break
                    nmt_out = nmt_out.replace(f"88010{idx}", val)
                if valid_restored:
                    return {"mode": f"neural_{nmt_eng}", "translated": nmt_out, "words_translated": len(nmt_out.split())}
        except Exception:
            pass

    for idx, val in enumerate(protected):
        result = result.replace(f"__PROT_{idx}__", val)

    return {"mode": "word_by_word" if replaced > 0 else "passthrough", "translated": result, "words_translated": replaced}
