from flask import current_app
from app.database import get_db
import csv
import os
import logging
from datetime import datetime
import re

def parse_deadline(deadline_str):
    """마감일 문자열을 MySQL date 형식으로 변환"""
    if not deadline_str or deadline_str.lower() == 'none':
        return None
        
    try:
        # "~ 01/09(목)" 형식 처리
        match = re.search(r'(\d{2})/(\d{2})', deadline_str)
        if match:
            month, day = match.groups()
            # 현재 연도 사용
            year = datetime.now().year
            # 만약 마감월이 현재월보다 작다면 다음해로 설정
            current_month = datetime.now().month
            if int(month) < current_month:
                year += 1
            return f"{year}-{month}-{day}"
            
        return None
    except Exception as e:
        logging.warning(f"날짜 파싱 실패: {deadline_str}, 에러: {str(e)}")
        return None

def import_csv_to_db(csv_file_path=None):
    """CSV 파일의 채용공고 데이터를 DB에 저장"""
    db = get_db()
    cursor = db.cursor(dictionary=True)

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
                # 회사 정보 처리
                cursor.execute("""
                    SELECT company_id FROM companies 
                    WHERE name = %s
                """, (row['company_name'],))
                
                company = cursor.fetchone()
                if not company:
                    cursor.execute("""
                        INSERT INTO companies (name, created_at) 
                        VALUES (%s, CURRENT_TIMESTAMP)
                    """, (row['company_name'],))
                    company_id = cursor.lastrowid
                else:
                    company_id = company['company_id']

                # 마감일 파싱
                deadline_date = parse_deadline(row.get('deadline'))

                # 이미 존재하는 공고인지 확인
                cursor.execute("""
                    SELECT posting_id FROM job_postings 
                    WHERE title = %s AND company_id = %s
                    AND deleted_at IS NULL
                """, (row['title'], company_id))
                
                existing = cursor.fetchone()
                
                if existing:
                    # 기존 공고 업데이트
                    cursor.execute("""
                        UPDATE job_postings 
                        SET job_description = %s,
                            experience_level = %s,
                            education_level = %s,
                            employment_type = %s,
                            salary_info = %s,
                            deadline_date = %s,
                            status = 'active'
                        WHERE posting_id = %s
                    """, (
                        row.get('description', ''),
                        row.get('experience', ''),
                        row.get('education', ''),
                        row.get('employment_type', ''),
                        row.get('salary', ''),
                        deadline_date,
                        existing['posting_id']
                    ))
                    updated_count += 1
                else:
                    # 새 공고 추가
                    cursor.execute("""
                        INSERT INTO job_postings (
                            company_id,
                            title,
                            job_description,
                            experience_level,
                            education_level,
                            employment_type,
                            salary_info,
                            deadline_date,
                            status,
                            created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'active', CURRENT_TIMESTAMP)
                    """, (
                        company_id,
                        row['title'],
                        row.get('description', ''),
                        row.get('experience', ''),
                        row.get('education', ''),
                        row.get('employment_type', ''),
                        row.get('salary', ''),
                        deadline_date
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