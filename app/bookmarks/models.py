from app.database import get_db
import logging

class Bookmark:
    @staticmethod
    def check_bookmark(user_id: int, job_id: int):
        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT bookmark_id 
                FROM bookmarks 
                WHERE user_id = %s AND posting_id = %s
            """, (user_id, job_id))
            
            exists = cursor.fetchone() is not None
            return {"is_bookmarked": exists}, None

        except Exception as e:
            logging.error(f"Bookmark check error: {str(e)}")
            return None, str(e)
        finally:
            cursor.close()

    @staticmethod
    def add_bookmark(user_id: int, job_id: int):
        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            # 채용공고 유효성 확인
            cursor.execute("""
                SELECT posting_id 
                FROM job_postings 
                WHERE posting_id = %s AND status = 'active'
            """, (job_id,))
            
            if not cursor.fetchone():
                return None, "Invalid job posting"

            # 이미 북마크 되어있는지 확인
            cursor.execute("""
                SELECT bookmark_id 
                FROM bookmarks 
                WHERE user_id = %s AND posting_id = %s
            """, (user_id, job_id))
            
            if cursor.fetchone():
                return None, "Already bookmarked"

            # 북마크 추가
            cursor.execute("""
                INSERT INTO bookmarks (user_id, posting_id)
                VALUES (%s, %s)
            """, (user_id, job_id))
            
            bookmark_id = cursor.lastrowid
            db.commit()
            return {"bookmark_id": bookmark_id}, None

        except Exception as e:
            db.rollback()
            logging.error(f"Bookmark add error: {str(e)}")
            return None, str(e)
        finally:
            cursor.close()

    @staticmethod
    def remove_bookmark(user_id: int, job_id: int):
        db = get_db()
        cursor = db.cursor()

        try:
            # 북마크 존재 확인
            cursor.execute("""
                SELECT bookmark_id 
                FROM bookmarks 
                WHERE user_id = %s AND posting_id = %s
            """, (user_id, job_id))
            
            bookmark = cursor.fetchone()
            if not bookmark:
                return None, "Bookmark not found"

            # 북마크 삭제
            cursor.execute("""
                DELETE FROM bookmarks 
                WHERE user_id = %s AND posting_id = %s
            """, (user_id, job_id))
            
            db.commit()
            return {"message": "Bookmark removed successfully"}, None

        except Exception as e:
            db.rollback()
            logging.error(f"Bookmark remove error: {str(e)}")
            return None, str(e)
        finally:
            cursor.close()

    @staticmethod
    def get_user_bookmarks(user_id: int, page: int = 1, per_page: int = 10):
        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            # 북마크 목록 조회
            cursor.execute("""
                SELECT 
                    b.bookmark_id,
                    b.created_at as bookmarked_at,
                    j.posting_id,
                    j.title,
                    j.experience_level,
                    j.employment_type,
                    j.salary_info,
                    j.deadline_date,
                    c.company_id,
                    c.name as company_name,
                    l.city,
                    l.district,
                    GROUP_CONCAT(DISTINCT ts.name) as tech_stacks
                FROM bookmarks b
                JOIN job_postings j ON b.posting_id = j.posting_id
                JOIN companies c ON j.company_id = c.company_id
                LEFT JOIN locations l ON j.location_id = l.location_id
                LEFT JOIN posting_tech_stacks pts ON j.posting_id = pts.posting_id
                LEFT JOIN tech_stacks ts ON pts.stack_id = ts.stack_id
                WHERE b.user_id = %s AND j.status = 'active'
                GROUP BY b.bookmark_id
                ORDER BY b.created_at DESC
                LIMIT %s OFFSET %s
            """, (user_id, per_page, (page - 1) * per_page))
            
            bookmarks = cursor.fetchall()

            # 전체 개수 조회
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM bookmarks b
                JOIN job_postings j ON b.posting_id = j.posting_id
                WHERE b.user_id = %s AND j.status = 'active'
            """, (user_id,))
            
            total = cursor.fetchone()['total']

            return {
                'bookmarks': bookmarks,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }, None

        except Exception as e:
            logging.error(f"Bookmarks fetch error: {str(e)}")
            return None, str(e)
        finally:
            cursor.close()