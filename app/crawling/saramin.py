import requests
from bs4 import BeautifulSoup
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional
from .config import CrawlingConfig
from app.database import get_db

class SaraminCrawler:
    def __init__(self):
        self.config = CrawlingConfig()
        self.session = requests.Session()
        self.session.headers.update(self.config.HEADERS)
        self.logger = logging.getLogger(__name__)

    def crawl_jobs(self) -> List[Dict]:
        """메인 크롤링 함수"""
        all_jobs = []
        
        for page in range(1, self.config.MAX_PAGES + 1):
            try:
                jobs = self._crawl_page(page)
                if not jobs:
                    break
                    
                for job in jobs:
                    job_detail = self._crawl_job_detail(job['posting_url'])
                    if job_detail:
                        job.update(job_detail)
                        all_jobs.append(job)
                        
                time.sleep(1)  # 요청 간격
                
            except Exception as e:
                self.logger.error(f"Error crawling page {page}: {str(e)}")
                continue
                
        return all_jobs

    def _crawl_page(self, page: int) -> List[Dict]:
        """한 페이지의 채용공고 목록 크롤링"""
        params = {'page': page}
        response = self._make_request(self.config.SEARCH_URL, params)
        if not response:
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        job_items = soup.select('.item_recruit')
        
        jobs = []
        for item in job_items:
            try:
                job = {
                    'title': item.select_one('.job_tit a').text.strip(),
                    'company_name': item.select_one('.company_nm a').text.strip(),
                    'posting_url': item.select_one('.job_tit a')['href'],
                    'location': item.select_one('.work_place').text.strip(),
                    'experience': item.select_one('.experience').text.strip(),
                    'education': item.select_one('.education').text.strip(),
                }
                jobs.append(job)
            except Exception as e:
                self.logger.error(f"Error parsing job item: {str(e)}")
                continue
                
        return jobs

    def _crawl_job_detail(self, url: str) -> Optional[Dict]:
        """채용공고 상세 페이지 크롤링"""
        response = self._make_request(url)
        if not response:
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        try:
            detail = {
                'job_description': soup.select_one('.job_detail').text.strip(),
                'salary': soup.select_one('.salary').text.strip(),
                'tech_stacks': [
                    tech.text.strip() 
                    for tech in soup.select('.job_stacks .stack')
                ],
                'deadline': soup.select_one('.deadline').text.strip(),
            }
            return detail
        except Exception as e:
            self.logger.error(f"Error parsing job detail: {str(e)}")
            return None

    def _make_request(self, url: str, params: Dict = None) -> Optional[requests.Response]:
        """재시도 로직이 포함된 요청 함수"""
        for attempt in range(self.config.MAX_RETRIES):
            try:
                response = self.session.get(url, params=params)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                self.logger.warning(f"Request failed (attempt {attempt + 1}): {str(e)}")
                if attempt < self.config.MAX_RETRIES - 1:
                    time.sleep(self.config.RETRY_DELAY)
                continue
        return None

    def save_to_db(self, jobs: List[Dict]) -> None:
        """크롤링한 데이터 DB 저장"""
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        try:
            for job in jobs:
                # 1. 회사 정보 저장/조회
                cursor.execute(
                    "SELECT company_id FROM companies WHERE name = %s",
                    (job['company_name'],)
                )
                company = cursor.fetchone()
                
                if company:
                    company_id = company['company_id']
                else:
                    cursor.execute(
                        "INSERT INTO companies (name) VALUES (%s)",
                        (job['company_name'],)
                    )
                    company_id = cursor.lastrowid
                
                # 2. 위치 정보 처리
                city, district = self._parse_location(job['location'])
                cursor.execute(
                    """
                    SELECT location_id FROM locations 
                    WHERE city = %s AND district = %s
                    """,
                    (city, district)
                )
                location = cursor.fetchone()
                
                if location:
                    location_id = location['location_id']
                else:
                    cursor.execute(
                        "INSERT INTO locations (city, district) VALUES (%s, %s)",
                        (city, district)
                    )
                    location_id = cursor.lastrowid
                
                # 3. 채용공고 저장
                cursor.execute(
                    """
                    INSERT INTO job_postings (
                        company_id, title, job_description, 
                        experience_level, education_level,
                        location_id, salary_info, deadline_date,
                        status, view_count
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'active', 0)
                    """,
                    (
                        company_id, job['title'], job['job_description'],
                        job['experience'], job['education'],
                        location_id, job['salary'],
                        self._parse_deadline(job['deadline'])
                    )
                )
                posting_id = cursor.lastrowid
                
                # 4. 기술 스택 처리
                for tech in job['tech_stacks']:
                    cursor.execute(
                        "SELECT stack_id FROM tech_stacks WHERE name = %s",
                        (tech,)
                    )
                    stack = cursor.fetchone()
                    
                    if stack:
                        stack_id = stack['stack_id']
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
                        (posting_id, stack_id)
                    )
                
            db.commit()
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error saving to database: {str(e)}")
            raise
        finally:
            cursor.close()

    def _parse_location(self, location: str) -> tuple:
        """위치 정보 파싱"""
        parts = location.split()
        if len(parts) >= 2:
            return parts[0], parts[1]
        return parts[0], None

    def _parse_deadline(self, deadline: str) -> Optional[str]:
        """마감일 파싱"""
        try:
            return datetime.strptime(deadline, '%Y-%m-%d').strftime('%Y-%m-%d')
        except ValueError:
            return None