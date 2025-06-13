import sqlite3
import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler, CallbackQueryHandler
)

import datar
from admin import *
from depot import *
from globale import *
from retraits import *
from update import *
from user import *
from menu import *
from etats import*
from store import*

load_dotenv()

ADMIN_ID = int(os.getenv("ADMIN_ID"))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        "Welcome! To begin, use the commands to proceed.",
        reply_markup=menu.get_menu_markup(user.id)
    )
    return ConversationHandler.END

async def callback_query_handler_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("confirmer_"):
        parts = data.split("_")

        if len(parts) == 4 and parts[1] == "supp":
            user_id = int(parts[2])
            montant = float(parts[3])
        else:
            user_id = int(parts[1])
            montant = float(parts[2])

        adresse_wallet = None
        try:
            conn = sqlite3.connect("bot.db")
            cursor = conn.cursor()
            cursor.execute("SELECT adresse FROM retraits WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
            row = cursor.fetchone()
            adresse_wallet = row[0] if row else None
        except Exception as e:
            print(f"[Error] callback_query_handler_admin: {e}")
        finally:
            conn.close()

        if utilisateur_existe(user_id):
            mettre_a_jour_solde(user_id, montant)
        else:
            enregistrer_utilisateur(user_id, montant, adresse_wallet)

        admin_text = f"✅ Deposit of {montant} USDT confirmed for user ID {user_id}."
        user_text = f"✅ Your deposit of {montant} USDT has been successfully confirmed. Thank you!\nJoin our channel to stay updated with all the latest information:\nhttps://t.me/+c0mWuQVC6OEwMTM0"

        await query.edit_message_text(admin_text)
        try:
            await context.bot.send_message(chat_id=user_id, text=user_text)
        except Exception as e:
            print(f"[User notification error]: {e}")

    elif data == "annuler":
        await query.edit_message_text("❌ Action cancelled.")
    
async def annuler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text("Operation cancelled.", reply_markup=get_menu_markup(user.id))
    return ConversationHandler.END

def main():
    application = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CommandHandler('withdraw', retrait),
            CommandHandler('deposit', depot),
            CommandHandler('top_up', depot_supplementaire),
            MessageHandler(filters.Regex("^💰 Deposit$"), depot),
            MessageHandler(filters.Regex("^💸 Withdraw$"), retrait),
            MessageHandler(filters.Regex("^📈 Top Up$"), depot_supplementaire),
        ],
        states={
            HASH_TRANSACTION_DEPOT_SUPPLEMENTAIRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, recevoir_hash_depot_supplementaire)],
            HASH_TRANSACTION_DEPOT: [MessageHandler(filters.TEXT & ~filters.COMMAND, recevoir_hash_depot)],
            SAISIE_HASH_RETRAIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, recevoir_hash_retrait)],
            ADRESSE_PORTEFEUILLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, recevoir_adresse)],
            RESEAU_BLOCKCHAIN: [CallbackQueryHandler(recevoir_reseau)],
            MONTANT_DEPOT: [MessageHandler(filters.TEXT & ~filters.COMMAND, recevoir_montant_depot)],
            MONTANT_DEPOT_SUPPLEMENTAIRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, recevoir_montant_depot_supplementaire)],
        },
        fallbacks=[CommandHandler('cancel', annuler)],
    )
    application.add_handler(conv_handler)

    admin_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(retrait_done, pattern=r"^retrait_done_\d+$")],
        states={
            SAISIE_HASH_RETRAIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, recevoir_hash_retrait)],
        },
        fallbacks=[CommandHandler('cancel', annuler)],
    )
    application.add_handler(admin_conv_handler)
    
    not_handler = CallbackQueryHandler(retrait_not, pattern=r"^retrait_not_\d+$")
    application.add_handler(not_handler)

    application.add_handler(CallbackQueryHandler(callback_query_handler_admin))
    
    application.add_handler(CallbackQueryHandler(gerer_callback_produit, 
                                               pattern=r"^(info_produit_|commander_produit_|retour_boutique|contact_support)"))

    application.add_handler(MessageHandler(filters.Regex("^🏪 Our Store$"), our_store))
    application.add_handler(MessageHandler(filters.Regex("^👤 My Info$"), infos))
    application.add_handler(MessageHandler(filters.Regex("^📊 Market Update$"), liens_utiles))
    application.add_handler(MessageHandler(filters.Regex("^ℹ️ About$"), a_propos))
    application.add_handler(MessageHandler(filters.Regex("^🆘 Support$"), support))
    application.add_handler(MessageHandler(filters.Regex("^👥 User List$"), liste_utilisateurs))
    application.add_handler(MessageHandler(filters.Regex("^🔍 User Info$"), info_utilisateur))
    application.add_handler(MessageHandler(filters.Regex("^📝 Set Description$"), set_description))

    application.run_polling()

if __name__ == "__main__":
    main()