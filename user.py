import sqlite3
import os
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes
import menu
from lang import *
from etats import*
from i18n import t
# Load environment variables
load_dotenv()

# Telegram Admin ID
ADMIN_ID = os.getenv("ADMIN_ID")

async def create_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(f"t.me/TradeWithBillion_bot?start={user_id}")
def enregistrer_utilisateur(user_id: int, montant: str = None, wallet: str = None, parrain_id: int = None, nom: str = "new user"):
    """Register or update a user in the database."""
   
    try:
        conn = sqlite3.connect("bot.db")
        cursor = conn.cursor()
        registration_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Check if user exists
        cursor.execute("SELECT user_id FROM utilisateurs WHERE user_id = ?", (user_id,))
        user_exists = cursor.fetchone() is not None
        
        if user_exists:
            # Update existing user - only update specified fields
            update_fields = []
            update_values = []
            
            if montant is not None:
                update_fields.append("montant_depot = ?")
                update_values.append(montant)
            
            if wallet is not None:
                update_fields.append("adresse_wallet = ?")
                update_values.append(wallet)
                
            if nom is not None:
                update_fields.append("nom = ?")
                update_values.append(nom)
            
            # Always update date_mise_a_jour when updating
            update_fields.append("date_mise_a_jour = ?")
            update_values.append(registration_date)
            update_fields.append("date_enregistrement = ?")
            update_values.append(registration_date)
            
            if update_fields:  # Only execute if there are fields to update
                update_values.append(user_id)  # Add user_id for WHERE clause
                query = f"UPDATE utilisateurs SET {', '.join(update_fields)} WHERE user_id = ?"
                cursor.execute(query, update_values)
        else:
            # Insert new user with default language
            def_lang = f"{t('user.DEFAULT_LANGUAGE')}"
            cursor.execute("""
                INSERT INTO utilisateurs (user_id, nom, langue, montant_depot, date_enregistrement, adresse_wallet, date_mise_a_jour)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, nom, def_lang, montant, registration_date, wallet, registration_date))
        
        # TODO: handle referral registration here if needed
        conn.commit()
    except Exception as e:
        print(f"{t('user.log_error_register_user').format(error=e)}")
    finally:
        conn.close()


def get_infos_utilisateur(user_id: int) -> dict:
    """Retrieve user information from the database."""
    try:
        conn = sqlite3.connect("bot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT nom, adresse_wallet, montant_depot, date_enregistrement, benefice_total, cycle FROM utilisateurs WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()

        nom = row[0] if row and row[0] else f"{t('user.user_name_not_registered')}"
        adresse_wallet = row[1] if row and row[1] else f"{t('user.user_address_not_registered')}"
        montant_depot = row[2] if row and row[2] else "0 USDT"
        date_enregistrement = row[3] if row and row[3] else None
        benefice_total = row[4] if row and row[4] else 0
        cycle = row[5] if row and row[5] else 1
        
        # Calcul du pourcentage de profit
        pourcentage_profit = 0.25 * cycle
        
    except Exception as e:
        print(f"{t('user.log_error_get_user_info').format(error=e)}")
        nom = f"{t('user.user_info_error')}"
        adresse_wallet = f"{t('user.user_info_error')}"
        montant_depot = f"{t('user.user_info_error')}"
        date_enregistrement = None
        benefice_total = 0
        cycle = 1
        pourcentage_profit = 0.25 * cycle
    finally:
        conn.close()

    return {
        "udi": f"UDI-{user_id}",
        "nom": nom,
        "binance_depot": adresse_wallet,
        "date_enregistrement": date_enregistrement,
        "solde": montant_depot,
        "benefice_total": benefice_total,
        "cycle": cycle,
        "pourcentage_profit": pourcentage_profit
    }


async def infos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/infos command to display user's data."""
    user_id = update.effective_user.id
    infos = get_infos_utilisateur(user_id)
    
    # Conversion du solde en float pour éviter l'erreur de multiplication
    try:
        solde_numeric = float(infos['solde'].replace(' USDT', '')) if isinstance(infos['solde'], str) else float(infos['solde'])
        benef = solde_numeric * 0.25
    except (ValueError, TypeError):
        benef = 0.0
    
    if infos['date_enregistrement']:
        message = (
            f"{t('user.user_udi_number').format(udi=infos['udi'])}\n"
            f"👤 {t('user.user_name').format(nom=infos['nom'])}\n"
            f"{t('user.user_binance_address').format(address=infos['binance_depot'])}\n"
            f"{t('user.user_balance').format(balance=infos['solde'])}\n"
            f"{t('user.user_registration_date').format(date=infos['date_enregistrement'])}\n"
            f"{t('user.user_benefice_hebdomadaire').format(benefice=benef)}\n"
            f"{t('user.user_benefice_total').format(benefice_total=infos['benefice_total'])}\n"
            f"⏳ Pourcent profit: {infos['pourcentage_profit']*100:.1f}%\n"
        )
    else:
        message = f"{t('user.user_not_registered')}"

    await update.message.reply_text(message, reply_markup=menu.get_menu_markup(user_id))


def utilisateur_existe(user_id: int) -> bool:
    """Check if a user is already registered in the database."""
    try:
        conn = sqlite3.connect("bot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM utilisateurs WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return row is not None
    except Exception as e:
        print(f"{t('user.log_error_user_exists').format(error=e)}")
        return False
    finally:
        conn.close()
def utilisateur_bloque(user_id: int) -> bool:
    """Check if a user is bloqué in the database."""
    try:
        conn = sqlite3.connect("bot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT statut FROM utilisateurs WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return row is not None
    except Exception as e:
        print(f"{t('user.log_error_user_bloque').format(error=e)}")
        return False
    finally:
        conn.close()