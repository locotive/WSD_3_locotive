from flask import Blueprint, request, jsonify, g
from werkzeug.utils import secure_filename
from app.common.middleware import login_required
from app.applications.models import Application

applications_bp = Blueprint('applications', __name__)

@applications_bp.route('/', methods=['POST'])
@login_required
def apply_for_job():
    try:
        if request.content_type.startswith('multipart/form-data'):
            posting_id = request.form.get('posting_id')
            resume_id = request.form.get('resume_id')
            resume_file = request.files.get('resume_file')
        else:
            data = request.get_json()
            posting_id = data.get('posting_id')
            resume_id = data.get('resume_id')
            resume_file = None

        if not posting_id:
            return jsonify({"message": "Posting ID is required"}), 400

        if not resume_id and not resume_file:
            return jsonify({"message": "Either resume_id or resume_file must be provided"}), 400

        resume_file_content = None
        if resume_file:
            if not resume_file.filename.lower().endswith('.pdf'):
                return jsonify({"message": "Only PDF files are allowed"}), 400
            resume_file_content = resume_file.read()

        application_id, error = Application.create_application(
            g.current_user['user_id'],
            posting_id,
            resume_id,
            resume_file_content
        )

        if error:
            return jsonify({"message": error}), 400

        return jsonify({
            "message": "Application submitted successfully",
            "application_id": application_id
        })

    except Exception as e:
        return jsonify({"message": str(e)}), 500

@applications_bp.route('/', methods=['GET'])
@login_required
def list_applications():
    status_filter = request.args.get('status_filter')
    sort_by_date = request.args.get('sort_by_date', 'desc')
    page = int(request.args.get('page', 1))

    applications = Application.get_applications(
        g.current_user['user_id'],
        status_filter,
        sort_by_date,
        page
    )
    
    return jsonify(applications)

@applications_bp.route('/<int:id>', methods=['DELETE'])
@login_required
def cancel_application(id):
    error = Application.delete_application(id, g.current_user['user_id'])
    
    if error:
        return jsonify({"message": error}), 400 if "Not authorized" in error else 404

    return jsonify({"message": "Application cancelled successfully"}) 