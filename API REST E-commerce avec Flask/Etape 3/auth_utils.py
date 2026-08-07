import jwt
from flask import jsonify, request
from functools import wraps
from config import JWT_SECRET

def decode_token(token):
    try:
        return jwt.decode(
            token,
            JWT_SECRET,
            algorithms="HS256")
    except Exception:
        print("Jeton JWT invalide.")
        return

def get_token_from_header():
    authorization_header = request.headers.get("Authorization", "")
    if authorization_header.startswith("Bearer "):
        return authorization_header[7:] # Supprime "Bearer " du début
    return authorization_header

def require_authentication(f):
    @wraps(f)
    def wrapper(**kwargs):
        token = get_token_from_header()
        if not decode_token(token):
            return {"error": "Jeton d'accès invalide."}, 401
        return f(**kwargs)
    return wrapper

def require_admin(f):
    @wraps(f)
    def wrapper(**kwargs):
        token = get_token_from_header()
        decoded_token = decode_token(token)
        if not decoded_token or decoded_token.get("user") is None:
            return {"error": "Jeton d'accès invalide."}, 401
        if decoded_token.get("role") != "admin":
            return {"error": "Accès refusé. Rôle administrateur requis."}, 403
        return f(**kwargs)
    return wrapper