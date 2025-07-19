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
import i18n
from lang import*
from etats import *
from user import utilisateur_bloque

load_dotenv()
ADMIN_ID = int(os.getenv("ADMIN_ID"))
WALLET_KEY = os.getenv("WALLET_KEY")
HASH_TRANSACTION_DEPOT = "hash_transaction_depot"

# def get_user_lang(update: Update) -> str:
#     return update.effective_user.langue or "en"

def enregistrer_depot(user_id: int, username: str, adresse: str,  montant: float):
    try:
        from datetime import datetime
        date_depot = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect("bot.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO depot (user_id, username, adresse,montant, date_depot)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, username, adresse,montant, date_depot))
        conn.commit()
    except Exception as e:
        print(f"[Error] enregistrer_depot: {e}")
    finally:
        conn.close()
def check_user_exists(user_id):
    try:
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM utilisateurs WHERE user_id = ?", (user_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    except sqlite3.Error:
        return False

def check_user_deposit_status(user_id):
    """
    Vérifie si l'utilisateur peut faire un dépôt.
    Retourne True si l'utilisateur n'existe pas OU s'il existe mais avec montant_depot = 0
    """
    try:
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT montant_depot FROM utilisateurs WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        # Si l'utilisateur n'existe pas, il peut faire un dépôt
        if result is None:
            return True
        
        # Si l'utilisateur existe, vérifier si montant_depot = 0
        montant_depot = result[0]
        return montant_depot == 0 or montant_depot is None
        
    except sqlite3.Error:
        return False

async def depot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    lang = get_user_lang(update)
    if utilisateur_bloque(user.id):
        await update.message.reply_text(
            i18n.t("user.log", locale=lang)
        )
        return ConversationHandler.END
    
    # Vérifier si l'utilisateur peut faire un dépôt
    if not check_user_deposit_status(user.id):
        await update.message.reply_text(
            i18n.t("depot.investment_exists", locale=lang),
            reply_markup=menu.get_menu_markup(user.id)
        )
        return ConversationHandler.END

    await update.message.reply_text(
        i18n.t("depot.enter_deposit_amount", locale=lang)
    )
    return MONTANT_DEPOT

async def recevoir_montant_depot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    montant_text = update.message.text
    user = update.effective_user
    lang = get_user_lang(update)

    try:
        montant = float(montant_text)
        if montant <= 0:
            await update.message.reply_text(
                i18n.t("depot.invalid_positive_amount", locale=lang),
                reply_markup=menu.get_menu_markup(user.id)
            )
            return MONTANT_DEPOT
    except ValueError:
        await update.message.reply_text(
            i18n.t("depot.invalid_numeric_amount", locale=lang),
            reply_markup=menu.get_menu_markup(user.id)
        )
        return MONTANT_DEPOT

    context.user_data["montant_depot"] = montant_text

    msg_user = i18n.t("depot.deposit_amount_confirm", locale=lang, amount=montant_text)
    await update.message.reply_text(msg_user, reply_markup=menu.get_menu_markup(user.id))
    await update.message.reply_text(f"{WALLET_KEY}")

    await update.message.reply_text(i18n.t("depot.enter_transaction_hash", locale=lang))
    return HASH_TRANSACTION_DEPOT

async def recevoir_hash_depot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    hash_transaction = update.message.text.strip()
    user = update.effective_user
    lang = set_user_locale(update)
    montant = context.user_data.get("montant_depot")
    context.user_data["hash_transaction"] = hash_transaction

    buttons = InlineKeyboardMarkup([[
        InlineKeyboardButton(i18n.t("depot.btn_confirm", locale=lang), callback_data=f"confirmer_{user.id}_{montant}"),
        InlineKeyboardButton(i18n.t("depot.btn_cancel", locale=lang), callback_data=f"annuler_{user.id}")
    ]])

    msg_admin = i18n.t("depot.admin_deposit_notification",locale=lang).format(username=user.username or user.first_name, user_id=user.id, amount=montant)
    await context.bot.send_message(chat_id=ADMIN_ID, text=msg_admin, reply_markup=buttons)
    await context.bot.send_message(chat_id=ADMIN_ID, text=f" {hash_transaction}")

    await update.message.reply_text(
        i18n.t("depot.deposit_request_processing", locale=lang),
        reply_markup=menu.get_menu_markup(user.id)
    )
    return ConversationHandler.END