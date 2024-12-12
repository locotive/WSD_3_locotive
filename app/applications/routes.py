from flask import Blueprint, request, jsonify, make_response, g
from app.applications.models import Application
from app.middleware.auth import login_required
import logging

applications_bp = Blueprint('applications', __name__, url_prefix='/applications')

@applications_bp.route('', methods=['POST'])
@login_required
def apply_job():
    try:
        data = request.get_json()
        
        if not all(k in data for k in ['posting_id', 'resume_id']):
            return make_response(jsonify({
                "status": "error",
                "message": "Missing required fields"
            }), 400)

        application_id, error = Application.apply_job(
            g.user_id,
            data['posting_id'],
            data['resume_id']
        )

        if error:
            return make_response(jsonify({
                "status": "error",
                "message": error
            }), 400)

        return make_response(jsonify({
            "status": "success",
            "data": {"application_id": application_id}
        }), 201)

    except Exception as e:
        logging.error(f"Job application error: {str(e)}")
        return make_response(jsonify({
            "status": "error",
            "message": str(e)
        }), 500)

@applications_bp.route('/<int:application_id>', methods=['DELETE'])
@login_required
def cancel_application(application_id):
    try:
        error = Application.cancel_application(g.user_id, application_id)
        
        if error:
            return make_response(jsonify({
                "status": "error",
                "message": error
            }), 400)

        return make_response(jsonify({
            "status": "success",
            "message": "Application cancelled successfully"
        }), 200)

    except Exception as e:
        logging.error(f"Application cancellation error: {str(e)}")
        return make_response(jsonify({
            "status": "error",
            "message": str(e)
        }), 500)

@applications_bp.route('', methods=['GET'])
@login_required
def get_applications():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))

        result, error = Application.get_user_applications(g.user_id, page, per_page)
        
        if error:
            return make_response(jsonify({
                "status": "error",
                "message": error
            }), 400)

        return make_response(jsonify({
            "status": "success",
            "data": result
        }), 200)

    except Exception as e:
        logging.error(f"Applications fetch error: {str(e)}")
        return make_response(jsonify({
            "status": "error",
            "message": str(e)
        }), 500) 