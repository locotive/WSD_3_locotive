from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from pyvirtualdisplay import Display
import logging
import time
import random
from datetime import datetime
from .models import Job, Company
from .config import CrawlingConfig
from app.database import db

class SaraminCrawler:
    def __init__(self):
        self.config = CrawlingConfig()
        self.display = None
        self.driver = None
        
    def setup_driver(self):
        """Chrome WebDriver 및 가상 디스플레이 설정"""
        try:
            # 가상 디스플레이 시작
            self.display = Display(visible=0, size=(1920, 1080))
            self.display.start()
            
            # Chrome 옵션 설정
            chrome_options = Options()
            chrome_options.add_argument('--headless=new')  # 새로운 headless 모드
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920x1080')
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # WebDriver 초기화
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 자동화 감지 우회
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": self.config.HEADERS["User-Agent"]
            })
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            
        except Exception as e:
            logging.error(f"WebDriver 설정 실패: {str(e)}")
            if self.display:
                self.display.stop()
            raise

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
                'exp_cd': '1',        # 신입
            }
            
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            self.driver.get(f"{search_url}?{query_string}")
            
            for page in range(1, self.config.MAX_PAGES + 1):
                try:
                    # 채용공고 목록 로딩 대기
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_all_elements_located(
                            (By.CLASS_NAME, "item_recruit")
                        )
                    )
                    
                    # 채용공고 정보 추출
                    job_elements = self.driver.find_elements(By.CLASS_NAME, "item_recruit")
                    for element in job_elements:
                        if job_info := self.extract_job_info(element):
                            all_jobs.append(job_info)
                    
                    # 다음 페이지로 이동
                    next_page = f"{search_url}?{query_string}&recruitPage={page + 1}"
                    self.driver.get(next_page)
                    time.sleep(random.uniform(2, 4))  # 랜덤 딜레이
                    
                except TimeoutException:
                    logging.error(f"페이지 {page} 로딩 시간 초과")
                    break
                    
                except Exception as e:
                    logging.error(f"페이지 {page} 처리 중 오류: {str(e)}")
                    continue
            
            # 수집된 데이터 저장
            saved_count = await self.save_jobs(all_jobs)
            return saved_count
            
        finally:
            self.driver.quit()

    def extract_job_info(self, element):
        """채용 정보 추출"""
        try:
            info = {}
            
            # 기본 정보
            title_elem = element.find_element(By.CSS_SELECTOR, '[class*="job_tit"]')
            info['title'] = title_elem.text.strip()
            info['link'] = title_elem.get_attribute('href')
            
            # 회사 정보
            company_elem = element.find_element(By.CSS_SELECTOR, '[class*="corp_name"]')
            info['company_name'] = company_elem.text.strip()
            
            # 상세 정보
            details = element.find_elements(By.CSS_SELECTOR, '[class*="job_condition"] > span')
            info.update({
                'location': details[0].text if len(details) > 0 else '',
                'experience': details[1].text if len(details) > 1 else '',
                'education': details[2].text if len(details) > 2 else '',
                'employment_type': details[3].text if len(details) > 3 else ''
            })
            
            # 추가 정보
            deadline_elem = element.find_element(By.CSS_SELECTOR, '[class*="date"]')
            info['deadline'] = deadline_elem.text if deadline_elem else ''
            
            sector_elem = element.find_element(By.CSS_SELECTOR, '[class*="job_sector"]')
            info['sector'] = sector_elem.text if sector_elem else ''
            
            return info
            
        except NoSuchElementException as e:
            logging.error(f"요소를 찾을 수 없음: {str(e)}")
            return None
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