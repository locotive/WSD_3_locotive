import aiohttp
import asyncio
import logging
import random
import time
from bs4 import BeautifulSoup
from aiohttp import ClientTimeout
from aiohttp_retry import RetryClient, ExponentialRetry
from .models import Job, Company
from .params_code import ConfigCode, get_location_code, get_job_code, get_sort_code, get_company_code

class SaraminCrawler:
    def __init__(self):
        self.base_url = "https://www.saramin.co.kr/zf_user/search/recruit"
        
        # 기본 설정
        self.keywords = ['python', 'java', 'javascript', 'react', 'node.js', 
                        'spring', 'django', 'vue.js', 'flutter', 'kotlin']
        self.location = "서울"  # 기본 지역
        self.job_category = "IT개발·데이터"  # 기본 직종
        self.sort_type = "등록일순"  # 기본 정렬
        self.company_type = "중견·중소"  # 기본 회사형태
        
        self.min_jobs = 100
        self.max_retries = 5
        self.retry_delay = 5
        self.page_delay = 2
        
        # aiohttp 설정
        self.timeout = ClientTimeout(total=30, connect=10)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
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
                await asyncio.sleep(self.page_delay + random.uniform(1, 2))
                
                params = {
                    'searchType': 'search',
                    'searchword': keyword,
                    'recruitPage': page,
                    'loc_mcd': get_location_code(self.location),
                    'cat_mcls': get_job_code(self.job_category),
                    'recruitSort': get_sort_code(self.sort_type),
                    'inner_com_type': get_company_code(self.company_type)
                }
                
                async with client.get(
                    self.base_url,
                    params=params,
                    headers=self.headers,
                    timeout=self.timeout,
                    ssl=False
                ) as response:
                    if response.status == 403:
                        logging.error(f"접근이 차단됨 (키워드: {keyword}, 페이지: {page})")
                        await asyncio.sleep(60)
                        return []
                        
                    response.raise_for_status()
                    html = await response.text()
                    
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
                    
                    logging.info(f"페이지 {page}에서 {len(jobs)}개의 채용공고를 찾았습니다 (키워드: {keyword})")
                    return jobs
                    
            except asyncio.TimeoutError:
                logging.error(f"타임아웃 발생 (키워드: {keyword}, 페이지: {page})")
                return []
            except Exception as e:
                logging.error(f"예상치 못한 오류 발생 (키워드: {keyword}, 페이지: {page}): {str(e)}")
                return []

    def _parse_job_item(self, job):
        try:
            company = job.select_one(".corp_name a")
            company = company.text.strip() if company else "N/A"

            title = job.select_one(".job_tit a")
            title = title.text.strip() if title else "N/A"

            link = job.select_one(".job_tit a")
            link = "https://www.saramin.co.kr" + link["href"] if link else "N/A"

            conditions = job.select(".job_condition span")
            location = conditions[0].text.strip() if len(conditions) > 0 else "N/A"
            experience = conditions[1].text.strip() if len(conditions) > 1 else "N/A"
            education = conditions[2].text.strip() if len(conditions) > 2 else "N/A"
            employment_type = conditions[3].text.strip() if len(conditions) > 3 else "N/A"

            deadline = job.select_one(".job_date .date")
            deadline = deadline.text.strip() if deadline else "N/A"

            job_sector = job.select_one(".job_sector")
            sector = job_sector.text.strip() if job_sector else "N/A"

            salary_badge = job.select_one(".area_badge .badge")
            salary = salary_badge.text.strip() if salary_badge else "N/A"

            return {
                "company": company,
                "title": title,
                "link": link,
                "location": location,
                "experience": experience,
                "education": education,
                "employment_type": employment_type,
                "deadline": deadline,
                "sector": sector,
                "salary": salary
            }
        except Exception as e:
            logging.error(f"채용 정보 파싱 중 오류 발생: {str(e)}")
            return None

    async def crawl(self):
        async with aiohttp.ClientSession() as session:
            all_jobs = []
            for keyword in self.keywords:
                logging.info(f"키워드 '{keyword}' 크롤링 시작")
                tasks = []
                
                for page in range(1, 11):
                    task = asyncio.create_task(self._crawl_page(session, keyword, page))
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks)
                keyword_jobs = []
                for page_jobs in results:
                    keyword_jobs.extend(page_jobs)
                
                logging.info(f"키워드 '{keyword}': {len(keyword_jobs)}개의 채용공고 수집 완료")
                all_jobs.extend(keyword_jobs)
            
            # DB 저장
            try:
                saved_count = 0
                for job_data in all_jobs:
                    # 회사 정보 저장
                    company = Company.query.filter_by(name=job_data['company']).first()
                    if not company:
                        company = Company(name=job_data['company'])
                        company.save()

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
                        salary=job_data['salary']
                    )
                    job.save()
                    saved_count += 1

                logging.info(f"총 {saved_count}개의 채용공고 저장 완료")
            except Exception as e:
                logging.error(f"DB 저장 중 오류 발생: {str(e)}")