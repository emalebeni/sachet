import sqlite3

DB_NAME = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Création des tables
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            telephone TEXT,
            email TEXT
        );

        CREATE TABLE IF NOT EXISTS produits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL
        );
        
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL
        );


        CREATE TABLE IF NOT EXISTS ventes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            nom_client TEXT,
            date TEXT,
            total REAL,
            statut TEXT CHECK(statut IN ('soldé', 'non soldé')) DEFAULT 'non soldé',
            FOREIGN KEY (client_id) REFERENCES clients(id)
        );

        CREATE TABLE IF NOT EXISTS ventes_produits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vente_id INTEGER,
            produit_id INTEGER,
            quantite INTEGER,
            prix_unitaire REAL,
            total REAL,
            FOREIGN KEY (vente_id) REFERENCES ventes(id),
            FOREIGN KEY (produit_id) REFERENCES produits(id)
        );

        CREATE TABLE IF NOT EXISTS recu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            nom_client_temporaire TEXT,
            total REAL,
            solde INTEGER DEFAULT 0,
            date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients (id)
           
        );

        CREATE TABLE IF NOT EXISTS recu_produits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recu_id INTEGER,
            produit_id INTEGER,
            quantite INTEGER,
            categorie_id INTEGER,
            prix_unitaire REAL,
            FOREIGN KEY (recu_id) REFERENCES recu (id),
            FOREIGN KEY (produit_id) REFERENCES produits (id),
            FOREIGN KEY (categorie_id) REFERENCES categories (id)
        );
        
        
    ''')

    conn.commit()
    conn.close()
