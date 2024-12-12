import pytest
from app.auth.utils import generate_token, verify_token, hash_password, check_password
from app.auth.models import User

def test_password_hashing():
    """비밀번호 해싱 테스트"""
    password = "test_password123"
    hashed = hash_password(password)
    
    assert hashed != password
    assert check_password(password, hashed) == True
    assert check_password("wrong_password", hashed) == False

def test_token_generation():
    """토큰 생성 및 검증 테스트"""
    user_data = {"user_id": 1, "email": "test@example.com"}
    token = generate_token(user_data)
    
    assert token is not None
    decoded = verify_token(token)
    assert decoded["user_id"] == user_data["user_id"]
    assert decoded["email"] == user_data["email"]

def test_token_expiration():
    """토큰 만료 테스트"""
    user_data = {"user_id": 1, "email": "test@example.com"}
    token = generate_token(user_data, expires_in=-1)  # 즉시 만료
    
    with pytest.raises(Exception):
        verify_token(token)

def test_invalid_token():
    """잘못된 토큰 테스트"""
    with pytest.raises(Exception):
        verify_token("invalid_token") 