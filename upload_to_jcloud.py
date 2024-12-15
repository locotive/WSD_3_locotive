from dotenv import load_dotenv
import os
import mysql.connector
import csv
import sys
import logging
from datetime import datetime
import re

# .env 파일 로드
load_dotenv()

def parse_deadline(deadline_str):
    if not deadline_str or deadline_str.lower() == 'none':
        return None
        
    try:
        match = re.search(r'(\d{2})/(\d{2})', deadline_str)
        if match:
            month, day = match.groups()
            year = datetime.now().year
            current_month = datetime.now().month
            if int(month) < current_month:
                year += 1
            return f"{year}-{month}-{day}"
        return None
    except Exception as e:
        logging.warning(f"날짜 파싱 실패: {deadline_str}, 에러: {str(e)}")
        return None

def upload_csv_to_jcloud(csv_file_path, host, user, password, database, port):
    """CSV 파일의 데이터를 JCloud DB에 업로드"""
    
    # DB 연결
    connection = mysql.connector.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database
    )
    cursor = connection.cursor(dictionary=True)

    try:
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

                # 중복 체크
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
                            deadline_date = %s,
                            status = 'active'
                        WHERE posting_id = %s
                    """, (
                        row.get('description', ''),
                        row.get('experience', ''),
                        row.get('education', ''),
                        row.get('employment_type', ''),
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
                            deadline_date,
                            status,
                            created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'active', CURRENT_TIMESTAMP)
                    """, (
                        company_id,
                        row['title'],
                        row.get('description', ''),
                        row.get('experience', ''),
                        row.get('education', ''),
                        row.get('employment_type', ''),
                        deadline_date
                    ))
                    saved_count += 1
            
            connection.commit()
            print(f"CSV 업로드 완료: {saved_count}개 새로 저장, {updated_count}개 업데이트")
            return saved_count + updated_count
            
    except Exception as e:
        connection.rollback()
        print(f"업로드 실패: {str(e)}")
        raise
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python upload_to_jcloud.py <csv_file_path>")
        sys.exit(1)

    # .env 파일에서 환경변수 가져오기
    DB_CONFIG = {
        'host': os.getenv('DB_HOST'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME'),
        'port': int(os.getenv('DB_PORT'))
    }

    csv_file = sys.argv[1]
    upload_csv_to_jcloud(csv_file, **DB_CONFIG)