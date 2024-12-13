import aiohttp
from bs4 import BeautifulSoup
import logging
import time
import random
from datetime import datetime
from .models import Job, Company
from .config import CrawlingConfig
from app.database import db
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import asyncio

class SaraminCrawler:
    def __init__(self):
        self.config = CrawlingConfig()
        self.session = self._create_session()
        self.current_page = 1
        self.error_count = 0
        self.MAX_ERRORS = 3
        self.MAX_RETRIES = 3
        self.RETRY_DELAY = 60  # 재시도 간격 1분으로 증가
        
        # 로거 설정
        self.logger = logging.getLogger('crawler')
        self.logger.setLevel(logging.DEBUG)
    
    async def _create_session(self):
        session = aiohttp.ClientSession()
        
        # 재시도 전략 강화
        retry_strategy = Retry(
            total=5,
            backoff_factor=2,  # 지수 백오프 증가
            status_forcelist=[500, 502, 503, 504, 429, 403],
            allowed_methods=["GET", "HEAD", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=5,  # 연결 풀 크기 조정
            pool_maxsize=5
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # 타더 다양화
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
        })
        
        return session
    
    async def crawl_jobs(self):
        """채용 정보 크롤링 실행"""
        try:
            self.logger.info("크롤링 시작")
            all_jobs = []
            search_url = f"{self.config.BASE_URL}/zf_user/search/recruit"
            
            self.logger.debug(f"검색 URL: {search_url}")
            
            params = {
                'searchType': 'search',
                'searchword': 'python',
                'loc_mcd': '101000',
                'job_type': '1',
                'exp_cd': '1',
                'panel_type': 'auto',
                'search_optional_item': 'y',
                'search_done': 'y',
                'panel_count': 'y'
            }
            
            self.logger.debug(f"검색 파라미터: {params}")
            
            retry_count = 0
            while retry_count < self.MAX_RETRIES:
                try:
                    params['recruitPage'] = self.current_page
                    params['page'] = self.current_page
                    
                    self.logger.info(f"페이지 {self.current_page} 크롤링 시작")
                    
                    # 랜덤 지연 시간 추가
                    delay = random.uniform(5, 8)
                    self.logger.debug(f"대기 시간: {delay}초")
                    await asyncio.sleep(delay)
                    
                    self.logger.debug(f"HTTP 요청 시작: {search_url}")
                    response = self.session.get(
                        search_url,
                        params=params,
                        timeout=(30, 60)  # (연결 타임아웃, 읽기 타임아웃)
                    )
                    self.logger.debug(f"HTTP 응답 상태 코드: {response.status_code}")
                    self.logger.debug(f"HTTP 응답 헤더: {dict(response.headers)}")
                    
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    job_elements = soup.select('.item_recruit')
                    
                    self.logger.info(f"페이지 {self.current_page}에서 {len(job_elements)}개의 채용공고 발견")
                    
                    if not job_elements:
                        self.logger.warning(f"페이지 {self.current_page}에서 채용공고를 찾을 수 없음")
                        if self.error_count < self.MAX_ERRORS:
                            self.error_count += 1
                            self.logger.warning(f"에러 카운트 증가: {self.error_count}/{self.MAX_ERRORS}")
                            await asyncio.sleep(10)
                            continue
                        else:
                            self.logger.error("최대 에러 횟수 초과")
                            break
                    
                    for element in job_elements:
                        if job_info := self.extract_job_info(element):
                            all_jobs.append(job_info)
                    
                    self.logger.info(f"페이지 {self.current_page} 크롤링 완료")
                    self.current_page += 1
                    self.error_count = 0
                    
                    return saved_count
                    
                except requests.exceptions.Timeout as e:
                    self.logger.error(f"타임아웃 발생: {str(e)}")
                    self.logger.error(f"현재 설정: 연결 타임아웃 30초, 읽기 타임아웃 60초")
                    self.error_count += 1
                    await asyncio.sleep(30)
                    
                except requests.exceptions.RequestException as e:
                    self.logger.error(f"HTTP 요청 실패: {str(e)}")
                    self.logger.error(f"요청 URL: {search_url}")
                    self.logger.error(f"요청 파라미터: {params}")
                    self.error_count += 1
                    await asyncio.sleep(30)
                    
                except Exception as e:
                    self.logger.error(f"예상치 못한 오류 발생: {str(e)}", exc_info=True)
                    self.error_count += 1
                    await asyncio.sleep(30)
                retry_count += 1
                self.logger.error(f"크롤링 시도 {retry_count} 실패: {str(e)}")
                if retry_count >= self.MAX_RETRIES:
                    raise
                await asyncio.sleep(self.RETRY_DELAY)
            
            self.logger.info(f"전체 수집된 채용공고 수: {len(all_jobs)}")
            
            if all_jobs:
                saved_count = await self.save_jobs(all_jobs)
                self.logger.info(f"저장된 채용공고 수: {saved_count}")
                return saved_count
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
        """채용 정보 저장"""
        try:
            saved = 0
            for job_data in jobs:
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
            logging.info(f"저장 완료: {saved}개의 채용공고")
            return saved
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"저장 실패: {str(e)}")
            return 0