from app.database import get_db
import logging
from datetime import datetime

class Resume:
    @staticmethod
    def create_resume(user_id: int, data: dict):
        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            # 기본 이력서가 있는지 확인
            cursor.execute(
                "SELECT COUNT(*) as count FROM resumes WHERE user_id = %s",
                (user_id,)
            )
            result = cursor.fetchone()
            is_primary = result['count'] == 0  # 첫 이력서면 기본 이력서로 설정

            cursor.execute("""
                INSERT INTO resumes (
                    user_id, title, content, is_primary
                ) VALUES (%s, %s, %s, %s)
            """, (
                user_id,
                data['title'],
                data['content'],
                is_primary
            ))
            
            resume_id = cursor.lastrowid
            db.commit()
            return resume_id, None

        except Exception as e:
            db.rollback()
            logging.error(f"Resume creation error: {str(e)}")
            return None, str(e)
        finally:
            cursor.close()

    @staticmethod
    def get_user_resumes(user_id: int):
        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT * FROM resumes 
                WHERE user_id = %s 
                ORDER BY is_primary DESC, created_at DESC
            """, (user_id,))
            
            return cursor.fetchall(), None

        except Exception as e:
            logging.error(f"Resume fetch error: {str(e)}")
            return None, str(e)
        finally:
            cursor.close()

    @staticmethod
    def get_resume(resume_id: int, user_id: int):
        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT * FROM resumes 
                WHERE resume_id = %s AND user_id = %s
            """, (resume_id, user_id))
            
            resume = cursor.fetchone()
            if not resume:
                return None, "Resume not found"
                
            return resume, None

        except Exception as e:
            logging.error(f"Resume fetch error: {str(e)}")
            return None, str(e)
        finally:
            cursor.close()

    @staticmethod
    def update_resume(resume_id: int, user_id: int, data: dict):
        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            # 이력서 존재 확인
            cursor.execute("""
                SELECT resume_id FROM resumes 
                WHERE resume_id = %s AND user_id = %s
            """, (resume_id, user_id))
            
            if not cursor.fetchone():
                return "Resume not found"

            # 업데이트할 필드 설정
            update_fields = []
            update_values = []
            
            if 'title' in data:
                update_fields.append("title = %s")
                update_values.append(data['title'])
            
            if 'content' in data:
                update_fields.append("content = %s")
                update_values.append(data['content'])

            if update_fields:
                update_values.extend([resume_id, user_id])
                query = f"""
                    UPDATE resumes 
                    SET {', '.join(update_fields)}
                    WHERE resume_id = %s AND user_id = %s
                """
                cursor.execute(query, update_values)
                db.commit()

            return None

        except Exception as e:
            db.rollback()
            logging.error(f"Resume update error: {str(e)}")
            return str(e)
        finally:
            cursor.close()

    @staticmethod
    def delete_resume(resume_id: int, user_id: int):
        db = get_db()
        cursor = db.cursor()

        try:
            # 이력서 존재 확인
            cursor.execute("""
                SELECT is_primary FROM resumes 
                WHERE resume_id = %s AND user_id = %s
            """, (resume_id, user_id))
            
            resume = cursor.fetchone()
            if not resume:
                return "Resume not found"

            # 기본 이력서는 삭제 불가
            if resume[0]:  # is_primary
                return "Cannot delete primary resume"

            cursor.execute("""
                DELETE FROM resumes 
                WHERE resume_id = %s AND user_id = %s
            """, (resume_id, user_id))
            
            db.commit()
            return None

        except Exception as e:
            db.rollback()
            logging.error(f"Resume deletion error: {str(e)}")
            return str(e)
        finally:
            cursor.close()