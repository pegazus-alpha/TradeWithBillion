import sqlite3
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from i18n import t
from lang import *

async def attribuer_commissions(user_id: int, montant_depot: float, bot, db_path="bot.db"):
    POURCENTAGE = 0.02  # 2% pour le parrain direct
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        # Obtenir le parrain direct
        cursor.execute("SELECT parrain_id FROM utilisateurs WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()

        if not result or result[0] is None:
            conn.close()
            print(f"❌ Pas de parrain direct pour l'utilisateur {user_id}.")
            return

        parrain_id = result[0]
        montant_commission = montant_depot * POURCENTAGE

        # Mise à jour des données du parrain
        cursor.execute("""
            UPDATE utilisateurs
            SET 
                commissions_totales = commissions_totales + ?
            WHERE user_id = ?
        """, (
            montant_commission,
            parrain_id
        ))

        # Insertion dans la table des commissions
        cursor.execute("""
            INSERT INTO commissions (
                user_id, filleul_id, niveau, montant, pourcentage, date
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            parrain_id,
            user_id,
            1,  # niveau 1 uniquement
            montant_commission,
            POURCENTAGE,
            datetime.now().isoformat()
        ))

        # 🔔 Notification Telegram au parrain
        try:
            # Définir la locale du parrain
            cursor.execute("SELECT language_code FROM utilisateurs WHERE user_id = ?", (parrain_id,))
            lang_result = cursor.fetchone()
            if lang_result and lang_result[0]:
                i18n.set('locale', lang_result[0][:2].lower())
            else:
                i18n.set('locale', 'en')
            
            await bot.send_message(
                chat_id=parrain_id,
                text=t('commissions.notification_received').format(montant=montant_commission, niveau=1)
            )
            
            # Vérifier si le parrain peut effectuer un retrait
            cursor.execute("SELECT commissions_totales FROM utilisateurs WHERE user_id = ?", (parrain_id,))
            result_commission = cursor.fetchone()
            
            if result_commission and result_commission[0] >= 10:
                await bot.send_message(
                    chat_id=parrain_id,
                    text=t('commissions.withdrawal_available').format(total=result_commission[0])
                )

        except Exception as e:
            print(f"Erreur envoi message Telegram au parrain {parrain_id} : {e}")

        conn.commit()
        print(f"✅ Commission attribuée pour le dépôt de {montant_depot} par l'utilisateur {user_id}.")

    except Exception as e:
        conn.rollback()
        print(f"❌ Erreur lors de l'attribution de la commission : {e}")

    finally:
        conn.close()
async def systeme_parrainage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    set_user_locale(update)  # Définir la locale de l'utilisateur
    
    message = t('referral_system.explanation')

    await update.message.reply_text(message, parse_mode="Markdown")