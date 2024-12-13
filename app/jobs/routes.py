from flask import Blueprint, request, jsonify, make_response, g
from app.jobs.models import JobPosting
from app.middleware.auth import login_required, company_required
import logging
from app.database import get_db

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

        db = get_db()
        cursor = db.cursor()
        
        try:
            # 현사 생성
            cursor.execute("""
                INSERT INTO companies (name) 
                VALUES (CONCAT('Company_', %s))
            """, (g.user_id,))
            
            company_id = cursor.lastrowid
            
            # 채용공고 생성
            cursor.execute("""
                INSERT INTO job_postings (
                    company_id, title, job_description, experience_level,
                    education_level, employment_type, salary_info,
                    location_id, deadline_date, status
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, 'active'
                )
            """, (
                company_id,
                data['title'],
                data['job_description'],
                data.get('experience_level'),
                data.get('education_level'),
                data.get('employment_type'),
                data.get('salary_info'),
                data.get('location_id'),
                data.get('deadline_date')
            ))
            
            posting_id = cursor.lastrowid
            
            # 카테고리 연결
            if 'categories' in data:
                for category_id in data['categories']:
                    cursor.execute("""
                        INSERT INTO posting_categories (posting_id, category_id)
                        VALUES (%s, %s)
                    """, (posting_id, category_id))
            
            # 기술 스택 연결
            if 'tech_stacks' in data:
                for stack_id in data['tech_stacks']:
                    cursor.execute("""
                        INSERT INTO job_tech_stacks (posting_id, stack_id)
                        VALUES (%s, %s)
                    """, (posting_id, stack_id))
            
            db.commit()
            
            return make_response(jsonify({
                "status": "success",
                "data": {"posting_id": posting_id}
            }), 201)
            
        except Exception as e:
            db.rollback()
            logging.error(f"Job posting creation error: {str(e)}")
            return make_response(jsonify({
                "status": "error",
                "message": str(e)
            }), 500)
        finally:
            cursor.close()

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