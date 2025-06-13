import sqlite3
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes
import menu
from etats import*
load_dotenv()

ADMIN_ID = int(os.getenv("ADMIN_ID"))


async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = (
        "If you need support, please contact our team at @TWBLiveChat"
    )
    await update.message.reply_text(msg, reply_markup=menu.get_menu_markup(user.id))


async def liens_utiles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = (
       "🔗 Useful links:\n"

    "📊 CoinMarketCap: https://coinmarketcap.com\n"
    "📈 CoinGecko: https://coingecko.com\n"
    "💱 Binance: https://binance.com\n"
    "🌐 Ethereum: https://ethereum.org\n"
    "🔍 BSCScan: https://bscscan.com\n"
    "☀️ Solana: https://solana.com\n"

    )
    await update.message.reply_text(message, reply_markup=menu.get_menu_markup(user_id))


async def a_propos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = (
        "About us:\n"
        "Automated Trading Futures and Earn 25% Weekly using TWB\n"

        "This advanced system trades for you, generating 25% weekly returns on your principal for 2 months or longer—scalable based on your investment.\n"

       " Best Part? No Lock-In!\n"
        "Your funds stay flexible—withdraw your principal anytime without restrictions.\n" 

        "How It Works:\n" 
        "⿡ Deposit – Fund your account securely. \n"
        "⿢ Wait 7 Days – Let TWB work its magic. \n"
        "⿣ Withdraw Profits – Enjoy consistent, hassle-free earnings\n"
                )
    await update.message.reply_text(message, reply_markup=menu.get_menu_markup(user_id))
