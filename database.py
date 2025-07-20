import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import sessionmaker, relationship, declarative_base, Session, joinedload
from contextlib import contextmanager
from datetime import datetime, timezone

# ==============================================================================
# CONFIGURATION ET MOTEUR DE LA BASE DE DONNÉES
# ==============================================================================

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

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
    frais_annexes = relationship("FraisAnnexe", back_populates="produit")

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
    produit_id = Column(Integer, ForeignKey("produits.id"), nullable=False)
    description = Column(String, nullable=False)
    montant = Column(Float, nullable=False)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    produit = relationship("Produit", back_populates="frais_annexes")

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
    # Recharger la relation pour un accès immédiat dans la réponse de l'API
    db.refresh(nouvelle_perte.produit)
    return nouvelle_perte

def update_vente(db: Session, vente_id: int, new_produit_id: int, new_quantite: int):
    vente_a_modifier = db.query(Vente).filter(Vente.id == vente_id).first()
    if not vente_a_modifier:
        raise ValueError("Vente non trouvée.")

    ancien_produit = db.query(Produit).filter(Produit.id == vente_a_modifier.produit_id).first()
    nouveau_produit = db.query(Produit).filter(Produit.id == new_produit_id).first()

    if not nouveau_produit:
        raise ValueError("Nouveau produit non trouvé.")

    # Logique de mise à jour du stock
    if ancien_produit.id == nouveau_produit.id:
        diff_quantite = new_quantite - vente_a_modifier.quantite
        if ancien_produit.quantite < diff_quantite:
            raise ValueError("Stock insuffisant pour la modification.")
        ancien_produit.quantite -= diff_quantite
    else:
        if nouveau_produit.quantite < new_quantite:
            raise ValueError("Stock insuffisant pour le nouveau produit.")
        ancien_produit.quantite += vente_a_modifier.quantite
        nouveau_produit.quantite -= new_quantite

    # Mettre à jour la vente elle-même
    vente_a_modifier.produit_id = new_produit_id
    vente_a_modifier.quantite = new_quantite
    vente_a_modifier.prix_total = nouveau_produit.prix_vente * new_quantite
    vente_a_modifier.date = datetime.now(timezone.utc)

    db.commit()
    db.refresh(vente_a_modifier)
    db.refresh(vente_a_modifier.produit)
    return vente_a_modifier

def delete_vente(db: Session, vente_id: int):
    vente = db.query(Vente).filter(Vente.id == vente_id).first()
    if vente:
        produit = vente.produit
        produit.quantite += vente.quantite
        db.delete(vente)
        db.commit()
    return vente

def delete_perte(db: Session, perte_id: int):
    perte = db.query(Perte).filter(Perte.id == perte_id).first()
    if perte:
        produit = perte.produit
        produit.quantite += perte.quantite
        db.delete(perte)
        db.commit()
    return perte

def update_perte(db: Session, perte_id: int, new_produit_id: int, new_quantite: int):
    perte_a_modifier = db.query(Perte).filter(Perte.id == perte_id).first()
    if not perte_a_modifier:
        raise ValueError("Perte non trouvée.")

    ancien_produit = db.query(Produit).filter(Produit.id == perte_a_modifier.produit_id).first()
    nouveau_produit = db.query(Produit).filter(Produit.id == new_produit_id).first()

    if not nouveau_produit:
        raise ValueError("Nouveau produit non trouvé.")

    # Logique de mise à jour du stock
    if ancien_produit.id == nouveau_produit.id:
        # Le produit est le même, on ajuste juste la quantité
        diff_quantite = new_quantite - perte_a_modifier.quantite
        if ancien_produit.quantite < diff_quantite:
            raise ValueError("Stock insuffisant pour la modification.")
        ancien_produit.quantite -= diff_quantite
    else:
        # Le produit a changé, on restaure l'ancien stock et déduit du nouveau
        if nouveau_produit.quantite < new_quantite:
            raise ValueError("Stock insuffisant pour le nouveau produit.")
        ancien_produit.quantite += perte_a_modifier.quantite
        nouveau_produit.quantite -= new_quantite

    # Mettre à jour la perte elle-même
    perte_a_modifier.produit_id = new_produit_id
    perte_a_modifier.quantite = new_quantite
    perte_a_modifier.date = datetime.now(timezone.utc)

    db.commit()
    db.refresh(perte_a_modifier)
    # Recharger la relation pour un accès immédiat dans la réponse de l'API
    db.refresh(perte_a_modifier.produit)
    return perte_a_modifier


def get_all_frais(db: Session):
    return db.query(FraisAnnexe).options(joinedload(FraisAnnexe.produit)).order_by(FraisAnnexe.date.desc()).all()

def add_frais(db: Session, produit_id: int, description: str, montant: float):
    nouveau_frais = FraisAnnexe(produit_id=produit_id, description=description, montant=montant)
    db.add(nouveau_frais)
    db.commit()
    db.refresh(nouveau_frais)
    db.refresh(nouveau_frais.produit)
    return nouveau_frais

