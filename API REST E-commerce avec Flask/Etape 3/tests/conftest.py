import pytest
from app import app as flask_app
from models import db

@pytest.fixture
def app():
    flask_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })

    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def admin_token(client):
    client.post('/api/auth/register', json={
        "email": "admin@exemple.com",
        "mot_de_passe": "test123",
        "nom": "Admin",
        "role": "admin"
    })
    login = client.post('/api/auth/login', json={
        "email": "admin@exemple.com",
        "mot_de_passe": "test123"
    })
    return login.get_json()["token"]