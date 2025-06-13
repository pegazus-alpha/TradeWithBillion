import os
import sqlite3
import re
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
from user import get_infos_utilisateur
import menu
from etats import*
load_dotenv()

ADMIN_ID = int(os.getenv("ADMIN_ID"))

# En haut de ton fichier ou dans un module global
RETRAIT_EN_ATTENTE = {}

async def retrait(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    msg = "Please enter your wallet address for the withdrawal:"
    if update.message:
        await update.message.reply_text(msg)
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(msg)
    else:
        return ConversationHandler.END
    return ADRESSE_PORTEFEUILLE

async def recevoir_adresse(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message or not update.message.text:
        await update.effective_chat.send_message("❌ Invalid input. Please try again.")
        return ConversationHandler.END

    adresse = update.message.text.strip()
    context.user_data["adresse_paiement"] = adresse

    networks = ["BSC", "Ethereum", "Solana", "Polygon", "Tron"]
    buttons = [[InlineKeyboardButton(text=n, callback_data=n)] for n in networks]
    reply_markup = InlineKeyboardMarkup(buttons)

    await update.message.reply_text("Please select the blockchain network:", reply_markup=reply_markup)
    return RESEAU_BLOCKCHAIN

async def recevoir_reseau(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    network = query.data
    address = context.user_data.get("adresse_paiement")
    user = update.effective_user
    infos = get_infos_utilisateur(user.id)

    if not is_valid_wallet(address, network):
        await query.edit_message_text("❌ The wallet address format does not match the selected blockchain network.")
        return ConversationHandler.END

    enregistrer_retrait(user.id, user.username or user.first_name, address, network)

    await context.bot.send_message(
        chat_id=user.id,
        text="✅ Your withdrawal request has been received. Please wait a moment.",
        reply_markup=menu.get_menu_markup(user.id)
    )

    msg_admin = (
        f"📤 [WITHDRAWAL]\n"
        f"👤 Username: @{user.username or user.first_name}\n"
        f"🆔 Telegram ID: {user.id}\n"
        f"🔢 UDI: {infos['udi']}\n"
        f"💸 Binance Deposit Address: {infos['binance_depot']}\n"
        f"💰 Balance: {infos['solde']}\n"
        f"🔍 Wallet Address: {address}\n"
        f"🌐 Blockchain Network: {network}"
    )
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Done", callback_data=f"retrait_done_{user.id}"),
            InlineKeyboardButton("❌ Not", callback_data=f"retrait_not_{user.id}")
        ]
    ])
    await context.bot.send_message(chat_id=ADMIN_ID, text=msg_admin, reply_markup=keyboard)
    await query.edit_message_text("✅ Your withdrawal request has been recorded.")
    return ConversationHandler.END

def enregistrer_retrait(user_id: int, username: str, adresse: str, reseau: str):
    try:
        conn = sqlite3.connect("bot.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO retraits (user_id, username, adresse, reseau)
            VALUES (?, ?, ?, ?)
        """, (user_id, username, adresse, reseau))
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
    if not update.message or not update.message.text:
        await update.effective_chat.send_message("❌ Hash invalide. Veuillez réessayer.")
        return SAISIE_HASH_RETRAIT
    
    hash_tx = update.message.text.strip()

    if not is_valid_tx_hash(hash_tx):
        await update.message.reply_text("❌ Format de hash invalide. Le hash doit commencer par '0x' et contenir 64 caractères hexadécimaux.")
        return SAISIE_HASH_RETRAIT
    admin_id = update.effective_user.id

    user_id = RETRAIT_EN_ATTENTE.get(admin_id)

    if not user_id:
        await update.message.reply_text("⚠️ Error: user not found.")
        return ConversationHandler.END

    etherscan_url = f"https://etherscan.io/tx/{hash_tx}"

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"✅ Your withdrawal has been successfully processed.\n\n🔗 Transaction hash:",
            parse_mode="Markdown"
        )
        await context.bot.send_message(
            chat_id=user_id,
            text=f"\n`{hash_tx}`\n\n",
            parse_mode="Markdown"
        )
        await update.message.reply_text("✅ The user has been notified with the transaction hash.")

        # Libère l'entrée une fois utilisée
        RETRAIT_EN_ATTENTE.pop(admin_id, None)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Failed to notify user: {e}")

    return ConversationHandler.END

async def retrait_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = int(data.split("_")[-1])
    RETRAIT_EN_ATTENTE[update.effective_user.id] = user_id

    await query.message.reply_text("✅ Please enter the transaction hash to confirm the withdrawal:")
    return SAISIE_HASH_RETRAIT

async def retrait_not(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("❌ Withdrawal was not confirmed.")


def is_valid_tx_hash(hash_tx: str) -> bool:
    return re.fullmatch(r"0x[a-fA-F0-9]{64}", hash_tx) is not None