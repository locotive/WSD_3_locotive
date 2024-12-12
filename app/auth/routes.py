from flask import Blueprint, request, jsonify, g
from app.auth.models import User
from app.auth.utils import validate_user_data, decode_token
from app.common.middleware import login_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    error = validate_user_data(data)
    if error:
        return jsonify({"message": error}), 400

    tokens, error = User.create_user(
        email=data['email'],
        password=data['password'],
        name=data['name'],
        phone=data.get('phone'),
        birth_date=data.get('birth_date')
    )

    if error:
        return jsonify({"message": error}), 400

    return jsonify(tokens)

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