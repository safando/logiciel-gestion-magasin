import sqlite3
import os

# Le chemin absolu vers le dossier du script actuel
_APP_DIR = os.path.dirname(os.path.abspath(__file__))
# Le chemin absolu vers le fichier de base de données
DB_NAME = os.path.join(_APP_DIR, "magasin.db")

def get_db_connection():
    """Crée et retourne une connexion à la base de données."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Permet d'accéder aux colonnes par leur nom
    return conn

# --- Fonctions pour les produits ---

def get_all_produits():
    conn = get_db_connection()
    produits = conn.execute('SELECT * FROM produits ORDER BY nom').fetchall()
    conn.close()
    return [dict(row) for row in produits]

def add_produit(nom, prix_achat, prix_vente, quantite):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO produits (nom, prix_achat, prix_vente, quantite) VALUES (?, ?, ?, ?)',
                 (nom, prix_achat, prix_vente, quantite))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def update_produit(id, nom, prix_achat, prix_vente, quantite):
    conn = get_db_connection()
    conn.execute('UPDATE produits SET nom = ?, prix_achat = ?, prix_vente = ?, quantite = ? WHERE id = ?',
                 (nom, prix_achat, prix_vente, quantite, id))
    conn.commit()
    conn.close()

def delete_produit(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM produits WHERE id = ?', (id,))
    conn.commit()
    conn.close()

# --- Fonctions pour les ventes ---

def get_all_ventes():
    conn = get_db_connection()
    # On joint les tables pour récupérer le nom du produit directement
    ventes = conn.execute('''
        SELECT v.id, p.nom as produit_nom, v.quantite, v.prix_total, v.date
        FROM ventes v
        JOIN produits p ON v.produit_id = p.id
        ORDER BY v.date DESC
    ''').fetchall()
    conn.close()
    return [dict(row) for row in ventes]

def add_vente(produit_id, quantite):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Récupérer le prix et le stock actuel du produit
        produit = cursor.execute('SELECT prix_vente, quantite FROM produits WHERE id = ?', (produit_id,)).fetchone()
        
        if produit is None:
            raise ValueError("Produit non trouvé.")
            
        if quantite > produit['quantite']:
            raise ValueError(f"Stock insuffisant. Quantité restante : {produit['quantite']}")
            
        # Mettre à jour la quantité du produit
        nouvelle_quantite = produit['quantite'] - quantite
        cursor.execute('UPDATE produits SET quantite = ? WHERE id = ?', (nouvelle_quantite, produit_id))
        
        # Enregistrer la vente
        prix_total_vente = quantite * produit['prix_vente']
        cursor.execute('INSERT INTO ventes (produit_id, quantite, prix_total) VALUES (?, ?, ?)',
                     (produit_id, quantite, prix_total_vente))
        
        conn.commit()
    except Exception as e:
        conn.rollback() # Annuler les changements en cas d'erreur
        raise e
    finally:
        conn.close()

# --- Fonctions pour les pertes ---

def get_all_pertes():
    conn = get_db_connection()
    # On joint les tables pour récupérer le nom du produit directement
    pertes = conn.execute('''
        SELECT p.id, pr.nom as produit_nom, p.quantite, p.date
        FROM pertes p
        JOIN produits pr ON p.produit_id = pr.id
        ORDER BY p.date DESC
    ''').fetchall()
    conn.close()
    return [dict(row) for row in pertes]

def add_perte(produit_id, quantite):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Récupérer le stock actuel du produit
        produit = cursor.execute('SELECT quantite FROM produits WHERE id = ?', (produit_id,)).fetchone()
        
        if produit is None:
            raise ValueError("Produit non trouvé.")
            
        if quantite > produit['quantite']:
            raise ValueError(f"Stock insuffisant. Quantité restante : {produit['quantite']}")
            
        # Mettre à jour la quantité du produit
        nouvelle_quantite = produit['quantite'] - quantite
        cursor.execute('UPDATE produits SET quantite = ? WHERE id = ?', (nouvelle_quantite, produit_id))
        
        # Enregistrer la perte
        cursor.execute('INSERT INTO pertes (produit_id, quantite) VALUES (?, ?)',
                     (produit_id, quantite))
        
        conn.commit()
    except Exception as e:
        conn.rollback() # Annuler les changements en cas d'erreur
        raise e
    finally:
        conn.close()

# --- Fonctions pour l'analyse ---

def get_analyse_financiere(start_date, end_date):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Requête 1: Calculer les totaux (CA et COGS) pour la période
    cursor.execute("""
        SELECT 
            SUM(v.prix_total) as chiffre_affaires,
            SUM(v.quantite * p.prix_achat) as cogs
        FROM 
            ventes v
        JOIN 
            produits p ON v.produit_id = p.id
        WHERE 
            DATE(v.date) BETWEEN ? AND ?
    """, (start_date, end_date))
    
    totals = cursor.fetchone()
    chiffre_affaires = totals['chiffre_affaires'] if totals['chiffre_affaires'] is not None else 0
    cogs = totals['cogs'] if totals['cogs'] is not None else 0
    benefice = chiffre_affaires - cogs

    # Requête 2: Données pour le graphique (CA par jour)
    cursor.execute("""
        SELECT 
            DATE(date) as jour, 
            SUM(prix_total) as ca_jour
        FROM ventes
        WHERE DATE(date) BETWEEN ? AND ?
        GROUP BY jour
        ORDER BY jour
    """, (start_date, end_date))
    
    ventes_par_jour = cursor.fetchall()

    conn.close()
    
    return {
        "chiffre_affaires": chiffre_affaires,
        "cogs": cogs,
        "benefice": benefice,
        "graph_data": [dict(row) for row in ventes_par_jour]
    }

# --- Fonctions pour le Tableau de Bord ---

def get_dashboard_kpis():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Chiffre d'affaires et nombre de ventes aujourd'hui
    cursor.execute("""
        SELECT 
            SUM(prix_total) as ca_today,
            COUNT(*) as ventes_today
        FROM ventes
        WHERE DATE(date) = DATE('now')
    """)
    today_sales = cursor.fetchone()

    # Stock total
    cursor.execute("""
        SELECT 
            SUM(quantite) as total_stock_quantite,
            SUM(quantite * prix_achat) as total_stock_valeur
        FROM produits
    """)
    stock_info = cursor.fetchone()

    # Ventes par produit aujourd'hui
    cursor.execute("""
        SELECT p.nom, SUM(v.quantite) as quantite_vendue
        FROM ventes v
        JOIN produits p ON v.produit_id = p.id
        WHERE DATE(v.date) = DATE('now')
        GROUP BY p.nom
        ORDER BY quantite_vendue DESC
    """)
    top_ventes_today = cursor.fetchall()

    # Produits avec stock faible (moins de 5)
    cursor.execute("""
        SELECT nom, quantite
        FROM produits
        WHERE quantite < 5
        ORDER BY quantite ASC
    """)
    low_stock_produits = cursor.fetchall()

    # Stock par produit
    cursor.execute("""
        SELECT nom, quantite
        FROM produits
        ORDER BY nom ASC
    """)
    stock_par_produit = cursor.fetchall()

    conn.close()

    return {
        "ca_today": today_sales['ca_today'] if today_sales['ca_today'] is not None else 0,
        "ventes_today": today_sales['ventes_today'] if today_sales['ventes_today'] is not None else 0,
        "total_stock_quantite": stock_info['total_stock_quantite'] if stock_info['total_stock_quantite'] is not None else 0,
        "total_stock_valeur": stock_info['total_stock_valeur'] if stock_info['total_stock_valeur'] is not None else 0,
        "top_ventes_today": [dict(row) for row in top_ventes_today],
        "low_stock_produits": [dict(row) for row in low_stock_produits],
        "stock_par_produit": [dict(row) for row in stock_par_produit]
    }


def create_tables():
    """Crée les tables de la base de données si elles n'existent pas."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Table des produits
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS produits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL UNIQUE,
        prix_achat REAL NOT NULL,
        prix_vente REAL NOT NULL,
        quantite INTEGER NOT NULL
    )
    """)
    
    # Table des ventes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ventes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produit_id INTEGER NOT NULL,
        quantite INTEGER NOT NULL,
        prix_total REAL NOT NULL,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (produit_id) REFERENCES produits (id)
    )
    """)
    
    # Table des pertes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pertes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produit_id INTEGER NOT NULL,
        quantite INTEGER NOT NULL,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (produit_id) REFERENCES produits (id)
    )
    """)
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    # Ce code ne s'exécute que si on lance le fichier directement
    # python database.py
    create_tables()
    print("Base de données et tables créées avec succès.")
