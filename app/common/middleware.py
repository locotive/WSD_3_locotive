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
            
            if not auth_header:
                logging.error("No Authorization header")
                return jsonify({"status": "error", "message": "No Authorization header"}), 401
                
            if not auth_header.startswith('Bearer '):
                logging.error("Invalid Authorization header format")
                return jsonify({"status": "error", "message": "Invalid Authorization format"}), 401

            token = auth_header.split(' ')[1]
            logging.info(f"Token extracted: {token[:10]}...")
            
            try:
                secret_key = current_app.config.get('JWT_SECRET_KEY')
                logging.info(f"Secret key exists: {bool(secret_key)}")
                
                payload = jwt.decode(token, secret_key, algorithms=['HS256'])
                logging.info(f"Token decoded successfully: {payload}")
                
                user_id = int(payload.get('user_id'))
                logging.info(f"User ID from token: {user_id}")

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
                    logging.error(f"User not found or not active: {user_id}")
                    return jsonify({"status": "error", "message": "User not found"}), 401

                g.current_user = user
                return f(*args, **kwargs)

            except jwt.ExpiredSignatureError:
                logging.error("Token has expired")
                return jsonify({"status": "error", "message": "Token has expired"}), 401
            except jwt.InvalidTokenError as e:
                logging.error(f"Invalid token: {str(e)}")
                return jsonify({"status": "error", "message": f"Invalid token: {str(e)}"}), 401
            except Exception as e:
                logging.error(f"Token verification error: {str(e)}")
                return jsonify({"status": "error", "message": "Token verification failed"}), 401

        except Exception as e:
            logging.error(f"Middleware error: {str(e)}")
            return jsonify({"status": "error", "message": "Server error"}), 500

    return decorated_function 