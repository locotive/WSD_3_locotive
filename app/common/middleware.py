from flask import request, jsonify, g, current_app
from functools import wraps
from app.database import get_db
import jwt
import logging

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            logging.info(f"[Auth] Endpoint: {request.endpoint}, Path: {request.path}")
            auth_header = request.headers.get('Authorization')
            logging.info(f"[Auth] Authorization header: {auth_header}")
            
            if not auth_header:
                logging.error("[Auth] No Authorization header present")
                return jsonify({
                    "status": "error",
                    "message": "No Authorization header"
                }), 401
                
            if not auth_header.startswith('Bearer '):
                logging.error("[Auth] Invalid Authorization format")
                return jsonify({
                    "status": "error",
                    "message": "Invalid Authorization format"
                }), 401

            token = auth_header.split(' ')[1]
            
            try:
                secret_key = current_app.config.get('JWT_SECRET_KEY')
                logging.info(f"[Auth] JWT_SECRET_KEY exists: {bool(secret_key)}")
                
                if not secret_key:
                    logging.error("[Auth] JWT_SECRET_KEY not found")
                    return jsonify({
                        "status": "error",
                        "message": "Server configuration error"
                    }), 500
                
                payload = jwt.decode(token, secret_key, algorithms=['HS256'])
                logging.info(f"[Middleware] Token payload: {payload}")
                
                if 'user_id' not in payload:
                    logging.error("[Auth] user_id not found in payload")
                    return jsonify({
                        "status": "error",
                        "message": "Invalid token content"
                    }), 401
                
                user_id = payload['user_id']
                logging.info(f"[Middleware] User ID from token: {user_id}")

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
                    logging.error(f"[Auth] User not found for ID: {user_id}")
                    return jsonify({
                        "status": "error",
                        "message": "User not found"
                    }), 401

                logging.info(f"[Middleware] User data fetched: {user}")
                g.current_user = user
                
                response = f(*args, **kwargs)
                logging.info(f"[Auth] Function response: {response}")
                return response

            except jwt.ExpiredSignatureError as e:
                logging.error(f"[Auth] Token expired: {str(e)}")
                return jsonify({
                    "status": "error",
                    "message": "Token has expired"
                }), 401
            except jwt.InvalidTokenError as e:
                return jsonify({
                    "status": "error",
                    "message": f"Invalid token: {str(e)}"
                }), 401
            except Exception as e:
                logging.error(f"[Middleware] Token verification error: {str(e)}")
                return jsonify({
                    "status": "error",
                    "message": "Token verification failed"
                }), 401

        except Exception as e:
            logging.error(f"[Middleware] Middleware error: {str(e)}")
            return jsonify({
                "status": "error",
                "message": "Server error"
            }), 500

    return decorated_function 