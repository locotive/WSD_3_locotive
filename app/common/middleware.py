from flask import request, jsonify, g
from functools import wraps
from app.auth.utils import verify_token
import logging
from app.database import get_db

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({
                    "status": "error",
                    "message": "Authentication required"
                }), 401

            token = auth_header.split(' ')[1]
            try:
                payload = verify_token(token)
                user_id = int(payload.get('user_id'))

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
                    return jsonify({
                        "status": "error",
                        "message": "User not found or not active"
                    }), 401

                g.current_user = user
                return f(*args, **kwargs)

            except ValueError as e:
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