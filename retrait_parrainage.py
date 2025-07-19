# import sqlite3
# import re
# from datetime import datetime
# from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
# from telegram.ext import ContextTypes, ConversationHandler
# import os
# from dotenv import load_dotenv
# from etats import *
# from lang import*
# import i18n

# from user import utilisateur_bloque
# load_dotenv()


# ADMIN_ID = int(os.getenv("ADMIN_ID"))
# RETRAIT_EN_ATTENTE2 = {}

# SEUIL_MINIMUM_RETRAIT = 10  # en USDT
# async def retrait_parrainage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     set_user_locale(update)

#     user = update.effective_user
#     conn = sqlite3.connect("bot.db")
#     cursor = conn.cursor()
#     if utilisateur_bloque(user.id):
#         await update.message.reply_text(
#             i18n.t("user.log_error_user_bloque")
#         )
#         return
#     try:
#         cursor.execute("SELECT commissions_totales FROM utilisateurs WHERE user_id = ?", (user.id,))
#         row = cursor.fetchone()
#         if not row:
#             await update.message.reply_text("❌ Vous n'êtes pas encore enregistré sur le système.")
#             return ConversationHandler.END

#         solde = row[0]
#         if solde < SEUIL_MINIMUM_RETRAIT:
#             await update.message.reply_text(
#                 f"{i18n.t('notif.texte')}.\n"
#                 f"{i18n.t('notif.solde')} {solde:.2f} USDT"
#             )
#             return ConversationHandler.END

#         context.user_data["montant_parrainage"] = solde
#         await update.message.reply_text("📝 Veuillez entrer votre adresse de wallet pour recevoir vos gains de parrainage :")
#         return ADRESSE_PARRAINAGE

#     except Exception as e:
#         await update.message.reply_text("❌ Erreur lors de la récupération de vos données.")
#         print(f"[ERREUR retrait_parrainage] {e}")
#         return ConversationHandler.END

#     finally:
#         conn.close()

# async def recevoir_adresse_parrainage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     adresse = update.message.text.strip()
#     context.user_data["adresse_parrainage"] = adresse

#     networks = ["BSC", "Ethereum", "Solana", "Polygon", "Tron"]
#     buttons = [[InlineKeyboardButton(text=n, callback_data=n)] for n in networks]
#     reply_markup = InlineKeyboardMarkup(buttons)

#     await update.message.reply_text("🌐 Sélectionnez le réseau blockchain :", reply_markup=reply_markup)
#     return RESEAU_PARRAINAGE


# async def recevoir_reseau_parrainage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     query = update.callback_query
#     await query.answer()

#     reseau = query.data
#     adresse = context.user_data["adresse_parrainage"]
#     user = update.effective_user
#     montant = context.user_data["montant_parrainage"]

#     if not is_valid_wallet_parrainage(adresse, reseau):
#         await query.edit_message_text("❌ Le format de l'adresse est invalide pour ce réseau.")
#         return ConversationHandler.END

#     enregistrer_retrait_parrainage(user.id, user.username or user.first_name, adresse, reseau, montant)

#     await query.edit_message_text(
#         f"{i18n.t('notif.demande')} {montant:.2f}"
#         f"{i18n.t('notif.address')} `{adresse}`\n"
#         f"{i18n.t('notif.reseau')} {reseau}",
#         parse_mode="Markdown"
#     )
    
#     # ✅ Notification à l’ADMIN
#     # msg_admin = (
#     #     f"📥 *Demande de retrait de parrainage reçue*\n\n"
#     #     f"👤 Utilisateur : @{user.username or user.first_name}\n"
#     #     f"🆔 ID Telegram : `{user.id}`\n"
#     #     f"💰 Montant : {montant:.2f} USDT\n"
#     #     f"🔗 Réseau : {reseau}\n"
#     #     f"🪪 Adresse : "
#     # )
#     msg_admin = (
#         f"{i18n.t('retraits.admin_withdrawal_header2')}\n"
#         f"{i18n.t('retraits.admin_username').format(username=user.username or user.first_name)}\n"
#         f"{i18n.t('retraits.admin_telegram_id').format(user_id=user.id)}\n"
#         f"{i18n.t('retraits.admin_available_amount').format(available_amount=montant)}\n"
#         f"{i18n.t('retraits.admin_wallet_address')} \n"
#         f"{i18n.t('retraits.admin_blockchain_network').format(network=reseau)}"
#     )
#     msg_ad=f"{adresse}"
#     keyboard = InlineKeyboardMarkup([
#         [
#             InlineKeyboardButton(i18n.t("retraits.btn_done"), callback_data=f"retrait_done2_{user.id}"),
#             # InlineKeyboardButton(i18n.t("retraits.btn_not"), callback_data=f"retrait_not_{user.id}")
#         ]
#     ])
#     await context.bot.send_message(chat_id=ADMIN_ID, text=msg_admin,reply_markup=keyboard )
#     await context.bot.send_message(chat_id=ADMIN_ID, text=msg_ad)
#     await query.edit_message_text(i18n.t("retraits.withdrawal_request_recorded"))

