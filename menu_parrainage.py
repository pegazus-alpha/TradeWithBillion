
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

        # Compter les filleuls par niveau
        niveau_counts = {1: 0, 2: 0, 3: 0}
        cursor.execute("SELECT niveau, COUNT(*) FROM commissions WHERE user_id = ? GROUP BY niveau", (user_id,))
        for niveau, count in cursor.fetchall():
            niveau_counts[niveau] = count

        # Montant reçu par niveau
        montant_niveaux = {1: 0, 2: 0, 3: 0}
        cursor.execute("SELECT niveau, SUM(montant) FROM commissions WHERE user_id = ? GROUP BY niveau", (user_id,))
        for niveau, montant in cursor.fetchall():
            montant_niveaux[niveau] = montant

        # Construction du message
        message = (
            f"{t('parrainage.title')}\n\n"
            f"{t('parrainage.referrals')} :\n"
            f"   • {t('parrainage.level')} 1 : {niveau_counts[1]} {t('parrainage.referrals_count')}\n"
            f"   • {t('parrainage.level')} 2 : {niveau_counts[2]} {t('parrainage.referrals_count')}\n"
            f"   • {t('parrainage.level')} 3 : {niveau_counts[3]} {t('parrainage.referrals_count')}\n\n"
            f"{t('parrainage.commissions_received')} :\n"
            f"   • {t('parrainage.level')} 1 : {montant_niveaux[1]:.2f} USDT\n"
            f"   • {t('parrainage.level')} 2 : {montant_niveaux[2]:.2f} USDT\n"
            f"   • {t('parrainage.level')} 3 : {montant_niveaux[3]:.2f} USDT\n\n"
            f"{t('parrainage.current_balance')} : {benefice_total:.2f} USDT"
        )

        await update.message.reply_text(message, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(t(f'errors.data_retrieval_error : {e}'))
        print(f"Erreur parrainage_infos: {e}")

    finally:
        conn.close()