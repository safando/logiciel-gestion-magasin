from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel
import database
import pandas as pd
from weasyprint import HTML
import io
from datetime import timedelta

# Importations pour l'authentification
from fastapi.security import OAuth2PasswordRequestForm
import auth
from sqlalchemy.orm import Session

# --- Base de données utilisateur "en dur" ---
# Dans une vraie application, cela viendrait d'une base de données.
# Le mot de passe pour "admin" est "Dakar2026@"
FAKE_USERS_DB = {
    "admin": {
        "username": "admin",
        "full_name": "Admin",
        "email": "admin@example.com",
        "hashed_password": "$2b$12$pAqiSQ2DJhVFKfD1e3dpCu0cqb6IR3DPKLuwpEqCwjuBvhUkO9Yhm", # Mdp: Dakar2026@
        "disabled": False,
    }
}

def get_user(db, username: str):
    if username in db:
        return db[username]

# Modèles de données Pydantic pour la validation
class Produit(BaseModel):
    nom: str
    prix_achat: float
    prix_vente: float
    quantite: int

class ProduitUpdate(Produit):
    id: int

class Vente(BaseModel):
    produit_id: int
    quantite: int

class Perte(BaseModel):
    produit_id: int
    quantite: int

# Crée les tables au démarrage si elles n'existent pas
database.create_tables()

app = FastAPI(
    title="API de Gestion de Magasin",
    description="API pour gérer les stocks, les ventes et les pertes.",
    version="1.0.0"
)

# Monte le dossier 'static' pour qu'il soit accessible depuis le navigateur
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", include_in_schema=False)
async def root():
    """Sert la page web principale."""
    return FileResponse('static/index.html')

# --- Endpoint de connexion ---
@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user(FAKE_USERS_DB, form_data.username)
    if not user or not auth.verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# --- Endpoints pour les PRODUITS (protégés) ---
@app.get("/api/produits")
async def api_get_produits(db: Session = Depends(database.get_db), current_user: dict = Depends(auth.get_current_user)):
    produits = database.get_all_produits(db)
    return produits

@app.post("/api/produits")
async def api_add_produit(produit: Produit, db: Session = Depends(database.get_db), current_user: dict = Depends(auth.get_current_user)):
    try:
        new_produit = database.add_produit(db, produit.nom, produit.prix_achat, produit.prix_vente, produit.quantite)
        return {"status": "success", "message": "Produit ajouté avec succès.", "id": new_produit.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur: {e}")

@app.put("/api/produits")
async def api_update_produit(produit: ProduitUpdate, db: Session = Depends(database.get_db), current_user: dict = Depends(auth.get_current_user)):
    updated_produit = database.update_produit(db, produit.id, produit.nom, produit.prix_achat, produit.prix_vente, produit.quantite)
    if not updated_produit:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return {"status": "success", "message": "Produit mis à jour avec succès."}

@app.delete("/api/produits/{produit_id}")
async def api_delete_produit(produit_id: int, db: Session = Depends(database.get_db), current_user: dict = Depends(auth.get_current_user)):
    deleted_produit = database.delete_produit(db, produit_id)
    if not deleted_produit:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return {"status": "success", "message": "Produit supprimé avec succès."}


# --- Endpoints pour les VENTES (protégés) ---
@app.get("/api/ventes")
async def api_get_ventes(db: Session = Depends(database.get_db), current_user: dict = Depends(auth.get_current_user)):
    # Cette fonction doit être ajoutée à database.py
    ventes = db.query(database.Vente).order_by(database.Vente.date.desc()).all()
    return ventes

@app.post("/api/ventes")
async def api_add_vente(vente: Vente, db: Session = Depends(database.get_db), current_user: dict = Depends(auth.get_current_user)):
    try:
        database.add_vente(db, vente.produit_id, vente.quantite)
        return {"status": "success", "message": "Vente enregistrée avec succès."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Endpoints pour les PERTES (protégés) ---
@app.get("/api/pertes")
async def api_get_pertes(db: Session = Depends(database.get_db), current_user: dict = Depends(auth.get_current_user)):
    # Cette fonction doit être ajoutée à database.py
    pertes = db.query(database.Perte).order_by(database.Perte.date.desc()).all()
    return pertes

@app.post("/api/pertes")
async def api_add_perte(perte: Perte, db: Session = Depends(database.get_db), current_user: dict = Depends(auth.get_current_user)):
    try:
        database.add_perte(db, perte.produit_id, perte.quantite)
        return {"status": "success", "message": "Perte enregistrée avec succès."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Endpoint pour le TABLEAU DE BORD (protégé) ---
@app.get("/api/dashboard")
async def api_get_dashboard_kpis(db: Session = Depends(database.get_db), current_user: dict = Depends(auth.get_current_user)):
    kpis = database.get_dashboard_kpis(db)
    return kpis


# --- Endpoint pour l'ANALYSE (protégé) ---
@app.get("/api/analyse")
async def api_get_analyse(start_date: str, end_date: str, db: Session = Depends(database.get_db), current_user: dict = Depends(auth.get_current_user)):
    data = database.get_analyse_financiere(db, start_date, end_date)
    return data


# --- Endpoint pour l'EXPORT (protégé) ---
@app.get("/api/export")
async def api_export_data(data_type: str, file_format: str, db: Session = Depends(database.get_db), current_user: dict = Depends(auth.get_current_user)):
    # ... (La logique d'export doit être adaptée pour SQLAlchemy)
    # Pour l'instant, nous laissons cette partie simplifiée
    if data_type == "stock":
        data = database.get_all_produits(db)
        df = pd.DataFrame([d.__dict__ for d in data])
    else:
        df = pd.DataFrame()

    if file_format == "excel":
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name=data_type.capitalize())
        
        headers = {
            'Content-Disposition': f'attachment; filename="export_{data_type}.xlsx"'
        }
        return StreamingResponse(io.BytesIO(output.getvalue()), media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers=headers)

    elif file_format == "pdf":
        html_string = f"<h1>Rapport - {data_type.capitalize()}</h1>{df.to_html(index=False)}"
        pdf_bytes = HTML(string=html_string).write_pdf()
        headers = {
            'Content-Disposition': f'attachment; filename="export_{data_type}.pdf"'
        }
        return StreamingResponse(io.BytesIO(pdf_bytes), media_type='application/pdf', headers=headers)

    else:
        raise HTTPException(status_code=400, detail="Format de fichier non valide.")
