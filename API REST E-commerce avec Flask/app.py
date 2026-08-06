import jwt

from flask import Flask, request, jsonify
from datetime import datetime, timedelta

JWT_SECRET = "d3fb12750c2eff92120742e1b334479e"

app = Flask(__name__)

# Connexion et génération de token JWT
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
    
def require_authentication(f):
    def wrapper(**kwargs):
        token = request.headers.get("Authorization", "0")
        if not decode_token(token):
            return {"error": "Jeton d'accès invalide."}, 401
        return f(**kwargs)
    return wrapper

@app.route('/api/auth/login', methods=["POST"])
def generate_token():
    body = request.get_json()
    if body and body.get("password", "") == "blent":
        token = jwt.encode(
            {
                "exp": datetime.utcnow() + timedelta(hours=1),
                "user": "blentie"
            },
            JWT_SECRET,
            algorithm="HS256"
        )
        return jsonify({"token": token}), 200
    else:
        return jsonify({"error": "Mot de passe invalide."}), 401
    

@app.route('/predict', methods=["GET"])
@require_authentication
def predict():
    return {"message": "Ok !"}, 200

# Inscription d'un nouvel utilisateur
@app.route('/api/auth/register', methods=["POST"])
def register_user():
    