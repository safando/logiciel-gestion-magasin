from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
import database
import pandas as pd
from weasyprint import HTML
import io
from datetime import datetime, timedelta

# Importations pour l'authentification
from fastapi.security import OAuth2PasswordRequestForm
import auth
from sqlalchemy.orm import Session, joinedload

# ==============================================================================
# DÉFINITION DES MODÈLES Pydantic (SCHEMAS)
# ==============================================================================
# Ces modèles définissent la "forme" des données pour l'API.
# Ils sont utilisés pour la validation, la sérialisation et la documentation.

class ProduitBase(BaseModel):
    nom: str
    prix_achat: float
    prix_vente: float
    quantite: int

class ProduitCreate(ProduitBase):
    pass

class Produit(ProduitBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class VenteBase(BaseModel):
    produit_id: int
    quantite: int

class VenteCreate(VenteBase):
    pass

class VenteUpdate(VenteBase):
    pass


class Vente(VenteBase):
    id: int
    prix_total: float
    date: datetime
    produit: Produit
    model_config = ConfigDict(from_attributes=True)

class PerteBase(BaseModel):
    produit_id: int
    quantite: int

class PerteCreate(PerteBase):
    pass

class PerteUpdate(PerteBase):
    pass


class Perte(PerteBase):
    id: int
    date: datetime
    produit: Produit
    model_config = ConfigDict(from_attributes=True)

class DashboardData(BaseModel):
    ca_today: float
    ventes_today: int
    total_stock_quantite: int
    total_stock_valeur: float
    top_ventes_today: List[dict]
    low_stock_produits: List[Produit]
    stock_par_produit: List[dict]

class AnalyseData(BaseModel):
    chiffre_affaires: float
    cogs: float
    benefice: float
    graph_data: List[dict]
    top_profitable_products: List[dict]
    top_lost_products: List[dict]

# ==============================================================================
# INITIALISATION DE L'APPLICATION
# ==============================================================================

database.create_tables()

app = FastAPI(
    title="API de Gestion de Magasin",
    description="API pour gérer les stocks, les ventes et les pertes.",
    version="2.0.0" # Version 2.0, refactorisée et robuste
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# ==============================================================================
# AUTHENTIFICATION
# ==============================================================================

FAKE_USERS_DB = {
    "admin": {
        "username": "admin",
        "hashed_password": "$2b$12$pAqiSQ2DJhVFKfD1e3dpCu0cqb6IR3DPKLuwpEqCwjuBvhUkO9Yhm",
    }
}

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = FAKE_USERS_DB.get(form_data.username)
    if not user or not auth.verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

# ==============================================================================
# ENDPOINTS DE L'API (entièrement typés et validés)
# ==============================================================================

@app.get("/", include_in_schema=False)
async def root():
    return FileResponse('static/index.html')

@app.get("/api/produits", response_model=List[Produit])
async def api_get_produits(current_user: dict = Depends(auth.get_current_user)):
    with database.get_db() as db:
        return database.get_all_produits(db)

@app.post("/api/produits", response_model=Produit)
async def api_add_produit(produit: ProduitCreate, current_user: dict = Depends(auth.get_current_user)):
    with database.get_db() as db:
        return database.add_produit(db, **produit.model_dump())

@app.put("/api/produits", response_model=Produit)
async def api_update_produit(produit: Produit, current_user: dict = Depends(auth.get_current_user)):
    with database.get_db() as db:
        updated = database.update_produit(db, produit.id, **produit.model_dump())
        if not updated:
            raise HTTPException(status_code=404, detail="Produit non trouvé")
        return updated

@app.delete("/api/produits/{produit_id}")
async def api_delete_produit(produit_id: int, current_user: dict = Depends(auth.get_current_user)):
    with database.get_db() as db:
        deleted = database.delete_produit(db, produit_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Produit non trouvé")
        return {"status": "success", "message": "Produit supprimé"}

@app.get("/api/ventes", response_model=List[Vente])
async def api_get_ventes(current_user: dict = Depends(auth.get_current_user)):
    with database.get_db() as db:
        return database.get_all_ventes(db)

@app.post("/api/ventes", response_model=Vente)
async def api_add_vente(vente: VenteCreate, current_user: dict = Depends(auth.get_current_user)):
    with database.get_db() as db:
        try:
            return database.add_vente(db, **vente.model_dump())
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/ventes/{vente_id}")
async def api_delete_vente(vente_id: int, current_user: dict = Depends(auth.get_current_user)):
    with database.get_db() as db:
        deleted = database.delete_vente(db, vente_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Vente non trouvée")
        return {"status": "success", "message": "Vente supprimée"}

@app.put("/api/ventes/{vente_id}", response_model=Vente)
async def api_update_vente(vente_id: int, vente: VenteUpdate, current_user: dict = Depends(auth.get_current_user)):
    with database.get_db() as db:
        try:
            return database.update_vente(db, vente_id, vente.produit_id, vente.quantite)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/pertes", response_model=List[Perte])
async def api_get_pertes(current_user: dict = Depends(auth.get_current_user)):
    with database.get_db() as db:
        return database.get_all_pertes(db)

@app.post("/api/pertes", response_model=Perte)
async def api_add_perte(perte: PerteCreate, current_user: dict = Depends(auth.get_current_user)):
    with database.get_db() as db:
        try:
            return database.add_perte(db, **perte.model_dump())
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/pertes/{perte_id}", response_model=Perte)
async def api_update_perte(perte_id: int, perte: PerteUpdate, current_user: dict = Depends(auth.get_current_user)):
    with database.get_db() as db:
        try:
            return database.update_perte(db, perte_id, perte.produit_id, perte.quantite)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/pertes/{perte_id}")
async def api_delete_perte(perte_id: int, current_user: dict = Depends(auth.get_current_user)):
    with database.get_db() as db:
        deleted = database.delete_perte(db, perte_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Perte non trouvée")
        return {"status": "success", "message": "Perte supprimée"}

@app.get("/api/dashboard", response_model=DashboardData)
async def api_get_dashboard_kpis(current_user: dict = Depends(auth.get_current_user)):
    with database.get_db() as db:
        return database.get_dashboard_kpis(db)

@app.get("/api/analyse", response_model=AnalyseData)
async def api_get_analyse(start_date: str, end_date: str, current_user: dict = Depends(auth.get_current_user)):
    with database.get_db() as db:
        try:
            start_date_iso = f"{start_date}T00:00:00"
            end_date_iso = f"{end_date}T23:59:59"
            return database.get_analyse_financiere(db, start_date_iso, end_date_iso)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse: {e}")

@app.get("/api/export")
async def api_export_data(data_type: str, file_format: str, current_user: dict = Depends(auth.get_current_user)):
    with database.get_db() as db:
        if data_type == "stock":
            data = database.get_all_produits(db)
            records = [p.model_dump() for p in data]
        elif data_type == "ventes":
            data = database.get_all_ventes(db)
            records = [v.model_dump() for v in data]
        elif data_type == "pertes":
            data = database.get_all_pertes(db)
            records = [p.model_dump() for p in data]
        else:
            raise HTTPException(status_code=400, detail="Type de données non valide.")

    df = pd.DataFrame(records)

    if file_format == "excel":
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name=data_type.capitalize())
        media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        filename = f"export_{data_type}.xlsx"
        content = output.getvalue()
    elif file_format == "pdf":
        html = f"<h1>Rapport - {data_type.capitalize()}</h1>{df.to_html(index=False)}"
        content = HTML(string=html).write_pdf()
        media_type = 'application/pdf'
        filename = f"export_{data_type}.pdf"
    else:
        raise HTTPException(status_code=400, detail="Format de fichier non valide.")

    headers = {'Content-Disposition': f'attachment; filename="{filename}"'}
    return StreamingResponse(io.BytesIO(content), media_type=media_type, headers=headers)