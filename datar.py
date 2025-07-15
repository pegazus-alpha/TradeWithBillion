import sqlite3

def init_db():
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS utilisateurs (
            user_id INTEGER PRIMARY KEY,
            parrain_id INTEGER,
            nom TEXT,
            langue TEXT,
            montant_depot FLOAT,
            benefice_total FLOAT DEFAULT 0,
            commissions_totales INTEGER DEFAULT 0,
            date_enregistrement TEXT,
            adresse_wallet TEXT,
            date_mise_a_jour TEXT,
            cycle INTEGER DEFAULT 0,
            statut TEXT
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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS depot (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            adresse TEXT,
            montant FLOAT,
            date_depot TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS commissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,  -- celui qui reçoit la commission
            filleul_id INTEGER,  -- celui qui a fait l’investissement
            niveau INTEGER, -- 1, 2 ou 3
            montant REAL,
            pourcentage REAL,
            date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()