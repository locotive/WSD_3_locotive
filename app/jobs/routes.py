from flask import Blueprint, request, jsonify, make_response, g
from app.jobs.models import JobPosting
from app.middleware.auth import login_required, company_required
import logging

jobs_bp = Blueprint('jobs', __name__, url_prefix='/jobs')

@jobs_bp.route('', methods=['GET'])
def get_job_postings():
    try:
        # 검색 및 필터링 파라미터
        filters = {}
        if request.args.get('search'):
            filters['search'] = request.args.get('search')
        if request.args.get('location_id'):
            filters['location_id'] = int(request.args.get('location_id'))
        if request.args.get('categories'):
            filters['categories'] = [int(x) for x in request.args.get('categories').split(',')]
        if request.args.get('tech_stacks'):
            filters['tech_stacks'] = [int(x) for x in request.args.get('tech_stacks').split(',')]

        # 페이지네이션
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))

        # 정렬
        sort_by = request.args.get('sort_by', 'latest')

        result, error = JobPosting.search_postings(filters, sort_by, page, per_page)
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
        logging.error(f"Job postings fetch error: {str(e)}")
        return make_response(jsonify({
            "status": "error",
            "message": str(e)
        }), 500)

@jobs_bp.route('/<int:posting_id>', methods=['GET'])
def get_job_posting(posting_id):
    try:
        posting, error = JobPosting.get_posting(posting_id)
        if error:
            return make_response(jsonify({
                "status": "error",
                "message": error
            }), 404)

        return make_response(jsonify({
            "status": "success",
            "data": posting
        }), 200)

    except Exception as e:
        logging.error(f"Job posting fetch error: {str(e)}")
        return make_response(jsonify({
            "status": "error",
            "message": str(e)
        }), 500)

@jobs_bp.route('', methods=['POST'])
@login_required
def create_job_posting():
    try:
        data = request.get_json()
        required_fields = ['title', 'job_description']
        
        for field in required_fields:
            if field not in data:
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Missing required field: {field}"
                }), 400)

        posting_id, error = JobPosting.create_posting(g.company_id, data)
        if error:
            return make_response(jsonify({
                "status": "error",
                "message": error
            }), 400)

        return make_response(jsonify({
            "status": "success",
            "data": {"posting_id": posting_id}
        }), 201)

    except Exception as e:
        logging.error(f"Job posting creation error: {str(e)}")
        return make_response(jsonify({
            "status": "error",
            "message": str(e)
        }), 500)

@jobs_bp.route('/<int:posting_id>', methods=['PUT'])
@login_required
@company_required
def update_job_posting(posting_id):
    try:
        data = request.get_json()
        
        # TODO: Implement update_posting method
        error = JobPosting.update_posting(posting_id, g.company_id, data)
        if error:
            return make_response(jsonify({
                "status": "error",
                "message": error
            }), 400)

        return make_response(jsonify({
            "status": "success",
            "message": "Job posting updated successfully"
        }), 200)

    except Exception as e:
        logging.error(f"Job posting update error: {str(e)}")
        return make_response(jsonify({
            "status": "error",
            "message": str(e)
        }), 500)

@jobs_bp.route('/<int:posting_id>', methods=['DELETE'])
@login_required
@company_required
def delete_job_posting(posting_id):
    try:
        # TODO: Implement delete_posting method
        error = JobPosting.delete_posting(posting_id, g.company_id)
        if error:
            return make_response(jsonify({
                "status": "error",
                "message": error
            }), 400)

        return make_response(jsonify({
            "status": "success",
            "message": "Job posting deleted successfully"
        }), 200)

    except Exception as e:
        logging.error(f"Job posting deletion error: {str(e)}")
        return make_response(jsonify({
            "status": "error",
            "message": str(e)
        }), 500)