
from fastapi import FastAPI, Depends, HTTPException, status, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
import database, auth, schemas

# Initialise la base de données (crée les tables si elles n'existent pas)
database.create_tables()

app = FastAPI(
    title="API de Gestion de Magasin",
    description="Une nouvelle API propre et robuste pour la gestion de magasin.",
    version="3.0.0"
)

# Monte le répertoire 'static' pour servir les fichiers HTML, CSS, JS
app.mount("/static", StaticFiles(directory="static"), name="static")

# ==============================================================================
# ENDPOINT D'AUTHENTIFICATION
# ==============================================================================

@app.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    """
    Fournit un jeton d'accès si les informations d'identification sont correctes.
    """
    user = database.get_user_by_username(db, username=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# ==============================================================================
# ENDPOINTS PROTÉGÉS DE L'API
# ==============================================================================

@app.get("/api/produits", response_model=List[schemas.Produit])
def get_produits(db: Session = Depends(database.get_db), current_user: schemas.User = Depends(auth.get_current_user)):
    return db.query(database.Produit).all()

@app.post("/api/produits", response_model=schemas.Produit)
def create_produit(produit: schemas.ProduitCreate, db: Session = Depends(database.get_db), current_user: schemas.User = Depends(auth.get_current_user)):
    db_produit = database.Produit(**produit.dict())
    db.add(db_produit)
    db.commit()
    db.refresh(db_produit)
    return db_produit

# ... (Ajoutez ici les autres endpoints pour les ventes, pertes, etc. si nécessaire)
# ... (Pour l'instant, je me concentre sur le strict minimum pour la connexion)

# ==============================================================================
# SERVIR L'INTERFACE UTILISATEUR (FRONTEND)
# ==============================================================================

@app.get("/")
def read_root():
    """Sert le fichier principal index.html."""
    return FileResponse('static/index.html')

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    """Gère la requête pour favicon.ico pour éviter les erreurs 404."""
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# =============================================================================
# ROUTE DE SERVICE TEMPORAIRE POUR RÉINITIALISER L'ADMIN
# =============================================================================
@app.get("/reset-admin-password-safando-12345", include_in_schema=False)
def reset_admin(db: Session = Depends(database.get_db)):
    """
    Cette route secrète et temporaire supprime et recrée l'utilisateur admin
    pour corriger le hachage du mot de passe sur le serveur de production.
    """
    username = "admin"
    password = "Dakar2026@"

    # Supprimer l'utilisateur existant s'il y en a un
    user = database.get_user_by_username(db, username=username)
    if user:
        db.delete(user)
        db.commit()
        msg = f"Utilisateur '{username}' existant supprimé. "
    else:
        msg = f"Aucun utilisateur '{username}' existant trouvé. "

    # Créer le nouvel utilisateur avec le hachage correct
    hashed_password = auth.get_password_hash(password)
    new_user = database.User(username=username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    
    return {"message": msg + f"Nouvel utilisateur '{username}' créé avec succès."}
