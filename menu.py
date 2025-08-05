import os
from telegram import ReplyKeyboardMarkup
from translat import tr  # ta fonction de traduction
ADMIN_ID = os.getenv("ADMIN_ID")
from lang import get_user_lang

def get_menu_markup(user_id: int, langue: str=None):
    # Menu de base avec emojis et texte propre (sans "/")
    menu = [
        ["💰 Deposit", "💸 Withdraw"],
        ["🆘 Support", "📊 Market Update"],
        ["👤 My Info", "ℹ️ About"],
        ["📈 Top Up", "🏪 Our Store"],
        ["/cancel"]
    ]
    
    # Ajout des commandes admin uniquement si c'est l'admin
    # if str(user_id) == ADMIN_ID:
    #     menu.append(["👥 User List", "🔍 User Info"])
        # menu.append(["📝 Set Description"])

    return ReplyKeyboardMarkup(menu, resize_keyboard=True)