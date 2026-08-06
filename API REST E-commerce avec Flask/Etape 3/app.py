import jwt

from flask import Flask, request, jsonify
from datetime import datetime, timedelta
from models import db, Utilisateur, Produit, Commande, LigneCommande
from functools import wraps

# Clé secrète JWT
# Dans un vrai projet, à déplacer dans une variable d'environnement (.env) ou config.py.
JWT_SECRET = "d3fb12750c2eff92120742e1b334479e"

app = Flask(__name__)

############################################
### Connexion et génération de token JWT ###
############################################
def decode_token(token):
    try:
        return jwt.decode(
            token,
            JWT_SECRET,
            algorithms="HS256"
        )
    except Exception:
        print("Jeton JWT invalide.")
        return

def get_token_from_header():
    authorization_header = request.headers.get("Authorization", "")
    if authorization_header.startswith("Bearer "):
        return authorization_header[7:]  # Supprime "Bearer " du début
    return authorization_header

def require_authentication(f):
    @wraps(f)
    def wrapper(**kwargs):
        token = get_token_from_header()
        if not decode_token(token):
            return {"error": "Jeton d'accès invalide."}, 401
        return f(**kwargs)
    return wrapper

@app.route('/api/auth/login', methods=["POST"])
def generate_token():
    body = request.get_json()

    if not body or not body.get("email") or not body.get("mot_de_passe"):
        return jsonify({"error": "Email et mot de passe sont requis."}), 400

    utilisateur = Utilisateur.query.filter_by(email=body.get("email")).first()
    if not utilisateur or utilisateur.mot_de_passe != body.get("mot_de_passe"):
        return jsonify({"error": "Email ou mot de passe invalide."}), 401

    token = jwt.encode(
        {
            "exp": datetime.utcnow() + timedelta(hours=1),
            "user": utilisateur.email,
            "role": utilisateur.role
        },
        JWT_SECRET,
        algorithm="HS256"
    )
    return jsonify({"token": token}), 200

@app.route('/predict', methods=["GET"])
@require_authentication
def predict():
    return {"message": "Ok !"}, 200

