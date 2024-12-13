from flask import current_app
from app.database import db
from app.models import Job
import csv
import os
import logging
from datetime import datetime

def import_csv_to_db(csv_file_path=None):
    """CSV 파일의 채용공고 데이터를 DB에 저장"""
    try:
        # CSV 파일 경로가 지정되지 않은 경우 최신 파일 사용
        if not csv_file_path:
            csv_dir = os.path.join(current_app.root_path, 'data', 'crawling')
            csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
            if not csv_files:
                logging.error("No CSV files found")
                return 0
            # 가장 최근 파일 선택
            csv_file_path = os.path.join(csv_dir, sorted(csv_files)[-1])

        saved_count = 0
        updated_count = 0
        
        with open(csv_file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # 이미 존재하는 공고인지 확인
                existing_job = Job.query.filter_by(
                    title=row['title'],
                    company_name=row['company_name']
                ).first()
                
                if existing_job:
                    # 기존 공고 업데이트
                    existing_job.location = row['location']
                    existing_job.experience = row['experience']
                    existing_job.education = row['education']
                    existing_job.employment_type = row['employment_type']
                    existing_job.deadline = row['deadline']
                    existing_job.tech_stacks = row['tech_stack']
                    existing_job.updated_at = datetime.now()
                    updated_count += 1
                else:
                    # 새 공고 추가
                    new_job = Job(
                        title=row['title'],
                        company_name=row['company_name'],
                        location=row['location'],
                        experience=row['experience'],
                        education=row['education'],
                        employment_type=row['employment_type'],
                        deadline=row['deadline'],
                        tech_stacks=row['tech_stack']
                    )
                    db.session.add(new_job)
                    saved_count += 1
            
            db.session.commit()
            logging.info(f"CSV import completed: {saved_count} new jobs saved, {updated_count} jobs updated")
            return saved_count + updated_count
            
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to import CSV: {str(e)}")
        raise

# CLI 실행을 위한 코드
if __name__ == '__main__':
    import sys
    from flask import Flask
    import os
    
    # PYTHONPATH에 프로젝트 루트 디렉토리 추가
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    sys.path.insert(0, project_root)
    
    from app import create_app
    
    app = create_app()
    with app.app_context():
        if len(sys.argv) > 1:
            csv_path = sys.argv[1]
            import_csv_to_db(csv_path)
        else:
            import_csv_to_db()