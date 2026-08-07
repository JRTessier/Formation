def test_register_success(client):
    response = client.post('/api/auth/register', json={
        "email": "test@exemple.com",
        "mot_de_passe": "test123",
        "nom": "Test User"
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data["utilisateur"]["email"] == "test@exemple.com"
    assert data["utilisateur"]["role"] == "client"

def test_register_missing_field(client):
    response = client.post('/api/auth/register', json={
        "email": "test@exemple.com"
        # mot_de_passe et nom manquants
    })
    assert response.status_code == 400

def test_register_duplicate_email(client):
    client.post('/api/auth/register', json={
        "email": "test@exemple.com",
        "mot_de_passe": "test123",
        "nom": "Test User"
    })
    response = client.post('/api/auth/register', json={
        "email": "test@exemple.com",
        "mot_de_passe": "autre",
        "nom": "Autre User"
    })
    assert response.status_code == 409

def test_login_success(client):
    client.post('/api/auth/register', json={
        "email": "test@exemple.com",
        "mot_de_passe": "test123",
        "nom": "Test User"
    })
    response = client.post('/api/auth/login', json={
        "email": "test@exemple.com",
        "mot_de_passe": "test123"
    })
    assert response.status_code == 200
    assert "token" in response.get_json()

def test_login_wrong_password(client):
    client.post('/api/auth/register', json={
        "email": "test@exemple.com",
        "mot_de_passe": "test123",
        "nom": "Test User"
    })
    response = client.post('/api/auth/login', json={
        "email": "test@exemple.com",
        "mot_de_passe": "mauvais_mdp"
    })
    assert response.status_code == 401