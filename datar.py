import sqlite3

def init_db():
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS utilisateurs (
            user_id INTEGER PRIMARY KEY,
            nom TEXT,
            langue TEXT,
            montant_depot FLOAT,
            benefice_total FLOAT DEFAULT 0,
            date_enregistrement TEXT,
            adresse_wallet TEXT,
            date_mise_a_jour TEXT,
            cycle INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS retraits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            adresse TEXT,
            reseau TEXT,
            montant FLOAT,
            date_retrait TEXT
        )
    """)
    
    conn.commit()
    conn.close()