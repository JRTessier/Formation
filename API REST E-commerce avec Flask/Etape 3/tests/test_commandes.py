def test_create_order_success(client, admin_token):
    # Créer un produit avec du stock
    client.post('/api/produits',
        json={"nom": "Clavier", "prix": 29.99, "quantite_stock": 10, "categorie": "Peripherique"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    # Créer un client et se connecter
    client.post('/api/auth/register', json={
        "email": "client@exemple.com", "mot_de_passe": "test123", "nom": "Client Test"
    })
    login = client.post('/api/auth/login', json={
        "email": "client@exemple.com", "mot_de_passe": "test123"
    })
    token_client = login.get_json()["token"]

    # Passer une commande
    response = client.post('/api/commandes',
        json={
            "adresse_livraison": "12 rue de la Paix, Paris",
            "produits": [{"produit_id": 1, "quantite": 2}]
        },
        headers={"Authorization": f"Bearer {token_client}"}
    )
    assert response.status_code == 201
    assert response.get_json()["commande"]["statut"] == "en_attente"

def test_create_order_insufficient_stock(client, admin_token):
    client.post('/api/produits',
        json={"nom": "Souris", "prix": 15.5, "quantite_stock": 3, "categorie": "Peripherique"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    client.post('/api/auth/register', json={
        "email": "client2@exemple.com", "mot_de_passe": "test123", "nom": "Client Test"
    })
    login = client.post('/api/auth/login', json={
        "email": "client2@exemple.com", "mot_de_passe": "test123"
    })
    token_client = login.get_json()["token"]

    response = client.post('/api/commandes',
        json={
            "adresse_livraison": "Test",
            "produits": [{"produit_id": 1, "quantite": 100}]
        },
        headers={"Authorization": f"Bearer {token_client}"}
    )
    assert response.status_code == 400

def test_order_decreases_stock(client, admin_token):
    client.post('/api/produits',
        json={"nom": "Ecran", "prix": 199.0, "quantite_stock": 10, "categorie": "Ecran"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    client.post('/api/auth/register', json={
        "email": "client3@exemple.com", "mot_de_passe": "test123", "nom": "Client Test"
    })
    login = client.post('/api/auth/login', json={
        "email": "client3@exemple.com", "mot_de_passe": "test123"
    })
    token_client = login.get_json()["token"]

    client.post('/api/commandes',
        json={
            "adresse_livraison": "Test",
            "produits": [{"produit_id": 1, "quantite": 4}]
        },
        headers={"Authorization": f"Bearer {token_client}"}
    )

    response = client.get('/api/produits/1')
    assert response.get_json()["quantite_stock"] == 6  # 10 - 4

def test_client_cannot_see_others_orders(client, admin_token):
    # Client A passe une commande
    client.post('/api/produits',
        json={"nom": "Casque", "prix": 49.0, "quantite_stock": 10, "categorie": "Audio"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    client.post('/api/auth/register', json={
        "email": "clientA@exemple.com", "mot_de_passe": "test123", "nom": "Client A"
    })
    login_a = client.post('/api/auth/login', json={
        "email": "clientA@exemple.com", "mot_de_passe": "test123"
    })
    token_a = login_a.get_json()["token"]

    order = client.post('/api/commandes',
        json={"adresse_livraison": "Test", "produits": [{"produit_id": 1, "quantite": 1}]},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    order_id = order.get_json()["commande"]["id"]

    # Client B essaie de voir la commande de Client A
    client.post('/api/auth/register', json={
        "email": "clientB@exemple.com", "mot_de_passe": "test123", "nom": "Client B"
    })
    login_b = client.post('/api/auth/login', json={
        "email": "clientB@exemple.com", "mot_de_passe": "test123"
    })
    token_b = login_b.get_json()["token"]

    response = client.get(f'/api/commandes/{order_id}',
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert response.status_code == 403