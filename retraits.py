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
RETRAIT_EN_ATTENTE = {}

async def retrait(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    set_user_locale(update)
    user = update.effective_user
    if utilisateur_bloque(user.id):
        await update.message.reply_text(
            i18n.t("user.log_error_user_bloque")
        )
        return

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

    msg = i18n.t("retraits.enter_wallet_address")
    if update.message:
        await update.message.reply_text(msg)
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(msg)
    else:
        return ConversationHandler.END

    return ADRESSE_PORTEFEUILLE


async def recevoir_adresse(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
    return RESEAU_BLOCKCHAIN

async def recevoir_reseau(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
    enregistrer_retrait(user.id, user.username or user.first_name, address, network, montant)

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
            # InlineKeyboardButton(i18n.t("retraits.btn_not"), callback_data=f"retrait_not_{user.id}")
        ]
    ])
    await context.bot.send_message(chat_id=ADMIN_ID, text=msg_admin, reply_markup=keyboard)
    await context.bot.send_message(chat_id=ADMIN_ID, text=msg_add)
    await query.edit_message_text(i18n.t("retraits.withdrawal_request_recorded"))
    return ConversationHandler.END

def enregistrer_retrait(user_id: int, username: str, adresse: str, reseau: str, montant: float):
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

async def recevoir_hash_retrait(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    set_user_locale(update)
    if not update.message or not update.message.text:
        await update.effective_chat.send_message(i18n.t("retraits.invalid_hash"))
        return SAISIE_HASH_RETRAIT

    hash_tx = update.message.text.strip()

    if not is_valid_tx_hash(hash_tx):
        await update.message.reply_text(i18n.t("retraits.invalid_hash_format"))
        return SAISIE_HASH_RETRAIT

    admin_id = update.effective_user.id
    user_id = RETRAIT_EN_ATTENTE.get(admin_id)

    if not user_id:
        await update.message.reply_text(i18n.t("retraits.user_not_found"))
        return ConversationHandler.END

    # Récupérer le montant depuis la table retraits (dernière demande de cet utilisateur)
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
        
        # Mettre benefice_total à 0
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
    
async def retrait_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    set_user_locale(update)
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = int(data.split("_")[-1])
    RETRAIT_EN_ATTENTE[update.effective_user.id] = user_id

   

    await query.message.reply_text(i18n.t("retraits.enter_transaction_hash"))
    return SAISIE_HASH_RETRAIT

async def retrait_not(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    set_user_locale(update)
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(i18n.t("retraits.btn_not"))

def is_valid_tx_hash(hash_tx: str) -> bool:
    return re.fullmatch(r"0x[a-fA-F0-9]{64}", hash_tx) is not None