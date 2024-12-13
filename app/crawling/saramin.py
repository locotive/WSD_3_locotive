import aiohttp
import asyncio
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from .models import Job, Company
from .params_code import SearchParams
from aiohttp import ClientTimeout, ClientSession, TCPConnector

class SaraminCrawler:
    def __init__(self):
        self.search_params = SearchParams()
        self.base_url = "https://www.saramin.co.kr/zf_user/search/recruit"
        self.timeout = ClientTimeout(total=30, connect=10)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive'
        }
        
        self.tech_stack = [
            'python', 'java', 'javascript', 'react',
            'spring', 'django', 'vue.js', 'flutter'
        ]
        self.regions = ['서울', '경기', '인천']
        self.max_pages = 3
        self.delay = 3  # 딜레이 증가

    async def fetch_page(self, session, params):
        """페이지 데이터 가져오기"""
        try:
            async with session.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=self.timeout,
                ssl=False,
                allow_redirects=True
            ) as response:
                if response.status == 200:
                    return await response.text()
                logging.error(f"HTTP {response.status}: {params}")
                return None
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
        connector = TCPConnector(limit=5, force_close=True)
        async with ClientSession(connector=connector) as session:
            all_jobs = []
            
            for tech in self.tech_stack:
                for region in self.regions:
                    tasks = []
                    
                    for page in range(1, self.max_pages + 1):
                        params = {
                            'searchType': 'search',
                            'searchword': tech,
                            'recruitPage': page,
                            'loc_mcd': region,
                            'recruitSort': 'reg_dt',
                            'recruitPageCount': 40,
                            'inner_com_type': '1',  # 대기업
                            'company_cd': '0,1,2,3,4,5,6,7,8,9'  # 모든 기업형태
                        }
                        
                        task = asyncio.create_task(self.fetch_and_process(
                            session, params
                        ))
                        tasks.append(task)
                        
                        await asyncio.sleep(self.delay)
                    
                    results = await asyncio.gather(*tasks)
                    for jobs in results:
                        if jobs:
                            all_jobs.extend(jobs)
                            
                    logging.info(f"{tech} - {region}: {len(all_jobs)}개 채용공고 수집")
            
            await self.save_jobs(all_jobs)
            return len(all_jobs)

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