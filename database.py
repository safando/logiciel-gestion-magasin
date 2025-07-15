import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import sessionmaker, relationship, declarative_base, Session, joinedload
from contextlib import contextmanager
from datetime import datetime

# ==============================================================================
# CONFIGURATION ET MOTEUR DE LA BASE DE DONNÉES
# ==============================================================================

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("La variable d'environnement DATABASE_URL n'est pas définie.")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==============================================================================
# MODÈLES DE TABLES (SQLAlchemy ORM)
# ==============================================================================

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

# ==============================================================================
# FONCTIONS UTILITAIRES
# ==============================================================================

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Erreur lors de la création des tables: {e}")

# ==============================================================================
# LOGIQUE MÉTIER (CRUD et autres opérations)
# ==============================================================================

def get_all_produits(db: Session):
    return db.query(Produit).order_by(Produit.nom).all()

def add_produit(db: Session, nom: str, prix_achat: float, prix_vente: float, quantite: int):
    nouveau_produit = Produit(nom=nom, prix_achat=prix_achat, prix_vente=prix_vente, quantite=quantite)
    db.add(nouveau_produit)
    db.commit()
    db.refresh(nouveau_produit)
    return nouveau_produit

def update_produit(db: Session, produit_id: int, **kwargs):
    produit = db.query(Produit).filter(Produit.id == produit_id).first()
    if produit:
        for key, value in kwargs.items():
            setattr(produit, key, value)
        db.commit()
        db.refresh(produit)
    return produit

def delete_produit(db: Session, produit_id: int):
    produit = db.query(Produit).filter(Produit.id == produit_id).first()
    if produit:
        db.delete(produit)
        db.commit()
    return produit

def get_all_ventes(db: Session):
    return db.query(Vente).options(joinedload(Vente.produit)).order_by(Vente.date.desc()).all()

def add_vente(db: Session, produit_id: int, quantite: int):
    produit = db.query(Produit).filter(Produit.id == produit_id).first()
    if not produit or produit.quantite < quantite:
        raise ValueError("Stock insuffisant ou produit non trouvé.")
    produit.quantite -= quantite
    nouvelle_vente = Vente(produit_id=produit_id, quantite=quantite, prix_total=produit.prix_vente * quantite)
    db.add(nouvelle_vente)
    db.commit()
    db.refresh(nouvelle_vente)
    # Recharger la relation pour l'accès au nom du produit
    db.refresh(nouvelle_vente.produit)
    return nouvelle_vente

def get_all_pertes(db: Session):
    return db.query(Perte).options(joinedload(Perte.produit)).order_by(Perte.date.desc()).all()

def add_perte(db: Session, produit_id: int, quantite: int):
    produit = db.query(Produit).filter(Produit.id == produit_id).first()
    if not produit or produit.quantite < quantite:
        raise ValueError("Stock insuffisant ou produit non trouvé.")
    produit.quantite -= quantite
    nouvelle_perte = Perte(produit_id=produit_id, quantite=quantite)
    db.add(nouvelle_perte)
    db.commit()
    db.refresh(nouvelle_perte)
    db.refresh(nouvelle_perte.produit)
    return nouvelle_perte

def get_dashboard_kpis(db: Session):
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
        "low_stock_produits": [p.model_dump() for p in low_stock_produits],
        "stock_par_produit": [dict(r._mapping) for r in stock_par_produit]
    }

def get_analyse_financiere(db: Session, start_date_str: str, end_date_str: str):
    start_date = datetime.fromisoformat(start_date_str)
    end_date = datetime.fromisoformat(end_date_str)
    chiffre_affaires = db.query(func.sum(Vente.prix_total)).filter(Vente.date >= start_date, Vente.date <= end_date).scalar() or 0
    cogs = db.query(func.sum(Produit.prix_achat * Vente.quantite)).join(Produit).filter(Vente.date >= start_date, Vente.date <= end_date).scalar() or 0
    benefice = chiffre_affaires - cogs
    graph_data_query = db.query(func.date(Vente.date).label('jour'), func.sum(Vente.prix_total).label('ca_jour')).filter(Vente.date >= start_date, Vente.date <= end_date).group_by(func.date(Vente.date)).order_by(func.date(Vente.date))
    graph_data = graph_data_query.all()
    return {
        "chiffre_affaires": chiffre_affaires,
        "cogs": cogs,
        "benefice": benefice,
        "graph_data": [{"jour": r.jour.isoformat(), "ca_jour": r.ca_jour} for r in graph_data]
    }