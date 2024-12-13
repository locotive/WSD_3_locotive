import aiohttp
import asyncio
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from .models import Job, Company
from .params_code import SearchParams
from aiohttp import ClientTimeout

class SaraminCrawler:
    def __init__(self):
        self.search_params = SearchParams()
        self.base_url = "https://www.saramin.co.kr/zf_user/search/recruit"
        self.session_config = {
            'timeout': ClientTimeout(total=30),
            'headers': {
                'User-Agent': f'Mozilla/5.0 JobSearchBot/{datetime.now().strftime("%Y%m%d")}',
                'Accept': 'text/html,application/xhtml+xml',
                'Accept-Language': 'ko-KR,ko;q=0.9'
            }
        }
        
        # 검색 설정
        self.tech_stack = [
            '백엔드', '프론트엔드', '데이터엔지니어',
            '데브옵스', '클라우드', '보안'
        ]
        self.regions = ['서울', '경기', '인천']
        self.max_pages = 5
        self.delay = 1.5

    async def fetch_page(self, session, params):
        """페이지 데이터 가져오기"""
        try:
            async with session.get(self.base_url, params=params) as response:
                if response.status != 200:
                    logging.error(f"HTTP {response.status}: {params}")
                    return None
                return await response.text()
        except Exception as e:
            logging.error(f"페이지 요청 실패: {str(e)}")
            return None

    def extract_job_info(self, element):
        """채용 정보 추출"""
        try:
            info = {}
            
            # 기본 정보
            if title_elem := element.select_one('[class*="job_tit"]'):
                info['title'] = title_elem.get_text(strip=True)
                info['link'] = title_elem.get('href', '')
                
            # 회사 정보
            if company_elem := element.select_one('[class*="corp_name"]'):
                info['company_name'] = company_elem.get_text(strip=True)
                
            # 상세 정보
            details = element.select('[class*="job_condition"] > span')
            info.update({
                'location': details[0].get_text(strip=True) if len(details) > 0 else '',
                'career': details[1].get_text(strip=True) if len(details) > 1 else '',
                'education': details[2].get_text(strip=True) if len(details) > 2 else '',
                'position_type': details[3].get_text(strip=True) if len(details) > 3 else ''
            })
            
            # 추가 정보
            info['deadline'] = element.select_one('[class*="date"]').get_text(strip=True) if element.select_one('[class*="date"]') else ''
            info['job_category'] = element.select_one('[class*="job_sector"]').get_text(strip=True) if element.select_one('[class*="job_sector"]') else ''
            
            return info
        except Exception as e:
            logging.error(f"정보 추출 실패: {str(e)}")
            return None

    async def process_search_results(self, html_content):
        """검색 결과 처리"""
        if not html_content:
            return []
            
        soup = BeautifulSoup(html_content, 'html.parser')
        job_elements = soup.select('[class*="item_recruit"]')
        
        job_listings = []
        for element in job_elements:
            if job_info := self.extract_job_info(element):
                job_listings.append(job_info)
                
        return job_listings

    async def crawl_jobs(self):
        """채용 정보 크롤링 실행"""
        async with aiohttp.ClientSession(**self.session_config) as session:
            all_jobs = []
            
            for tech in self.tech_stack:
                for region in self.regions:
                    tasks = []
                    
                    for page in range(1, self.max_pages + 1):
                        params = self.search_params.build_params(
                            keyword=tech,
                            region=region,
                            page=page,
                            sort="최신순"
                        )
                        
                        task = asyncio.create_task(self.fetch_and_process(
                            session, params
                        ))
                        tasks.append(task)
                        
                        await asyncio.sleep(self.delay)
                    
                    results = await asyncio.gather(*tasks)
                    for jobs in results:
                        if jobs:
                            all_jobs.extend(jobs)
            
            await self.save_jobs(all_jobs)

    async def fetch_and_process(self, session, params):
        """페이지 데이터 가져오기 및 처리"""
        if html := await self.fetch_page(session, params):
            return await self.process_search_results(html)
        return []

    async def save_jobs(self, jobs):
        """채용 정보 저장"""
        try:
            saved = 0
            for job_data in jobs:
                # 회사 정보 처리
                company = await self.get_or_create_company(job_data['company_name'])
                
                # 채용 공고 저장
                if await self.create_job(company.id, job_data):
                    saved += 1
                    
            logging.info(f"저장 완료: {saved}개의 채용공고")
        except Exception as e:
            logging.error(f"저장 실패: {str(e)}")

    async def get_or_create_company(self, name):
        """회사 정보 조회 또는 생성"""
        company = Company.query.filter_by(name=name).first()
        if not company:
            company = Company(name=name)
            company.save()
        return company

    async def create_job(self, company_id, data):
        """채용 공고 생성"""
        try:
            job = Job(
                company_id=company_id,
                title=data['title'],
                link=data['link'],
                location=data['location'],
                experience=data['career'],
                education=data['education'],
                employment_type=data['position_type'],
                deadline=data['deadline'],
                sector=data['job_category']
            )
            job.save()
            return True
        except Exception as e:
            logging.error(f"채용공고 저장 실패: {str(e)}")
            return False