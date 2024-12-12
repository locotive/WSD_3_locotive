from flask import Blueprint, request, jsonify, g
from app.common.middleware import login_required
from app.jobs.models import Job
from app.jobs.utils import validate_job_data, prepare_job_filters

jobs_bp = Blueprint('jobs', __name__)

@jobs_bp.route('/', methods=['GET'])
def list_jobs():
    page = int(request.args.get('page', 1))
    filters = prepare_job_filters(request.args)
    
    jobs = Job.list_jobs(filters, page)
    return jsonify({
        "jobs": jobs,
        "page": page,
        "filters": filters
    })

@jobs_bp.route('/<int:id>', methods=['GET'])
def get_job_detail(id):
    job = Job.get_job_detail(id)
    if not job:
        return jsonify({"message": "Job not found"}), 404
    return jsonify(job)

@jobs_bp.route('/', methods=['POST'])
@login_required
def create_job():
    data = request.get_json()
    if not data:
        return jsonify({"message": "No input data provided"}), 400

    error = validate_job_data(data)
    if error:
        return jsonify({"message": error}), 400

    result = Job.create_job(data)
    if isinstance(result, str):
        return jsonify({"message": result}), 500

    return jsonify({
        "message": "Job posting created successfully",
        "posting_id": result
    })

@jobs_bp.route('/<int:id>', methods=['PUT'])
@login_required
def update_job(id):
    data = request.get_json()
    if not data:
        return jsonify({"message": "No input data provided"}), 400

    error = Job.update_job(id, data)
    if error:
        status_code = 404 if error == "Job posting not found" else 400
        return jsonify({"message": error}), status_code

    return jsonify({"message": "Job posting updated successfully"})

@jobs_bp.route('/<int:id>', methods=['DELETE'])
@login_required
def delete_job(id):
    error = Job.delete_job(id)
    if error:
        status_code = 404 if error == "Job posting not found" else 400
        return jsonify({"message": error}), status_code

    return jsonify({"message": "Job posting deleted successfully"}) 