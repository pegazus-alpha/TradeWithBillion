
import asyncio
from telegram import Bot, BotCommand, MenuButtonCommands,Update
from telegram.constants import ParseMode
from telegram.ext import Application,ContextTypes
import sqlite3
from lang import *
from i18n import t

from user import utilisateur_bloque

# Remplace ceci par le token de ton bot
BOT_TOKEN = "TON_TOKEN_ICI"


async def parrainage_infos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    set_user_locale(update)  # Définir la locale de l'utilisateur
    user_id = update.effective_user.id
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    if utilisateur_bloque(user_id):
        await update.message.reply_text(
            i18n.t("user.log_error_user_bloque")
        )
        return

    try:
        # Récupérer le bénéfice total
        cursor.execute("SELECT commissions_totales FROM utilisateurs WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        benefice_total = result[0] if result else 0

        # Compter les filleuls niveau 1 uniquement
        cursor.execute("SELECT COUNT(*) FROM commissions WHERE user_id = ? AND niveau = 1", (user_id,))
        niveau1_count = cursor.fetchone()[0] if cursor.fetchone() else 0

        # Montant reçu niveau 1 uniquement
        cursor.execute("SELECT SUM(montant) FROM commissions WHERE user_id = ? AND niveau = 1", (user_id,))
        montant_niveau1 = cursor.fetchone()[0] if cursor.fetchone() else 0

        # Construction du message
        message = (
            f"{t('parrainage.title')}\n\n"
            f"{t('parrainage.referrals')} :\n"
            f"   • {t('parrainage.level')} 1 : {niveau1_count} {t('parrainage.referrals_count')}\n\n"
            f"{t('parrainage.commissions_received')} :\n"
            f"   • {t('parrainage.level')} 1 : {montant_niveau1:.2f} USDT\n\n"
            f"{t('parrainage.current_balance')} : {benefice_total:.2f} USDT"
        )

        await update.message.reply_text(message, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(t(f'errors.data_retrieval_error : {e}'))
        print(f"Erreur parrainage_infos: {e}")

    finally:
        conn.close()