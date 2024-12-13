import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import time
from .models import Job, Company
from sqlalchemy.exc import IntegrityError
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import exists
import random

class SaraminCrawler:
    def __init__(self):
        self.base_url = "https://www.saramin.co.kr/zf_user/search/recruit"
        self.session = requests.Session()
        
        # 더 자연스러운 User-Agent 설정
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        })
        
        # 크롤링 설정 조정
        self.keywords = ['python', 'java', 'javascript', 'react', 'node.js', 
                        'spring', 'django', 'vue.js', 'flutter', 'kotlin']
        self.min_jobs = 100  # 최소 수집 공고 수 줄임
        self.max_retries = 3
        self.retry_delay = 2  # 재시도 대기 시간 줄임
        self.page_delay = 3   # 페이지 간 대기 시간 증가
        self.timeout = 15    # 타임아웃 증가

    def crawl_jobs(self):
        all_jobs = []
        for keyword in self.keywords:
            logging.info(f"Starting crawl for keyword: {keyword}")
            try:
                jobs = self.crawl_keyword_pages(keyword)
                all_jobs.extend(jobs)
                logging.info(f"Keyword '{keyword}': Collected {len(jobs)} jobs")
            except Exception as e:
                logging.error(f"Error crawling keyword '{keyword}': {str(e)}")
        logging.info(f"Total jobs collected: {len(all_jobs)}")
        return all_jobs
    
    def crawl_keyword_pages(self, keyword):
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(self._crawl_page, keyword, page) for page in range(1, 11)]
            results = [future.result() for future in futures]
        return [job for result in results for job in result if result]


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

    def _crawl_page(self, keyword, page):
        for attempt in range(self.max_retries):
            try:
                # 랜덤 지연 추가
                delay = self.page_delay + random.uniform(1, 2)
                time.sleep(delay)
                
                params = {
                    'searchType': 'search',
                    'searchword': keyword,
                    'start': page,
                    'recruitPage': page,
                    'recruitSort': 'relation',
                    'recruitPageCount': 40
                }
                
                response = self.session.get(
                    self.base_url, 
                    params=params,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                # 응답 확인
                if '채용정보가 없습니다' in response.text:
                    logging.info(f"검색 결과 없음 (키워드: {keyword}, 페이지: {page})")
                    return []
                    
                soup = BeautifulSoup(response.text, 'html.parser')
                job_items = soup.select('.item_recruit')
                
                if not job_items:
                    logging.warning(f"채용 항목을 찾을 수 없음 (키워드: {keyword}, 페이지: {page})")
                    return []
                
                jobs = []
                for job in job_items:
                    job_data = self._parse_job_item(job)
                    if job_data:
                        jobs.append(job_data)
                        
                return jobs
                
            except requests.RequestException as e:
                logging.error(f"페이지 크롤링 중 오류 발생 (키워드: {keyword}, 페이지: {page}, 시도: {attempt+1}/{self.max_retries}): {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))  # 점진적 대기 시간 증가
                continue
            except Exception as e:
                logging.error(f"예상치 못한 오류 발생 (키워드: {keyword}, 페이지: {page}): {str(e)}")
                return []
        
        return []  # 모든 재시도 실패 시