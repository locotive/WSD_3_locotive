import pytest
from app.database import get_db

def test_register(client):
    response = client.post('/auth/register', json={
        'email': 'new@example.com',
        'password': 'password123',
        'name': 'New User'
    })
    assert response.status_code == 200
    assert 'access_token' in response.json
    assert 'refresh_token' in response.json

def test_login(client):
    # 먼저 회원가입
    client.post('/auth/register', json={
        'email': 'test@example.com',
        'password': 'testpass123',
        'name': 'Test User'
    })
    
    # 로그인 테스트
    response = client.post('/auth/login', json={
        'username': 'test@example.com',
        'password': 'testpass123'
    })
    assert response.status_code == 200
    assert 'access_token' in response.json

def test_refresh_token(client):
    # 회원가입으로 토큰 받기
    register_response = client.post('/auth/register', json={
        'email': 'refresh@example.com',
        'password': 'testpass123',
        'name': 'Refresh User'
    })
    
    # 리프레시 토큰으로 새 액세스 토큰 받기
    response = client.post('/auth/refresh', json={
        'refresh_token': register_response.json['refresh_token']
    })
    assert response.status_code == 200
    assert 'access_token' in response.json 