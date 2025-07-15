from fastapi.testclient import TestClient
from main import app


def test_full_app_flow():
    client = TestClient(app)
    # 1. Connexion pour obtenir un token
    login_data = {
        "username": "admin",
        "password": "Dakar2026@"
    }
    response = client.post("/token", data=login_data)
    assert response.status_code == 200
    token_data = response.json()
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Tester chaque endpoint GET pour s'assurer qu'il ne plante pas et renvoie du JSON
    endpoints_to_test = [
        "/api/dashboard",
        "/api/produits",
        "/api/ventes",
        "/api/pertes",
        "/api/analyse?start_date=2023-01-01&end_date=2023-01-31" # Exemple de dates
    ]

    for endpoint in endpoints_to_test:
        print(f"Testing endpoint: {endpoint}")
        response = client.get(endpoint, headers=headers)
        
        # Vérification cruciale : le statut doit être 200 OK
        assert response.status_code == 200, f"Endpoint {endpoint} failed with status {response.status_code} and message {response.text}"
        
        # Vérification cruciale : la réponse doit être du JSON valide
        try:
            response.json()
        except ValueError:
            pytest.fail(f"Endpoint {endpoint} did not return valid JSON.")

    print("All GET endpoints returned valid JSON with a 200 OK status.")
