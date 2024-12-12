from app.database import get_db
from datetime import datetime

class Application:
    @staticmethod
    def create_application(user_id: int, posting_id: int, resume_id: int = None, resume_file_content = None):
        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            # Check for existing application
            cursor.execute(
                """
                SELECT application_id FROM applications 
                WHERE user_id=%s AND posting_id=%s
                """,
                (user_id, posting_id)
            )
            if cursor.fetchone():
                return None, "Already applied for this job posting"

            # If resume file is provided, create new resume
            if resume_file_content:
                cursor.execute(
                    """
                    INSERT INTO resumes(user_id, title, content, is_primary)
                    VALUES(%s, %s, %s, 0)
                    """,
                    (user_id, f"Resume {datetime.now()}", resume_file_content)
                )
                db.commit()
                resume_id = cursor.lastrowid

            # Verify resume ownership
            if resume_id:
                cursor.execute(
                    "SELECT resume_id FROM resumes WHERE resume_id=%s AND user_id=%s",
                    (resume_id, user_id)
                )
                if not cursor.fetchone():
                    return None, "Not authorized to use this resume"

            # Create application
            cursor.execute(
                """
                INSERT INTO applications(user_id, posting_id, resume_id, status)
                VALUES (%s, %s, %s, 'pending')
                """,
                (user_id, posting_id, resume_id)
            )
            db.commit()
            return cursor.lastrowid, None

        except Exception as e:
            db.rollback()
            return None, str(e)
        finally:
            cursor.close()

    @staticmethod
    def get_applications(user_id: int, status_filter: str = None, sort_by_date: str = "desc", page: int = 1):
        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            query = """
            SELECT a.application_id, a.posting_id, jp.title, a.status, a.applied_at
            FROM applications a
            JOIN job_postings jp ON a.posting_id=jp.posting_id
            WHERE a.user_id=%s
            """
            params = [user_id]

            if status_filter:
                query += " AND a.status=%s"
                params.append(status_filter)

            query += " ORDER BY a.applied_at " + ("ASC" if sort_by_date == "asc" else "DESC")

            page_size = 20
            offset = (page - 1) * page_size
            query += f" LIMIT {page_size} OFFSET {offset}"

            cursor.execute(query, params)
            return cursor.fetchall()

        finally:
            cursor.close()

    @staticmethod
    def delete_application(application_id: int, user_id: int):
        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            cursor.execute(
                "SELECT user_id FROM applications WHERE application_id=%s",
                (application_id,)
            )
            application = cursor.fetchone()

            if not application:
                return "Application not found"
            
            if application['user_id'] != user_id:
                return "Not authorized to cancel this application"

            cursor.execute(
                "DELETE FROM applications WHERE application_id=%s",
                (application_id,)
            )
            db.commit()
            return None

        except Exception as e:
            db.rollback()
            return str(e)
        finally:
            cursor.close() 