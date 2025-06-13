import sqlite3
def get_user_lang(user_id: int) -> str:
    try:
        conn = sqlite3.connect("bot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT langue FROM utilisateurs WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        return result[0] if result else "fr"  # Par défaut: français
    except Exception as e:
        print(f"[Erreur get_user_lang] {e}")
        return "en"
    finally:
        conn.close()