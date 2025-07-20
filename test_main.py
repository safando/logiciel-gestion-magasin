import pytest
from fastapi.testclient import TestClient
import os

# Créer le répertoire static s'il n'existe pas
if not os.path.exists('static'):
    os.makedirs('static')

from main import app

@pytest.fixture(scope="module")
def client():
    from database import Base, engine
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return TestClient(app)

def test_full_workflow(client: TestClient):
    # 1. Connexion
    login_data = {"username": "admin", "password": "Dakar2026@"}
    response = client.post("/token", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Création des produits
    p1_res = client.post("/api/produits", headers=headers, json={"nom": "Produit A", "prix_achat": 10, "prix_vente": 20, "quantite": 100})
    p2_res = client.post("/api/produits", headers=headers, json={"nom": "Produit B", "prix_achat": 15, "prix_vente": 25, "quantite": 100})
    produit1 = p1_res.json()
    produit2 = p2_res.json()

    # 3. Test des VENTES
    # Création
    vente_res = client.post("/api/ventes", headers=headers, json={"produit_id": produit1["id"], "quantite": 10})
    assert vente_res.status_code == 200
    vente1 = vente_res.json()
    assert vente1["produit"]["nom"] == "Produit A"
    assert vente1["quantite"] == 10
    # Modification
    vente_update_res = client.put(f"/api/ventes/{vente1['id']}", headers=headers, json={"produit_id": produit2["id"], "quantite": 5})
    assert vente_update_res.status_code == 200
    vente1_updated = vente_update_res.json()
    assert vente1_updated["produit"]["nom"] == "Produit B"
    assert vente1_updated["quantite"] == 5

    # 4. Test des PERTES
    # Création
    perte_res = client.post("/api/pertes", headers=headers, json={"produit_id": produit1["id"], "quantite": 20})
    assert perte_res.status_code == 200
    perte1 = perte_res.json()
    assert perte1["produit"]["nom"] == "Produit A"
    assert perte1["quantite"] == 20
    # Modification
    perte_update_res = client.put(f"/api/pertes/{perte1['id']}", headers=headers, json={"produit_id": produit2["id"], "quantite": 15})
    assert perte_update_res.status_code == 200
    perte1_updated = perte_update_res.json()
    assert perte1_updated["produit"]["nom"] == "Produit B"
    assert perte1_updated["quantite"] == 15

    # 5. Vérification finale des stocks
    produits_res = client.get("/api/produits", headers=headers)
    produits_final = produits_res.json()
    p1_final = next(p for p in produits_final if p["id"] == produit1["id"])
    p2_final = next(p for p in produits_final if p["id"] == produit2["id"])
    # Produit A: 100 (initial) - 10 (vente) + 10 (vente modifiée) - 20 (perte) + 20 (perte modifiée) = 100
    # Produit B: 100 (initial) - 5 (vente modifiée) - 15 (perte modifiée) = 80
    assert p1_final["quantite"] == 100
    assert p2_final["quantite"] == 80

    # 6. Suppression
    # Suppression de la vente modifiée
    res = client.delete(f"/api/ventes/{vente1_updated['id']}", headers=headers)
    assert res.status_code == 200
    # Suppression de la perte modifiée
    res = client.delete(f"/api/pertes/{perte1_updated['id']}", headers=headers)
    assert res.status_code == 200

    # 7. Vérification finale des stocks après suppression
    produits_res = client.get("/api/produits", headers=headers)
    produits_final_2 = produits_res.json()
    p1_final_2 = next(p for p in produits_final_2 if p["id"] == produit1["id"])
    p2_final_2 = next(p for p in produits_final_2 if p["id"] == produit2["id"])
    assert p1_final_2["quantite"] == 100 # Stock restauré
    assert p2_final_2["quantite"] == 100 # Stock restauré

    print("\n>>> All workflow tests passed successfully.")