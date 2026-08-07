import jwt
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Utilisateur
from config import JWT_SECRET

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/login', methods=["POST"])
def generate_token():
    body = request.get_json()

    if not body or not body.get("email") or not body.get("mot_de_passe"):
        return jsonify({"error": "Email et mot de passe sont requis."}), 400

    utilisateur = Utilisateur.query.filter_by(email=body.get("email")).first()
    if not utilisateur or not check_password_hash(utilisateur.mot_de_passe, body.get("mot_de_passe")):
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

@auth_bp.route('/register', methods=["POST"])
def register_user():
    data = request.get_json()

    # Vérification des champs obligatoires
    if not data or not data.get("email") or not data.get("mot_de_passe") or not data.get("nom"):
        return jsonify({"error": "Tous les champs sont obligatoires."}), 400

    email = data.get("email")
    mot_de_passe = data.get("mot_de_passe")
    nom = data.get("nom")
    role = data.get("role", "client") # Rôle par défaut : client

    # Vérification de l'email unique
    utilisateur_existant = Utilisateur.query.filter_by(email=email).first()
    if utilisateur_existant:
        return jsonify({"error": "Un utilisateur avec cet email existe déjà."}), 409

    # Création du nouvel utilisateur
    nouvel_utilisateur = Utilisateur(
        email=email,
        mot_de_passe=generate_password_hash(mot_de_passe), # Hashage du mot de passe pour la sécurité
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