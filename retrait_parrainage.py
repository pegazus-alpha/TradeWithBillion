import sqlite3
import re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import os
from dotenv import load_dotenv
from etats import *
from lang import*
import i18n
load_dotenv()


ADMIN_ID = int(os.getenv("ADMIN_ID"))
RETRAIT_EN_ATTENTE2 = {}

SEUIL_MINIMUM_RETRAIT = 10  # en USDT
async def retrait_parrainage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    set_user_locale(update)

    user = update.effective_user
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT commissions_totales FROM utilisateurs WHERE user_id = ?", (user.id,))
        row = cursor.fetchone()
        if not row:
            await update.message.reply_text("❌ Vous n'êtes pas encore enregistré sur le système.")
            return ConversationHandler.END

        solde = row[0]
        if solde < SEUIL_MINIMUM_RETRAIT:
            await update.message.reply_text(
                f"{i18n.t('notif.texte')}.\n"
                f"{i18n.t('notif.solde')} {solde:.2f} USDT"
            )
            return ConversationHandler.END

        context.user_data["montant_parrainage"] = solde
        await update.message.reply_text("📝 Veuillez entrer votre adresse de wallet pour recevoir vos gains de parrainage :")
        return ADRESSE_PARRAINAGE

    except Exception as e:
        await update.message.reply_text("❌ Erreur lors de la récupération de vos données.")
        print(f"[ERREUR retrait_parrainage] {e}")
        return ConversationHandler.END

    finally:
        conn.close()

async def recevoir_adresse_parrainage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    adresse = update.message.text.strip()
    context.user_data["adresse_parrainage"] = adresse

    networks = ["BSC", "Ethereum", "Solana", "Polygon", "Tron"]
    buttons = [[InlineKeyboardButton(text=n, callback_data=n)] for n in networks]
    reply_markup = InlineKeyboardMarkup(buttons)

    await update.message.reply_text("🌐 Sélectionnez le réseau blockchain :", reply_markup=reply_markup)
    return RESEAU_PARRAINAGE


async def recevoir_reseau_parrainage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    reseau = query.data
    adresse = context.user_data["adresse_parrainage"]
    user = update.effective_user
    montant = context.user_data["montant_parrainage"]

    if not is_valid_wallet_parrainage(adresse, reseau):
        await query.edit_message_text("❌ Le format de l'adresse est invalide pour ce réseau.")
        return ConversationHandler.END

    enregistrer_retrait_parrainage(user.id, user.username or user.first_name, adresse, reseau, montant)

    await query.edit_message_text(
        f"{i18n.t('notif.demande')} {montant:.2f}"
        f"{i18n.t('notif.address')} `{adresse}`\n"
        f"{i18n.t('notif.reseau')} {reseau}",
        parse_mode="Markdown"
    )
    
    # ✅ Notification à l’ADMIN
    # msg_admin = (
    #     f"📥 *Demande de retrait de parrainage reçue*\n\n"
    #     f"👤 Utilisateur : @{user.username or user.first_name}\n"
    #     f"🆔 ID Telegram : `{user.id}`\n"
    #     f"💰 Montant : {montant:.2f} USDT\n"
    #     f"🔗 Réseau : {reseau}\n"
    #     f"🪪 Adresse : "
    # )
    msg_admin = (
        f"{i18n.t('retraits.admin_withdrawal_header2')}\n"
        f"{i18n.t('retraits.admin_username').format(username=user.username or user.first_name)}\n"
        f"{i18n.t('retraits.admin_telegram_id').format(user_id=user.id)}\n"
        f"{i18n.t('retraits.admin_available_amount').format(available_amount=montant)}\n"
        f"{i18n.t('retraits.admin_wallet_address')} \n"
        f"{i18n.t('retraits.admin_blockchain_network').format(network=reseau)}"
    )
    msg_ad=f"{adresse}"
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(i18n.t("retraits.btn_done"), callback_data=f"retrait_done2_{user.id}"),
            # InlineKeyboardButton(i18n.t("retraits.btn_not"), callback_data=f"retrait_not_{user.id}")
        ]
    ])
    await context.bot.send_message(chat_id=ADMIN_ID, text=msg_admin,reply_markup=keyboard )
    await context.bot.send_message(chat_id=ADMIN_ID, text=msg_ad)
    await query.edit_message_text(i18n.t("retraits.withdrawal_request_recorded"))

    return ConversationHandler.END

def enregistrer_retrait_parrainage(user_id: int, username: str, adresse: str, reseau: str, montant: float):
    try:
        conn = sqlite3.connect("bot.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO retraits (user_id, username, adresse, reseau, montant, date_retrait)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, username, adresse, reseau, montant, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
    except Exception as e:
        print(f"[ERREUR] enregistrer_retrait_parrainage : {e}")
    finally:
        conn.close()


def is_valid_wallet_parrainage(address: str, network: str) -> bool:
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

    if not is_valid_tx_hash2(hash_tx):
        await update.message.reply_text(i18n.t("retraits.invalid_hash_format"))
        return SAISIE_HASH_RETRAIT2

    admin_id = update.effective_user.id
    user_id = RETRAIT_EN_ATTENTE2.get(admin_id)

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
            cursor.execute("UPDATE utilisateurs SET commissions_totales = 0 WHERE user_id = ?", (user_id,))
            conn.commit()
        except Exception as e:
            print(f"Error updating benefice_total: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
        
        RETRAIT_EN_ATTENTE2.pop(admin_id, None)
    except Exception as e:
        await update.message.reply_text(i18n.t("retraits.failed_notify_user").format(error=e))

    return ConversationHandler.END
async def retrait_done2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    set_user_locale(update)
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = int(data.split("_")[-1])
    RETRAIT_EN_ATTENTE2[update.effective_user.id] = user_id

   

    await query.message.reply_text(i18n.t("retraits.enter_transaction_hash"))
    return SAISIE_HASH_RETRAIT2

def is_valid_tx_hash2(hash_tx: str) -> bool:
    return re.fullmatch(r"0x[a-fA-F0-9]{64}", hash_tx) is not None