#     return ConversationHandler.END

# def enregistrer_retrait_parrainage(user_id: int, username: str, adresse: str, reseau: str, montant: float):
#     try:
#         conn = sqlite3.connect("bot.db")
#         cursor = conn.cursor()
#         cursor.execute("""
#             INSERT INTO retraits (user_id, username, adresse, reseau, montant, date_retrait)
#             VALUES (?, ?, ?, ?, ?, ?)
#         """, (user_id, username, adresse, reseau, montant, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
#         conn.commit()
#     except Exception as e:
#         print(f"[ERREUR] enregistrer_retrait_parrainage : {e}")
#     finally:
#         conn.close()


# def is_valid_wallet_parrainage(address: str, network: str) -> bool:
#     network = network.lower()
#     if network in ("bsc", "ethereum", "polygon"):
#         return re.fullmatch(r"0x[a-fA-F0-9]{40}", address) is not None
#     elif network == "solana":
#         return re.fullmatch(r"[1-9A-HJ-NP-Za-km-z]{32,44}", address) is not None
#     elif network == "tron":
#         return re.fullmatch(r"T[a-zA-Z0-9]{33}", address) is not None
#     else:
#         return True

# async def recevoir_hash_retrait2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     set_user_locale(update)
#     if not update.message or not update.message.text:
#         await update.effective_chat.send_message(i18n.t("retraits.invalid_hash"))
#         return SAISIE_HASH_RETRAIT2

#     hash_tx = update.message.text.strip()

#     if not is_valid_tx_hash2(hash_tx):
#         await update.message.reply_text(i18n.t("retraits.invalid_hash_format"))
#         return SAISIE_HASH_RETRAIT2

#     admin_id = update.effective_user.id
#     user_id = RETRAIT_EN_ATTENTE2.get(admin_id)

#     if not user_id:
#         await update.message.reply_text(i18n.t("retraits.user_not_found"))
#         return ConversationHandler.END

#     # Récupérer le montant depuis la table retraits (dernière demande de cet utilisateur)
#     montant = 0
#     try:
#         conn = sqlite3.connect("bot.db")
#         cursor = conn.cursor()
#         cursor.execute("""
#             SELECT montant FROM retraits 
#             WHERE user_id = ? 
#             ORDER BY date_retrait DESC 
#             LIMIT 1
#         """, (user_id,))
#         row = cursor.fetchone()
#         if row:
#             montant = row[0]
#     except Exception as e:
#         print(f"Error getting withdrawal amount: {e}")
#     finally:
#         if 'conn' in locals():
#             conn.close()

#     try:
#         await context.bot.send_message(
#             chat_id=user_id,
#             text=f"{i18n.t('retraits.withdrawal_processed').format(montant=montant)}",
#             parse_mode="Markdown"
#         )
#         await context.bot.send_message(
#             chat_id=user_id,
#             text=f"\n`{hash_tx}`\n\n",
#             parse_mode="Markdown"
#         )
#         await update.message.reply_text(i18n.t("retraits.user_notified"))
        
#         # Mettre benefice_total à 0
#         try:
#             conn = sqlite3.connect("bot.db")
#             cursor = conn.cursor()
#             cursor.execute("UPDATE utilisateurs SET commissions_totales = 0 WHERE user_id = ?", (user_id,))
#             conn.commit()
#         except Exception as e:
#             print(f"Error updating benefice_total: {e}")
#         finally:
#             if 'conn' in locals():
#                 conn.close()
        
#         RETRAIT_EN_ATTENTE2.pop(admin_id, None)
#     except Exception as e:
#         await update.message.reply_text(i18n.t("retraits.failed_notify_user").format(error=e))

#     return ConversationHandler.END
# async def retrait_done2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     set_user_locale(update)
#     query = update.callback_query
#     await query.answer()

