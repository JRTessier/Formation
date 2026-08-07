from flask import Blueprint, request, jsonify
from models import db, Produit
from auth_utils import require_admin

produits_bp = Blueprint('produits', __name__, url_prefix='/api/produits')

# Récupérer la liste des produits
@produits_bp.route('', methods=["GET"])
def product_list():
    query = Produit.query

    nom_recherche = request.args.get("nom")
    if nom_recherche:
        query = query.filter(Produit.nom.ilike(f"%{nom_recherche}%"))

    categorie_recherche = request.args.get("categorie")
    if categorie_recherche:
        query = query.filter(Produit.categorie.ilike(f"%{categorie_recherche}%"))

    produits = query.all()

    liste_produits = [
        {
            "id": produit.id,
            "nom": produit.nom,
            "description": produit.description,
            "categorie": produit.categorie,
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
@produits_bp.route('/<int:id>', methods=["GET"])
def product_get(id):
    this_product = Produit.query.get(id)

    if this_product is None:
        return jsonify({"error": "Produit non trouvé."}), 404

    return jsonify({
        "id": this_product.id,
        "nom": this_product.nom,
        "description": this_product.description,
        "categorie": this_product.categorie,
        "prix": this_product.prix, "quantite_stock": this_product.quantite_stock,
        "date_creation": this_product.date_creation.isoformat()
    }), 200

# Ajouter un nouveau produit - Admin only
@produits_bp.route('', methods=["POST"])
@require_admin
def product_create():
    data = request.get_json()
    if not data or not data.get("nom") or not data.get("prix") or not data.get("quantite_stock") or not data.get("categorie"):
        return jsonify({"error": "Tous les champs obligatoires ne sont pas remplis."}), 400

    new_product = Produit(
        nom=data.get("nom"),
        description=data.get("description", ""),
        categorie=data.get("categorie"),
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
                "categorie": new_product.categorie,
                "prix": new_product.prix, "quantite_stock": new_product.quantite_stock,
                "date_creation": new_product.date_creation.isoformat()
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Erreur lors de la création du produit."}), 500

# Mettre à jour un produit existant - Admin only
@produits_bp.route('/<int:id>', methods=["PUT"])
@require_admin
def product_update(id):
    data = request.get_json()
    if not data or not data.get("nom") or not data.get("prix") or not data.get("quantite_stock") or not data.get("categorie"):
        return jsonify({"error": "Tous les champs obligatoires ne sont pas remplis."}), 400

    product_to_update = Produit.query.get(id)
    if product_to_update is None:
        return jsonify({"error": "Produit non trouvé."}), 404

    product_to_update.nom = data.get("nom")
    product_to_update.description = data.get("description", "")
    product_to_update.categorie = data.get("categorie")
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
                "categorie": product_to_update.categorie,
                "prix": product_to_update.prix,
                "quantite_stock": product_to_update.quantite_stock,
                "date_creation": product_to_update.date_creation.isoformat()
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Erreur lors de la mise à jour du produit."}), 500

# Supprimer un produit - Admin only
@produits_bp.route('/<int:id>', methods=["DELETE"])
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