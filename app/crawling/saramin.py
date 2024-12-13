import aiohttp
from bs4 import BeautifulSoup
import logging
import time
import random
from datetime import datetime
from .models import Job, Company
from .config import CrawlingConfig
from app.database import get_db
import asyncio
import csv
import os
from flask import current_app

class SaraminCrawler:
    def __init__(self):
        self.config = CrawlingConfig()
        self.session = None
        self.current_page = 1
        self.error_count = 0
        self.MAX_ERRORS = 3
        self.MAX_PAGES = 5  
        
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
        start_time = time.time()
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
                # 크롤링된 데이터 구조 로깅
                current_app.logger.info(f"Sample job data structure: {all_jobs[0]}")
                
                # CSV 파일로 저장
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                csv_dir = os.path.join(current_app.root_path, 'data', 'crawling')
                os.makedirs(csv_dir, exist_ok=True)
                
                csv_file = os.path.join(csv_dir, f'jobs_{timestamp}.csv')
                
                # 고정된 필드명 사용
                fieldnames = [
                    'id', 'company_name', 'title', 
                    'description', 'experience', 'education',
                    'employment_type', 'salary', 'location',
                    'deadline', 'tech_stack', 'created_at'
                ]
                
                with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for job in all_jobs:
                        # 데이터 매핑
                        row = {
                            'id': job.get('id', ''),
                            'company_name': job.get('company_name', ''),
                            'title': job.get('title', ''),
                            'description': job.get('description', ''),
                            'experience': job.get('experience', ''),
                            'education': job.get('education', ''),
                            'employment_type': job.get('employment_type', ''),
                            'salary': job.get('salary', ''),
                            'location': job.get('location', ''),
                            'deadline': job.get('deadline', ''),
                            'tech_stack': job.get('tech_stack', ''),
                            'created_at': job.get('created_at', '')
                        }
                        writer.writerow(row)
                
                current_app.logger.info(f"CSV file created: {csv_file}")
                
                # DB 저장도 계속 유지
                return await self.save_jobs(all_jobs)
            return 0
            
        except Exception as e:
            self.logger.error(f"크롤링 실패: {str(e)}", exc_info=True)
            raise
        
        # 로그 기록
        current_app.logger.info("Crawling completed", extra={
            'details': {
                'success_count': success_count,
                'error_count': error_count,
                'execution_time': time.time() - start_time
            }
        })

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
            db = get_db()
            cursor = db.cursor(dictionary=True)
            
            for job_data in jobs:
                # 중복 체크
                cursor.execute("""
                    SELECT j.* FROM job_postings j
                    INNER JOIN companies c ON j.company_id = c.company_id
                    WHERE c.name = %s AND j.title = %s
                    AND j.deleted_at IS NULL
                """, (job_data['company_name'], job_data['title']))
                
                if cursor.fetchone():
                    self.logger.debug(f"중복 공고 건너뜀: {job_data['title']}")
                    continue
                
                # 회사 정보 처리
                cursor.execute("SELECT company_id FROM companies WHERE name = %s", 
                             (job_data['company_name'],))
                company = cursor.fetchone()
                
                if not company:
                    cursor.execute("""
                        INSERT INTO companies (name, created_at) 
                        VALUES (%s, CURRENT_TIMESTAMP)
                    """, (job_data['company_name'],))
                    company_id = cursor.lastrowid
                else:
                    company_id = company['company_id']
                
                # 채용 공고 저장
                cursor.execute("""
                    INSERT INTO job_postings (
                        company_id, 
                        title,
                        job_description,
                        experience_level,
                        education_level,
                        employment_type,
                        salary_info,
                        deadline_date,
                        status,
                        created_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, 'active', CURRENT_TIMESTAMP
                    )
                """, (
                    company_id,
                    job_data['title'],
                    job_data.get('description', ''),
                    job_data.get('experience', ''),
                    job_data.get('education', ''),
                    job_data.get('employment_type', ''),
                    job_data.get('salary', ''),
                    job_data.get('deadline', None)  # deadline이 없으면 NULL
                ))
                saved += 1
            
            db.commit()
            self.logger.info(f"저장 완료: {saved}개의 채용공고")
            return saved
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"저장 실패: {str(e)}")
            raise
        finally:
            cursor.close()