#     data = query.data
#     user_id = int(data.split("_")[-1])
#     RETRAIT_EN_ATTENTE2[update.effective_user.id] = user_id

   

#     await query.message.reply_text(i18n.t("retraits.enter_transaction_hash"))
#     return SAISIE_HASH_RETRAIT2

# def is_valid_tx_hash2(hash_tx: str) -> bool:
#     return re.fullmatch(r"0x[a-fA-F0-9]{64}", hash_tx) is not None
import os
import sqlite3
import re
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from user import *
import menu
from etats import *
from lang import*
import i18n
load_dotenv()

ADMIN_ID = int(os.getenv("ADMIN_ID"))
# RETRAIT_EN_ATTENTE = {}

# Nouveaux états pour le processus de retrait
# MODE_PAIEMENT, CHOIX_PAYS, CHOIX_OPERATEUR, NUMERO_MOBILE, NOM_UTILISATEUR = range(5, 10)

# Données des pays et opérateurs
PAYS_OPERATEURS = {
    "Cameroun": ["MTN Mobile Money", "Orange Money", "YooMee"],
    "Sénégal": ["Orange Money", "Free Money", "Wave"],
    "Côte d'Ivoire": ["MTN Mobile Money", "Orange Money", "Moov Money"],
    "Burkina Faso": ["Orange Money", "Moov Money"],
    "Mali": ["Orange Money", "Malitel Money"],
    "Niger": ["Airtel Money", "Orange Money"],
    "Tchad": ["Airtel Money", "Tigo Cash"],
    "Centrafrique": ["Orange Money", "Telecel Money"],
    "Gabon": ["Airtel Money", "Moov Money"],
    "Congo Brazzaville": ["Airtel Money", "MTN Mobile Money"],
    "RDC": ["Airtel Money", "Orange Money", "Vodacom M-Pesa"],
    "Guinée": ["Orange Money", "MTN Mobile Money"],
    "Bénin": ["MTN Mobile Money", "Moov Money"],
    "Togo": ["Flooz", "T-Money"],
    "Ghana": ["MTN Mobile Money", "AirtelTigo Money", "Vodafone Cash"],
    "Nigeria": ["Opay", "PalmPay", "Kuda"]
}

