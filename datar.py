
import sqlite3

def init_db():
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS utilisateurs (
            user_id INTEGER PRIMARY KEY,
            langue TEXT,
            montant_depot FLOAT,
            date_enregistrement TEXT,
            adresse_wallet TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS retraits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            adresse TEXT,
            reseau TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wallets_boite (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_wallet TEXT,
            adresse_wallet TEXT,
            reseau TEXT,
            remarques TEXT
        )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parrainages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        parrain_id INTEGER,
        filleul_id INTEGER,
        gain TEXT DEFAULT '0'
    )
""")
    conn.commit()
    conn.close()