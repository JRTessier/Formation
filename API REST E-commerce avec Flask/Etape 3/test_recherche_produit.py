# Recherche par nom
import requests

BASE_URL = "http://127.0.0.1:5000"

response = requests.get(f"{BASE_URL}/api/produits?nom=sou") # recherche correspondance partielle (sou / souris) et insensible à la casse
print("Recherche 'sou' :", response.status_code)
print(response.json())
print()

# Recherche par catégorie
response = requests.get(f"{BASE_URL}/api/produits?categorie=All-In-One")
print("Recherche catégorie :", response.status_code)
print(response.json())
print()

# Sans filtre (comportement inchangé)
response = requests.get(f"{BASE_URL}/api/produits")
print("Liste complète :", response.status_code)
print(len(response.json().get("produits")), "produits trouvés")