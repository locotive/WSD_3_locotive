from typing import Dict, List, Optional, Union
from app.database import get_db
import logging
from datetime import datetime

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

class JobPosting:
    @staticmethod
    def create_posting(company_id: int, data: dict):
        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            # 채용공고 기본 정보 입력
            cursor.execute("""
                INSERT INTO job_postings (
                    company_id, title, job_description, 
                    experience_level, education_level,
                    employment_type, salary_info, location_id,
                    deadline_date, status
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, 'active'
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

            # 직무 카테고리 연결
            if 'categories' in data:
                for category_id in data['categories']:
                    cursor.execute("""
                        INSERT INTO posting_categories (posting_id, category_id)
                        VALUES (%s, %s)
                    """, (posting_id, category_id))

            # 기술 스택 연결
            if 'tech_stacks' in data:
                for stack_id in data['tech_stacks']:
                    cursor.execute("""
                        INSERT INTO posting_tech_stacks (posting_id, stack_id)
                        VALUES (%s, %s)
                    """, (posting_id, stack_id))

            db.commit()
            return posting_id, None

        except Exception as e:
            db.rollback()
            logging.error(f"Posting creation error: {str(e)}")
            return None, str(e)
        finally:
            cursor.close()

    @staticmethod
    def get_posting(posting_id: int):
        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            # 채용공고 기본 정보 조회
            cursor.execute("""
                SELECT 
                    p.*,
                    c.name as company_name,
                    c.description as company_description,
                    l.city, l.district,
                    GROUP_CONCAT(DISTINCT jc.name) as categories,
                    GROUP_CONCAT(DISTINCT ts.name) as tech_stacks
                FROM job_postings p
                LEFT JOIN companies c ON p.company_id = c.company_id
                LEFT JOIN locations l ON p.location_id = l.location_id
                LEFT JOIN posting_categories pc ON p.posting_id = pc.posting_id
                LEFT JOIN job_categories jc ON pc.category_id = jc.category_id
                LEFT JOIN posting_tech_stacks pts ON p.posting_id = pts.posting_id
                LEFT JOIN tech_stacks ts ON pts.stack_id = ts.stack_id
                WHERE p.posting_id = %s AND p.status = 'active'
                GROUP BY p.posting_id
            """, (posting_id,))
            
            posting = cursor.fetchone()
            if not posting:
                return None, "Posting not found"

            # 조회수 증가
            cursor.execute("""
                UPDATE job_postings 
                SET view_count = view_count + 1 
                WHERE posting_id = %s
            """, (posting_id,))
            
            db.commit()
            return posting, None

        except Exception as e:
            db.rollback()
            logging.error(f"Posting fetch error: {str(e)}")
            return None, str(e)
        finally:
            cursor.close()

    @staticmethod
    def search_postings(filters: dict = None, sort_by: str = None, page: int = 1, per_page: int = 10):
        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            # 기본 쿼리 구성
            query = """
                SELECT 
                    p.*,
                    c.name as company_name,
                    l.city, l.district,
                    GROUP_CONCAT(DISTINCT jc.name) as categories,
                    GROUP_CONCAT(DISTINCT ts.name) as tech_stacks
                FROM job_postings p
                LEFT JOIN companies c ON p.company_id = c.company_id
                LEFT JOIN locations l ON p.location_id = l.location_id
                LEFT JOIN posting_categories pc ON p.posting_id = pc.posting_id
                LEFT JOIN job_categories jc ON pc.category_id = jc.category_id
                LEFT JOIN posting_tech_stacks pts ON p.posting_id = pts.posting_id
                LEFT JOIN tech_stacks ts ON pts.stack_id = ts.stack_id
                WHERE p.status = 'active'
            """
            params = []

            # 필터 적용
            if filters:
                if 'search' in filters:
                    query += " AND (p.title LIKE %s OR p.job_description LIKE %s)"
                    search_term = f"%{filters['search']}%"
                    params.extend([search_term, search_term])
                
                if 'location_id' in filters:
                    query += " AND p.location_id = %s"
                    params.append(filters['location_id'])
                
                if 'categories' in filters:
                    query += " AND jc.category_id IN (%s)"
                    params.append(filters['categories'])
                
                if 'tech_stacks' in filters:
                    query += " AND ts.stack_id IN (%s)"
                    params.append(filters['tech_stacks'])

            # 그룹화
            query += " GROUP BY p.posting_id"

            # 정렬
            if sort_by == 'latest':
                query += " ORDER BY p.created_at DESC"
            elif sort_by == 'views':
                query += " ORDER BY p.view_count DESC"
            elif sort_by == 'deadline':
                query += " ORDER BY p.deadline_date ASC"

            # 페이지네이션
            query += " LIMIT %s OFFSET %s"
            params.extend([per_page, (page - 1) * per_page])

            cursor.execute(query, params)
            postings = cursor.fetchall()

            # 전체 결과 수 조회
            count_query = """
                SELECT COUNT(DISTINCT p.posting_id) as total
                FROM job_postings p
                LEFT JOIN posting_categories pc ON p.posting_id = pc.posting_id
                LEFT JOIN posting_tech_stacks pts ON p.posting_id = pts.posting_id
                WHERE p.status = 'active'
            """
            cursor.execute(count_query)
            total = cursor.fetchone()['total']

            return {
                'postings': postings,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }, None

        except Exception as e:
            logging.error(f"Posting search error: {str(e)}")
            return None, str(e)
        finally:
            cursor.close()

    @staticmethod
    def update_posting(posting_id: int, company_id: int, data: dict):
        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            # 채용공고 존재 여부 및 권한 확인
            cursor.execute("""
                SELECT posting_id 
                FROM job_postings 
                WHERE posting_id = %s AND company_id = %s AND status = 'active'
            """, (posting_id, company_id))
            
            if not cursor.fetchone():
                return "Posting not found or unauthorized"

            # 기본 정보 업데이트
            update_fields = []
            update_values = []
            
            field_mappings = {
                'title': 'title',
                'job_description': 'job_description',
                'experience_level': 'experience_level',
                'education_level': 'education_level',
                'employment_type': 'employment_type',
                'salary_info': 'salary_info',
                'location_id': 'location_id',
                'deadline_date': 'deadline_date'
            }

            for key, field in field_mappings.items():
                if key in data:
                    update_fields.append(f"{field} = %s")
                    update_values.append(data[key])

            if update_fields:
                update_values.extend([posting_id, company_id])
                query = f"""
                    UPDATE job_postings 
                    SET {', '.join(update_fields)}
                    WHERE posting_id = %s AND company_id = %s
                """
                cursor.execute(query, update_values)

            # 직무 카테고리 업데이트
            if 'categories' in data:
                cursor.execute("DELETE FROM posting_categories WHERE posting_id = %s", (posting_id,))
                for category_id in data['categories']:
                    cursor.execute("""
                        INSERT INTO posting_categories (posting_id, category_id)
                        VALUES (%s, %s)
                    """, (posting_id, category_id))

            # 기술 스택 업데이트
            if 'tech_stacks' in data:
                cursor.execute("DELETE FROM posting_tech_stacks WHERE posting_id = %s", (posting_id,))
                for stack_id in data['tech_stacks']:
                    cursor.execute("""
                        INSERT INTO posting_tech_stacks (posting_id, stack_id)
                        VALUES (%s, %s)
                    """, (posting_id, stack_id))

            db.commit()
            return None

        except Exception as e:
            db.rollback()
            logging.error(f"Posting update error: {str(e)}")
            return str(e)
        finally:
            cursor.close()

    @staticmethod
    def delete_posting(posting_id: int, company_id: int):
        db = get_db()
        cursor = db.cursor()

        try:
            # 채용공고 존재 여부 및 권한 확인
            cursor.execute("""
                SELECT posting_id 
                FROM job_postings 
                WHERE posting_id = %s AND company_id = %s AND status = 'active'
            """, (posting_id, company_id))
            
            if not cursor.fetchone():
                return "Posting not found or unauthorized"

            # 채용공고 상태를 'inactive'로 변경하고 deleted_at 설정
            cursor.execute("""
                UPDATE job_postings 
                SET status = 'inactive',
                    deleted_at = CURRENT_TIMESTAMP 
                WHERE posting_id = %s AND company_id = %s
            """, (posting_id, company_id))

            # 관련된 지원 내역 상태 변경
            cursor.execute("""
                UPDATE applications 
                SET status = 'cancelled' 
                WHERE posting_id = %s AND status = 'pending'
            """, (posting_id,))

            # 북마크는 그대로 유지 (히스토리 목적)
            
            db.commit()
            return None

        except Exception as e:
            db.rollback()
            logging.error(f"Posting deletion error: {str(e)}")
            return str(e)
        finally:
            cursor.close()

    @staticmethod
    def get_related_jobs(posting_id: int, limit: int = 5):
        """관련 채용공고 추천"""
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        try:
            # 현재 공고의 회사ID와 기술스택 조회
            cursor.execute("""
                SELECT company_id, 
                       GROUP_CONCAT(stack_id) as tech_stacks
                FROM job_postings j
                LEFT JOIN posting_tech_stacks pt ON j.posting_id = pt.posting_id
                WHERE j.posting_id = %s
                GROUP BY j.posting_id
            """, (posting_id,))
            
            current_job = cursor.fetchone()
            if not current_job:
                return [], "Job posting not found"
            
            # 관련 공고 조회 (같은 회사의 다른 공고 또는 비슷한 기술스택을 가진 공고)
            cursor.execute("""
                SELECT DISTINCT j.*, c.name as company_name,
                       GROUP_CONCAT(DISTINCT t.name) as tech_stacks
                FROM job_postings j
                LEFT JOIN companies c ON j.company_id = c.company_id
                LEFT JOIN posting_tech_stacks pt ON j.posting_id = pt.posting_id
                LEFT JOIN tech_stacks t ON pt.stack_id = t.stack_id
                WHERE j.posting_id != %s 
                AND j.deleted_at IS NULL
                AND (j.company_id = %s 
                     OR pt.stack_id IN (
                         SELECT stack_id 
                         FROM posting_tech_stacks 
                         WHERE posting_id = %s
                     ))
                GROUP BY j.posting_id
                ORDER BY j.created_at DESC
                LIMIT %s
            """, (posting_id, current_job['company_id'], posting_id, limit))
            
            related_jobs = cursor.fetchall()
            
            # tech_stacks 처리
            for job in related_jobs:
                if job['tech_stacks']:
                    job['tech_stacks'] = job['tech_stacks'].split(',')
                else:
                    job['tech_stacks'] = []
                
            return related_jobs, None
            
        except Exception as e:
            logging.error(f"Related jobs fetch error: {str(e)}")
            return [], str(e)
        finally:
            cursor.close() 