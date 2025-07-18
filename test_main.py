import pytest
from fastapi.testclient import TestClient
from main import app

# Utiliser une base de données de test en mémoire pour l'isolation
# (Ceci sera géré par la configuration de la base de données dans database.py)

@pytest.fixture(scope="module")
def client():
    # Nettoyer la base de données de test avant de commencer
    from database import Base, engine
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return TestClient(app)

def test_full_workflow(client: TestClient):
    # 1. Connexion pour obtenir un token
    login_data = {"username": "admin", "password": "Dakar2026@"}
    response = client.post("/token", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Créer deux produits de test
    produit1_data = {"nom": "Test Produit A", "prix_achat": 10, "prix_vente": 20, "quantite": 50}
    response = client.post("/api/produits", headers=headers, json=produit1_data)
    assert response.status_code == 200
    produit1 = response.json()
    assert produit1["nom"] == produit1_data["nom"]

    produit2_data = {"nom": "Test Produit B", "prix_achat": 15, "prix_vente": 25, "quantite": 30}
    response = client.post("/api/produits", headers=headers, json=produit2_data)
    assert response.status_code == 200
    produit2 = response.json()

    # 3. Créer une perte initiale
    perte1_data = {"produit_id": produit1["id"], "quantite": 5}
    response = client.post("/api/pertes", headers=headers, json=perte1_data)
    assert response.status_code == 200
    perte1 = response.json()
    assert perte1["quantite"] == 5
    # Vérification cruciale : le nom du produit doit être correct dès la création
    assert perte1["produit"]["nom"] == produit1["nom"]

    # 4. Vérifier que le stock du produit A a bien diminué
    response = client.get(f"/api/produits", headers=headers)
    produits = response.json()
    p1_after_perte = next(p for p in produits if p["id"] == produit1["id"])
    assert p1_after_perte["quantite"] == 45 # 50 - 5

    # 5. Modifier la perte
    perte_update_data = {"produit_id": produit2["id"], "quantite": 2} # Changement de produit et de quantité
    response = client.put(f"/api/pertes/{perte1['id']}", headers=headers, json=perte_update_data)
    assert response.status_code == 200
    perte1_updated = response.json()
    
    # Vérification cruciale : le nom du produit doit être correct après la mise à jour
    assert perte1_updated["produit"]["nom"] == produit2["nom"]
    assert perte1_updated["quantite"] == 2

    # 6. Vérifier que les stocks ont été correctement ajustés
    response = client.get("/api/produits", headers=headers)
    produits_final = response.json()
    p1_final = next(p for p in produits_final if p["id"] == produit1["id"])
    p2_final = next(p for p in produits_final if p["id"] == produit2["id"])
    
    assert p1_final["quantite"] == 50 # Stock restauré
    assert p2_final["quantite"] == 28 # 30 - 2

    # 7. Vérifier que l'onglet des pertes est accessible et renvoie les bonnes données
    response = client.get("/api/pertes", headers=headers)
    assert response.status_code == 200
    pertes_final = response.json()
    assert len(pertes_final) == 1
    assert pertes_final[0]["produit"]["nom"] == produit2["nom"]

    print("\n>>> Test de workflow complet réussi. La logique de mise à jour des pertes et des stocks est correcte.")