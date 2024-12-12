from flask import Blueprint, request, jsonify, g, make_response
from app.common.middleware import login_required
from app.database import get_db
from app.auth.utils import hash_password, verify_password, generate_tokens
from app.models import User
import logging

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register_user():
    try:
        data = request.get_json(force=True)
        
        if not data:
            return make_response(jsonify({
                "status": "error",
                "code": "InvalidJSON",
                "message": "No JSON data received"
            }), 400)

        # 필수 필드 검증
        required_fields = ['email', 'password', 'name']
        for field in required_fields:
            if field not in data:
                return make_response(jsonify({
                    "status": "error",
                    "code": "MissingField",
                    "message": f"Missing required field: {field}"
                }), 400)

        # 사용자 생성 시도
        try:
            result = User.create_user(
                email=data['email'],
                password=data['password'],
                name=data['name']
            )
            
            # 디버깅을 위한 로그 추가
            logging.info(f"Create user result: {result}")
            
            if result is False:
                return make_response(jsonify({
                    "status": "error",
                    "code": "UserCreationError",
                    "message": "Failed to create user"
                }), 400)
            
            if isinstance(result, str):  # 에러 메시지인 경우
                return make_response(jsonify({
                    "status": "error",
                    "code": "UserCreationError",
                    "message": result
                }), 400)

            # 성공한 경우 (result가 사용자 데이터인 경우)
            return make_response(jsonify({
                "status": "success",
                "message": "User registered successfully",
                "data": result
            }), 201)

        except Exception as e:
            logging.error(f"User creation error: {str(e)}")
            return make_response(jsonify({
                "status": "error",
                "code": "UserCreationError",
                "message": str(e)
            }), 400)

    except Exception as e:
        logging.error(f"Registration error: {str(e)}")
        return make_response(jsonify({
            "status": "error",
            "code": type(e).__name__,
            "message": str(e)
        }), 500)

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data.get('email') or not data.get('password'):
            return jsonify({
                "status": "error",
                "message": "Email and password are required"
            }), 400

        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, email, name, password_hash 
            FROM users 
            WHERE email = %s AND status = 'active'
        """, (data['email'],))
        
        user = cursor.fetchone()
        if not user or not verify_password(data['password'], user['password_hash']):
            return jsonify({
                "status": "error",
                "message": "Invalid credentials"
            }), 401

        tokens = generate_tokens(user['id'])

        return jsonify({
            "status": "success",
            "data": {
                "user_id": user['id'],
                "email": user['email'],
                "name": user['name'],
                **tokens
            }
        })

    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    finally:
        cursor.close()

@auth_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, email, name, created_at, updated_at
            FROM users
            WHERE id = %s
        """, (g.user_id,))
        
        user = cursor.fetchone()
        if not user:
            return jsonify({
                "status": "error",
                "message": "User not found"
            }), 404

        return jsonify({
            "status": "success",
            "data": user
        })

    except Exception as e:
        logging.error(f"Profile fetch error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    finally:
        cursor.close()

@auth_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "message": "No data provided"
            }), 400

        db = get_db()
        cursor = db.cursor()

        # 업데이트 가능한 필드
        allowed_fields = ['name', 'password']
        update_data = {}
        
        for field in allowed_fields:
            if field in data:
                if field == 'password':
                    update_data['password_hash'] = hash_password(data['password'])
                else:
                    update_data[field] = data[field]

        if not update_data:
            return jsonify({
                "status": "error",
                "message": "No valid fields to update"
            }), 400

        # SQL 쿼리 생성
        query = "UPDATE users SET " + \
                ", ".join(f"{k} = %s" for k in update_data.keys()) + \
                ", updated_at = NOW() WHERE id = %s"
        
        values = list(update_data.values()) + [g.user_id]
        cursor.execute(query, values)
        db.commit()

        return jsonify({
            "status": "success",
            "message": "Profile updated successfully"
        })

    except Exception as e:
        db.rollback()
        logging.error(f"Profile update error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    finally:
        cursor.close()

@auth_bp.route('/profile', methods=['DELETE'])
@login_required
def delete_account():
    try:
        db = get_db()
        cursor = db.cursor()

        # 소프트 삭제 구현
        cursor.execute("""
            UPDATE users 
            SET status = 'deleted', updated_at = NOW() 
            WHERE id = %s
        """, (g.user_id,))
        
        db.commit()

        return jsonify({
            "status": "success",
            "message": "Account deleted successfully"
        })

    except Exception as e:
        db.rollback()
        logging.error(f"Account deletion error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    finally:
        cursor.close()