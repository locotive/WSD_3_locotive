# app/crawling/local_crawler.py

import aiohttp
from bs4 import BeautifulSoup
import logging
import time
import random
from datetime import datetime
import asyncio
import csv
import os

class LocalSaraminCrawler:
    def __init__(self):
        self.base_url = "https://www.saramin.co.kr"
        self.session = None
        self.current_page = 1
        self.error_count = 0
        self.MAX_ERRORS = 3
        self.MAX_PAGES = 10
        
        # 로깅 설정
        self.logger = logging.getLogger('local_crawler')
        self.logger.setLevel(logging.INFO)
        
    async def _create_session(self):
        return aiohttp.ClientSession(headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
        })
    
    async def crawl_jobs(self):
        """채용 정보 크롤링 실행"""
        try:
            self.logger.info("크롤링 시작")
            all_jobs = []
            search_url = f"{self.base_url}/zf_user/search/recruit"
            
            async with await self._create_session() as session:
                self.session = session
                
                while self.current_page <= self.MAX_PAGES:
                    try:
                        params = {
                            'searchType': 'search',
                            'searchword': 'python',
                            'recruitPage': self.current_page
                        }
                        
                        self.logger.info(f"페이지 {self.current_page} 크롤링 중...")
                        
                        # 요청 간 딜레이
                        delay = random.uniform(1, 3)
                        await asyncio.sleep(delay)
                        
                        async with session.get(search_url, params=params) as response:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            job_elements = soup.select('.item_recruit')
                            
                            if not job_elements:
                                break
                                
                            for element in job_elements:
                                if job_info := self.extract_job_info(element):
                                    all_jobs.append(job_info)
                            
                            self.current_page += 1
                            
                    except Exception as e:
                        self.logger.error(f"페이지 크롤링 실패: {str(e)}")
                        break
                        
            # 결과 저장
            if all_jobs:
                self.save_to_csv(all_jobs)
                
            return len(all_jobs)
            
        except Exception as e:
            self.logger.error(f"크롤링 실패: {str(e)}")
            return 0
            
    def extract_job_info(self, element):
        """채용 정보 추출"""
        try:
            info = {}
            
            # 제목과 회사명
            title_elem = element.select_one('[class*="job_tit"] a')
            company_elem = element.select_one('[class*="corp_name"] a')
            
            if title_elem and company_elem:
                info['title'] = title_elem.text.strip()
                info['company_name'] = company_elem.text.strip()
                
                # 상세 정보
                details = element.select('[class*="job_condition"] > span')
                info['location'] = details[0].text.strip() if len(details) > 0 else ''
                info['experience'] = details[1].text.strip() if len(details) > 1 else ''
                info['education'] = details[2].text.strip() if len(details) > 2 else ''
                
                # 마감일
                deadline_elem = element.select_one('[class*="date"]')
                info['deadline'] = deadline_elem.text.strip() if deadline_elem else ''
                
                return info
                
        except Exception as e:
            self.logger.error(f"정보 추출 실패: {str(e)}")
            return None
            
    def save_to_csv(self, jobs):
        """결과를 CSV 파일로 저장"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        os.makedirs('crawled_data', exist_ok=True)
        filename = f'crawled_data/saramin_jobs_{timestamp}.csv'
        
        fieldnames = ['title', 'company_name', 'location', 'experience', 
                     'education', 'deadline']
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(jobs)
            
            self.logger.info(f"결과가 {filename}에 저장되었습니다.")
            
        except Exception as e:
            self.logger.error(f"CSV 저장 실패: {str(e)}")

if __name__ == '__main__':
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # 크롤러 실행
    crawler = LocalSaraminCrawler()
    result = asyncio.run(crawler.crawl_jobs())
    print(f"\n크롤링 완료: {result}개의 채용공고를 찾았습니다.")