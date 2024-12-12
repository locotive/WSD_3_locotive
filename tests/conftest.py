import pytest
import os
from app import create_app
from app.database import get_db
import mysql.connector
from datetime import datetime

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        'TESTING': True,
    })
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def db():
    connection = mysql.connector.connect(
        host=os.getenv('DB_HOST', '113.198.66.75'),
        user=os.getenv('DB_USER', 'admin'),
        password=os.getenv('DB_PASSWORD', 'xodbs1234'),
        database=os.getenv('DB_NAME', 'wsd3_test'),
        port=int(os.getenv('DB_PORT', '13145'))
    )
    yield connection
    connection.close()

@pytest.fixture
def auth_token(client):
    response = client.post('/auth/register', json={
        'email': 'test@example.com',
        'password': 'testpass123',
        'name': 'Test User'
    })
    return response.json['access_token']

@pytest.fixture
def auth_headers(auth_token):
    return {'Authorization': f'Bearer {auth_token}'} 