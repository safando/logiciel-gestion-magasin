import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from datetime import datetime

# --- Configuration de la Base de Données ---
# Récupère l'URL de la base de données depuis les variables d'environnement.
# C'est la méthode sécurisée pour gérer les secrets.
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("La variable d'environnement DATABASE_URL n'est pas définie.")

# Crée le "moteur" de la base de données. C'est le point d'entrée pour SQLAlchemy.
engine = create_engine(DATABASE_URL)

# Crée une "Session" configurée. C'est à travers elle que nous communiquerons avec la DB.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base est une classe de base pour nos modèles de données (nos tables).
Base = declarative_base()

# --- Modèles de Données (Tables) ---

class Produit(Base):
    __tablename__ = "produits"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, unique=True, nullable=False, index=True)
    prix_achat = Column(Float, nullable=False)
    prix_vente = Column(Float, nullable=False)
    quantite = Column(Integer, nullable=False)

    ventes = relationship("Vente", back_populates="produit")
    pertes = relationship("Perte", back_populates="produit")

class Vente(Base):
    __tablename__ = "ventes"
    id = Column(Integer, primary_key=True, index=True)
    produit_id = Column(Integer, ForeignKey("produits.id"), nullable=False)
    quantite = Column(Integer, nullable=False)
    prix_total = Column(Float, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)

    produit = relationship("Produit", back_populates="ventes")

class Perte(Base):
    __tablename__ = "pertes"
    id = Column(Integer, primary_key=True, index=True)
    produit_id = Column(Integer, ForeignKey("produits.id"), nullable=False)
    quantite = Column(Integer, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)

    produit = relationship("Produit", back_populates="pertes")

# --- Gestionnaire de Session ---

@contextmanager
def get_db():
    """Crée une session de base de données pour une requête et la ferme ensuite."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Fonctions de l'Application ---

def create_tables():
    """Crée toutes les tables dans la base de données si elles n'existent pas."""
    try:
        Base.metadata.create_all(bind=engine)
        print("Tables créées avec succès (si elles n'existaient pas).")
    except Exception as e:
        print(f"Erreur lors de la création des tables: {e}")

# --- Fonctions CRUD pour les Produits ---

def add_produit(db, nom: str, prix_achat: float, prix_vente: float, quantite: int):
    nouveau_produit = Produit(nom=nom, prix_achat=prix_achat, prix_vente=prix_vente, quantite=quantite)
    db.add(nouveau_produit)
    db.commit()
    db.refresh(nouveau_produit)
    return nouveau_produit

def get_all_produits(db):
    return db.query(Produit).order_by(Produit.nom).all()

def update_produit(db, produit_id: int, nom: str, prix_achat: float, prix_vente: float, quantite: int):
    produit = db.query(Produit).filter(Produit.id == produit_id).first()
    if produit:
        produit.nom = nom
        produit.prix_achat = prix_achat
        produit.prix_vente = prix_vente
        produit.quantite = quantite
        db.commit()
    return produit

def delete_produit(db, produit_id: int):
    produit = db.query(Produit).filter(Produit.id == produit_id).first()
    if produit:
        db.delete(produit)
        db.commit()
    return produit

# --- Fonctions pour les Ventes et Pertes ---

def add_vente(db, produit_id: int, quantite: int):
    produit = db.query(Produit).filter(Produit.id == produit_id).first()
    if not produit or produit.quantite < quantite:
        raise ValueError("Stock insuffisant ou produit non trouvé.")
    
    produit.quantite -= quantite
    nouvelle_vente = Vente(produit_id=produit_id, quantite=quantite, prix_total=produit.prix_vente * quantite)
    db.add(nouvelle_vente)
    db.commit()
    return nouvelle_vente

def add_perte(db, produit_id: int, quantite: int):
    produit = db.query(Produit).filter(Produit.id == produit_id).first()
    if not produit or produit.quantite < quantite:
        raise ValueError("Stock insuffisant ou produit non trouvé.")

    produit.quantite -= quantite
    nouvelle_perte = Perte(produit_id=produit_id, quantite=quantite)
    db.add(nouvelle_perte)
    db.commit()
    return nouvelle_perte

# --- Fonctions pour le Dashboard et l'Analyse ---

def get_dashboard_kpis(db):
    today = datetime.utcnow().date()
    ca_today = db.query(func.sum(Vente.prix_total)).filter(func.date(Vente.date) == today).scalar() or 0
    ventes_today = db.query(func.sum(Vente.quantite)).filter(func.date(Vente.date) == today).scalar() or 0
    total_stock_quantite = db.query(func.sum(Produit.quantite)).scalar() or 0
    total_stock_valeur = db.query(func.sum(Produit.quantite * Produit.prix_achat)).scalar() or 0

    top_ventes_today = db.query(Produit.nom, func.sum(Vente.quantite).label('quantite_vendue')).join(Vente).filter(func.date(Vente.date) == today).group_by(Produit.nom).order_by(func.sum(Vente.quantite).desc()).limit(5).all()
    low_stock_produits = db.query(Produit).filter(Produit.quantite < 5).order_by(Produit.quantite).limit(5).all()
    stock_par_produit = db.query(Produit.nom, Produit.quantite).order_by(Produit.quantite.desc()).limit(10).all()

    return {
        "ca_today": ca_today,
        "ventes_today": ventes_today,
        "total_stock_quantite": total_stock_quantite,
        "total_stock_valeur": total_stock_valeur,
        "top_ventes_today": [dict(r._mapping) for r in top_ventes_today],
        "low_stock_produits": low_stock_produits,
        "stock_par_produit": [dict(r._mapping) for r in stock_par_produit]
    }

def get_analyse_financiere(db, start_date_str: str, end_date_str: str):
    start_date = datetime.fromisoformat(start_date_str)
    end_date = datetime.fromisoformat(end_date_str)

    # Chiffre d'affaires total sur la période
    chiffre_affaires = db.query(func.sum(Vente.prix_total))         .filter(Vente.date >= start_date, Vente.date <= end_date)         .scalar() or 0

    # Coût des marchandises vendues (COGS)
    cogs_query = db.query(func.sum(Produit.prix_achat * Vente.quantite))         .join(Produit)         .filter(Vente.date >= start_date, Vente.date <= end_date)
    cogs = cogs_query.scalar() or 0

    # Bénéfice brut
    benefice = chiffre_affaires - cogs

    # Données pour le graphique (CA par jour)
    graph_data_query = db.query(
            func.date(Vente.date).label('jour'),
            func.sum(Vente.prix_total).label('ca_jour')
        )         .filter(Vente.date >= start_date, Vente.date <= end_date)         .group_by(func.date(Vente.date))         .order_by(func.date(Vente.date))
    
    graph_data = graph_data_query.all()

    return {
        "chiffre_affaires": chiffre_affaires,
        "cogs": cogs,
        "benefice": benefice,
        "graph_data": [{"jour": r.jour.isoformat(), "ca_jour": r.ca_jour} for r in graph_data]
    }
