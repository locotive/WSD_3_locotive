from flask import Blueprint, request, jsonify
from app.common.middleware import login_required
from app.database import get_db
import logging

jobs_bp = Blueprint('jobs', __name__)

@jobs_bp.route('', methods=['GET'])
def get_jobs():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        # 페이지네이션 파라미터
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        offset = (page - 1) * per_page

        # 필터링 파라미터
        filters = {
            'location': request.args.get('location'),
            'experience': request.args.get('experience'),
            'education': request.args.get('education'),
            'salary_min': request.args.get('salary_min'),
            'salary_max': request.args.get('salary_max'),
            'keyword': request.args.get('keyword')
        }

        # 정렬 파라미터
        sort = request.args.get('sort', 'created_at')
        order = request.args.get('order', 'desc')

        # 기본 쿼리
        query = """
            SELECT SQL_CALC_FOUND_ROWS 
                j.*, c.name as company_name, 
                c.location as company_location
            FROM jobs j
            JOIN companies c ON j.company_id = c.id
            WHERE j.status = 'active'
        """
        params = []

        # 필터 조건 추가
        if filters['location']:
            query += " AND c.location LIKE %s"
            params.append(f"%{filters['location']}%")
        
        if filters['experience']:
            query += " AND j.experience = %s"
            params.append(filters['experience'])
            
        if filters['education']:
            query += " AND j.education = %s"
            params.append(filters['education'])
            
        if filters['salary_min']:
            query += " AND j.salary >= %s"
            params.append(filters['salary_min'])
            
        if filters['salary_max']:
            query += " AND j.salary <= %s"
            params.append(filters['salary_max'])
            
        if filters['keyword']:
            query += """ AND (
                j.title LIKE %s OR 
                j.description LIKE %s OR
                c.name LIKE %s
            )"""
            keyword = f"%{filters['keyword']}%"
            params.extend([keyword] * 3)

        # 정렬 추가
        query += f" ORDER BY {sort} {order}"

        # 페이지네이션 추가
        query += " LIMIT %s OFFSET %s"
        params.extend([per_page, offset])

        # 쿼리 실행
        cursor.execute(query, params)
        jobs = cursor.fetchall()

        # 전체 결과 수 조회
        cursor.execute("SELECT FOUND_ROWS()")
        total = cursor.fetchone()['FOUND_ROWS()']

        return jsonify({
            "status": "success",
            "data": {
                "jobs": jobs,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "pages": (total + per_page - 1) // per_page
                }
            }
        })

    except Exception as e:
        logging.error(f"Jobs fetch error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    finally:
        cursor.close()