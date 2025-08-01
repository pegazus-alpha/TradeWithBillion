import sqlite3
import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler, CallbackQueryHandler
)
from datetime import datetime, timedelta
import asyncio

# Import your existing modules
from datar import*
from admin import *
from depot import *
from globale import *
from retraits import *
from update import *
from user import *
from menu import *
from etats import*
from store import*
from parrainage import*
from menu_parrainage import*
from retrait_parrainage import *
# Import internationalization
from lang import*
import i18n

load_dotenv()

ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Helper function to get translated text

# =# ====== AUTOMATIC BENEFITS SYSTEM OPTIMISÉ ======
async def verifier_et_mettre_a_jour_benefices(application):
    """Checks and updates benefits - called every 30 minutes but updates only when 7+ days have passed"""
    try:
        conn = sqlite3.connect("bot.db")
        cursor = conn.cursor()
        
        # Get all users with deposits (montant_depot > 0)
        cursor.execute("""
            SELECT user_id, montant_depot, benefice_total, date_mise_a_jour, adresse_wallet, cycle 
            FROM utilisateurs 
            WHERE montant_depot > 0
        """)
        utilisateurs = cursor.fetchall()
        
        if not utilisateurs:
            # No users with deposits, skip processing
            return
        
        date_actuelle = datetime.now()
        users_updated = 0
        
        for user_id, montant_depot, benefice_total, date_mise_a_jour_str, adresse_wallet, cycle in utilisateurs:
            try:
                # Set locale for this user (for proper translation)
                try:
                    # Try to get user language from database or default to 'en'
                    set_user_locale(application.update)
                except:
                    i18n.set('locale', 'en')
                
                # Convert update date to datetime
                if date_mise_a_jour_str:
                    date_mise_a_jour = datetime.strptime(date_mise_a_jour_str, "%Y-%m-%d %H:%M:%S")
                else:
                    # If no update date, use current date minus 8 days to trigger immediate update
                    date_mise_a_jour = date_actuelle - timedelta(days=8)
                    cursor.execute(
                        "UPDATE utilisateurs SET date_mise_a_jour = ? WHERE user_id = ?",
                        (date_mise_a_jour.strftime("%Y-%m-%d %H:%M:%S"), user_id)
                    )
                
                # Calculate time difference in days
                difference_days = (date_actuelle - date_mise_a_jour).total_seconds() / (24 * 3600)
                
                # Check if at least 7 days have passed
                if difference_days >= 7.0:
                    # Calculate how many complete weeks have passed
                    weeks_passees = int(difference_days / 7)
                    
                    # Calculate new benefits (25% of deposit amount per week)
                    nouveaux_benefices = montant_depot * 0.25 * weeks_passees
                    nouveau_benefice_total = (benefice_total or 0) + nouveaux_benefices
                    
                    # Increment cycle count
                    nouveau_cycle = (cycle or 0) + weeks_passees
                    
                    # Check if user has reached 8 cycles limit
                    nouveau_montant_depot = montant_depot
                    if nouveau_cycle >= 8:
                        nouveau_montant_depot = 0  # Reset deposit amount after 8 cycles
                        nouveau_cycle = 0  # Reset cycle count after 8 cycles
                    
                    # Update database with current time
                    nouvelle_date_mise_a_jour = date_mise_a_jour + timedelta(weeks=weeks_passees)
                    nouvelle_date_maj = nouvelle_date_mise_a_jour.strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute("""
                        UPDATE utilisateurs 
                        SET benefice_total = ?, date_mise_a_jour = ?, cycle = ?, montant_depot = ?
                        WHERE user_id = ?
                    """, (nouveau_benefice_total, nouvelle_date_maj, nouveau_cycle, nouveau_montant_depot, user_id))
                    
                    users_updated += 1
                    
                    # Send notification to user with translation
                    message_utilisateur = f"""{i18n.t('telegrame.benefits_update_title')}

{i18n.t('telegrame.new_benefits').format(amount=nouveaux_benefices, weeks=weeks_passees)}
{i18n.t('telegrame.total_benefits').format(amount=nouveau_benefice_total)}
{i18n.t('telegrame.initial_investment').format(amount=montant_depot)}
{i18n.t('telegrame.wallet_address').format(address=adresse_wallet or i18n.t('telegrame.wallet_not_provided'))}
Cycles complétés: {nouveau_cycle}/8

{i18n.t('telegrame.benefits_added_message')}
{i18n.t('telegrame.join_channel_message')}"""
                    
                    # Add cycle completion message if 8 cycles reached
                    if nouveau_cycle >= 8:
                        message_utilisateur += f"\n\n🎉 Félicitations! Vous avez terminé tous votre investissement!"
                    
                    try:
                        await application.bot.send_message(chat_id=user_id, text=message_utilisateur)
                    except Exception as e:
                        print(i18n.t('telegrame.error_user_notification').format(error=str(e)))
                    
                    # Send notification to admin (always in English for admin)
                    # i18n.set('locale', 'en')
                    message_admin = f"""{i18n.t('telegrame.admin_benefits_update')}

{i18n.t('telegrame.admin_user_id').format(user_id=user_id)}
{i18n.t('telegrame.admin_benefits_added').format(amount=nouveaux_benefices)}
{i18n.t('telegrame.admin_new_total_benefits').format(amount=nouveau_benefice_total)}
{i18n.t('telegrame.admin_investment').format(amount=montant_depot)}
{i18n.t('telegrame.wallet_address').format(address=adresse_wallet or i18n.t('telegrame.wallet_not_provided'))}
{i18n.t('telegrame.admin_update_date').format(date=nouvelle_date_maj)}
{i18n.t('telegrame.admin_weeks_processed').format(weeks=weeks_passees)}
Cycles: {nouveau_cycle}/8"""
                    
                    # Add admin message if 8 cycles completed
                    if nouveau_cycle >= 8:
                        message_admin += f"\n⚠️ User {user_id} has completed all 8 cycles. Deposit amount reset to 0."
                    
                    try:
                        await application.bot.send_message(chat_id=ADMIN_ID, text=message_admin)
                    except Exception as e:
                        print(i18n.t('telegrame.error_admin_notification').format(user_id=user_id, error=str(e)))
                        
            except Exception as e:
                print(i18n.t('telegrame.error_user_processing').format(user_id=user_id, error=str(e)))
                continue
        
        # Only commit if there were updates
        if users_updated > 0:
            conn.commit()
            i18n.set('locale', 'en')  # Reset to English for logs
            print(i18n.t('telegrame.log_benefits_updated').format(count=users_updated, time=date_actuelle.strftime('%H:%M:%S')))
        
    except Exception as e:
        i18n.set('locale', 'en')
        print(i18n.t('telegrame.error_benefits_verification').format(error=str(e)))
    finally:
        if 'conn' in locals():
            conn.close()

