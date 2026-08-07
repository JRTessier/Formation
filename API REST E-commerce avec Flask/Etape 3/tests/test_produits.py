def test_create_product_requires_admin(client):
    # Créer un utilisateur client (non-admin)
    client.post('/api/auth/register', json={
        "email": "client@exemple.com",
        "mot_de_passe": "test123",
        "nom": "Client Test"
    })
    login = client.post('/api/auth/login', json={
        "email": "client@exemple.com",
        "mot_de_passe": "test123"
    })
    token = login.get_json()["token"]

    # Tenter de créer un produit avec un token client
    response = client.post('/api/produits',
        json={"nom": "Souris", "prix": 15.5, "quantite_stock": 5, "categorie": "Peripherique"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403

def test_create_product_as_admin(client):
    client.post('/api/auth/register', json={
        "email": "admin@exemple.com",
        "mot_de_passe": "test123",
        "nom": "Admin",
        "role": "admin"
    })
    login = client.post('/api/auth/login', json={
        "email": "admin@exemple.com",
        "mot_de_passe": "test123"
    })
    token = login.get_json()["token"]

    response = client.post('/api/produits',
        json={"nom": "Clavier", "prix": 29.99, "quantite_stock": 10, "categorie": "Peripherique"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    assert response.get_json()["produit"]["nom"] == "Clavier"

def test_list_products_public(client):
    response = client.get('/api/produits')
    assert response.status_code == 200
    assert "produits" in response.get_json()

def test_search_product_by_name(client, admin_token):
    client.post('/api/produits',
        json={"nom": "Souris sans fil", "prix": 15.5, "quantite_stock": 5, "categorie": "Peripherique"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    response = client.get('/api/produits?nom=souris')
    data = response.get_json()
    assert response.status_code == 200
    assert len(data["produits"]) == 1
    assert "Souris" in data["produits"][0]["nom"]

def test_get_product_not_found(client):
    response = client.get('/api/produits/999')
    assert response.status_code == 404