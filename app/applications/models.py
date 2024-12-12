from app.database import get_db
import logging
from datetime import datetime

class Application:
    @staticmethod
    def apply_job(user_id: int, posting_id: int, resume_id: int):
        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            # 채용공고 유효성 확인
            cursor.execute("""
                SELECT posting_id 
                FROM job_postings 
                WHERE posting_id = %s AND status = 'active'
                AND deadline_date >= CURDATE()
            """, (posting_id,))
            
            if not cursor.fetchone():
                return None, "Invalid or expired job posting"

            # 이력서 유효성 확인
            cursor.execute("""
                SELECT resume_id 
                FROM resumes 
                WHERE resume_id = %s AND user_id = %s
            """, (resume_id, user_id))
            
            if not cursor.fetchone():
                return None, "Invalid resume"

            # 중복 지원 확인
            cursor.execute("""
                SELECT application_id 
                FROM applications 
                WHERE user_id = %s AND posting_id = %s AND status != 'cancelled'
            """, (user_id, posting_id))
            
            if cursor.fetchone():
                return None, "Already applied to this posting"

            # 지원 생성
            cursor.execute("""
                INSERT INTO applications (user_id, posting_id, resume_id, status)
                VALUES (%s, %s, %s, 'pending')
            """, (user_id, posting_id, resume_id))
            
            application_id = cursor.lastrowid
            db.commit()

            return application_id, None

        except Exception as e:
            db.rollback()
            logging.error(f"Application creation error: {str(e)}")
            return None, str(e)
        finally:
            cursor.close()

    @staticmethod
    def cancel_application(user_id: int, application_id: int):
        db = get_db()
        cursor = db.cursor()

        try:
            # 지원 내역 확인
            cursor.execute("""
                SELECT status 
                FROM applications 
                WHERE application_id = %s AND user_id = %s
            """, (application_id, user_id))
            
            application = cursor.fetchone()
            if not application:
                return "Application not found"
            
            if application[0] == 'cancelled':
                return "Application already cancelled"

            # 지원 취소
            cursor.execute("""
                UPDATE applications 
                SET status = 'cancelled' 
                WHERE application_id = %s AND user_id = %s
            """, (application_id, user_id))
            
            db.commit()
            return None

        except Exception as e:
            db.rollback()
            logging.error(f"Application cancellation error: {str(e)}")
            return str(e)
        finally:
            cursor.close()

    @staticmethod
    def get_user_applications(user_id: int, page: int = 1, per_page: int = 10):
        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            # 지원 내역 조회
            cursor.execute("""
                SELECT 
                    a.*,
                    j.title as posting_title,
                    j.deadline_date,
                    c.name as company_name,
                    r.title as resume_title
                FROM applications a
                JOIN job_postings j ON a.posting_id = j.posting_id
                JOIN companies c ON j.company_id = c.company_id
                JOIN resumes r ON a.resume_id = r.resume_id
                WHERE a.user_id = %s
                ORDER BY a.applied_at DESC
                LIMIT %s OFFSET %s
            """, (user_id, per_page, (page - 1) * per_page))
            
            applications = cursor.fetchall()

            # 전체 개수 조회
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM applications
                WHERE user_id = %s
            """, (user_id,))
            
            total = cursor.fetchone()['total']

            return {
                'applications': applications,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }, None

        except Exception as e:
            logging.error(f"Applications fetch error: {str(e)}")
            return None, str(e)
        finally:
            cursor.close() 