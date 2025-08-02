
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import sessionmaker, relationship, declarative_base, Session
from contextlib import contextmanager
from datetime import datetime, timezone

# ==============================================================================
# CONFIGURATION DE LA BASE DE DONNÉES
# ==============================================================================

# Utilise la base de données 'magasin.db' par défaut.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==============================================================================
# DÉPENDANCE POUR L'INJECTION DE SESSION
# ==============================================================================

def get_db():
    """
    Dépendance FastAPI pour fournir une session de base de données par requête.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==============================================================================
# MODÈLES DE TABLES (SQLAlchemy ORM)
# ==============================================================================

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

class Produit(Base):
    __tablename__ = "produits"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, unique=True, nullable=False, index=True)
    prix_achat = Column(Float, nullable=False)
    prix_vente = Column(Float, nullable=False)
    quantite = Column(Integer, nullable=False)
    
    ventes = relationship("Vente", back_populates="produit", cascade="all, delete-orphan")
    pertes = relationship("Perte", back_populates="produit", cascade="all, delete-orphan")

class Vente(Base):
    __tablename__ = "ventes"
    id = Column(Integer, primary_key=True, index=True)
    produit_id = Column(Integer, ForeignKey("produits.id"), nullable=False)
    quantite = Column(Integer, nullable=False)
    prix_total = Column(Float, nullable=False)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    produit = relationship("Produit", back_populates="ventes")

class Perte(Base):
    __tablename__ = "pertes"
    id = Column(Integer, primary_key=True, index=True)
    produit_id = Column(Integer, ForeignKey("produits.id"), nullable=False)
    quantite = Column(Integer, nullable=False)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    produit = relationship("Produit", back_populates="pertes")

class FraisAnnexe(Base):
    __tablename__ = "frais_annexes"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)
    montant = Column(Float, nullable=False)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# ==============================================================================
# FONCTION POUR CRÉER LES TABLES
# ==============================================================================

def create_tables():
    """
    Crée toutes les tables dans la base de données si elles n'existent pas.
    """
    try:
        Base.metadata.create_all(bind=engine)
        print("Tables créées avec succès (si elles n'existaient pas).")
    except Exception as e:
        print(f"Erreur lors de la création des tables: {e}")

# ==============================================================================
# OPÉRATIONS CRUD (Create, Read, Update, Delete)
# ==============================================================================

def get_user_by_username(db: Session, username: str):
    """
    Récupère un utilisateur par son nom d'utilisateur.
    """
    return db.query(User).filter(User.username == username).first()
