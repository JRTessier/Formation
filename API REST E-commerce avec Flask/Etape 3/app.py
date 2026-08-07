from flask import Flask
from models import db
import config
from routes.auth_routes import auth_bp
from routes.produits_routes import produits_bp
from routes.commandes_routes import commandes_bp

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI

db.init_app(app)

app.register_blueprint(auth_bp)
app.register_blueprint(produits_bp)
app.register_blueprint(commandes_bp)

with app.app_context():
    db.create_all()