async def retrait_parrainage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    set_user_locale(update)
    user = update.effective_user
    if utilisateur_bloque(user.id):
        await update.message.reply_text(
            i18n.t("user.log_error_user_bloque")
        )
        return ConversationHandler.END

    try:
        conn = sqlite3.connect("bot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT benefice_total FROM utilisateurs WHERE user_id = ?", (user.id,))
        row = cursor.fetchone()
        if not row:
            await update.message.reply_text(i18n.t("retraits.user_not_registered"))
            return ConversationHandler.END
        benefice_total = row[0]
        if benefice_total <= 0:
            await update.message.reply_text(i18n.t("retraits.no_benefits"))
            return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(i18n.t("retraits.database_error").format(error=str(e)))
        return ConversationHandler.END
    finally:
        conn.close()

    # Demander le mode de paiement
    buttons = [
        [InlineKeyboardButton("💰 USDT (Crypto)", callback_data="mode_usdt")],
        [InlineKeyboardButton("📱 Paiement Local (Mobile Money)", callback_data="mode_local")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    
    msg = "Choisissez votre mode de paiement :"
    if update.message:
        await update.message.reply_text(msg, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(msg, reply_markup=reply_markup)
    else:
        return ConversationHandler.END

    return MODE_PAIEMENT2

async def recevoir_mode_paiement_parrainage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    set_user_locale(update)
    query = update.callback_query
    await query.answer()
    
    mode = query.data
    context.user_data["mode_paiement"] = mode
    
    if mode == "mode_usdt":
        # Procédure USDT existante
        msg = i18n.t("retraits.enter_wallet_address")
        await query.edit_message_text(msg)
        return ADRESSE_PARRAINAGE
    
    elif mode == "mode_local":
        # Nouvelle procédure pour paiement local
        pays_list = list(PAYS_OPERATEURS.keys())
        buttons = [[InlineKeyboardButton(pays, callback_data=f"pays_{pays}")] for pays in pays_list]
        reply_markup = InlineKeyboardMarkup(buttons)
        
        await query.edit_message_text("🌍 Choisissez votre pays :", reply_markup=reply_markup)
        return CHOIX_PAYS2
    
    return ConversationHandler.END

async def recevoir_pays_parrainage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    set_user_locale(update)
    query = update.callback_query
    await query.answer()
    
    pays = query.data.replace("pays_", "")
    context.user_data["pays"] = pays
    
    # Afficher les opérateurs du pays choisi
    operateurs = PAYS_OPERATEURS.get(pays, [])
    if not operateurs:
        await query.edit_message_text("❌ Aucun opérateur disponible pour ce pays.")
        return ConversationHandler.END
    
    buttons = [[InlineKeyboardButton(op, callback_data=f"op_{op}")] for op in operateurs]
    reply_markup = InlineKeyboardMarkup(buttons)
    
    await query.edit_message_text(f"📱 Choisissez votre opérateur mobile ({pays}) :", reply_markup=reply_markup)
    return CHOIX_OPERATEUR2

async def recevoir_operateur_parrainage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    set_user_locale(update)
    query = update.callback_query
    await query.answer()
    
    operateur = query.data.replace("op_", "")
    context.user_data["operateur"] = operateur
    
    await query.edit_message_text(f"📞 Veuillez entrer votre numéro de téléphone associé à {operateur} :")
    return NUMERO_MOBILE2

async def recevoir_numero_mobile_parrainage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    set_user_locale(update)
    if not update.message or not update.message.text:
        await update.effective_chat.send_message("❌ Veuillez entrer un numéro valide.")
        return NUMERO_MOBILE2

    numero = update.message.text.strip()
    context.user_data["numero_mobile"] = numero
    
    await update.message.reply_text("👤 Veuillez entrer votre nom complet :")
    return NOM_UTILISATEUR2

async def recevoir_nom_utilisateur_parrainage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    set_user_locale(update)
    if not update.message or not update.message.text:
        await update.effective_chat.send_message("❌ Veuillez entrer votre nom.")
        return NOM_UTILISATEUR2

    nom = update.message.text.strip()
    context.user_data["nom_utilisateur"] = nom
    
    user = update.effective_user
    infos = get_infos_utilisateur(user.id)
    montant = infos['benefice_total']
    
    # Enregistrer le retrait local
    enregistrer_retrait_local2(user.id, user.username or user.first_name, 
                            context.user_data["pays"], context.user_data["operateur"],
                            context.user_data["numero_mobile"], context.user_data["nom_utilisateur"], montant)
    
    await update.message.reply_text(
        "✅ Votre demande de retrait par paiement local a été enregistrée.\n"
        "Vous recevrez une confirmation dès que le paiement sera effectué.",
        reply_markup=menu.get_menu_markup(user.id)
    )
    
    # Notification à l'admin pour paiement local
    msg_admin = (
        f"🏦 NOUVELLE DEMANDE DE RETRAIT LOCAL\n"
        f"👤 Utilisateur: {user.username or user.first_name}\n"
        f"🆔 Telegram ID: {user.id}\n"
        f"🆔 UDI: {infos['udi']}\n"
        f"💳 Dépôt Binance: {infos['binance_depot']}\n"
        f"💰 Solde: {infos['solde']}\n"
        f"💸 Montant disponible: {infos['benefice_total']}\n"
        f"🌍 Pays: {context.user_data['pays']}\n"
        f"📱 Opérateur: {context.user_data['operateur']}\n"
        f"📞 Numéro: {context.user_data['numero_mobile']}\n"
        f"👤 Nom: {context.user_data['nom_utilisateur']}"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Paiement Effectué", callback_data=f"retrait_local_done_{user.id}")]
    ])
    
    await context.bot.send_message(chat_id=ADMIN_ID, text=msg_admin, reply_markup=keyboard)
    
    return ConversationHandler.END

async def recevoir_adresse_parrainage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    set_user_locale(update)
    if not update.message or not update.message.text:
        await update.effective_chat.send_message(i18n.t("retraits.invalid_input"))
        return ConversationHandler.END

    adresse = update.message.text.strip()
    context.user_data["adresse_paiement"] = adresse

    networks = ["BSC", "Ethereum", "Solana", "Polygon", "Tron"]
    buttons = [[InlineKeyboardButton(text=n, callback_data=n)] for n in networks]
    reply_markup = InlineKeyboardMarkup(buttons)

    await update.message.reply_text(i18n.t("retraits.select_blockchain_network"), reply_markup=reply_markup)
    return RESEAU_PARRAINAGE

async def recevoir_reseau_parrainage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    set_user_locale(update)
    query = update.callback_query
    await query.answer()

    network = query.data
    address = context.user_data.get("adresse_paiement")
    user = update.effective_user
    infos = get_infos_utilisateur(user.id)

    if not is_valid_wallet(address, network):
        await query.edit_message_text(i18n.t("retraits.invalid_wallet_format"))
        return ConversationHandler.END

    montant = infos['benefice_total']
    enregistrer_retrait2(user.id, user.username or user.first_name, address, network, montant)

    await context.bot.send_message(
        chat_id=user.id,
        text=i18n.t("retraits.withdrawal_request_received"),
        reply_markup=menu.get_menu_markup(user.id)
    )

    msg_admin = (
        f"{i18n.t('retraits.admin_withdrawal_header')}\n"
        f"{i18n.t('retraits.admin_username').format(username=user.username or user.first_name)}\n"
        f"{i18n.t('retraits.admin_telegram_id').format(user_id=user.id)}\n"
        f"{i18n.t('retraits.admin_udi').format(udi=infos['udi'])}\n"
        f"{i18n.t('retraits.admin_binance_deposit').format(binance_depot=infos['binance_depot'])}\n"
        f"{i18n.t('retraits.admin_balance').format(balance=infos['solde'])}\n"
        f"{i18n.t('retraits.admin_available_amount').format(available_amount=infos['benefice_total'])}\n"
        f"{i18n.t('retraits.admin_wallet_address')} \n"
        f"{i18n.t('retraits.admin_blockchain_network').format(network=network)}"
    )
    msg_add=(f"{address}\n")
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(i18n.t("retraits.btn_done"), callback_data=f"retrait_done_{user.id}"),
        ]
    ])
    await context.bot.send_message(chat_id=ADMIN_ID, text=msg_admin, reply_markup=keyboard)
    await context.bot.send_message(chat_id=ADMIN_ID, text=msg_add)
    await query.edit_message_text(i18n.t("retraits.withdrawal_request_recorded"))
    return ConversationHandler.END

