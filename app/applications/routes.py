from flask import Blueprint, request, jsonify, g
from app.common.middleware import login_required
from app.database import get_db
import logging
from datetime import datetime

applications_bp = Blueprint('applications', __name__)

@applications_bp.route('/apply', methods=['POST'])
@login_required
def apply_job():
    try:
        data = request.get_json()
        if not data.get('job_id'):
            return jsonify({
                "status": "error",
                "message": "Job ID is required"
            }), 400

        db = get_db()
        cursor = db.cursor(dictionary=True)

        # 이미 지원했는지 확인
        cursor.execute("""
            SELECT id FROM applications 
            WHERE user_id = %s AND job_id = %s AND status != 'cancelled'
        """, (g.user_id, data['job_id']))
        
        if cursor.fetchone():
            return jsonify({
                "status": "error",
                "message": "Already applied to this job"
            }), 409

        # 채용공고가 유효한지 확인
        cursor.execute("""
            SELECT deadline FROM jobs 
            WHERE id = %s AND status = 'active'
        """, (data['job_id'],))
        
        job = cursor.fetchone()
        if not job:
            return jsonify({
                "status": "error",
                "message": "Invalid or expired job posting"
            }), 404

        if job['deadline'] < datetime.now():
            return jsonify({
                "status": "error",
                "message": "Job application deadline has passed"
            }), 400

        # 지원 생성
        cursor.execute("""
            INSERT INTO applications (
                user_id, job_id, status, created_at
            ) VALUES (%s, %s, 'applied', NOW())
        """, (g.user_id, data['job_id']))
        
        application_id = cursor.lastrowid
        db.commit()

        return jsonify({
            "status": "success",
            "message": "Successfully applied to job",
            "data": {"application_id": application_id}
        }), 201

    except Exception as e:
        db.rollback()
        logging.error(f"Job application error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    finally:
        cursor.close()

@applications_bp.route('/cancel/<int:application_id>', methods=['POST'])
@login_required
def cancel_application(application_id):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        # 지원 내역 확인
        cursor.execute("""
            SELECT status FROM applications 
            WHERE id = %s AND user_id = %s
        """, (application_id, g.user_id))
        
        application = cursor.fetchone()
        if not application:
            return jsonify({
                "status": "error",
                "message": "Application not found"
            }), 404

        if application['status'] == 'cancelled':
            return jsonify({
                "status": "error",
                "message": "Application already cancelled"
            }), 400

        # 지원 취소
        cursor.execute("""
            UPDATE applications 
            SET status = 'cancelled', updated_at = NOW() 
            WHERE id = %s AND user_id = %s
        """, (application_id, g.user_id))
        
        db.commit()

        return jsonify({
            "status": "success",
            "message": "Application cancelled successfully"
        })

    except Exception as e:
        db.rollback()
        logging.error(f"Application cancellation error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    finally:
        cursor.close()

@applications_bp.route('/history', methods=['GET'])
@login_required
def get_application_history():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        # 페이지네이션
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        offset = (page - 1) * per_page

        # 지원 내역 조회
        cursor.execute("""
            SELECT SQL_CALC_FOUND_ROWS 
                a.*, j.title as job_title, 
                c.name as company_name
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            JOIN companies c ON j.company_id = c.id
            WHERE a.user_id = %s
            ORDER BY a.created_at DESC
            LIMIT %s OFFSET %s
        """, (g.user_id, per_page, offset))
        
        applications = cursor.fetchall()

        # 전체 결과 수 조회
        cursor.execute("SELECT FOUND_ROWS()")
        total = cursor.fetchone()['FOUND_ROWS()']

        return jsonify({
            "status": "success",
            "data": {
                "applications": applications,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "pages": (total + per_page - 1) // per_page
                }
            }
        })

    except Exception as e:
        logging.error(f"Application history fetch error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    finally:
        cursor.close() 