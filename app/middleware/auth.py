from functools import wraps
from flask import request, jsonify, g
import jwt
from app.database import get_db
import logging
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# 'your-secret-key' 대신 환경변수 사용
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Bearer 토큰 확인
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({
                    "status": "error",
                    "message": "Invalid token format"
                }), 401

        if not token:
            return jsonify({
                "status": "error",
                "message": "Token is missing"
            }), 401

        try:
            # 토큰 디코딩
            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
            
            db = get_db()
            cursor = db.cursor(dictionary=True)
            
            # 사용자 확인
            cursor.execute("""
                SELECT user_id, email, status 
                FROM users 
                WHERE user_id = %s AND status = 'active'
            """, (data['user_id'],))
            
            current_user = cursor.fetchone()
            cursor.close()

            if not current_user:
                return jsonify({
                    "status": "error",
                    "message": "User not found or inactive"
                }), 401

            # 전역 컨텍스트에 사용자 정보 저장
            g.user_id = current_user['user_id']
            g.email = current_user['email']

        except jwt.ExpiredSignatureError:
            return jsonify({
                "status": "error",
                "message": "Token has expired"
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                "status": "error",
                "message": "Invalid token"
            }), 401
        except Exception as e:
            logging.error(f"Token validation error: {str(e)}")
            return jsonify({
                "status": "error",
                "message": "Token validation failed"
            }), 401

        return f(*args, **kwargs)
    return decorated_function

def company_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'user_id'):
            return jsonify({
                "status": "error",
                "message": "Authentication required"
            }), 401

        try:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            
            # 회사 권한 확인
            cursor.execute("""
                SELECT company_id 
                FROM company_users 
                WHERE user_id = %s AND status = 'active'
            """, (g.user_id,))
            
            company_user = cursor.fetchone()
            cursor.close()

            if not company_user:
                return jsonify({
                    "status": "error",
                    "message": "Company permission required"
                }), 403

            g.company_id = company_user['company_id']

        except Exception as e:
            logging.error(f"Company permission check error: {str(e)}")
            return jsonify({
                "status": "error",
                "message": "Permission check failed"
            }), 500

        return f(*args, **kwargs)
    return decorated_function 