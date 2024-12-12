from flask import Blueprint, request, jsonify, make_response, g
from app.common.middleware import login_required
from app.database import get_db
from app.auth.utils import hash_password, verify_password, generate_tokens
from app.auth.models import User
import logging

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register_user():
    try:
        data = request.get_json()
        
        required_fields = ['email', 'password', 'name']
        for field in required_fields:
            if not data.get(field):
                response = jsonify({
                    "status": "error",
                    "message": f"{field} is required"
                })
                response.status_code = 400
                return response

        result, error = User.create_user(
            email=data['email'],
            password=data['password'],
            name=data['name'],
            phone=data.get('phone'),
            birth_date=data.get('birth_date')
        )

        if error:
            response = jsonify({
                "status": "error",
                "message": error
            })
            response.status_code = 400
            return response

        response = jsonify({
            "status": "success",
            "data": result
        })
        response.status_code = 201
        return response

    except Exception as e:
        logging.error(f"Registration error: {str(e)}")
        response = jsonify({
            "status": "error",
            "message": str(e)
        })
        response.status_code = 500
        return response

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data.get('email') or not data.get('password'):
            return make_response(jsonify({
                "status": "error",
                "message": "Email and password are required"
            }), 400)

        result, error = User.authenticate(
            username=data['email'],
            password=data['password']
        )

        if error:
            return make_response(jsonify({
                "status": "error",
                "message": error
            }), 401)

        return make_response(jsonify({
            "status": "success",
            "data": result
        }), 200)

    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        return make_response(jsonify({
            "status": "error",
            "message": str(e)
        }), 500)

@auth_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    try:
        if not hasattr(g, 'current_user'):
            logging.error("[Route] No current_user in g object")
            return jsonify({
                "status": "error",
                "message": "Authentication required"
            }), 401
            
        if not g.current_user:
            logging.error("[Route] current_user is None")
            return jsonify({
                "status": "error",
                "message": "User not found"
            }), 404
            
        logging.info(f"[Route] Starting get_profile for user: {g.current_user}")
        user_id = g.current_user.get('user_id')
        
        if not user_id:
            logging.error("[Route] No user_id in current_user")
            return jsonify({
                "status": "error",
                "message": "Invalid user data"
            }), 400
            
        logging.info(f"[Route] Extracted user_id: {user_id}")
        
        user, error = User.get_user_profile(user_id)
        logging.info(f"[Route] get_user_profile result - user: {user}, error: {error}")
        
        if error:
            logging.error(f"[Route] Profile fetch error: {error}")
            return jsonify({
                "status": "error",
                "message": error
            }), 404
            
        if not user:
            logging.error("[Route] User data not found")
            return jsonify({
                "status": "error",
                "message": "User not found"
            }), 404
            
        logging.info(f"[Route] Profile fetched successfully for user: {user_id}")
        
        if user.get('created_at'):
            user['created_at'] = user['created_at'].isoformat()
        if user.get('last_login'):
            user['last_login'] = user['last_login'].isoformat()
        if user.get('birth_date'):
            user['birth_date'] = user['birth_date'].isoformat()
            
        return jsonify({
            "status": "success",
            "data": user
        }), 200

    except Exception as e:
        logging.error(f"[Route] Profile fetch error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@auth_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    try:
        user_id = g.current_user['user_id']
        data = request.get_json()
        if not data:
            return make_response(jsonify({
                "status": "error",
                "message": "No data provided"
            }), 400)

        error = User.update_profile(user_id, data)
        if error:
            return make_response(jsonify({
                "status": "error",
                "message": error
            }), 400)

        return make_response(jsonify({
            "status": "success",
            "message": "Profile updated successfully"
        }), 200)

    except Exception as e:
        logging.error(f"Profile update error: {str(e)}")
        return make_response(jsonify({
            "status": "error",
            "message": str(e)
        }), 500)

@auth_bp.route('/profile', methods=['DELETE'])
@login_required
def delete_user():
    try:
        user_id = g.current_user['user_id']
        error = User.delete_user(user_id)
        if error:
            return make_response(jsonify({
                "status": "error",
                "message": error
            }), 400)

        return make_response(jsonify({
            "status": "success",
            "message": "User account deactivated successfully"
        }), 200)

    except Exception as e:
        logging.error(f"User deletion error: {str(e)}")
        return make_response(jsonify({
            "status": "error",
            "message": str(e)
        }), 500)