###########################################
### Inscription d'un nouvel utilisateur ###
###########################################
@app.route('/api/auth/register', methods=["POST"])
def register_user():
    data = request.get_json()

    # Vérification des champs obligatoires
    if not data or not data.get("email") or not data.get("mot_de_passe") or not data.get("nom"):
        return jsonify({"error": "Tous les champs sont obligatoires."}), 400

    email = data.get("email")
    mot_de_passe = data.get("mot_de_passe")
    nom = data.get("nom")
    role = data.get("role", "client")  # Rôle par défaut : client

    # Vérification de l'email unique
    utilisateur_existant = Utilisateur.query.filter_by(email=email).first()
    if utilisateur_existant:
        return jsonify({"error": "Un utilisateur avec cet email existe déjà."}), 409

    # Hachage du mot de passe
    mot_de_passe_hache = mot_de_passe  # A remplacer par un vrai hachage dans une application réelle

    # Création du nouvel utilisateur
    nouvel_utilisateur = Utilisateur(
        email=email,
        mot_de_passe=mot_de_passe_hache,
        nom=nom,
        role=role
    )

    # Ajout de l'utilisateur à la base de données
    try:
        db.session.add(nouvel_utilisateur)
        db.session.commit()
        return jsonify({
                "message": "Utilisateur enregistré avec succès.",
                "utilisateur": {
                    "id": nouvel_utilisateur.id,
                    "email": nouvel_utilisateur.email,
                    "nom": nouvel_utilisateur.nom,
                    "role": nouvel_utilisateur.role,
                    "date_creation": nouvel_utilisateur.date_creation.isoformat()
                }
            }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Erreur lors de l'enregistrement de l'utilisateur."}), 500

# Decorateur pour gatekeeper les routes nécessitant un rôle administrateur
def require_admin(f):
    @wraps(f)
    def wrapper(**kwargs):
        token = get_token_from_header()
        decoded_token = decode_token(token)
        if not decoded_token:
            return jsonify({"error": "Jeton d'accès invalide."}), 401
        if decoded_token.get("user") is None:
            return jsonify({"error": "Jeton d'accès invalide."}), 401
        if decoded_token.get("role") != "admin":
            return jsonify({"error": "Accès refusé. Rôle administrateur requis."}), 403
        return f(**kwargs)
    return wrapper

###############################
### Routes API des produits ###
###############################
# Récupérer la liste des produits
@app.route('/api/produits', methods=["GET"])
def product_list():
    produits = Produit.query.all()

    liste_produits = [
        {
            "id": produit.id,
            "nom": produit.nom,
            "description": produit.description,
            "prix": produit.prix,
            "quantite_stock": produit.quantite_stock,
            "date_creation": produit.date_creation.isoformat()
        }
        for produit in produits
    ]

    return jsonify({
        "message": "Liste des produits",
        "produits": liste_produits
    }), 200

# Récupérer un produit spécifique
@app.route('/api/produits/<int:id>', methods=["GET"])
def product_get(id):
    this_product = Produit.query.get(id)

    if this_product is None:
        return jsonify({"error": "Produit non trouvé."}), 404

    return jsonify({
        "id": this_product.id,
        "nom": this_product.nom,
        "description": this_product.description,
        "prix": this_product.prix,
        "quantite_stock": this_product.quantite_stock,
        "date_creation": this_product.date_creation.isoformat()
    }), 200

# Ajouter un nouveau produit - Admin only
@app.route('/api/produits', methods=["POST"])
@require_admin
def product_create():
    data = request.get_json()
    if not data or not data.get("nom") or not data.get("prix") or not data.get("quantite_stock"):
        return jsonify({"error": "Tous les champs obligatoires ne sont pas remplis."}), 400

    new_product = Produit(
        nom=data.get("nom"),
        description=data.get("description", ""),
        prix=data.get("prix"),
        quantite_stock=data.get("quantite_stock")
    )

    try:
        db.session.add(new_product)
        db.session.commit()
        return jsonify({
            "message": "Produit créé avec succès.",
            "produit": {
                "id": new_product.id,
                "nom": new_product.nom,
                "description": new_product.description,
                "prix": new_product.prix,
                "quantite_stock": new_product.quantite_stock,
                "date_creation": new_product.date_creation.isoformat()
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Erreur lors de la création du produit."}), 500

# Mettre à jour un produit existant - Admin only
@app.route('/api/produits/<int:id>', methods=["PUT"])
@require_admin
def product_update(id):
    data = request.get_json()
    if not data or not data.get("nom") or not data.get("prix") or not data.get("quantite_stock"):
        return jsonify({"error": "Tous les champs obligatoires ne sont pas remplis."}), 400

    product_to_update = Produit.query.get(id)
    if product_to_update is None:
        return jsonify({"error": "Produit non trouvé."}), 404

    product_to_update.nom = data.get("nom")
    product_to_update.description = data.get("description", "")
    product_to_update.prix = data.get("prix")
    product_to_update.quantite_stock = data.get("quantite_stock")

    try:
        db.session.commit()
        return jsonify({
            "message": "Produit mis à jour avec succès.",
            "produit": {
                "id": product_to_update.id,
                "nom": product_to_update.nom,
                "description": product_to_update.description,
                "prix": product_to_update.prix,
                "quantite_stock": product_to_update.quantite_stock,
                "date_creation": product_to_update.date_creation.isoformat()
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Erreur lors de la mise à jour du produit."}), 500

# Supprimer un produit - Admin only
@app.route('/api/produits/<int:id>', methods=["DELETE"])
@require_admin
def product_delete(id):
    product_to_delete = Produit.query.get(id)
    if product_to_delete is None:
        return jsonify({"error": "Produit non trouvé."}), 404

    try:
        db.session.delete(product_to_delete)
        db.session.commit()
        return jsonify({"message": "Produit supprimé avec succès."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Erreur lors de la suppression du produit."}), 500

###########################################
### Routes API de gestion des commandes ###
###########################################
# Récupérer la liste des commandes - Admin voit tout, client voit ses commandes
@app.route('/api/commandes', methods=["GET"])
@require_authentication
def order_list():
    token = get_token_from_header()
    decoded_token = decode_token(token)
    user_email = decoded_token.get("user")
    user_role = decoded_token.get("role")

    if user_role == "admin":
        commandes = Commande.query.all()
    else:
        utilisateur = Utilisateur.query.filter_by(email=user_email).first()
        commandes = Commande.query.filter_by(utilisateur_id=utilisateur.id).all()

    liste_commandes = [
        {
            "id": commande.id,
            "utilisateur_id": commande.utilisateur_id,
            "date_commande": commande.date_commande.isoformat(),
            "adresse_livraison": commande.adresse_livraison,
            "statut": commande.statut
        }
        for commande in commandes
    ]

    return jsonify({
        "message": "Liste des commandes",
        "commandes": liste_commandes
    }), 200

# Récupérer une commande spécifique
@app.route('/api/commandes/<int:id>', methods=["GET"])
@require_authentication
def order_get(id):
    token = get_token_from_header()
    decoded_token = decode_token(token)
    user_email = decoded_token.get("user")
    user_role = decoded_token.get("role")

    commande = Commande.query.get(id)
    if commande is None:
        return jsonify({"error": "Commande non trouvée."}), 404

    if user_role != "admin":
        utilisateur = Utilisateur.query.filter_by(email=user_email).first()
        if commande.utilisateur_id != utilisateur.id:
            return jsonify({"error": "Accès refusé à cette commande."}), 403

    return jsonify({
        "id": commande.id,
        "utilisateur_id": commande.utilisateur_id,
        "date_commande": commande.date_commande.isoformat(),
        "adresse_livraison": commande.adresse_livraison,
        "statut": commande.statut
    }), 200

## Créer une nouvelle commande
@app.route('/api/commandes', methods=["POST"])
@require_authentication
def order_create():
    token = get_token_from_header()
    decoded_token = decode_token(token)
    user_email = decoded_token.get("user")

    data = request.get_json()
    if not data or not data.get("adresse_livraison"):
        return jsonify({"error": "L'adresse de livraison est obligatoire."}), 400

    utilisateur = Utilisateur.query.filter_by(email=user_email).first()
    if not utilisateur:
        return jsonify({"error": "Utilisateur non trouvé."}), 404

    new_order = Commande(
        utilisateur_id=utilisateur.id,
        adresse_livraison=data.get("adresse_livraison"),
        statut="en attente"
    )

    try:
        db.session.add(new_order)
        db.session.commit()
        return jsonify({
            "message": "Commande créée avec succès.",
            "commande": {
                "id": new_order.id,
                "utilisateur_id": new_order.utilisateur_id,
                "date_commande": new_order.date_commande.isoformat(),
                "adresse_livraison": new_order.adresse_livraison,
                "statut": new_order.statut
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Erreur lors de la création de la commande."}), 500

# Modifier le statut d'une commande - Admin only
@app.route('/api/commandes/<int:id>', methods=["PATCH"])
@require_admin
def order_update_status(id):
    data = request.get_json()
    if not data or not data.get("statut"):
        return jsonify({"error": "Le statut est obligatoire."}), 400

    commande = Commande.query.get(id)
    if commande is None:
        return jsonify({"error": "Commande non trouvée."}), 404

    commande.statut = data.get("statut")

    try:
        db.session.commit()
        return jsonify({
            "message": "Statut de la commande mis à jour avec succès.",
            "commande": {
                "id": commande.id,
                "utilisateur_id": commande.utilisateur_id,
                "date_commande": commande.date_commande.isoformat(),
                "adresse_livraison": commande.adresse_livraison,
                "statut": commande.statut
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Erreur lors de la mise à jour du statut de la commande."}), 500

# Consulter les lignes d'une commande
@app.route('/api/commandes/<int:id>/lignes', methods=["GET"])
@require_authentication
def order_get_lines(id):
    token = get_token_from_header()
    decoded_token = decode_token(token)
    user_email = decoded_token.get("user")
    user_role = decoded_token.get("role") # Pas spécifié dans la doc mais on assume qu'un admin à accès à toutes les lignes d'une commande

    commande = Commande.query.get(id)
    if commande is None:
        return jsonify({"error": "Commande non trouvée."}), 404


    if user_role != "admin":
        utilisateur = Utilisateur.query.filter_by(email=user_email).first()
        if commande.utilisateur_id != utilisateur.id:
            return jsonify({"error": "Accès refusé à cette commande."}), 403

    lignes = LigneCommande.query.filter_by(commande_id=commande.id).all()

    liste_lignes = [
        {
            "id": ligne.id,
            "commande_id": ligne.commande_id,
            "produit_id": ligne.produit_id,
            "quantite": ligne.quantite,
            "prix_unitaire": ligne.prix_unitaire
        }
        for ligne in lignes
    ]

    return jsonify({
        "message": "Lignes de la commande",
        "lignes": liste_lignes
    }), 200