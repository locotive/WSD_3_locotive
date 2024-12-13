from datetime import datetime
from app.database import get_db

class Job:
    def __init__(self, title, company_name, location=None, experience=None, 
                 education=None, employment_type=None, deadline=None, tech_stacks=None):
        self.title = title
        self.company_name = company_name
        self.location = location
        self.experience = experience
        self.education = education
        self.employment_type = employment_type
        self.deadline = deadline
        self.tech_stacks = tech_stacks

    @staticmethod
    def save(job):
        db = get_db()
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute("""
                INSERT INTO job_postings (
                    title, company_name, location, experience,
                    education, employment_type, deadline, tech_stacks,
                    created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """, (
                job.title,
                job.company_name,
                job.location,
                job.experience,
                job.education,
                job.employment_type,
                job.deadline,
                job.tech_stacks
            ))
            db.commit()
        finally:
            cursor.close()

class Company:
    def __init__(self, name):
        self.name = name

    @staticmethod
    def get_or_create(name):
        db = get_db()
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM companies WHERE name = %s", (name,))
            result = cursor.fetchone()
            if result:
                return Company(name)
            
            cursor.execute("INSERT INTO companies (name) VALUES (%s)", (name,))
            db.commit()
            return Company(name)
        finally:
            cursor.close()