def update_frais(db: Session, frais_id: int, new_produit_id: int, new_description: str, new_montant: float):
    frais_a_modifier = db.query(FraisAnnexe).filter(FraisAnnexe.id == frais_id).first()
    if not frais_a_modifier:
        raise ValueError("Frais non trouvé.")

    frais_a_modifier.produit_id = new_produit_id
    frais_a_modifier.description = new_description
    frais_a_modifier.montant = new_montant
    frais_a_modifier.date = datetime.now(timezone.utc)

    db.commit()
    db.refresh(frais_a_modifier)
    db.refresh(frais_a_modifier.produit)
    return frais_a_modifier

def delete_frais(db: Session, frais_id: int):
    frais = db.query(FraisAnnexe).filter(FraisAnnexe.id == frais_id).first()
    if frais:
        db.delete(frais)
        db.commit()
    return frais


def get_dashboard_kpis(db: Session):
    today = datetime.now(timezone.utc).date()
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

    # Chiffre d'affaires et coût des marchandises vendues (COGS) pour la période
    chiffre_affaires = db.query(func.sum(Vente.prix_total)).filter(Vente.date >= start_date, Vente.date <= end_date).scalar() or 0
    cogs = db.query(func.sum(Produit.prix_achat * Vente.quantite)).select_from(Vente).join(Produit).filter(Vente.date >= start_date, Vente.date <= end_date).scalar() or 0
    benefice_brut = chiffre_affaires - cogs

    # Calcul des dépenses proportionnelles aux ventes de la période
    depenses_ajustees = 0
    ventes_period = db.query(Vente.produit_id, func.sum(Vente.quantite).label('quantite_vendue')).filter(Vente.date >= start_date, Vente.date <= end_date).group_by(Vente.produit_id).all()

    for vente_info in ventes_period:
        produit_id = vente_info.produit_id
        quantite_vendue_period = vente_info.quantite_vendue

        # 1. Coût total des frais pour ce produit (historique)
        total_frais_produit = db.query(func.sum(FraisAnnexe.montant)).filter(FraisAnnexe.produit_id == produit_id).scalar() or 0

        # 2. Quantité totale historique du produit (pour calculer le coût par unité)
        produit = db.query(Produit).filter(Produit.id == produit_id).first()
        total_ventes_historique = db.query(func.sum(Vente.quantite)).filter(Vente.produit_id == produit_id).scalar() or 0
        total_pertes_historique = db.query(func.sum(Perte.quantite)).filter(Perte.produit_id == produit_id).scalar() or 0
        quantite_totale_historique = produit.quantite + total_ventes_historique + total_pertes_historique
        
        if quantite_totale_historique > 0 and total_frais_produit > 0:
            # 3. Coût du frais par unité
            cout_frais_par_unite = total_frais_produit / quantite_totale_historique
            # 4. Dépense pour la période = coût par unité * quantité vendue dans la période
            depenses_ajustees += cout_frais_par_unite * quantite_vendue_period

    benefice_net = benefice_brut - depenses_ajustees

    # Données pour les graphiques (inchangées)
    graph_data_query = db.query(func.date(Vente.date).label('jour'), func.sum(Vente.prix_total).label('ca_jour')).filter(Vente.date >= start_date, Vente.date <= end_date).group_by(func.date(Vente.date)).order_by(func.date(Vente.date))
    graph_data = graph_data_query.all()

    top_profitable_query = db.query(
        Produit.nom,
        func.sum((Vente.prix_total) - (Produit.prix_achat * Vente.quantite)).label('total_profit')
    ).join(Produit, Vente.produit_id == Produit.id).filter(Vente.date >= start_date, Vente.date <= end_date).group_by(Produit.nom).order_by(func.sum((Vente.prix_total) - (Produit.prix_achat * Vente.quantite)).desc()).limit(5)
    top_profitable_products = top_profitable_query.all()

    top_lost_query = db.query(
        Produit.nom,
        func.sum(Perte.quantite).label('total_lost')
    ).join(Produit, Perte.produit_id == Produit.id).filter(Perte.date >= start_date, Perte.date <= end_date).group_by(Produit.nom).order_by(func.sum(Perte.quantite).desc()).limit(5)
    top_lost_products = top_lost_query.all()

    return {
        "chiffre_affaires": chiffre_affaires,
        "cogs": cogs,
        "benefice": benefice_brut, # Renommé pour plus de clarté
        "depenses": depenses_ajustees,
        "benefice_net": benefice_net,
        "graph_data": [{"jour": r.jour.isoformat(), "ca_jour": r.ca_jour} for r in graph_data],
        "top_profitable_products": [dict(r._mapping) for r in top_profitable_products],
        "top_lost_products": [dict(r._mapping) for r in top_lost_products]
    }