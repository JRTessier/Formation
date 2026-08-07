from flask import Blueprint, request, jsonify
from models import db, Utilisateur, Produit, Commande, LigneCommande
from auth_utils import require_authentication, require_admin, get_token_from_header, decode_token

commandes_bp = Blueprint('commandes', __name__, url_prefix='/api/commandes')

# Récupérer la liste des commandes - Admin voit tout, client voit ses commandes
@commandes_bp.route('', methods=["GET"])
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
@commandes_bp.route('/<int:id>', methods=["GET"])
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

# Créer une nouvelle commande
@commandes_bp.route('', methods=["POST"])
@require_authentication
def order_create():
    token = get_token_from_header()
    decoded_token = decode_token(token)
    user_email = decoded_token.get("user")

    data = request.get_json()
    if not data or not data.get("adresse_livraison"):
        return jsonify({"error": "L'adresse de livraison est obligatoire."}), 400

    produits_commandes = data.get("produits")
    if not produits_commandes or not isinstance(produits_commandes, list) or len(produits_commandes) == 0:
        return jsonify({"error": "La commande doit contenir au moins un produit."}), 400

    utilisateur = Utilisateur.query.filter_by(email=user_email).first()
    if not utilisateur:
        return jsonify({"error": "Utilisateur non trouvé."}), 404

    # Verification de chaque ligne avant toute modification (produit existe et stock suffisant)
    for item in produits_commandes:
        produit_id = item.get("produit_id")
        quantite = item.get("quantite")

        if not produit_id or not quantite or quantite <= 0:
            return jsonify({"error": "Chaque produit doit avoir un produit_id et une quantite valide."}), 400

        produit = Produit.query.get(produit_id)
        if produit is None:
            return jsonify({"error": f"Produit {produit_id} introuvable."}), 404

        if produit.quantite_stock < quantite:
            return jsonify({
                "error": f"Stock insuffisant pour le produit '{produit.nom}'. Disponible : {produit.quantite_stock}, demandé : {quantite}."}), 400

    # Création de la commande
    try:
        new_order = Commande(
            utilisateur_id=utilisateur.id,
            adresse_livraison=data.get("adresse_livraison"),
            statut="en_attente"
        )
        db.session.add(new_order)
        db.session.flush()

        lignes_creees = []
        for item in produits_commandes:
            produit = Produit.query.get(item.get("produit_id"))
            quantite = item.get("quantite")

            nouvelle_ligne = LigneCommande(
                commande_id=new_order.id,
                produit_id=produit.id,
                quantite=quantite,
                prix_unitaire=produit.prix
            )
            db.session.add(nouvelle_ligne)
            lignes_creees.append(nouvelle_ligne)

            # Mise à jour du stock du produit
            produit.quantite_stock -= quantite

        db.session.commit()

        return jsonify({
            "message": "Commande créée avec succès.",
            "commande": {
                "id": new_order.id,
                "utilisateur_id": new_order.utilisateur_id,
                "date_commande": new_order.date_commande.isoformat(),
                "adresse_livraison": new_order.adresse_livraison,
                "statut": new_order.statut,
                "lignes": [
                    {
                        "produit_id": ligne.produit_id,
                        "quantite": ligne.quantite,
                        "prix_unitaire": ligne.prix_unitaire
                    }
                    for ligne in lignes_creees
                ]
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Erreur lors de la création de la commande."}), 500

# Modifier le statut d'une commande - Admin only
@commandes_bp.route('/<int:id>', methods=["PATCH"])
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
@commandes_bp.route('/<int:id>/lignes', methods=["GET"])
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