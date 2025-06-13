import os
from dotenv import load_dotenv
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ContextTypes, ConversationHandler
)
import menu
import sqlite3
from etats import *
load_dotenv()

ADMIN_ID = int(os.getenv("ADMIN_ID"))  # ADMIN_ID must be int
WALLET_KEY = os.getenv("WALLET_KEY")  # wallet de l'entreprise must be int
HASH_TRANSACTION_DEPOT = "hash_transaction_depot"

async def depot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    msg = "Please enter the USDT amount you want to deposit :"
    await update.message.reply_text(msg)
    return MONTANT_DEPOT


async def recevoir_montant_depot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    montant = update.message.text
    user = update.effective_user
    context.user_data["montant_depot"] = montant

    # User message explaining deposit instructions
    msg_user = (
        f"You want to deposit {montant} USDT.\n\n"
        "Please send the amount to the following wallet address:\n"
        "\n"
        "Use the Binance Smart Chain (BEP20) blockchain network."
    )
    msg_u=(f"{WALLET_KEY}")

    await update.message.reply_text(
        msg_user,
        reply_markup=menu.get_menu_markup(user.id)
    )
    await update.message.reply_text(
        msg_u
    )

    # Demander le hash de transaction
    msg_hash = "Veuillez maintenant entrer le hash de votre transaction pour confirmer le dépôt :"
    await update.message.reply_text(msg_hash)
    
    return HASH_TRANSACTION_DEPOT


async def recevoir_hash_depot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    hash_transaction = update.message.text.strip()
    user = update.effective_user
    montant = context.user_data.get("montant_depot")
    
    # Stocker le hash dans user_data
    context.user_data["hash_transaction"] = hash_transaction

    btn_confirmer = "✅ Confirm"
    btn_annuler = "❌ Cancel"

    # Admin notification message avec le hash
    msg_admin = (
        "New deposit request:\n"
        f"User: {user.username or user.first_name}\n"
        f"User ID: {user.id}\n"
        f"Amount: {montant} USDT\n"
        f"Transaction Hash:\n"
        
    )
    msg_a=(f" {hash_transaction}")

    buttons = InlineKeyboardMarkup([[
        InlineKeyboardButton(btn_confirmer, callback_data=f"confirmer_{user.id}_{montant}"),
        InlineKeyboardButton(btn_annuler, callback_data="annuler")
    ]])

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=msg_admin,
        reply_markup=buttons
    )
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=msg_a
    )
    
    # Confirmer à l'utilisateur que sa demande a été soumise
    await update.message.reply_text(
        "✅ Votre demande de dépôt avec le hash de transaction a été soumise à l'administrateur pour vérification.",
        reply_markup=menu.get_menu_markup(user.id)
    )
    
    return ConversationHandler.END