async def demarrer_verification_benefices(application):
    """Starts periodic benefits verification - checks every 30 minutes"""
    i18n.set('locale', 'en')  # System messages in English
    print(i18n.t('telegrame.log_starting_benefits_system'))
    print(i18n.t('telegrame.log_checking_frequency'))
    
    while True:
        try:
            # Run benefits check every 30 minutes
            await verifier_et_mettre_a_jour_benefices(application)
            
            # Wait 10 minutes (600 seconds) before next verification
            await asyncio.sleep(600)
            
        except Exception as e:
            print(i18n.t('telegrame.error_verification_loop').format(error=str(e)))
            # In case of error, wait 5 minutes before retrying
            await asyncio.sleep(300)

# ====== END OF AUTOMATIC BENEFITS SYSTEM ======

# ====== UNIVERSAL CANCELLATION SYSTEM ======
USER_IN_CONVERSATION = {}

async def cancel_all_conversations(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Universal function to cancel any ongoing conversation"""
    user_lang=set_user_locale(update)
    user_id = update.effective_user.id
    USER_IN_CONVERSATION.pop(user_id, None)
    context.user_data.clear()
    
    # Set user locale for proper translation
    set_user_locale(update)
    await update.message.reply_text(i18n.t('telegrame.operation_cancelled'), reply_markup=get_menu_markup(user_id))
    return ConversationHandler.END

def is_command_while_in_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_lang=set_user_locale(update)
    """Checks if user types a command while in a conversation"""
    if not update.message or not update.message.text:
        return False
    text = update.message.text.strip()
    user_id = update.effective_user.id
    if text.startswith('/') and USER_IN_CONVERSATION.get(user_id, False):
        return True
    return False

async def handle_command_interruption(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles interruption by a command during a conversation"""
    user_id = update.effective_user.id
    command = update.message.text.strip()
    USER_IN_CONVERSATION.pop(user_id, None)
    context.user_data.clear()
    
    # Set user locale for proper translation
    set_user_locale(update)
    
    if command == '/cancel':
        await update.message.reply_text(i18n.t('telegrame.operation_cancelled'), reply_markup=get_menu_markup(user_id))
    else:
        await update.message.reply_text(i18n.t('telegrame.previous_operation_cancelled').format(command=command), reply_markup=get_menu_markup(user_id))
    return ConversationHandler.END

def create_universal_message_handler(handler_function):
    """Wrapper that adds universal cancellation handling to your existing handlers"""
    async def wrapped_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if is_command_while_in_conversation(update, context):
            return await handle_command_interruption(update, context)
        return await handler_function(update, context)
    return wrapped_handler
# ====== END OF UNIVERSAL SYSTEM ======

# import sqlite3
# from datetime import datetime

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    set_user_locale(update)

    user = update.effective_user
    args = context.args
    parrain_id = 0
    if args:
        try:
            parrain_id = int(args[0])
            if parrain_id == user.id:
                parrain_id = 0  # éviter que l'utilisateur se parraine lui-même
        except:
            parrain_id = 0  # sécurité si paramètre invalide

    # Set user locale and save language preference
    user_lang = set_user_locale(update)

    try:
        conn = sqlite3.connect("bot.db")
        cursor = conn.cursor()

        # Vérifie si l'utilisateur existe déjà
        cursor.execute("SELECT parrain_id FROM utilisateurs WHERE user_id = ?", (user.id,))
        existing = cursor.fetchone()

        if existing:
            # Utilisateur existe : mise à jour de la langue uniquement
            cursor.execute("""
                UPDATE utilisateurs SET langue = ? WHERE user_id = ?
            """, (user_lang, user.id))
        else:
            # Vérifie que le parrain existe et que ce n'est pas une boucle (pas d'auto-parrainage)
            if parrain_id != 0:
                cursor.execute("SELECT 1 FROM utilisateurs WHERE user_id = ?", (parrain_id,))
                if not cursor.fetchone():
                    parrain_id = 0  # parrain non trouvé
            # else:
            #     parrain_id=0
            # Enregistre le nouvel utilisateur avec parrain_id
            cursor.execute("""
                INSERT INTO utilisateurs (user_id, parrain_id, langue)
                VALUES (?, ?, ?)
            """, (
                user.id,
                parrain_id,
                user_lang,
            ))

        conn.commit()

    except Exception as e:
        print(f"Error saving user: {e}")

    finally:
        if 'conn' in locals():
            conn.close()

    await update.message.reply_text(
        f"{i18n.t('telegrame.welcome_message', locale=user_lang)}",
        reply_markup=menu.get_menu_markup(user.id)
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    set_user_locale(update)
    await update.message.reply_text("/start")
    return ConversationHandler.END

async def callback_query_handler_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
   
    # Set user locale for proper translation
    set_user_locale(update)
    print(f"\ndonnées: {data}\n")
    if data.startswith("confirmer_") :
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
            print(i18n.t('telegrame.error_callback_admin').format(error=str(e)))
        finally:
            conn.close()
        
        # Récupérer le nom de l'utilisateur cible depuis Telegram
        nom = None
        try:
            user_info = await context.bot.get_chat(user_id)
            first = user_info.first_name or ""
            last = user_info.last_name or ""
            full_name = (first + " " + last).strip()
            username = f"@{user_info.username}" if user_info.username else ""

            if full_name:
                nom = full_name
            elif username:
                nom = username
            else:
                nom = f"Utilisateur_{user_id}"  # valeur de repli sûre
        except Exception as e:
            print(f"Erreur lors de la récupération des infos utilisateur: {e}")
            nom = f"Utilisateur_{user_id}"  # valeur de repli sûre

        
        enregistrer_utilisateur(user_id=user_id, montant=montant, wallet=None, nom=nom)
        enregistrer_depot(user_id=user_id, username=nom, adresse=HASH_TRANSACTION_DEPOT,montant=montant)

        admin_text = i18n.t('telegrame.deposit_confirmed_admin').format(amount=montant, user_id=user_id)
        user_text = i18n.t('telegrame.deposit_confirmed_user').format(amount=montant)
        await query.message.reply_text(admin_text)
        try:
            # Set locale for the target user
            try:
                conn = sqlite3.connect("bot.db")
                cursor = conn.cursor()
                cursor.execute("SELECT langue FROM utilisateurs WHERE user_id = ?", (user_id,))
                lang_row = cursor.fetchone()
                target_user_lang = lang_row[0] if lang_row and lang_row[0] else 'en'
                i18n.set('locale', target_user_lang)
                user_text = i18n.t('telegrame.deposit_confirmed_user').format(amount=montant)
            except:
                pass
            finally:
                if 'conn' in locals():
                    conn.close()
                   
            await context.bot.send_message(chat_id=user_id, text=user_text)
            await attribuer_commissions(user_id=user_id,montant_depot= montant, bot=context.bot)


        except Exception as e:
            print(i18n.t('telegrame.error_user_notification').format(error=str(e)))
    elif data.startswith("annuler_"):
        parts = data.split("_")
        if len(parts) == 2:
            try:
                user_id = int(parts[1])
                await query.edit_message_text(i18n.t('telegrame.action_cancelled'))
                print(f"[INFO] Annulation confirmée pour l'utilisateur {user_id}")
                # Déterminer la langue de l'utilisateur
                try:
                    conn = sqlite3.connect("bot.db")
                    cursor = conn.cursor()
                    cursor.execute("SELECT langue FROM utilisateurs WHERE user_id = ?", (user_id,))
                    row = cursor.fetchone()
                    user_lang = row[0] if row and row[0] else 'en'
                    i18n.set('locale', user_lang)
                except:
                    user_lang = 'en'
                finally:
                    if 'conn' in locals():
                        conn.close()
                # Envoyer la notification à l'utilisateur
                await context.bot.send_message(
                    chat_id=user_id,
                    text=i18n.t('telegrame.action_cancelled'),
                    reply_markup=get_menu_markup(user_id)
                )
                print(f"[INFO] Notification d'annulation envoyée à l'utilisateur {user_id}")
            except Exception as e:
                print(i18n.t('telegrame.error_user_notification').format(error=str(e)))
        else:
            print("[ERREUR] Format du callback_data invalide pour annulation.")

async def annuler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    set_user_locale(update)
    await update.message.reply_text(i18n.t('telegrame.operation_cancelled'), reply_markup=get_menu_markup(user.id))
    return ConversationHandler.END

async def post_init(application):
    """Démarre les tâches après l'initialisation de l'application"""
    asyncio.create_task(demarrer_verification_benefices(application))

# Remplacez la partie des handlers à la fin de votre fonction main() par ceci :

def main():
    application = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
    init_db()
    
    # Add langue column to users table if not exists
    try:
        conn = sqlite3.connect("bot.db")
        cursor = conn.cursor()
        cursor.execute("ALTER TABLE utilisateurs ADD COLUMN langue TEXT DEFAULT 'en'")
        conn.commit()
    except sqlite3.OperationalError:
        # Column already exists
        pass
    finally:
        conn.close()
    
    # Handlers pour les confirmations de dépôt (doivent être ajoutés en premier)
    application.add_handler(CallbackQueryHandler(callback_query_handler_admin, pattern=r"^confirmer_\d+_[\d.]+$"))
    application.add_handler(CallbackQueryHandler(confirmer_depot_supplementaire, pattern=r"^confir_supp_\d+_[\d.]+$"))
    application.add_handler(CallbackQueryHandler(callback_query_handler_admin, pattern=r"^annuler_\d+$"))
    application.add_handler(CallbackQueryHandler(confirmer_depot_supplementaire, pattern=r"^annuler_supp_\d+$"))

    # Handler principal pour les conversations (dépôts, retraits normaux)
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("referral_infos", parrainage_infos),
            CommandHandler("referral_tuto", systeme_parrainage),
            CommandHandler("referral_link", create_link),
            CommandHandler("referral_withdraw", retrait_parrainage),
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
            ADRESSE_PARRAINAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, recevoir_adresse_parrainage)],
            RESEAU_PARRAINAGE: [CallbackQueryHandler(recevoir_reseau_parrainage)],
            SAISIE_HASH_RETRAIT2: [MessageHandler(filters.TEXT & ~filters.COMMAND, recevoir_hash_retrait2)],
            MODE_PAIEMENT: [CallbackQueryHandler(recevoir_mode_paiement, pattern="^mode_(usdt|local)$")],
            CHOIX_PAYS: [CallbackQueryHandler(recevoir_pays, pattern="^pays_")],
            CHOIX_OPERATEUR: [CallbackQueryHandler(recevoir_operateur, pattern="^op_")],
            NUMERO_MOBILE: [MessageHandler(filters.TEXT & ~filters.COMMAND, recevoir_numero_mobile)],
            NOM_UTILISATEUR: [MessageHandler(filters.TEXT & ~filters.COMMAND, recevoir_nom_utilisateur)],
            CHOIX_PAYS2: [CallbackQueryHandler(recevoir_pays_parrainage, pattern="^pays_")],
            CHOIX_OPERATEUR2: [CallbackQueryHandler(recevoir_operateur_parrainage, pattern="^op_")],
            NUMERO_MOBILE2: [MessageHandler(filters.TEXT & ~filters.COMMAND, recevoir_numero_mobile_parrainage)],
            NOM_UTILISATEUR2: [MessageHandler(filters.TEXT & ~filters.COMMAND, recevoir_nom_utilisateur_parrainage)],
        },
        fallbacks=[
            CommandHandler('cancel', cancel_all_conversations),
            MessageHandler(filters.COMMAND, handle_command_interruption)
        ],
    )
    application.add_handler(conv_handler)

    # Handler pour les retraits normaux (admin confirme le retrait)
    admin_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(retrait_done, pattern=r"^retrait_done_\d+$")],
        states={
            SAISIE_HASH_RETRAIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, recevoir_hash_retrait)],
            # SAISIE_IMAGE_PAIEMENT_LOCAL: [MessageHandler(filters.PHOTO, recevoir_image_paiement_local2)],
        },
        fallbacks=[
            CommandHandler('cancel', cancel_all_conversations),
            MessageHandler(filters.COMMAND, handle_command_interruption)
        ],
    )
    application.add_handler(admin_conv_handler)
    admin_conv_handler2 = ConversationHandler(
        entry_points=[CallbackQueryHandler(retrait_local_done, pattern=r"^retrait_local_done_\d+$")],
        states={
            # SAISIE_HASH_RETRAIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, recevoir_hash_retrait)],
            SAISIE_IMAGE_PAIEMENT_LOCAL: [MessageHandler(filters.PHOTO, recevoir_image_paiement_local)],
        },
        fallbacks=[
            CommandHandler('cancel', cancel_all_conversations),
            MessageHandler(filters.COMMAND, handle_command_interruption)
        ],
    )
    application.add_handler(admin_conv_handler2)

    # Handler pour les retraits de parrainage (admin confirme le retrait parrainage)
    handler_retrait_parrainage = ConversationHandler(
        entry_points=[CallbackQueryHandler(retrait_done2, pattern=r"^retrait_done2_\d+$")],
        states={
            SAISIE_HASH_RETRAIT2: [MessageHandler(filters.TEXT & ~filters.COMMAND, recevoir_hash_retrait2)],
            SAISIE_IMAGE_PAIEMENT_LOCAL2: [MessageHandler(filters.PHOTO, recevoir_image_paiement_local2)],
        },
        fallbacks=[
            CommandHandler('cancel', cancel_all_conversations),
            MessageHandler(filters.COMMAND, handle_command_interruption)
        ],
    )
    application.add_handler(handler_retrait_parrainage)

    # Handler pour les refus de retrait (doit être ajouté séparément)
    application.add_handler(CallbackQueryHandler(retrait_not, pattern=r"^retrait_not_\d+$"))

    # Handlers pour la boutique
    application.add_handler(CallbackQueryHandler(gerer_callback_produit, 
                                               pattern=r"^(info_produit_|commander_produit_|retour_boutique|contact_support)"))

    # Handlers pour les messages du menu
    application.add_handler(MessageHandler(filters.Regex("^🏪 Our Store$"), our_store))
    application.add_handler(MessageHandler(filters.Regex("^👤 My Info$"), infos))
    application.add_handler(MessageHandler(filters.Regex("^📊 Market Update$"), liens_utiles))
    application.add_handler(MessageHandler(filters.Regex("^ℹ️ About$"), a_propos))
    application.add_handler(MessageHandler(filters.Regex("^🆘 Support$"), support))
    application.add_handler(MessageHandler(filters.Regex("^👥 User List$"), liste_utilisateurs))
    application.add_handler(MessageHandler(filters.Regex("^🔍 User Info$"), info_utilisateur))
    application.add_handler(MessageHandler(filters.Regex("^❌cancel$"), cancel_all_conversations))
    
    # Commands handlers supplémentaires
    application.add_handler(CommandHandler("referral_info", parrainage_infos))
    application.add_handler(CommandHandler("tuto_referral", systeme_parrainage))
    application.add_handler(CommandHandler("referal_link", create_link))

    # Start automatic benefits verification in background
    application.post_init = post_init

    application.run_polling()

if __name__ == "__main__":
    main()