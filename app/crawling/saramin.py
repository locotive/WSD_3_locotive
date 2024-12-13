import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.models import Job, Company
from app import db

class SaraminCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.timeout = 10
        self.retry_delay = 5
        self.max_workers = 3
        
    def _fetch_page(self, keyword, page):
        url = f"https://www.saramin.co.kr/zf_user/search/recruit?searchType=search&searchword={keyword}&recruitPage={page}"
        retries = 3
        
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response.text
            except Exception as e:
                logging.warning(f"Request failed (attempt {attempt + 1}): {str(e)}")
                if attempt < retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    return None

    def _parse_job(self, job_item):
        try:
            company_name = job_item.select_one('.corp_name a').text.strip()
            title = job_item.select_one('.job_tit a').text.strip()
            link = 'https://www.saramin.co.kr' + job_item.select_one('.job_tit a')['href']
            
            conditions = job_item.select('.job_condition span')
            location = conditions[0].text.strip() if len(conditions) > 0 else ''
            experience = conditions[1].text.strip() if len(conditions) > 1 else ''
            education = conditions[2].text.strip() if len(conditions) > 2 else ''
            employment_type = conditions[3].text.strip() if len(conditions) > 3 else ''
            
            deadline = job_item.select_one('.job_date .date').text.strip()
            job_sector = job_item.select_one('.job_sector')
            sector = job_sector.text.strip() if job_sector else ''
            
            salary_badge = job_item.select_one('.area_badge .badge')
            salary = salary_badge.text.strip() if salary_badge else ''

            return {
                'company_name': company_name,
                'title': title,
                'link': link,
                'location': location,
                'experience': experience,
                'education': education,
                'employment_type': employment_type,
                'deadline': deadline,
                'sector': sector,
                'salary': salary,
                'created_at': datetime.now()
            }
        except Exception as e:
            logging.error(f"Job parsing error: {str(e)}")
            return None

    def crawl_jobs(self, keywords=['python', 'java', 'javascript'], min_jobs=100):
        jobs = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_page = {}
            page = 1
            
            while len(jobs) < min_jobs:
                for keyword in keywords:
                    future = executor.submit(self._fetch_page, keyword, page)
                    future_to_page[future] = (keyword, page)
                
                for future in as_completed(future_to_page):
                    keyword, page = future_to_page[future]
                    html = future.result()
                    
                    if html:
                        soup = BeautifulSoup(html, 'html.parser')
                        job_items = soup.select('.item_recruit')
                        
                        for item in job_items:
                            job_data = self._parse_job(item)
                            if job_data:
                                jobs.append(job_data)
                                
                    time.sleep(1)
                
                page += 1
                if page > 20:
                    break
                    
        return jobs

    def save_to_db(self, jobs):
        saved_count = 0
        for job_data in jobs:
            try:
                # 회사 정보 처리
                company = Company.query.filter_by(name=job_data['company_name']).first()
                if not company:
                    company = Company(name=job_data['company_name'])
                    db.session.add(company)
                    db.session.flush()

                # 채용공고 중복 체크
                existing_job = Job.query.filter_by(
                    company_id=company.id,
                    title=job_data['title'],
                    link=job_data['link']
                ).first()

                if not existing_job:
                    job = Job(
                        company_id=company.id,
                        title=job_data['title'],
                        link=job_data['link'],
                        location=job_data['location'],
                        experience=job_data['experience'],
                        education=job_data['education'],
                        employment_type=job_data['employment_type'],
                        deadline=job_data['deadline'],
                        sector=job_data['sector'],
                        salary=job_data['salary'],
                        created_at=job_data['created_at']
                    )
                    db.session.add(job)
                    saved_count += 1

            except Exception as e:
                logging.error(f"Error saving job: {str(e)}")
                continue

        try:
            db.session.commit()
            logging.info(f"Successfully saved {saved_count} new jobs")
            return saved_count
        except Exception as e:
            db.session.rollback()
            logging.error(f"Database error: {str(e)}")
            return 0