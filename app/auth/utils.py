from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from flask import current_app
import logging

def hash_password(password: str) -> str:
    """비밀번호를 해싱하는 함수"""
    try:
        return generate_password_hash(password)
    except Exception as e:
        logging.error(f"Password hashing error: {str(e)}")
        raise

def verify_password(password: str, hashed_password: str) -> bool:
    """비밀번호를 검증하는 함수"""
    try:
        return check_password_hash(hashed_password, password)
    except Exception as e:
        logging.error(f"Password verification error: {str(e)}")
        return False

def generate_tokens(user_id: int) -> dict:
    """Access Token과 Refresh Token을 생성하는 함수"""
    try:
        secret_key = str(current_app.config['JWT_SECRET_KEY'])  # JWT_SECRET_KEY 사용
        
        # Access Token 생성 (만료시간 1시간)
        access_token = jwt.encode(
            {
                'user_id': int(user_id),
                'exp': datetime.utcnow() + timedelta(hours=1)
            },
            secret_key,
            algorithm='HS256'
        )

        return {
            'access_token': access_token.decode('utf-8') if isinstance(access_token, bytes) else access_token
        }
    except Exception as e:
        logging.error(f"Token generation error: {str(e)}")
        raise

def verify_token(token: str) -> dict:
    """토큰을 검증하고 페이로드를 반환하는 함수"""
    try:
        secret_key = str(current_app.config['JWT_SECRET_KEY'])  # JWT_SECRET_KEY 사용
        
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=['HS256']
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid token: {str(e)}")
    except Exception as e:
        logging.error(f"Token verification error: {str(e)}")
        raise 