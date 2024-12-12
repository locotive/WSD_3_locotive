from flask import request, jsonify, g
from functools import wraps
from jose import jwt, JWTError
from app.config import Config
from app.database import get_db

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"message": "Authentication required"}), 401

        token = auth_header.split(' ')[1]
        try:
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.ALGORITHM])
            user_id = int(payload.get("sub"))

            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT user_id, email, name, status, phone, birth_date 
                FROM users 
                WHERE user_id=%s
                """,
                (user_id,)
            )
            user = cursor.fetchone()
            cursor.close()

            if not user or user['status'] in ['inactive', 'blocked']:
                return jsonify({"message": "User is not active"}), 401

            g.current_user = user
            return f(*args, **kwargs)

        except (JWTError, ValueError):
            return jsonify({"message": "Invalid token"}), 401

    return decorated_function 