import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import time
from .models import Job, Company
from sqlalchemy.exc import IntegrityError
from sqlalchemy import exists

class SaraminCrawler:
    def __init__(self):
        self.base_url = "https://www.saramin.co.kr/zf_user/search/recruit"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # 크롤링 설정
        self.keywords = ['python', 'java', 'javascript', 'react', 'node.js', 
                        'spring', 'django', 'vue.js', 'flutter', 'kotlin']
        self.min_jobs = 100  # 최소 수집 공고 수
        self.max_retries = 3  # 최대 재시도 횟수
        self.retry_delay = 5  # 재시도 대기 시간
        self.page_delay = 1   # 페이지 간 대기 시간

    def crawl_jobs(self):
        all_jobs = []
        total_pages = 0
        
        for keyword in self.keywords:
            page = 1
            while len(all_jobs) < self.min_jobs and page <= 10:  # 최대 10페이지까지
                try:
                    jobs = self._crawl_page(keyword, page)
                    if not jobs:  # 더 이상 결과가 없으면 다음 키워드로
                        break
                    
                    # 중복 제거
                    new_jobs = self._filter_duplicates(jobs, all_jobs)
                    all_jobs.extend(new_jobs)
                    
                    logging.info(f"Collected {len(all_jobs)} jobs so far ({keyword}, page {page})")
                    page += 1
                    total_pages += 1
                    time.sleep(self.page_delay)
                    
                except Exception as e:
                    logging.error(f"Error crawling {keyword} page {page}: {str(e)}")
                    if page == 1:  # 첫 페이지 실패시 다음 키워드로
                        break
                    page += 1
                    
        logging.info(f"Total jobs collected: {len(all_jobs)} from {total_pages} pages")
        return all_jobs

    def _crawl_page(self, keyword, page, attempt=1):
        url = f"{self.base_url}?searchType=search&searchword={keyword}&recruitPage={page}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            job_listings = soup.select('.item_recruit')
            if not job_listings:
                return []
            
            jobs = []
            for job in job_listings:
                try:
                    job_data = self._parse_job_item(job)
                    if job_data:
                        jobs.append(job_data)
                except Exception as e:
                    logging.error(f"Error parsing job item: {str(e)}")
                    continue
            
            return jobs
            
        except requests.RequestException as e:
            if attempt < self.max_retries:
                logging.warning(f"Retry {attempt}/{self.max_retries} for {url}: {str(e)}")
                time.sleep(self.retry_delay)
                return self._crawl_page(keyword, page, attempt + 1)
            logging.error(f"Failed to crawl {url} after {self.max_retries} attempts")
            return []

    def _filter_duplicates(self, new_jobs, existing_jobs):
        # 메모리상의 중복 제거
        seen_links = {job['link'] for job in existing_jobs}
        return [job for job in new_jobs if job['link'] not in seen_links]

    def _parse_job_item(self, job):
        try:
            company_name = job.select_one('.corp_name a').text.strip()
            title = job.select_one('.job_tit a').text.strip()
            link = 'https://www.saramin.co.kr' + job.select_one('.job_tit a')['href']
            
            conditions = job.select('.job_condition span')
            location = conditions[0].text.strip() if len(conditions) > 0 else ''
            experience = conditions[1].text.strip() if len(conditions) > 1 else ''
            education = conditions[2].text.strip() if len(conditions) > 2 else ''
            employment_type = conditions[3].text.strip() if len(conditions) > 3 else ''
            
            deadline = job.select_one('.job_date .date').text.strip()
            
            job_sector = job.select_one('.job_sector')
            sector = job_sector.text.strip() if job_sector else ''
            
            salary_badge = job.select_one('.area_badge .badge')
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
                'created_at': datetime.utcnow()
            }
            
        except AttributeError as e:
            logging.error(f"Error parsing job attributes: {str(e)}")
            return None

    def save_to_db(self, jobs):
        saved_count = 0
        duplicate_count = 0
        
        for job_data in jobs:
            try:
                # 이미 존재하는 채용공고인지 확인
                if Job.query.filter_by(link=job_data['link']).first():
                    duplicate_count += 1
                    continue
                
                # 회사 정보 저장 (없는 경우에만)
                company = Company.query.filter_by(name=job_data['company_name']).first()
                if not company:
                    company = Company(name=job_data['company_name'])
                    db.session.add(company)
                    db.session.flush()
                
                # 채용공고 저장
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
                
                # 주기적으로 커밋
                if saved_count % 50 == 0:
                    db.session.commit()
                
            except IntegrityError:
                logging.warning(f"Duplicate job found: {job_data['link']}")
                db.session.rollback()
                duplicate_count += 1
            except Exception as e:
                logging.error(f"Error saving job to database: {str(e)}")
                db.session.rollback()
                continue
        
        try:
            db.session.commit()
        except Exception as e:
            logging.error(f"Error in final commit: {str(e)}")
            db.session.rollback()
            
        logging.info(f"Saved {saved_count} new jobs, found {duplicate_count} duplicates")
        return saved_count