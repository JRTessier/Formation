from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialisation de l'extension SQLAlchemy
db = SQLAlchemy()

# Définition des modèles
class Utilisateur(db.Model):
    __tablename__ = 'utilisateurs'
    
    id = db.Column(db.Integer, primary_key=True) # Clé primaire
    email = db.Column(db.String(100), unique=True, nullable=False) # Email unique de l'utilisateur
    mot_de_passe = db.Column(db.String(100), nullable=False) # Mot de passe haché
    nom = db.Column(db.String(100), nullable=False) # Nom de l'utilisateur
    role = db.Column(db.String(20), default="client") # Rôle : client ou admin
    date_creation = db.Column(db.DateTime, default=datetime.utcnow) # Date de création du compte 
    
    def __repr__(self):
        return f'<Utilisateur {self.nom}>'

class Produit(db.Model):
    __tablename__ = 'produits'
    
    id = db.Column(db.Integer, primary_key=True) # Clé primaire
    nom = db.Column(db.String(100), nullable=False) # Nom du produit
    description = db.Column(db.Text, nullable=True) # Description détaillée
    categorie = db.Column(db.String(50), nullable=False) # Nom de la catégorie
    prix = db.Column(db.Float, nullable=False) # Prix unitaire
    quantite_stock = db.Column(db.Integer, nullable=False) # Quantité disponible en stock
    date_creation = db.Column(db.DateTime, default=datetime.utcnow) # Date d'ajout du produit
    
    def __repr__(self):
        return f'<Produit {self.nom}>'

class Commande(db.Model):
    __tablename__ = 'commandes'
    
    id = db.Column(db.Integer, primary_key=True) # Clé primaire
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False) # Clé étrangère vers Utilisateur
    date_commande = db.Column(db.DateTime, default=datetime.utcnow) # Date de création de la commande
    adresse_livraison = db.Column(db.String(200), nullable=False) # Adresse de livraison
    statut = db.Column(db.String(20), default="en_attente") # Statut : en attente, validée, expédiée, annulée

    def __repr__(self):
        return f'<Commande {self.id} - Utilisateur {self.utilisateur_id}>'

class LigneCommande(db.Model):
    __tablename__ = 'lignes_commandes'
    
    id = db.Column(db.Integer, primary_key=True) # Clé primaire
    commande_id = db.Column(db.Integer, db.ForeignKey('commandes.id'), nullable=False) # Clé étrangère vers Commande
    produit_id = db.Column(db.Integer, db.ForeignKey('produits.id'), nullable=False) # Clé étrangère vers Produit
    quantite = db.Column(db.Integer, nullable=False) # Quantité commandée
    prix_unitaire = db.Column(db.Float, nullable=False) # Prix unitaire au moment de la commande

    def __repr__(self):
        return f'<LigneCommande {self.id} - Commande {self.commande_id} - Produit {self.produit_id}>'