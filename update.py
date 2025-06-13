import sqlite3
import os
from dotenv import load_dotenv
from telegram import (
    Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler, CallbackQueryHandler
)
from menu import *
from user import utilisateur_existe
from etats import*
load_dotenv()

HASH_TRANSACTION_DEPOT_SUPPLEMENTAIRE = "hash_transaction_depot_supplementaire"
ADMIN_ID = int(os.getenv("ADMIN_ID"))  # Must be an int
WALLET_KEY = os.getenv("WALLET_KEY") # wallet de l'entreprise must be int

def mettre_a_jour_solde(user_id: int, montant_ajoute: float):
    """Update the deposit amount of a user by adding a new amount."""
    try:
        conn = sqlite3.connect("bot.db")
        cursor = conn.cursor()

        cursor.execute("SELECT montant_depot FROM utilisateurs WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()

        if row:
            montant_actuel = row[0]
            montant_total = montant_actuel + montant_ajoute

            cursor.execute(
                "UPDATE utilisateurs SET montant_depot = ? WHERE user_id = ?",
                (montant_total, user_id)
            )
            conn.commit()
    except Exception as e:
        print(f"[Error] mettre_a_jour_solde: {e}")
    finally:
        conn.close()


async def depot_supplementaire(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the process for an additional deposit."""
    user_id = update.effective_user.id

    if not utilisateur_existe(user_id):
        await update.message.reply_text(
            "❌ You must first register using /start to make your first deposit.",
            reply_markup=get_menu_markup(user_id)
        )
        return ConversationHandler.END

    await update.message.reply_text("💰 How much more would you like to deposit? (in USDT):")
    return MONTANT_DEPOT_SUPPLEMENTAIRE


async def recevoir_montant_depot_supplementaire(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the entered amount for additional deposit."""
    montant = update.message.text.strip()
    user = update.effective_user
    user_id = user.id

    try:
        montant_float = float(montant)
        if montant_float <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid and positive amount (numbers only).")
        return MONTANT_DEPOT_SUPPLEMENTAIRE

    context.user_data["montant_depot_supplementaire"] = montant_float

    msg_user = (
        f"Thank you. To make an additional deposit of {montant_float:.2f} USDT, here is the information:\n"
        "📥 Wallet address of the platform in next message: \n"
        "🌐 Blockchain network: Binance Smart Chain (BSC)\n\n"
        "Once the transfer is completed, the admin will confirm your deposit."
    )
    msg_us=(f"{WALLET_KEY}")

    await update.message.reply_text(msg_user, reply_markup=get_menu_markup(user_id), parse_mode="Markdown")
    await update.message.reply_text(msg_us, reply_markup=get_menu_markup(user_id), parse_mode="Markdown")

    # Demander le hash de transaction
    msg_hash = "Veuillez maintenant entrer le hash de votre transaction pour confirmer le dépôt supplémentaire :"
    await update.message.reply_text(msg_hash)
    
    return HASH_TRANSACTION_DEPOT_SUPPLEMENTAIRE


async def recevoir_hash_depot_supplementaire(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the transaction hash for additional deposit."""
    hash_transaction = update.message.text.strip()
    user = update.effective_user
    user_id = user.id
    montant_float = context.user_data.get("montant_depot_supplementaire")
    
    # Stocker le hash dans user_data
    context.user_data["hash_transaction_supplementaire"] = hash_transaction

    btn_confirmer = InlineKeyboardButton(
        "✅ Confirm deposit",
        callback_data=f"confirmer_supp_{user_id}_{montant_float}"
    )
    btn_annuler = InlineKeyboardButton("❌ Cancel", callback_data="annuler")
    buttons = InlineKeyboardMarkup([[btn_confirmer, btn_annuler]])

    msg_admin = (
        f"📥 [ADDITIONAL DEPOSIT INITIATED]\n"
        f"👤 User: @{user.username or user.first_name}\n"
        f"🆔 Telegram ID: {user_id}\n"
        f"💵 Declared additional amount: {montant_float:.2f} USDT\n"
        f"🔗 Transaction Hash:\n"
        f"ℹ️ User already registered"
    )
    msg_adm=(f"{hash_transaction}")
    await context.bot.send_message(chat_id=ADMIN_ID, text=msg_admin, reply_markup=buttons)
    await context.bot.send_message(chat_id=ADMIN_ID, text=msg_adm, reply_markup=buttons)
    
    # Confirmer à l'utilisateur que sa demande a été soumise
    await update.message.reply_text(
        "✅ Votre demande de dépôt supplémentaire avec le hash de transaction a été soumise à l'administrateur pour vérification.",
        reply_markup=get_menu_markup(user_id)
    )
    
    return ConversationHandler.END


async def confirmer_depot_supplementaire(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("confirmer_supp_"):
        try:
            parts = data.split("_", 3)
            _, _, user_id_str, montant_str = parts
            user_id = int(user_id_str)
            montant = float(montant_str)
        except Exception:
            await query.edit_message_text("❌ Invalid confirmation data.")
            return

        mettre_a_jour_solde(user_id, montant)

        await query.edit_message_text(
            f"✅ Additional deposit of {montant:.2f} USDT confirmed for user {user_id}."
        )

        # Optional: notify the user
        # await context.bot.send_message(chat_id=user_id, text=f"✅ Your deposit of {montant:.2f} USDT has been successfully added.")
    
    elif data == "annuler":
        await query.edit_message_text("❌ Additional deposit cancelled by the admin.")