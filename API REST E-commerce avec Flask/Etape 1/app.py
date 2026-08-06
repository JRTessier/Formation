import jwt

from flask import Flask, request, jsonify
from datetime import datetime, timedelta
from models import db, Utilisateur

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
            "user": utilisateur.email
        },
        JWT_SECRET,
        algorithm="HS256"
    )
    return jsonify({"token": token}), 200
    

@app.route('/predict', methods=["GET"])
@require_authentication
def predict():
    return {"message": "Ok !"}, 200

# Inscription d'un nouvel utilisateur
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
    