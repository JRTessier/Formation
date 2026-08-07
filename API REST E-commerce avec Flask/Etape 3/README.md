# DIGIMARKET - API REST E-commerce

API REST développée avec Flask permettant la gestion des utilisateurs, des produits et des commandes pour une plateforme e-commerce, avec authentification par tokens JWT.

## Stack technique

- **Langage** : Python
- **Framework** : Flask
- **Base de données** : SQLite
- **ORM** : SQLAlchemy (Flask-SQLAlchemy)
- **Authentification** : JWT (JSON Web Tokens)
- **Hachage des mots de passe** : Werkzeug Security

## Structure du projet

```
.
├── app.py                     # Point d'entrée de l'application
├── models.py                  # Modèles SQLAlchemy (Utilisateur, Produit, Commande, LigneCommande)
├── config.py                  # Configuration (clé JWT, URI base de données)
├── auth_utils.py              # Fonctions et décorateurs d'authentification/autorisation
├── routes/
│   ├── __init__.py
│   ├── auth_routes.py         # Routes d'inscription et de connexion
│   ├── produits_routes.py     # Routes du catalogue produits
│   └── commandes_routes.py    # Routes de gestion des commandes
├── *test.py                   # Scripts de test manuel de l'API
└── requirements.txt           # Dépendances Python
```

## Installation

### 1. Cloner le dépôt

```
git clone <url-du-repo>
cd <nom-du-dossier>
```

### 2. Créer et activer un environnement virtuel

```
python -m venv venv
```

*Activation pour Windows (PowerShell) :*
```
venv\Scripts\Activate.ps1
```

*Activation pour Mac/Linux :*
```
source venv/bin/activate
```

### 3. Installer les dépendances

```
pip install -r requirements.txt
```

### 4. Lancer l'application

```
flask run --debug
```

L'API est accessible sur ["http://127.0.0.1:5000"].

La base de données SQLite "digimarket.db" est créée automatiquement au démarrage, dans le dossier `instance/`.

## Authentification

L'API utilise des tokens JWT. Après connexion, le token doit être fourni dans l'en-tête "Authorization" de chaque requête vers une route protégée :
`Authorization: Bearer <token>`

Deux niveaux de protection existent :
- **Utilisateur connecté** :

    Accès aux routes nécessitant un compte (ex. consultation de ses propres commandes).
- **Administrateur uniquement** :

    Gestion du catalogue produits et des statuts de commande.

## Documentation de l'API

### Authentification/Autorisation

- Inscription d'un nouvel utilisateur : `POST /api/auth/register` (public)

    *Corps de la requête :*
    ```json
    {
        "email": "client@exemple.com",
        "mot_de_passe": "fire123",
        "nom": "Maurice Moss",
        "role": "client"
    }
    ```

- Connexion et génération de token JWT : `POST /api/auth/login` (public)

    *Corps de la requête :*
    ```json
    {
        "email": "client@exemple.com",
        "mot_de_passe": "fire123"
    }
    ```

### Produits

- Récupérer la liste des produits : `GET /api/produits` (public)
    
- Récupérer un produit spécifique : `GET /api/produits/{id}` (public)
    
- Créer un nouveau produit : `POST /api/produits` (Admin)
    
    *Corps de la requête :*
    ```json
    {
        "nom": "EX DISPLAY : MSI PRO",
        "description": "Flex-036AU 15.6",
        "categorie": "All-In-One",
        "prix": 499.99,
        "quantite_stock": 25
    }
    ```
- Modifier un produit existant : `PUT /api/produits/{id}` (Admin)

    *Corps de la requête :*
    ```json
    {
        "nom": "EX DISPLAY : MSI PRO 16",
        "description": "Flex-036AU 15.6 MULTITOUCH",
        "categorie": "All-In-One",
        "prix": 449.99,
        "quantite_stock": 20
    }
    ```
    
- Supprimer un produit : `DELETE /api/produits/{id}` (Admin)

### Commandes

- Récupérer la liste des commandes: `GET /api/commandes` (Admin voit tout, client voit ses commandes)
- Récupérer une commande spécifique : `GET /api/commandes/{id}` (User ou admin)
- Créer une nouvelle commande : `POST /api/commandes` (User)
    
    *Corps de la requête :*
    ```json
    {
        "adresse_livraison": "60 rue François 1er, 75008 Paris",
        "produits": [
            { "produit_id": 1, "quantite": 2 },
            { "produit_id": 3, "quantite": 1 }
        ]
    }
    ```
- Modifier le statut d'une commande : `PATCH /api/commandes/{id}` (Admin)

    *Corps de la requête :*
    ```json
    {
        "statut": "validée"
    }
    ```
- Consulter les lignes d'une commande : `GET /api/commandes/{id}/lignes` (User ou admin)