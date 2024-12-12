import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
from jose import jwt
from app.config import Config

def base64_encode_password(raw_password: str) -> str:
    return base64.b64encode(raw_password.encode('utf-8')).decode('utf-8')

def verify_password(plain: str, encoded: str) -> bool:
    return base64_encode_password(plain) == encoded

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    if "sub" in data and not isinstance(data["sub"], str):
        data["sub"] = str(data["sub"])

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, Config.SECRET_KEY, algorithm=Config.ALGORITHM)

def create_refresh_token(data: dict) -> str:
    if "sub" in data and not isinstance(data["sub"], str):
        data["sub"] = str(data["sub"])

    expire = datetime.now() + timedelta(days=Config.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = data.copy()
    to_encode.update({"exp": expire, "scope": "refresh_token"})
    return jwt.encode(to_encode, Config.SECRET_KEY, algorithm=Config.ALGORITHM)

def validate_user_data(data: Dict) -> Optional[str]:
    """
    Validate user registration/update data
    Returns error message if validation fails, None if successful
    """
    if not data:
        return "No input data provided"

    if 'email' in data and not '@' in data['email']:
        return "Invalid email format"

    if 'password' in data and len(data['password']) < 6:
        return "Password must be at least 6 characters long"

    return None

def decode_token(token: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Decode and validate JWT token
    Returns (payload, error)
    """
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.ALGORITHM])
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, "Token has expired"
    except jwt.JWTError:
        return None, "Invalid token" 