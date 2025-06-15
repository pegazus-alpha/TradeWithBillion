import sqlite3
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes
import i18n
from lang import*  # Assure-toi d’avoir ce fichier
from etats import *

load_dotenv()
ADMIN_ID = int(os.getenv("ADMIN_ID"))

def get_user_lang(update: Update) -> str:
    return update.effective_user.language_code or "en"

async def liste_utilisateurs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_user_lang(update)

    if user_id != ADMIN_ID:
        await update.message.reply_text(i18n.t("admin.access_denied", locale=lang))
        return

    try:
        conn = sqlite3.connect("bot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, langue, montant_depot, date_enregistrement, date_mise_a_jour, benefice_total FROM utilisateurs")
        rows = cursor.fetchall()

        if not rows:
            await update.message.reply_text(i18n.t("admin.no_users_found", locale=lang))
            return

        message = i18n.t("admin.users_list_header", locale=lang) + "\n"
        for row in rows:
            message += (
                f"\n{i18n.t('admin.user_id_label', locale=lang)}: {row[0]}\n"
                f"{i18n.t('admin.language_label', locale=lang)}: {row[1]}\n"
                f"{i18n.t('admin.amount_deposited_label', locale=lang)}: {row[2]}\n"
                f"{i18n.t('admin.registration_date_label', locale=lang)}: {row[3]}\n"
                f"{i18n.t('admin.total_profit_label', locale=lang)}: {row[5]}\n"
                f"{i18n.t('admin.last_update_label', locale=lang)}: {row[4]}\n"
                f"{i18n.t('admin.separator', locale=lang)}"
            )

        await update.message.reply_text(message)

    except Exception as e:
        await update.message.reply_text(i18n.t("admin.error_retrieving_users", locale=lang, error=str(e)))
    finally:
        conn.close()

async def info_utilisateur(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_user_lang(update)

    if user_id != ADMIN_ID:
        await update.message.reply_text(i18n.t("admin.access_denied", locale=lang))
        return

    if not context.args:
        await update.message.reply_text(i18n.t("admin.provide_user_id", locale=lang), parse_mode="Markdown")
        return

    cible_id = context.args[0]

    try:
        conn = sqlite3.connect("bot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM utilisateurs WHERE user_id = ?", (cible_id,))
        row = cursor.fetchone()

        if not row:
            await update.message.reply_text(i18n.t("admin.user_not_found", locale=lang))
            return

        message = (
            f"{i18n.t('admin.user_info_header', locale=lang, user_id=cible_id)}\n"
            f"{i18n.t('admin.language_label', locale=lang)}: {row[1]}\n"
            f"{i18n.t('admin.amount_deposited_label', locale=lang)}: {row[2]}\n"
            f"{i18n.t('admin.total_profit_label', locale=lang)}: {row[3]}\n"
            f"{i18n.t('admin.registration_date_label', locale=lang)}: {row[4]}\n"
            f"{i18n.t('admin.wallet_address_label', locale=lang)}: {row[5]}\n"
            f"{i18n.t('admin.last_update_label', locale=lang)}: {row[6]}"
        )
        await update.message.reply_text(message)

    except Exception as e:
        await update.message.reply_text(i18n.t("admin.error_occurred", locale=lang, error=str(e)))
    finally:
        conn.close()

# async def set_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     user_id = update.effective_user.id
#     lang = get_user_lang(update)

#     if user_id != ADMIN_ID:
#         await update.message.reply_text(i18n.t("admin.access_denied", locale=lang))
#         return

#     if len(context.args) < 2:
#         await update.message.reply_text(i18n.t("admin.set_description_usage", locale=lang))
#         return

#     wallet_id = context.args[0]
#     nouvelle_description = " ".join(context.args[1:])

#     try:
#         conn = sqlite3.connect("bot.db")
#         cursor = conn.cursor()
#         cursor.execute("UPDATE wallets_boite SET remarques = ? WHERE id = ?", (nouvelle_description, wallet_id))
#         conn.commit()
#         await update.message.reply_text(i18n.t("admin.description_updated", locale=lang))
#     except Exception as e:
#         await update.message.reply_text(i18n.t("admin.error_occurred", locale=lang, error=str(e)))
#     finally:
#         conn.close()
