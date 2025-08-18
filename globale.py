

import sqlite3
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes
import i18n
from lang import*  # Assure-toi d’avoir ce fichier
import menu
from etats import *
from user import utilisateur_bloque

load_dotenv()
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# def get_user_lang(update: Update) -> str:
#     """Récupère la langue de l'utilisateur ou 'en' par défaut."""
#     return update.effective_user.langue or "en"

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    lang = get_user_lang(update)
    if utilisateur_bloque(user.id):
        await update.message.reply_text(
            i18n.t("user.log_error_user_bloque")
        )
        return
    msg = i18n.t("globale.support_message", locale=lang)
    await update.message.reply_text(msg, reply_markup=menu.get_menu_markup(user.id))

async def liens_utiles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if utilisateur_bloque(user_id):
        await update.message.reply_text(
            i18n.t("user.log_error_user_bloque")
        )
        return
    lang = get_user_lang(update)
    message = "\n".join([
        i18n.t("globale.useful_links_header", locale=lang),
        i18n.t("globale.coinmarketcap_link", locale=lang),
        i18n.t("globale.coingecko_link", locale=lang),
        i18n.t("globale.binance_link", locale=lang),
        i18n.t("globale.ethereum_link", locale=lang),
        i18n.t("globale.bscscan_link", locale=lang),
        i18n.t("globale.solana_link", locale=lang),
    ])
    await update.message.reply_text(message, reply_markup=menu.get_menu_markup(user_id))

async def a_propos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_user_lang(update)
    message = "\n".join([
        i18n.t("globale.about_us_header", locale=lang),
        "",
        f"{i18n.t('globale.about_title', locale=lang)}",
        i18n.t("globale.about_description", locale=lang),
        "",
        f"{i18n.t('globale.best_part_title', locale=lang)}",
        i18n.t("globale.best_part_description", locale=lang),
        "",
        f"{i18n.t('globale.how_it_works_title', locale=lang)}",
        i18n.t("globale.step_1", locale=lang),
        i18n.t("globale.step_2", locale=lang),
        i18n.t("globale.step_3", locale=lang),
    ])
    await update.message.reply_text(message, reply_markup=menu.get_menu_markup(user_id))
