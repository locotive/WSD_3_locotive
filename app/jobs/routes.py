from flask import Blueprint, request, jsonify, make_response, g
from app.jobs.models import JobPosting
from app.middleware.auth import login_required, company_required
import logging
from app.database import get_db
from app.config.location_config import LocationConfig
from app.config.job_config import JobConfig

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
        # 기존 상세 정보 조회
        posting, error = JobPosting.get_posting(posting_id)
        if error:
            return make_response(jsonify({
                "status": "error",
                "message": error
            }), 404)

        # 관련 공고 추천 추가
        related_jobs, _ = JobPosting.get_related_jobs(posting_id, limit=5)

        return make_response(jsonify({
            "status": "success",
            "data": {
                "posting": posting,
                "related_jobs": related_jobs
            }
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
            # 회사 생성
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
                    location_id, deadline_date
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
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
                for tech_stack_id in data['tech_stacks']:
                    cursor.execute("""
                        INSERT INTO posting_tech_stacks (posting_id, stack_id)
                        VALUES (%s, %s)
                    """, (posting_id, tech_stack_id))
            
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
def update_job_posting(posting_id):
    try:
        data = request.get_json()
        db = get_db()
        cursor = db.cursor()
        
        try:
            # 해당 채용공고의 작성자 확인
            cursor.execute("""
                SELECT jp.company_id 
                FROM job_postings jp
                JOIN companies c ON jp.company_id = c.company_id
                WHERE jp.posting_id = %s 
                AND c.name = CONCAT('Company_', %s)
            """, (posting_id, g.user_id))
            
            result = cursor.fetchone()
            if not result:
                return make_response(jsonify({
                    "status": "error",
                    "message": "Permission denied or posting not found"
                }), 403)
                
            # 채용공고 업데이트
            cursor.execute("""
                UPDATE job_postings SET
                    title = %s,
                    job_description = %s,
                    experience_level = %s,
                    education_level = %s,
                    employment_type = %s,
                    salary_info = %s,
                    location_id = %s,
                    deadline_date = %s
                WHERE posting_id = %s
            """, (
                data['title'],
                data['job_description'],
                data.get('experience_level'),
                data.get('education_level'),
                data.get('employment_type'),
                data.get('salary_info'),
                data.get('location_id'),
                data.get('deadline_date'),
                posting_id
            ))
            
            # 기존 카테고리 삭제
            cursor.execute("""
                DELETE FROM posting_categories 
                WHERE posting_id = %s
            """, (posting_id,))
            
            # 새 카테고리 연결
            if 'categories' in data:
                for category_id in data['categories']:
                    cursor.execute("""
                        INSERT INTO posting_categories (posting_id, category_id)
                        VALUES (%s, %s)
                    """, (posting_id, category_id))
            
            # 기존 기술 스택 삭제
            cursor.execute("""
                DELETE FROM job_tech_stacks 
                WHERE posting_id = %s
            """, (posting_id,))
            
            # 새 기술 스택 연결
            if 'tech_stacks' in data:
                for stack_id in data['tech_stacks']:
                    cursor.execute("""
                        INSERT INTO job_tech_stacks (posting_id, stack_id)
                        VALUES (%s, %s)
                    """, (posting_id, stack_id))
            
            db.commit()
            
            return make_response(jsonify({
                "status": "success",
                "message": "Job posting updated successfully"
            }), 200)
            
        except Exception as e:
            db.rollback()
            logging.error(f"Job posting update error: {str(e)}")
            return make_response(jsonify({
                "status": "error",
                "message": str(e)
            }), 500)
        finally:
            cursor.close()
            
    except Exception as e:
        logging.error(f"Job posting update error: {str(e)}")
        return make_response(jsonify({
            "status": "error",
            "message": str(e)
        }), 500)

@jobs_bp.route('/<int:posting_id>', methods=['DELETE'])
@login_required
def delete_job_posting(posting_id):
    try:
        db = get_db()
        cursor = db.cursor()
        
        try:
            # 해당 채용공고의 작성자 확인
            cursor.execute("""
                SELECT jp.company_id 
                FROM job_postings jp
                JOIN companies c ON jp.company_id = c.company_id
                WHERE jp.posting_id = %s 
                AND c.name = CONCAT('Company_', %s)
            """, (posting_id, g.user_id))
            
            result = cursor.fetchone()
            if not result:
                return make_response(jsonify({
                    "status": "error",
                    "message": "Permission denied or posting not found"
                }), 403)
            
            # 채용공고 삭제 (또는 soft delete)
            cursor.execute("""
                UPDATE job_postings 
                SET status = 'deleted', deleted_at = CURRENT_TIMESTAMP
                WHERE posting_id = %s
            """, (posting_id,))
            
            db.commit()
            
            return make_response(jsonify({
                "status": "success",
                "message": "Job posting deleted successfully"
            }), 200)
            
        except Exception as e:
            db.rollback()
            logging.error(f"Job posting deletion error: {str(e)}")
            return make_response(jsonify({
                "status": "error",
                "message": str(e)
            }), 500)
        finally:
            cursor.close()
            
    except Exception as e:
        logging.error(f"Job posting deletion error: {str(e)}")
        return make_response(jsonify({
            "status": "error",
            "message": str(e)
        }), 500)