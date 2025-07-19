import sqlite3
import os
import re

from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import (
    Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler, CallbackQueryHandler
)
from menu import *
from user import utilisateur_existe, utilisateur_bloque
from etats import*
import i18n
from lang import *
load_dotenv()


HASH_TRANSACTION_DEPOT_SUPPLEMENTAIRE = "hash_transaction_depot_supplementaire"
ADMIN_ID = int(os.getenv("ADMIN_ID"))  # Must be an int
WALLET_KEY = os.getenv("WALLET_KEY")  # Must be a string (wallet address)

def get_user_registration_date(user_id: int):
    conn = None
    try:
        conn = sqlite3.connect("bot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT date_enregistrement FROM utilisateurs WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            return datetime.fromisoformat(row[0])
        return None
    except Exception as e:
        print(i18n.t("update.error_get_registration_date").format(error=str(e)))
        return None
    finally:
        if conn:
            conn.close()

def can_update_balance(user_id: int):
    registration_date = get_user_registration_date(user_id)
    if not registration_date:
        return False, i18n.t("update.registration_date_not_found")

    # Vérifier si le montant_depot est à 0
    try:
        conn = sqlite3.connect("bot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT montant_depot FROM utilisateurs WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row is None or float(row[0]) == 0:
            return False, i18n.t("update.deposit_required")  # Assure-toi que cette clé existe dans ton fichier de langue
    except Exception as e:
        print(f"[ERREUR] Impossible de récupérer le montant_depot : {e}")
        return False, i18n.t("update.error_checking_deposit")
    finally:
        conn.close()

    # current_date = datetime.now()
    # days_since_registration = (current_date - registration_date).days

    # if days_since_registration >= 14:
    #     days_until_cycle_end = 60 - days_since_registration
    #     if days_until_cycle_end <= 0:
    #         days_until_cycle_end = 60
    #     return False, i18n.t("update.balance_update_not_profitable").format(days=days_until_cycle_end)

    # days_to_next_update = 7 - (days_since_registration % 7)
    # if days_since_registration % 7 != 0:
    #     return False, i18n.t("update.balance_update_wait").format(days=days_to_next_update)

    return True, i18n.t("update.balance_update_allowed")


def mettre_a_jour_solde(user_id: int, montant_ajoute: float):
    conn = None
    try:
        db_path = os.path.abspath("bot.db")
        print(i18n.t("update.log_database_path").format(path=db_path))
        print(i18n.t("update.log_updating_user").format(user_id=user_id, amount=montant_ajoute))

        conn = sqlite3.connect("bot.db")
        cursor = conn.cursor()

        cursor.execute("SELECT montant_depot FROM utilisateurs WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()

        if row:
            montant_actuel = row[0] if row[0] is not None else 0.0
            montant_total = montant_actuel + montant_ajoute
            print(i18n.t("update.log_sql_update").format(total=montant_total, user_id=user_id))

            cursor.execute(
                "UPDATE utilisateurs SET montant_depot = ? WHERE user_id = ?",
                (montant_total, user_id)
            )
            conn.commit()
            print(i18n.t("update.log_balance_success").format(user_id=user_id, current=montant_actuel, added=montant_ajoute, total=montant_total))
            return True
        else:
            print(i18n.t("update.log_user_not_found").format(user_id=user_id))
            return False
    except Exception as e:
        print(i18n.t("update.error_update_balance").format(error=str(e)))
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

async def depot_supplementaire(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    set_user_locale(update)
    user_id = update.effective_user.id
    if not utilisateur_existe(user_id):
        await update.message.reply_text(
            i18n.t("update.must_register_first"),
            reply_markup=get_menu_markup(user_id)
        )
        return ConversationHandler.END
    if utilisateur_bloque(user_id):
        await update.message.reply_text(
            i18n.t("user.log_error_user_bloque"),
            reply_markup=get_menu_markup(user_id)
        )
        return
    can_update, message = can_update_balance(user_id)
    if not can_update:
        await update.message.reply_text(
            f"❌ {message}",
            reply_markup=get_menu_markup(user_id)
        )
        return ConversationHandler.END
    await update.message.reply_text(i18n.t("update.additional_deposit_amount"))
    return MONTANT_DEPOT_SUPPLEMENTAIRE

async def recevoir_montant_depot_supplementaire(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    set_user_locale(update)
    montant = update.message.text.strip()
    user = update.effective_user
    user_id = user.id
    try:
        montant_float = float(montant)
        if montant_float <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(i18n.t("update.invalid_amount_error"))
        return MONTANT_DEPOT_SUPPLEMENTAIRE
    context.user_data["montant_depot_supplementaire"] = montant_float
    msg_user = i18n.t("update.additional_deposit_info").format(amount=montant_float)
    msg_us = f"{WALLET_KEY}"
    await update.message.reply_text(msg_user, reply_markup=get_menu_markup(user_id), parse_mode="Markdown")
    await update.message.reply_text(msg_us, reply_markup=get_menu_markup(user_id), parse_mode="Markdown")
    msg_hash = i18n.t("update.hash_request_message")
    await update.message.reply_text(msg_hash)
    return HASH_TRANSACTION_DEPOT_SUPPLEMENTAIRE

async def recevoir_hash_depot_supplementaire(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    set_user_locale(update)
    hash_transaction = update.message.text.strip()
    user = update.effective_user
    user_id = user.id
    montant_float = context.user_data.get("montant_depot_supplementaire")
    if not montant_float:
        await update.message.reply_text(i18n.t("update.amount_error_restart"))
        return ConversationHandler.END
    context.user_data["hash_transaction_supplementaire"] = hash_transaction
    btn_confirmer = InlineKeyboardButton(
        i18n.t("update.confirm_deposit_button"),
        callback_data=f"{i18n.t('update.pattern_confirm_supp')}{user_id}_{montant_float}"
    )
    btn_annuler = InlineKeyboardButton(i18n.t('update.cancel_button_supp'), callback_data= f"{i18n.t('update.pattern_cancel_supp')}{user_id}_")
    buttons = InlineKeyboardMarkup([[btn_confirmer, btn_annuler]])
    msg_admin = (
        f"{i18n.t('update.admin_additional_deposit_title')}\n"
        f"{i18n.t('update.admin_user_info').format(username=user.username or user.first_name)}\n"
        f"{i18n.t('update.admin_telegram_id').format(user_id=user_id)}\n"
        f"{i18n.t('update.admin_declared_amount').format(amount=montant_float)}\n"
        f"{i18n.t('update.admin_transaction_hash')}\n"
        f"{i18n.t('update.admin_user_registered')}"
    )
    msg_a = f"{hash_transaction}"
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg_admin, reply_markup=buttons)
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg_a)
        print(i18n.t("update.log_admin_notification_success").format(user_id=user_id))
    except Exception as e:
        print(i18n.t("update.log_admin_notification_failed").format(error=str(e)))
        await update.message.reply_text(i18n.t("update.processing_error"))
        return ConversationHandler.END
    await update.message.reply_text(
        i18n.t("update.processing_request"),
        reply_markup=get_menu_markup(user_id)
    )
    return ConversationHandler.END

async def confirmer_depot_supplementaire(update: Update, context: ContextTypes.DEFAULT_TYPE):
    set_user_locale(update)
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith(i18n.t("update.pattern_confirm_supp")):
        try:
            parts = data.split("_")
            print(i18n.t("update.log_callback_data").format(data=data))
            print(i18n.t("update.log_parsed_parts").format(parts=parts))
            if len(parts) < 4:
                raise ValueError("Invalid callback data format")
            user_id = int(parts[2])
            montant = float(parts[3])
            print(i18n.t("update.log_confirming_deposit").format(user_id=user_id, amount=montant))
        except (ValueError, IndexError) as e:
            print(i18n.t("update.log_invalid_confirmation").format(error=str(e)))
            await query.edit_message_text(i18n.t("update.invalid_confirmation_data"))
            return
        success = mettre_a_jour_solde(user_id, montant)
        if success:
            await query.edit_message_text(
                i18n.t("update.additional_deposit_confirmed").format(amount=montant, user_id=user_id)
            )
            try:
                await context.bot.send_message(
                    chat_id=user_id, 
                    text=i18n.t("update.additional_deposit_confirmed_user").format(amount=montant),
                    reply_markup=get_menu_markup(user_id)
                )
                print(i18n.t("update.log_user_notified").format(user_id=user_id))
            except Exception as e:
                print(i18n.t("update.log_user_notification_failed").format(user_id=user_id, error=str(e)))
        else:
            await query.edit_message_text(
                i18n.t("update.balance_update_failed").format(user_id=user_id)
            )
    elif data.startswith(i18n.t("update.pattern_cancel_supp")):
        await query.edit_message_text(i18n.t("update.additional_deposit_cancelled"))
        print(i18n.t("update.log_deposit_cancelled"))

        # Extraire user_id depuis le callback_data (ex: "annuler_supp_123456_")
        try:
            parts = data.split("_")
            if len(parts) >= 3:
                user_id = int(parts[2])
                await context.bot.send_message(
                    chat_id=user_id,
                    text=i18n.t("update.additional_deposit_cancelled"),
                    reply_markup=get_menu_markup(user_id)
                )
                print(i18n.t("update.log_user_notified").format(user_id=user_id))
            else:
                print("[Erreur] Données callback mal formées :", data)
        except Exception as e:
            print(i18n.t("update.log_user_notification_failed").format(user_id="inconnu", error=str(e)))

def test_balance_update(user_id: int, amount: float):
    print(i18n.t("update.log_testing_balance").format(user_id=user_id, amount=amount))
    if not utilisateur_existe(user_id):
        print(i18n.t("update.log_user_does_not_exist").format(user_id=user_id))
        return False
    success = mettre_a_jour_solde(user_id, amount)
    if success:
        print(i18n.t("update.log_test_success"))
    else:
        print(i18n.t("update.log_test_failed"))
    return success