import sqlite3
import os
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes
import menu
from lang import *
from etats import*
# Charger les variables d’environnement
load_dotenv()

# États de la conversation (si besoin)

# ID de l'admin Telegram
ADMIN_ID = os.getenv("ADMIN_ID")


def enregistrer_utilisateur(user_id: int, montant: str = None, wallet: str = None, parrain_id: int = None):
    """Enregistre ou met à jour un utilisateur dans la base de données."""
    try:
        conn = sqlite3.connect("bot.db")
        cursor = conn.cursor()
        date_enregistrement = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Insère ou met à jour l'utilisateur (langue française par défaut)
        cursor.execute("""
            INSERT OR REPLACE INTO utilisateurs (user_id, langue, montant_depot, date_enregistrement, adresse_wallet)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, "fr", montant, date_enregistrement, wallet))

        # TODO: gérer l'enregistrement du parrain si besoin ici

        conn.commit()
    except Exception as e:
        print(f"[Erreur] enregistrer_utilisateur: {e}")
    finally:
        conn.close()


def get_infos_utilisateur(user_id: int) -> dict:
    """Récupère les informations d’un utilisateur depuis la base."""
    try:
        conn = sqlite3.connect("bot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT adresse_wallet, montant_depot, date_enregistrement FROM utilisateurs WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()

        adresse_wallet = row[0] if row and row[0] else "Non enregistré"
        montant_depot = row[1] if row and row[1] else "0 USDT"
        date_enregistrement = row[2] if row and row[2] else None

    except Exception as e:
        print(f"[Erreur] get_infos_utilisateur: {e}")
        adresse_wallet = "Erreur"
        montant_depot = "Erreur"
        date_enregistrement = None
    finally:
        conn.close()

    return {
        "udi": f"UDI-{user_id}",
        "binance_depot": adresse_wallet,
        "date_enregistrement": date_enregistrement,
        "solde": montant_depot,
    }


async def infos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /infos affichant les données de l'utilisateur."""
    user_id = update.effective_user.id
    infos = get_infos_utilisateur(user_id)

    if infos['date_enregistrement']:
        message = (
            f"🆔 Votre numéro UDI : {infos['udi']}\n"
            f"💼 Adresse dépôt Binance : {infos['binance_depot']}\n"
            f"💰 Solde : {infos['solde']}\n"
            f"📅 Date d'enregistrement : {infos['date_enregistrement']}\n"
        )
    else:
        message = "ℹ️ Vous n'êtes pas encore enregistré. Veuillez effectuer un investissement pour commencer."

    await update.message.reply_text(message, reply_markup=menu.get_menu_markup(user_id))


def utilisateur_existe(user_id: int) -> bool:
    """Vérifie si un utilisateur est déjà enregistré en base."""
    try:
        conn = sqlite3.connect("bot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM utilisateurs WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return row is not None
    except Exception as e:
        print(f"[Erreur] utilisateur_existe: {e}")
        return False
    finally:
        conn.close()