def enregistrer_retrait2(user_id: int, username: str, adresse: str, reseau: str, montant: float):
    try:
        from datetime import datetime
        date_retrait = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect("bot.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO retraits (user_id, username, adresse, reseau, montant, date_retrait)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, username, adresse, reseau, montant, date_retrait))
        conn.commit()
    except Exception as e:
        print(f"[Error] enregistrer_retrait: {e}")
    finally:
        conn.close()

def enregistrer_retrait_local2(user_id: int, username: str, pays: str, operateur: str, numero: str, nom: str, montant: float):
    try:
        from datetime import datetime
        date_retrait = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect("bot.db")
        cursor = conn.cursor()
        
        # Créer la table si elle n'existe pas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS retraits_locaux (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                pays TEXT,
                operateur TEXT,
                numero TEXT,
                nom TEXT,
                montant REAL,
                date_retrait TEXT,
                statut TEXT DEFAULT 'en_attente'
            )
        """)
        
        cursor.execute("""
            INSERT INTO retraits_locaux (user_id, username, pays, operateur, numero, nom, montant, date_retrait)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, username, pays, operateur, numero, nom, montant, date_retrait))
        conn.commit()
    except Exception as e:
        print(f"[Error] enregistrer_retrait_local: {e}")
    finally:
        conn.close()

def is_valid_wallet(address: str, network: str) -> bool:
    network = network.lower()
    if network in ("bsc", "ethereum", "polygon"):
        return re.fullmatch(r"0x[a-fA-F0-9]{40}", address) is not None
    elif network == "solana":
        return re.fullmatch(r"[1-9A-HJ-NP-Za-km-z]{32,44}", address) is not None
    elif network == "tron":
        return re.fullmatch(r"T[a-zA-Z0-9]{33}", address) is not None
    else:
        return True

