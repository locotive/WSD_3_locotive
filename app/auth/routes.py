from flask import Blueprint, request, jsonify, g, make_response
from app.auth.models import User
from app.auth.utils import validate_user_data, decode_token
from app.common.middleware import login_required
import logging
from flask_jwt_extended import create_access_token, create_refresh_token

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register_user():
    try:
        # JSON 데이터 파싱
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

        # 사용자 생성
        error = User.create_user(
            email=data['email'],
            password=data['password'],
            name=data['name']
        )
        
        if error:
            return make_response(jsonify({
                "status": "error",
                "code": "UserCreationError",
                "message": str(error)
            }), 400)

        # 토큰 생성
        access_token = create_access_token(identity=data['email'])
        refresh_token = create_refresh_token(identity=data['email'])

        return make_response(jsonify({
            "status": "success",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "email": data['email'],
                "name": data['name']
            }
        }), 200)

    except Exception as e:
        logging.error(f"Registration error: {str(e)}")
        return make_response(jsonify({
            "status": "error",
            "code": type(e).__name__,
            "message": str(e)
        }), 500)

@auth_bp.route('/login', methods=['POST'])
def login():
    if request.content_type == 'application/x-www-form-urlencoded':
        username = request.form.get('username')
        password = request.form.get('password')
    else:
        data = request.get_json()
        if not data:
            return jsonify({"message": "Invalid request format"}), 400
        username = data.get('username')
        password = data.get('password')

    if not username or not password:
        return jsonify({"message": "Missing username or password"}), 400

    tokens, error = User.authenticate(username, password)
    if error:
        return jsonify({"message": error}), 401

    return jsonify(tokens)

@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    data = request.get_json()
    if not data or 'refresh_token' not in data:
        return jsonify({"message": "Refresh token is required"}), 400

    payload, error = decode_token(data['refresh_token'])
    if error:
        return jsonify({"message": error}), 401

    if payload.get("scope") != "refresh_token":
        return jsonify({"message": "Invalid token type"}), 401

    tokens, error = User.authenticate_by_id(int(payload.get("sub")))
    if error:
        return jsonify({"message": error}), 401

    return jsonify(tokens)

@auth_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    data = request.get_json()
    error = validate_user_data(data)
    if error:
        return jsonify({"message": error}), 400

    error = User.update_profile(g.current_user['user_id'], data)
    if error:
        return jsonify({"message": error}), 400

    return jsonify({"message": "Profile updated successfully"})