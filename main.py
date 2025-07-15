from fastapi import FastAPI, HTTPException
import sqlite3
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel
import database
import pandas as pd
from weasyprint import HTML
import io

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

# --- API Endpoints (seront ajoutés ici) ---

# --- Endpoints pour les PRODUITS ---
@app.get("/api/produits")
async def api_get_produits():
    produits = database.get_all_produits()
    return JSONResponse(content=produits)

@app.post("/api/produits")
async def api_add_produit(produit: Produit):
    try:
        new_id = database.add_produit(produit.nom, produit.prix_achat, produit.prix_vente, produit.quantite)
        return {"status": "success", "message": "Produit ajouté avec succès.", "id": new_id}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Un produit avec ce nom existe déjà.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur: {e}")

@app.put("/api/produits")
async def api_update_produit(produit: ProduitUpdate):
    try:
        database.update_produit(produit.id, produit.nom, produit.prix_achat, produit.prix_vente, produit.quantite)
        return {"status": "success", "message": "Produit mis à jour avec succès."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur: {e}")

@app.delete("/api/produits/{produit_id}")
async def api_delete_produit(produit_id: int):
    try:
        database.delete_produit(produit_id)
        return {"status": "success", "message": "Produit supprimé avec succès."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur: {e}")


# --- Endpoints pour les VENTES ---
@app.get("/api/ventes")
async def api_get_ventes():
    ventes = database.get_all_ventes()
    return JSONResponse(content=ventes)

@app.post("/api/ventes")
async def api_add_vente(vente: Vente):
    try:
        database.add_vente(vente.produit_id, vente.quantite)
        return {"status": "success", "message": "Vente enregistrée avec succès."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erreur interne du serveur.")


# --- Endpoints pour les PERTES ---
@app.get("/api/pertes")
async def api_get_pertes():
    pertes = database.get_all_pertes()
    return JSONResponse(content=pertes)

@app.post("/api/pertes")
async def api_add_perte(perte: Perte):
    try:
        database.add_perte(perte.produit_id, perte.quantite)
        return {"status": "success", "message": "Perte enregistrée avec succès."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erreur interne du serveur.")


# --- Endpoint pour l'ANALYSE ---
@app.get("/api/analyse")
async def api_get_analyse(start_date: str, end_date: str):
    try:
        data = database.get_analyse_financiere(start_date, end_date)
        return JSONResponse(content=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Endpoint pour le TABLEAU DE BORD ---
@app.get("/api/dashboard")
async def api_get_dashboard_kpis():
    try:
        kpis = database.get_dashboard_kpis()
        return JSONResponse(content=kpis)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Endpoint pour l'EXPORT ---
@app.get("/api/export")
async def api_export_data(data_type: str, file_format: str):
    data_fetchers = {
        "stock": database.get_all_produits,
        "ventes": database.get_all_ventes,
        "pertes": database.get_all_pertes
    }

    if data_type not in data_fetchers:
        raise HTTPException(status_code=400, detail="Type de données non valide.")

    data = data_fetchers[data_type]()
    df = pd.DataFrame(data)

    if file_format == "excel":
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name=data_type.capitalize())
        
        headers = {
            'Content-Disposition': f'attachment; filename="export_{data_type}.xlsx"'
        }
        return StreamingResponse(io.BytesIO(output.getvalue()), media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers=headers)

    elif file_format == "pdf":
        html_string = f"""
        <html>
            <head><title>Export {data_type.capitalize()}</title></head>
            <body>
                <h1>Rapport - {data_type.capitalize()}</h1>
                {df.to_html(index=False)}
            </body>
        </html>
        """
        pdf_bytes = HTML(string=html_string).write_pdf()
        headers = {
            'Content-Disposition': f'attachment; filename="export_{data_type}.pdf"'
        }
        return StreamingResponse(io.BytesIO(pdf_bytes), media_type='application/pdf', headers=headers)

    else:
        raise HTTPException(status_code=400, detail="Format de fichier non valide.")


# Exemple pour lancer le serveur (à taper dans le terminal):
# uvicorn main:app --reload
