import requests

BASE_URL = "http://127.0.0.1:5000"

# 1. Création d'un utilisateur admin
response = requests.post(
    f"{BASE_URL}/api/auth/register",
    json={
        "email": "admin@digimarket.com",
        "mot_de_passe": "dm123",
        "nom": "AdminJoe",
        "role": "admin"
    }
)
print("1 - Register admin :", response.status_code)
print(response.json())
print()

# 2. login admin
response = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={
        "email": "admin@digimarket.com",
        "mot_de_passe": "dm123"
    }
)
print("2 - Login :", response.status_code)
data = response.json()
print(data)
token = data.get("token")
print()

# 3. Ajout d'un produit
headers = {"Authorization": f"Bearer {token}"}
response = requests.post(
    f"{BASE_URL}/api/produits",
    json={
        "nom": "EX DISPLAY : MSI PRO 16",
        "description": "Flex-036AU 15.6 MULTITOUCH",
        "prix": 499.00,
        "quantite_stock": 10,
        "categorie": "All-In-One"
    },
    headers=headers
)
print("3 - Création produit 1 :", response.status_code)
print(response.json())

# 4. Création d'un deuxième produit
response = requests.post(
    f"{BASE_URL}/api/produits",
    json={
        "nom": "Souris",
        "prix": 15.50,
        "description": "Souris sans fil",
        "quantite_stock": 5,
        "categorie": "Peripherique"
    },
    headers=headers
)
print("4 - Création produit 2 :", response.status_code)
print(response.json())
print()

# 5. Création d'un utilisateur client
response = requests.post(
    f"{BASE_URL}/api/auth/register",
    json={
        "email": "JoeClient@test.com",
        "mot_de_passe": "jc123",
        "nom": "Joe Client"
    }
)
print("5 - Register client :", response.status_code)
print(response.json())
print()

# 6. Login client
response = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={
        "email": "JoeClient@test.com",
        "mot_de_passe": "jc123"
    }
)
data = response.json()
print("6 - Login client :", response.status_code)
token_client = data.get("token")
headers_client = {"Authorization": f"Bearer {token_client}"}
print()

# 7. Passer une commande
response = requests.post(
    f"{BASE_URL}/api/commandes",
    json={
        "adresse_livraison": "60 rue François 1er, 75008 Paris",
        "produits": [
            {"produit_id": 1, "quantite": 2},
            {"produit_id": 2, "quantite": 1}
        ]
    },
    headers=headers_client
)
print("7 - Commande :", response.status_code)
print(response.json())
print()

# 8. Vérification mise à jour du stock
response = requests.get(f"{BASE_URL}/api/produits/1")
print("8 - Stock produit 1 après commande :", response.json().get("quantite_stock"))
print()