async def recevoir_hash_retrait2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    set_user_locale(update)
    if not update.message or not update.message.text:
        await update.effective_chat.send_message(i18n.t("retraits.invalid_hash"))
        return SAISIE_HASH_RETRAIT2

    hash_tx = update.message.text.strip()

    if not is_valid_tx_hash(hash_tx):
        await update.message.reply_text(i18n.t("retraits.invalid_hash_format"))
        return SAISIE_HASH_RETRAIT2

    admin_id = update.effective_user.id
    user_id = RETRAIT_EN_ATTENTE.get(admin_id)

    if not user_id:
        await update.message.reply_text(i18n.t("retraits.user_not_found"))
        return ConversationHandler.END

    montant = 0
    try:
        conn = sqlite3.connect("bot.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT montant FROM retraits 
            WHERE user_id = ? 
            ORDER BY date_retrait DESC 
            LIMIT 1
        """, (user_id,))
        row = cursor.fetchone()
        if row:
            montant = row[0]
    except Exception as e:
        print(f"Error getting withdrawal amount: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"{i18n.t('retraits.withdrawal_processed').format(montant=montant)}",
            parse_mode="Markdown"
        )
        await context.bot.send_message(
            chat_id=user_id,
            text=f"\n`{hash_tx}`\n\n",
            parse_mode="Markdown"
        )
        await update.message.reply_text(i18n.t("retraits.user_notified"))
        
        try:
            conn = sqlite3.connect("bot.db")
            cursor = conn.cursor()
            cursor.execute("UPDATE utilisateurs SET benefice_total = 0 WHERE user_id = ?", (user_id,))
            conn.commit()
        except Exception as e:
            print(f"Error updating benefice_total: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
        
        RETRAIT_EN_ATTENTE.pop(admin_id, None)
    except Exception as e:
        await update.message.reply_text(i18n.t("retraits.failed_notify_user").format(error=e))

    return ConversationHandler.END

async def recevoir_image_paiement_local2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    set_user_locale(update)
    if not update.message or not update.message.photo:
        await update.effective_chat.send_message("❌ Veuillez envoyer une image de confirmation du paiement.")
        return SAISIE_IMAGE_PAIEMENT_LOCAL

    admin_id = update.effective_user.id
    user_id = RETRAIT_EN_ATTENTE.get(admin_id)

    if not user_id:
        await update.message.reply_text("❌ Utilisateur non trouvé.")
        return ConversationHandler.END

    # Récupérer le montant depuis la table retraits_locaux
    montant = 0
    try:
        conn = sqlite3.connect("bot.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT montant FROM retraits_locaux 
            WHERE user_id = ? 
            ORDER BY date_retrait DESC 
            LIMIT 1
        """, (user_id,))
        row = cursor.fetchone()
        if row:
            montant = row[0]
    except Exception as e:
        print(f"Error getting local withdrawal amount: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

    try:
        # Envoyer l'image de confirmation à l'utilisateur
        photo = update.message.photo[-1]  # Prendre la meilleure qualité
        await context.bot.send_photo(
            chat_id=user_id,
            photo=photo.file_id,
            caption=f"✅ Votre retrait de {montant} a été traité avec succès.\nVoici la preuve de paiement :"
        )
        
        await update.message.reply_text("✅ L'utilisateur a été notifié avec la preuve de paiement.")
        
        # Mettre benefice_total à 0
        try:
            conn = sqlite3.connect("bot.db")
            cursor = conn.cursor()
            cursor.execute("UPDATE utilisateurs SET benefice_total = 0 WHERE user_id = ?", (user_id,))
            cursor.execute("UPDATE retraits_locaux SET statut = 'traité' WHERE user_id = ? AND statut = 'en_attente'", (user_id,))
            conn.commit()
        except Exception as e:
            print(f"Error updating benefice_total and status: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
        
        RETRAIT_EN_ATTENTE.pop(admin_id, None)
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur lors de la notification de l'utilisateur: {e}")

    return ConversationHandler.END
    
async def retrait_done2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    set_user_locale(update)
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = int(data.split("_")[-1])
    RETRAIT_EN_ATTENTE[update.effective_user.id] = user_id

    await query.message.reply_text(i18n.t("retraits.enter_transaction_hash"))
    return SAISIE_HASH_RETRAIT2

async def retrait_local_done2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    set_user_locale(update)
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = int(data.split("_")[-1])
    RETRAIT_EN_ATTENTE[update.effective_user.id] = user_id

    await query.message.reply_text("📷 Veuillez envoyer une image de confirmation du paiement mobile money :")
    return SAISIE_IMAGE_PAIEMENT_LOCAL

async def retrait_not2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    set_user_locale(update)
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(i18n.t("retraits.btn_not"))

def is_valid_tx_hash(hash_tx: str) -> bool:
    return re.fullmatch(r"0x[a-fA-F0-9]{64}", hash_tx) is not None or re.fullmatch(r"[A-Za-z0-9]{8,12}", hash_tx) is not None
