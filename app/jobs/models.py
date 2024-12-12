from typing import Dict, List, Optional, Union
from app.database import get_db

class Job:
    @staticmethod
    def list_jobs(filters: Dict, page: int = 1) -> List[Dict]:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            query = """
            SELECT DISTINCT
                jp.posting_id,
                c.name as company_name,
                jp.title,
                jp.job_description,
                jp.experience_level,
                jp.education_level,
                jp.employment_type,
                jp.salary_info,
                jp.location_id,
                CONCAT(l.city, ' ', COALESCE(l.district, '')) as location,
                jp.deadline_date,
                jp.view_count,
                jp.created_at,
                GROUP_CONCAT(DISTINCT ts.name) as tech_stacks,
                GROUP_CONCAT(DISTINCT jc.name) as job_categories
            FROM job_postings jp
            JOIN companies c ON jp.company_id = c.company_id
            LEFT JOIN locations l ON jp.location_id = l.location_id
            LEFT JOIN posting_tech_stacks pts ON jp.posting_id = pts.posting_id
            LEFT JOIN tech_stacks ts ON pts.stack_id = ts.stack_id
            LEFT JOIN posting_categories pc ON jp.posting_id = pc.posting_id
            LEFT JOIN job_categories jc ON pc.category_id = jc.category_id
            WHERE jp.status = 'active'
            """

            params = []

            if filters.get('keyword'):
                query += " AND (jp.title LIKE %s OR jp.job_description LIKE %s)"
                params.extend([f"%{filters['keyword']}%", f"%{filters['keyword']}%"])
            
            if filters.get('company'):
                query += " AND c.name LIKE %s"
                params.append(f"%{filters['company']}%")
            
            if filters.get('employment_type'):
                query += " AND jp.employment_type = %s"
                params.append(filters['employment_type'])
            
            if filters.get('position'):
                query += " AND jp.title LIKE %s"
                params.append(f"%{filters['position']}%")

            if filters.get('location_id'):
                query += " AND jp.location_id = %s"
                params.append(filters['location_id'])
            
            if filters.get('salary_info'):
                query += " AND jp.salary_info LIKE %s"
                params.append(f"%{filters['salary_info']}%")
            
            if filters.get('experience_level'):
                query += " AND jp.experience_level = %s"
                params.append(filters['experience_level'])

            tech_stacks = filters.get('tech_stacks', [])
            if tech_stacks:
                query += f" AND ts.name IN ({','.join(['%s'] * len(tech_stacks))})"
                params.extend(tech_stacks)

            job_categories = filters.get('job_categories', [])
            if job_categories:
                query += f" AND jc.name IN ({','.join(['%s'] * len(job_categories))})"
                params.extend(job_categories)

            query += " GROUP BY jp.posting_id"

            valid_sort_fields = {
                'created_at': 'jp.created_at',
                'view_count': 'jp.view_count',
                'deadline_date': 'jp.deadline_date',
                'title': 'jp.title'
            }

            sort_field = valid_sort_fields.get(filters.get('sort_field'), 'jp.created_at')
            sort_direction = 'DESC' if filters.get('sort_order', 'desc').lower() == 'desc' else 'ASC'
            query += f" ORDER BY {sort_field} {sort_direction}"

            page_size = 20
            offset = (page - 1) * page_size
            query += f" LIMIT {page_size} OFFSET {offset}"

            cursor.execute(query, params)
            jobs = cursor.fetchall()

            for job in jobs:
                if job['tech_stacks']:
                    job['tech_stacks'] = job['tech_stacks'].split(',')
                else:
                    job['tech_stacks'] = []

                if job['job_categories']:
                    job['job_categories'] = job['job_categories'].split(',')
                else:
                    job['job_categories'] = []

            return jobs

        finally:
            cursor.close()

    @staticmethod
    def get_job_detail(job_id: int) -> Optional[Dict]:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            cursor.execute(
                "UPDATE job_postings SET view_count = view_count + 1 WHERE posting_id = %s",
                (job_id,)
            )
            db.commit()

            query = """
            SELECT 
                jp.*,
                c.name as company_name,
                l.city,
                l.district,
                GROUP_CONCAT(DISTINCT ts.name) as tech_stacks,
                GROUP_CONCAT(DISTINCT jc.name) as job_categories
            FROM job_postings jp
            JOIN companies c ON jp.company_id = c.company_id
            LEFT JOIN locations l ON jp.location_id = l.location_id
            LEFT JOIN posting_tech_stacks pts ON jp.posting_id = pts.posting_id
            LEFT JOIN tech_stacks ts ON pts.stack_id = ts.stack_id
            LEFT JOIN posting_categories pc ON jp.posting_id = pc.posting_id
            LEFT JOIN job_categories jc ON pc.category_id = jc.category_id
            WHERE jp.posting_id = %s AND jp.status != 'deleted'
            GROUP BY jp.posting_id
            """

            cursor.execute(query, (job_id,))
            job = cursor.fetchone()

            if not job:
                return None

            if job['tech_stacks']:
                job['tech_stacks'] = job['tech_stacks'].split(',')
            else:
                job['tech_stacks'] = []

            if job['job_categories']:
                job['job_categories'] = job['job_categories'].split(',')
            else:
                job['job_categories'] = []

            # Get related jobs
            related_query = """
            SELECT DISTINCT jp.posting_id, jp.title, c.name as company_name
            FROM job_postings jp
            JOIN companies c ON jp.company_id = c.company_id
            LEFT JOIN posting_tech_stacks pts ON jp.posting_id = pts.posting_id
            LEFT JOIN tech_stacks ts ON pts.stack_id = ts.stack_id
            WHERE jp.status = 'active' 
            AND jp.posting_id != %s
            AND (jp.company_id = %s 
                 OR ts.name IN (SELECT ts2.name 
                               FROM posting_tech_stacks pts2 
                               JOIN tech_stacks ts2 ON pts2.stack_id = ts2.stack_id 
                               WHERE pts2.posting_id = %s))
            ORDER BY RAND()
            LIMIT 5
            """

            cursor.execute(related_query, (job_id, job['company_id'], job_id))
            job['related_jobs'] = cursor.fetchall()

            return job

        finally:
            cursor.close()

    @staticmethod
    def create_job(job_data: Dict) -> Union[int, str]:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            # Handle location
            location_id = None
            if 'location' in job_data:
                cursor.execute(
                    """
                    SELECT location_id FROM locations 
                    WHERE city = %s AND (district = %s OR (district IS NULL AND %s IS NULL))
                    """,
                    (job_data['location']['city'], job_data['location'].get('district'),
                     job_data['location'].get('district'))
                )
                location_result = cursor.fetchone()

                if location_result:
                    location_id = location_result['location_id']
                else:
                    cursor.execute(
                        "INSERT INTO locations (city, district) VALUES (%s, %s)",
                        (job_data['location']['city'], job_data['location'].get('district'))
                    )
                    location_id = cursor.lastrowid

            # Insert job posting
            cursor.execute(
                """
                INSERT INTO job_postings(
                    company_id, title, job_description, experience_level,
                    education_level, employment_type, salary_info,
                    location_id, deadline_date, status, view_count
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'active', 0)
                """,
                (job_data['company_id'], job_data['title'], job_data['job_description'],
                 job_data.get('experience_level'), job_data.get('education_level'),
                 job_data.get('employment_type'), job_data.get('salary_info'),
                 location_id, job_data.get('deadline_date'))
            )

            posting_id = cursor.lastrowid

            # Handle tech stacks
            if job_data.get('tech_stacks'):
                for tech in job_data['tech_stacks']:
                    cursor.execute("SELECT stack_id FROM tech_stacks WHERE name = %s", (tech,))
                    result = cursor.fetchone()
                    if result:
                        stack_id = result['stack_id']
                    else:
                        cursor.execute(
                            "INSERT INTO tech_stacks (name, category) VALUES (%s, 'Other')",
                            (tech,)
                        )
                        stack_id = cursor.lastrowid

                    cursor.execute(
                        "INSERT INTO posting_tech_stacks (posting_id, stack_id) VALUES (%s, %s)",
                        (posting_id, stack_id)
                    )

            # Handle job categories
            if job_data.get('job_categories'):
                for category in job_data['job_categories']:
                    cursor.execute(
                        "SELECT category_id FROM job_categories WHERE name = %s",
                        (category,)
                    )
                    result = cursor.fetchone()
                    if result:
                        category_id = result['category_id']
                    else:
                        cursor.execute(
                            "INSERT INTO job_categories (name) VALUES (%s)",
                            (category,)
                        )
                        category_id = cursor.lastrowid

                    cursor.execute(
                        "INSERT INTO posting_categories (posting_id, category_id) VALUES (%s, %s)",
                        (posting_id, category_id)
                    )

            db.commit()
            return posting_id

        except Exception as e:
            db.rollback()
            return str(e)
        finally:
            cursor.close()

    @staticmethod
    def update_job(job_id: int, job_data: Dict) -> Optional[str]:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                SELECT jp.*, l.city, l.district 
                FROM job_postings jp
                LEFT JOIN locations l ON jp.location_id = l.location_id
                WHERE jp.posting_id = %s
                """,
                (job_id,)
            )
            if not cursor.fetchone():
                return "Job posting not found"

            updates = {}
            update_fields = [
                'title', 'job_description', 'experience_level', 'education_level',
                'employment_type', 'salary_info', 'deadline_date', 'status'
            ]

            for field in update_fields:
                if field in job_data:
                    updates[field] = job_data[field]

            if 'location' in job_data:
                cursor.execute(
                    """
                    SELECT location_id FROM locations 
                    WHERE city = %s AND (district = %s OR (district IS NULL AND %s IS NULL))
                    """,
                    (job_data['location']['city'], job_data['location'].get('district'),
                     job_data['location'].get('district'))
                )
                location_result = cursor.fetchone()

                if location_result:
                    updates['location_id'] = location_result['location_id']
                else:
                    cursor.execute(
                        "INSERT INTO locations (city, district) VALUES (%s, %s)",
                        (job_data['location']['city'], job_data['location'].get('district'))
                    )
                    updates['location_id'] = cursor.lastrowid

            if updates:
                set_clause = ", ".join(f"{key} = %s" for key in updates)
                query = f"UPDATE job_postings SET {set_clause} WHERE posting_id = %s"
                cursor.execute(query, list(updates.values()) + [job_id])

            if 'tech_stacks' in job_data:
                cursor.execute("DELETE FROM posting_tech_stacks WHERE posting_id = %s", (job_id,))
                for tech in job_data['tech_stacks']:
                    cursor.execute("SELECT stack_id FROM tech_stacks WHERE name = %s", (tech,))
                    result = cursor.fetchone()
                    if result:
                        stack_id = result['stack_id']
                    else:
                        cursor.execute(
                            "INSERT INTO tech_stacks (name) VALUES (%s)",
                            (tech,)
                        )
                        stack_id = cursor.lastrowid

                    cursor.execute(
                        """
                        INSERT INTO posting_tech_stacks (posting_id, stack_id)
                        VALUES (%s, %s)
                        """,
                        (job_id, stack_id)
                    )

            if 'job_categories' in job_data:
                cursor.execute("DELETE FROM posting_categories WHERE posting_id = %s", (job_id,))
                for category in job_data['job_categories']:
                    cursor.execute(
                        "SELECT category_id FROM job_categories WHERE name = %s",
                        (category,)
                    )
                    result = cursor.fetchone()
                    if result:
                        category_id = result['category_id']
                    else:
                        cursor.execute(
                            "INSERT INTO job_categories (name) VALUES (%s)",
                            (category,)
                        )
                        category_id = cursor.lastrowid

                    cursor.execute(
                        """
                        INSERT INTO posting_categories (posting_id, category_id)
                        VALUES (%s, %s)
                        """,
                        (job_id, category_id)
                    )

            db.commit()
            return None

        except Exception as e:
            db.rollback()
            return str(e)
        finally:
            cursor.close()

    @staticmethod
    def delete_job(job_id: int) -> Optional[str]:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            cursor.execute(
                "SELECT status FROM job_postings WHERE posting_id = %s",
                (job_id,)
            )
            job = cursor.fetchone()

            if not job:
                return "Job posting not found"

            if job['status'] == 'deleted':
                return "Job posting already deleted"

            cursor.execute(
                "UPDATE job_postings SET status='deleted' WHERE posting_id=%s",
                (job_id,)
            )
            db.commit()
            return None

        except Exception as e:
            db.rollback()
            return str(e)
        finally:
            cursor.close() 