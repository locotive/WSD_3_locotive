import requests
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

class SaraminCrawler:
    def __init__(self):
        self.config = CrawlingConfig()
        self.session = self._create_session()
    
    def _create_session(self):
        """요청 세션 생성 및 설정"""
        session = requests.Session()
        
        # 재시도 전략 설정
        retry_strategy = Retry(
            total=3,  # 최대 재시도 횟수
            backoff_factor=0.5,  # 재시도 간격
            status_forcelist=[500, 502, 503, 504]  # 재시도할 HTTP 상태 코드
        )
        
        # 세션 어댑터 설정
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=10
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # 타임아웃 및 헤더 설정
        session.headers.update(self.config.HEADERS)
        session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        return session
    
    async def crawl_jobs(self):
        """채용 정보 크롤링 실행"""
        try:
            all_jobs = []
            search_url = f"{self.config.BASE_URL}/zf_user/search/recruit"
            
            # Python 개발자 채용공고 검색
            params = {
                'searchword': 'python',
                'loc_mcd': '101000',  # 서울
                'job_type': '1',      # 정규직
                'exp_cd': '1',        
            }
            
            for page in range(1, self.config.MAX_PAGES + 1):
                try:
                    params['recruitPage'] = page
                    response = self.session.get(
                        search_url, 
                        params=params,
                        timeout=(5, 15)  # (연결 타임아웃, 읽기 타임아웃)
                    )
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    job_elements = soup.select('.item_recruit')
                    
                    if not job_elements:
                        break
                        
                    for element in job_elements:
                        if job_info := self.extract_job_info(element):
                            all_jobs.append(job_info)
                    
                    time.sleep(random.uniform(2, 3))  # 딜레이 증가
                    
                except requests.exceptions.RequestException as e:
                    logging.error(f"페이지 {page} 요청 실패: {str(e)}")
                    time.sleep(5)  # 오류 발생시 더 긴 대기
                    continue
                except Exception as e:
                    logging.error(f"페이지 {page} 처리 중 오류: {str(e)}")
                    continue
            
            # 수집된 데이터 저장
            saved_count = await self.save_jobs(all_jobs)
            return saved_count
            
        except Exception as e:
            logging.error(f"크롤링 실패: {str(e)}")
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