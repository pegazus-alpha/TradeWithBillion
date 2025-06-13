import sqlite3
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes
from etats import *
load_dotenv()


ADMIN_ID = int(os.getenv("ADMIN_ID"))  # ADMIN_ID must be int


async def liste_utilisateurs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id != ADMIN_ID:
        await update.message.reply_text("Access denied. You are not authorized to use this command.")
        return

    try:
        conn = sqlite3.connect("bot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, langue, montant_depot, date_enregistrement FROM utilisateurs")
        rows = cursor.fetchall()

        if not rows:
            await update.message.reply_text("No users found in the database.")
            return

        message = "List of registered users:\n"
        for row in rows:
            message += (
                f"\nUser ID: {row[0]}\n"
                f"Language: {row[1]}\n"
                f"Amount Deposited: {row[2]}\n"
                f"Registration Date: {row[3]}\n"
                "------------------------"
            )

        await update.message.reply_text(message)

    except Exception as e:
        await update.message.reply_text(f"Error retrieving users: {str(e)}")
    finally:
        conn.close()


async def info_utilisateur(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id != ADMIN_ID:
        await update.message.reply_text("Access denied. You are not authorized to use this command.")
        return

    if not context.args:
        await update.message.reply_text("Please provide a user ID.\nUsage: /info _ utilisateur <user_id>", parse_mode="Markdown")
        return

    cible_id = context.args[0]

    try:
        conn = sqlite3.connect("bot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM utilisateurs WHERE user_id = ?", (cible_id,))
        row = cursor.fetchone()

        if not row:
            await update.message.reply_text("User not found.")
            return

        message = (
            f"Information for user ID {cible_id}:\n"
            f"Language: {row[1]}\n"
            f"Amount Deposited: {row[2]}\n"
            f"Registration Date: {row[3]}\n"
            f"Wallet Address: {row[4]}"
        )
        await update.message.reply_text(message)

    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}")
    finally:
        conn.close()


async def set_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id != ADMIN_ID:
        await update.message.reply_text("Access denied. You are not authorized to use this command.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /set_description <wallet_id> <new_description>")
        return

    wallet_id = context.args[0]
    nouvelle_description = " ".join(context.args[1:])

    try:
        conn = sqlite3.connect("bot.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE wallets_boite SET remarques = ? WHERE id = ?", (nouvelle_description, wallet_id))
        conn.commit()
        await update.message.reply_text("Description updated successfully.")
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}")
    finally:
        conn.close()
