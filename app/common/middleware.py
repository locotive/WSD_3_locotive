from flask import request, jsonify, g
from functools import wraps
from app.auth.utils import verify_token
from app.database import get_db
import logging

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            auth_header = request.headers.get('Authorization')
            logging.info(f"Auth header: {auth_header}")
            
            if not auth_header or not auth_header.startswith('Bearer '):
                logging.error("Missing or invalid Authorization header")
                return jsonify({
                    "status": "error",
                    "message": "Authentication required"
                }), 401

            token = auth_header.split(' ')[1]
            logging.info(f"Token: {token[:10]}...")
            
            try:
                payload = verify_token(token)
                logging.info(f"Token payload: {payload}")
                
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
                    return jsonify({
                        "status": "error",
                        "message": "User not found or not active"
                    }), 401

                g.current_user = user
                logging.info(f"User authenticated successfully: {user_id}")
                return f(*args, **kwargs)

            except ValueError as e:
                logging.error(f"Token verification error: {str(e)}")
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 401

        except Exception as e:
            logging.error(f"Authentication error: {str(e)}")
            return jsonify({
                "status": "error",
                "message": "Authentication failed"
            }), 500

    return decorated_function 