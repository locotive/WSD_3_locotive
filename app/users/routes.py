from flask import Blueprint

user_bp = Blueprint('users', __name__)

@user_bp.route('/')
def get_users():
    return {"message": "Users endpoint"}
