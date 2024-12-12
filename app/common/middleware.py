from flask import request, jsonify, g, current_app
from functools import wraps
from app.database import get_db
import jwt  # jose 대신 PyJWT 사용
import logging

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            auth_header = request.headers.get('Authorization')
            logging.info(f"Auth header received: {auth_header}")
            
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({"status": "error", "message": "Authentication required"}), 401

            token = auth_header.split(' ')[1]
            
            try:
                # PyJWT를 사용한 토큰 검증
                secret_key = current_app.config.get('JWT_SECRET_KEY')
                payload = jwt.decode(token, secret_key, algorithms=['HS256'])
                user_id = int(payload.get('user_id'))  # sub 대신 user_id 사용

                db = get_db()
                cursor = db.cursor(dictionary=True)
                cursor.execute(
                    """
                    SELECT user_id, email, name, status, phone, birth_date 
                    FROM users 
                    WHERE user_id=%s AND status='active'
                    """,
                    (user_id,)
                )
                user = cursor.fetchone()
                cursor.close()

                if not user:
                    return jsonify({"status": "error", "message": "User not found"}), 401

                g.current_user = user
                return f(*args, **kwargs)

            except jwt.ExpiredSignatureError:
                return jsonify({"status": "error", "message": "Token has expired"}), 401
            except jwt.InvalidTokenError as e:
                return jsonify({"status": "error", "message": f"Invalid token: {str(e)}"}), 401

        except Exception as e:
            logging.error(f"Authentication error: {str(e)}")
            return jsonify({"status": "error", "message": "Authentication failed"}), 500

    return decorated_function 