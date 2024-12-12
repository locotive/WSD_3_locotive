from app.database import get_db

class Bookmark:
    @staticmethod
    def toggle_bookmark(user_id: int, posting_id: int):
        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                SELECT bookmark_id FROM bookmarks 
                WHERE user_id=%s AND posting_id=%s
                """,
                (user_id, posting_id)
            )
            existing = cursor.fetchone()

            if existing:
                cursor.execute(
                    "DELETE FROM bookmarks WHERE bookmark_id=%s",
                    (existing['bookmark_id'],)
                )
                db.commit()
                return "Bookmark removed", None
            else:
                cursor.execute(
                    "INSERT INTO bookmarks(user_id, posting_id) VALUES(%s,%s)",
                    (user_id, posting_id)
                )
                db.commit()
                return "Bookmark added", cursor.lastrowid

        except Exception as e:
            db.rollback()
            return None, str(e)
        finally:
            cursor.close()

    @staticmethod
    def get_bookmarks(user_id: int, page: int = 1, sort: str = "desc"):
        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            query = """
            SELECT 
                b.bookmark_id, 
                b.posting_id, 
                jp.title,
                jp.job_description,
                jp.experience_level,
                jp.education_level,
                jp.employment_type,
                jp.salary_info,
                CONCAT(l.city, ' ', COALESCE(l.district, '')) as location,
                jp.deadline_date,
                jp.view_count,
                c.name as company_name,
                GROUP_CONCAT(DISTINCT ts.name) as tech_stacks,
                GROUP_CONCAT(DISTINCT jc.name) as job_categories
            FROM bookmarks b
            JOIN job_postings jp ON b.posting_id = jp.posting_id
            JOIN companies c ON jp.company_id = c.company_id
            LEFT JOIN locations l ON jp.location_id = l.location_id
            LEFT JOIN posting_tech_stacks pts ON jp.posting_id = pts.posting_id
            LEFT JOIN tech_stacks ts ON pts.stack_id = ts.stack_id
            LEFT JOIN posting_categories pc ON jp.posting_id = pc.posting_id
            LEFT JOIN job_categories jc ON pc.category_id = jc.category_id
            WHERE b.user_id = %s
            GROUP BY b.bookmark_id
            """

            query += " ORDER BY b.created_at " + ("ASC" if sort == "asc" else "DESC")

            page_size = 20
            offset = (page - 1) * page_size
            query += f" LIMIT {page_size} OFFSET {offset}"

            cursor.execute(query, (user_id,))
            bookmarks = cursor.fetchall()

            for bookmark in bookmarks:
                if bookmark['tech_stacks']:
                    bookmark['tech_stacks'] = bookmark['tech_stacks'].split(',')
                else:
                    bookmark['tech_stacks'] = []

                if bookmark['job_categories']:
                    bookmark['job_categories'] = bookmark['job_categories'].split(',')
                else:
                    bookmark['job_categories'] = []

            return bookmarks

        finally:
            cursor.close() 