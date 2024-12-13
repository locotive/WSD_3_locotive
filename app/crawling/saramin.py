import aiohttp
import asyncio
import logging
import random
import time
from bs4 import BeautifulSoup
from aiohttp import ClientTimeout
from aiohttp_retry import RetryClient, ExponentialRetry
from .models import Job, Company
from sqlalchemy.exc import IntegrityError
from sqlalchemy import exists

class SaraminCrawler:
    def __init__(self):
        self.base_url = "https://www.saramin.co.kr/zf_user/search/recruit"
        
        # 기본 설정
        self.keywords = ['python', 'java', 'javascript', 'react', 'node.js', 
                        'spring', 'django', 'vue.js', 'flutter', 'kotlin']
        self.min_jobs = 100
        self.max_retries = 5
        self.retry_delay = 5
        self.page_delay = 5
        
        # aiohttp 설정
        self.timeout = ClientTimeout(total=30, connect=10)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Upgrade-Insecure-Requests': '1'
        }

    async def _crawl_page(self, session, keyword, page):
        retry_options = ExponentialRetry(
            attempts=self.max_retries,
            start_timeout=1,
            max_timeout=10,
            factor=2
        )
        
        async with RetryClient(
            client_session=session,
            retry_options=retry_options
        ) as client:
            try:
                # 랜덤 지연
                await asyncio.sleep(self.page_delay + random.uniform(2, 5))
                
                params = {
                    'searchType': 'search',
                    'searchword': keyword,
                    'start': page,
                    'recruitPage': page,
                    'recruitSort': 'relation',
                    'recruitPageCount': 40
                }
                
                async with client.get(
                    self.base_url,
                    params=params,
                    headers=self.headers,
                    timeout=self.timeout,
                    ssl=False  # SSL 검증 비활성화
                ) as response:
                    if response.status == 403:
                        logging.error(f"접근이 차단됨 (키워드: {keyword}, 페이지: {page})")
                        await asyncio.sleep(60)
                        return []
                        
                    response.raise_for_status()
                    html = await response.text()
                    
                    if '채용정보가 없습니다' in html:
                        logging.info(f"검색 결과 없음 (키워드: {keyword}, 페이지: {page})")
                        return []
                    
                    soup = BeautifulSoup(html, 'html.parser')
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
                    
            except asyncio.TimeoutError:
                logging.error(f"타임아웃 발생 (키워드: {keyword}, 페이지: {page})")
                return []
            except Exception as e:
                logging.error(f"예상치 못한 오류 발생 (키워드: {keyword}, 페이지: {page}): {str(e)}")
                return []

    async def crawl(self):
        async with aiohttp.ClientSession() as session:
            for keyword in self.keywords:
                logging.info(f"Starting crawl for keyword: {keyword}")
                jobs = []
                tasks = []
                
                # 병렬로 페이지 크롤링
                for page in range(1, 11):
                    task = asyncio.create_task(self._crawl_page(session, keyword, page))
                    tasks.append(task)
                
                # 모든 태스크 완료 대기
                results = await asyncio.gather(*tasks)
                for page_jobs in results:
                    jobs.extend(page_jobs)
                
                logging.info(f"Keyword '{keyword}': Collected {len(jobs)} jobs")
                
                # 결과 처리
                for job in jobs:
                    try:
                        self._save_job(job)
                    except Exception as e:
                        logging.error(f"작업 저장 중 오류 발생: {str(e)}")

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

    def _save_job(self, job):
        try:
            # 이미 존재하는 채용공고인지 확인
            if Job.query.filter_by(link=job['link']).first():
                return
            
            # 회사 정보 저장 (없는 경우에만)
            company = Company.query.filter_by(name=job['company_name']).first()
            if not company:
                company = Company(name=job['company_name'])
                db.session.add(company)
                db.session.flush()
            
            # 채용공고 저장
            job = Job(
                company_id=company.id,
                title=job['title'],
                link=job['link'],
                location=job['location'],
                experience=job['experience'],
                education=job['education'],
                employment_type=job['employment_type'],
                deadline=job['deadline'],
                sector=job['sector'],
                salary=job['salary'],
                created_at=job['created_at']
            )
            db.session.add(job)
            
            # 주기적으로 커밋
            if saved_count % 50 == 0:
                db.session.commit()
            
        except IntegrityError:
            logging.warning(f"Duplicate job found: {job['link']}")
            db.session.rollback()
        except Exception as e:
            logging.error(f"Error saving job to database: {str(e)}")
            db.session.rollback()