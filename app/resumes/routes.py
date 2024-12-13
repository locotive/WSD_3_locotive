from flask import Blueprint, request, jsonify, make_response, g
from app.resumes.models import Resume
from app.middleware.auth import login_required
import logging

resumes_bp = Blueprint('resumes', __name__, url_prefix='/resumes')

@resumes_bp.route('', methods=['POST'])
@login_required
def create_resume():
    try:
        data = request.get_json()
        
        if not all(k in data for k in ['title', 'content']):
            return make_response(jsonify({
                "status": "error",
                "message": "Missing required fields"
            }), 400)

        resume_id, error = Resume.create_resume(g.user_id, data)

        if error:
            return make_response(jsonify({
                "status": "error",
                "message": error
            }), 400)

        return make_response(jsonify({
            "status": "success",
            "data": {"resume_id": resume_id}
        }), 201)

    except Exception as e:
        logging.error(f"Resume creation error: {str(e)}")
        return make_response(jsonify({
            "status": "error",
            "message": str(e)
        }), 500)

@resumes_bp.route('', methods=['GET'])
@login_required
def get_resumes():
    try:
        resumes, error = Resume.get_user_resumes(g.user_id)
        
        if error:
            return make_response(jsonify({
                "status": "error",
                "message": error
            }), 400)

        return make_response(jsonify({
            "status": "success",
            "data": resumes
        }), 200)

    except Exception as e:
        logging.error(f"Resumes fetch error: {str(e)}")
        return make_response(jsonify({
            "status": "error",
            "message": str(e)
        }), 500)

@resumes_bp.route('/<int:resume_id>', methods=['GET'])
@login_required
def get_resume(resume_id):
    try:
        resume, error = Resume.get_resume(resume_id, g.user_id)
        
        if error:
            return make_response(jsonify({
                "status": "error",
                "message": error
            }), 400)

        return make_response(jsonify({
            "status": "success",
            "data": resume
        }), 200)

    except Exception as e:
        logging.error(f"Resume fetch error: {str(e)}")
        return make_response(jsonify({
            "status": "error",
            "message": str(e)
        }), 500)

@resumes_bp.route('/<int:resume_id>', methods=['PUT'])
@login_required
def update_resume(resume_id):
    try:
        data = request.get_json()
        error = Resume.update_resume(resume_id, g.user_id, data)
        
        if error:
            return make_response(jsonify({
                "status": "error",
                "message": error
            }), 400)

        return make_response(jsonify({
            "status": "success",
            "message": "Resume updated successfully"
        }), 200)

    except Exception as e:
        logging.error(f"Resume update error: {str(e)}")
        return make_response(jsonify({
            "status": "error",
            "message": str(e)
        }), 500)

@resumes_bp.route('/<int:resume_id>', methods=['DELETE'])
@login_required
def delete_resume(resume_id):
    try:
        error = Resume.delete_resume(resume_id, g.user_id)
        
        if error:
            return make_response(jsonify({
                "status": "error",
                "message": error
            }), 400)

        return make_response(jsonify({
            "status": "success",
            "message": "Resume deleted successfully"
        }), 200)

    except Exception as e:
        logging.error(f"Resume deletion error: {str(e)}")
        return make_response(jsonify({
            "status": "error",
            "message": str(e)
        }), 500)