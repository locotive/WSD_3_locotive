import aiohttp
from bs4 import BeautifulSoup
import logging
import time
import random
from datetime import datetime
from .models import Job, Company
from .config import CrawlingConfig
from app.database import db
import asyncio

class SaraminCrawler:
    def __init__(self):
        self.config = CrawlingConfig()
        self.session = None
        self.current_page = 1
        self.error_count = 0
        self.MAX_ERRORS = 3
        self.MAX_PAGES = 20  
        
        self.logger = logging.getLogger('crawler')
        self.logger.setLevel(logging.DEBUG)
    
    async def _create_session(self):
        return aiohttp.ClientSession(headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Upgrade-Insecure-Requests': '1'
        })
    
    async def crawl_jobs(self):
        """채용 정보 크롤링 실행"""
        try:
            self.logger.info("크롤링 시작")
            all_jobs = []
            search_url = f"{self.config.BASE_URL}/zf_user/search/recruit"
            
            async with await self._create_session() as session:
                self.session = session
                
                while self.current_page <= self.MAX_PAGES:
                    try:
                        params = {
                            'searchType': 'search',
                            'searchword': 'python',
                            'loc_mcd': '101000',
                            'job_type': '1',
                            'exp_cd': '1',
                            'panel_type': 'auto',
                            'search_optional_item': 'y',
                            'search_done': 'y',
                            'panel_count': 'y',
                            'recruitPage': self.current_page,
                            'page': self.current_page
                        }
                        
                        self.logger.info(f"페이지 {self.current_page} 크롤링 시작")
                        
                        delay = random.uniform(10, 15)
                        self.logger.debug(f"대기 시간: {delay}초")
                        await asyncio.sleep(delay)
                        
                        async with session.get(search_url, params=params) as response:
                            self.logger.debug(f"HTTP 응답 상태 코드: {response.status}")
                            response.raise_for_status()
                            html = await response.text()
                            
                            soup = BeautifulSoup(html, 'html.parser')
                            job_elements = soup.select('.item_recruit')
                            
                            if not job_elements:
                                self.error_count += 1
                                if self.error_count >= self.MAX_ERRORS:
                                    break
                                continue
                            
                            for element in job_elements:
                                if job_info := self.extract_job_info(element):
                                    all_jobs.append(job_info)
                            
                            self.current_page += 1
                            self.error_count = 0
                            
                            if self.current_page >= self.MAX_PAGES:
                                self.logger.info(f"최대 페이지 수({self.MAX_PAGES}) 도달")
                                break
                            
                    except aiohttp.ClientError as e:
                        self.logger.error(f"HTTP 요청 실패: {str(e)}")
                        self.error_count += 1
                        if self.error_count >= self.MAX_ERRORS:
                            break
                        await asyncio.sleep(30)
                        
            if all_jobs:
                return await self.save_jobs(all_jobs)
            return 0
            
        except Exception as e:
            self.logger.error(f"크롤링 실패: {str(e)}", exc_info=True)
            raise

    def extract_job_info(self, element):
        """채용 정보 추출"""
        try:
            info = {}
            
            # 기본 정보
            title_elem = element.select_one('[class*="job_tit"] a')
            info['title'] = title_elem.text.strip()
            info['link'] = title_elem.get('href')
            
            # 회사 정보
            company_elem = element.select_one('[class*="corp_name"] a')
            info['company_name'] = company_elem.text.strip()
            
            # 상세 정보
            details = element.select('[class*="job_condition"] > span')
            info.update({
                'location': details[0].text.strip() if len(details) > 0 else '',
                'experience': details[1].text.strip() if len(details) > 1 else '',
                'education': details[2].text.strip() if len(details) > 2 else '',
                'employment_type': details[3].text.strip() if len(details) > 3 else ''
            })
            
            # 추가 정보
            deadline_elem = element.select_one('[class*="date"]')
            info['deadline'] = deadline_elem.text.strip() if deadline_elem else ''
            
            sector_elem = element.select_one('[class*="job_sector"]')
            info['sector'] = sector_elem.text.strip() if sector_elem else ''
            
            return info
            
        except Exception as e:
            logging.error(f"정보 추출 실패: {str(e)}")
            return None

    async def save_jobs(self, jobs):
        """채용 정보 저장 - 중복 체크 추가"""
        try:
            saved = 0
            for job_data in jobs:
                # 중복 체크 - 같은 회사의 같은 제목 공고가 있는지 확인
                existing_job = Job.query.join(Company).filter(
                    Company.name == job_data['company_name'],
                    Job.title == job_data['title']
                ).first()
                
                if existing_job:
                    self.logger.debug(f"중복 공고 건너뜀: {job_data['title']}")
                    continue
                
                # 회사 정보 처리
                company = Company.query.filter_by(name=job_data['company_name']).first()
                if not company:
                    company = Company(name=job_data['company_name'])
                    db.session.add(company)
                    db.session.commit()
                
                # 채용 공고 저장
                job = Job(
                    company_id=company.id,
                    title=job_data['title'],
                    link=job_data['link'],
                    location=job_data['location'],
                    experience=job_data['experience'],
                    education=job_data['education'],
                    employment_type=job_data['employment_type'],
                    deadline=job_data['deadline'],
                    sector=job_data['sector']
                )
                db.session.add(job)
                saved += 1
            
            db.session.commit()
            self.logger.info(f"저장 완료: {saved}개의 채용공고")
            return saved
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"저장 실패: {str(e)}")
            return 0