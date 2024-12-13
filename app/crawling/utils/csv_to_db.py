from flask import current_app
from app.database import get_db
import csv
import os
import logging
from datetime import datetime

def import_csv_to_db(csv_file_path=None):
    """CSV 파일의 채용공고 데이터를 DB에 저장"""
    db = get_db()
    cursor = db.cursor()

    try:
        # CSV 파일 경로가 지정되지 않은 경우 최신 파일 사용
        if not csv_file_path:
            csv_dir = os.path.join(current_app.root_path, 'data', 'crawling')
            csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
            if not csv_files:
                logging.error("No CSV files found")
                return 0
            csv_file_path = os.path.join(csv_dir, sorted(csv_files)[-1])

        saved_count = 0
        updated_count = 0
        
        with open(csv_file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # 이미 존재하는 공고인지 확인
                cursor.execute("""
                    SELECT posting_id FROM job_postings 
                    WHERE title = %s AND company_name = %s
                """, (row['title'], row['company_name']))
                
                existing = cursor.fetchone()
                
                if existing:
                    # 기존 공고 업데이트
                    cursor.execute("""
                        UPDATE job_postings 
                        SET location = %s,
                            experience = %s,
                            education = %s,
                            employment_type = %s,
                            deadline = %s,
                            tech_stacks = %s,
                            updated_at = NOW()
                        WHERE posting_id = %s
                    """, (
                        row['location'],
                        row['experience'],
                        row['education'],
                        row['employment_type'],
                        row['deadline'],
                        row['tech_stack'],
                        existing[0]
                    ))
                    updated_count += 1
                else:
                    # 새 공고 추가
                    cursor.execute("""
                        INSERT INTO job_postings (
                            title, company_name, location, experience,
                            education, employment_type, deadline, tech_stacks,
                            created_at, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    """, (
                        row['title'],
                        row['company_name'],
                        row['location'],
                        row['experience'],
                        row['education'],
                        row['employment_type'],
                        row['deadline'],
                        row['tech_stack']
                    ))
                    saved_count += 1
            
            db.commit()
            logging.info(f"CSV import completed: {saved_count} new jobs saved, {updated_count} jobs updated")
            return saved_count + updated_count
            
    except Exception as e:
        db.rollback()
        logging.error(f"Failed to import CSV: {str(e)}")
        raise
    finally:
        cursor.close()

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