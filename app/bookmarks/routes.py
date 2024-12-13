from flask import Blueprint, request, jsonify, g
from app.common.middleware import login_required
from app.database import get_db
import logging

bookmarks_bp = Blueprint('bookmarks', __name__)

@bookmarks_bp.route('/add', methods=['POST'])
@login_required
def add_bookmark():
    try:
        data = request.get_json()
        if not data.get('job_id'):
            return jsonify({
                "status": "error",
                "message": "Job ID is required"
            }), 400

        db = get_db()
        cursor = db.cursor(dictionary=True)

        # 이미 북마크했는지 확인
        cursor.execute("""
            SELECT id FROM bookmarks 
            WHERE user_id = %s AND job_id = %s AND status = 'active'
        """, (g.user_id, data['job_id']))
        
        if cursor.fetchone():
            return jsonify({
                "status": "error",
                "message": "Job already bookmarked"
            }), 409

        # 채용공고가 유효한지 확인
        cursor.execute("""
            SELECT id FROM jobs 
            WHERE id = %s AND status = 'active'
        """, (data['job_id'],))
        
        if not cursor.fetchone():
            return jsonify({
                "status": "error",
                "message": "Invalid job posting"
            }), 404

        # 북마크 추가
        cursor.execute("""
            INSERT INTO bookmarks (
                user_id, job_id, status, created_at
            ) VALUES (%s, %s, 'active', NOW())
        """, (g.user_id, data['job_id']))
        
        bookmark_id = cursor.lastrowid
        db.commit()

        return jsonify({
            "status": "success",
            "message": "Job bookmarked successfully",
            "data": {"bookmark_id": bookmark_id}
        }), 201

    except Exception as e:
        db.rollback()
        logging.error(f"Bookmark creation error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    finally:
        cursor.close()

@bookmarks_bp.route('/remove/<int:job_id>', methods=['DELETE'])
@login_required
def remove_bookmark(job_id):
    try:
        db = get_db()
        cursor = db.cursor()

        # 북마크 삭제 (소프트 딜리트)
        cursor.execute("""
            UPDATE bookmarks 
            SET status = 'deleted', updated_at = NOW() 
            WHERE user_id = %s AND job_id = %s AND status = 'active'
        """, (g.user_id, job_id))
        
        if cursor.rowcount == 0:
            return jsonify({
                "status": "error",
                "message": "Bookmark not found"
            }), 404

        db.commit()

        return jsonify({
            "status": "success",
            "message": "Bookmark removed successfully"
        })

    except Exception as e:
        db.rollback()
        logging.error(f"Bookmark removal error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    finally:
        cursor.close()

@bookmarks_bp.route('', methods=['GET'])
@login_required
def get_bookmarks():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        offset = (page - 1) * per_page

        # 컬럼명 수정: job_id -> posting_id
        cursor.execute("""
            SELECT SQL_CALC_FOUND_ROWS 
                b.bookmark_id, b.posting_id, b.created_at,
                j.title as job_title, 
                j.deadline_date as deadline, j.salary_info as salary,
                c.name as company_name,
                l.city as company_location
            FROM bookmarks b
            JOIN job_postings j ON b.posting_id = j.posting_id
            JOIN companies c ON j.company_id = c.company_id
            LEFT JOIN locations l ON j.location_id = l.location_id
            WHERE b.user_id = %s
            ORDER BY b.created_at DESC
            LIMIT %s OFFSET %s
        """, (g.user_id, per_page, offset))
        
        bookmarks = cursor.fetchall()

        cursor.execute("SELECT FOUND_ROWS()")
        total = cursor.fetchone()['FOUND_ROWS()']

        return jsonify({
            "status": "success",
            "data": {
                "bookmarks": bookmarks,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "pages": (total + per_page - 1) // per_page
                }
            }
        })

    except Exception as e:
        logging.error(f"Bookmarks fetch error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    finally:
        cursor.close()

@bookmarks_bp.route('/check/<int:job_id>', methods=['GET'])
@login_required
def check_bookmark(job_id):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT id FROM bookmarks 
            WHERE user_id = %s AND job_id = %s AND status = 'active'
        """, (g.user_id, job_id))
        
        is_bookmarked = bool(cursor.fetchone())

        return jsonify({
            "status": "success",
            "data": {
                "is_bookmarked": is_bookmarked
            }
        })

    except Exception as e:
        logging.error(f"Bookmark check error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    finally:
        cursor.close() 