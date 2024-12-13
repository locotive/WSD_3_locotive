from app.crawling.saramin import SaraminCrawler
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/crawling_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_manual_crawling():
    logger.info("수동 크롤링 시작")
    crawler = SaraminCrawler()
    
    try:
        # 채용공고 크롤링 (최소 100개)
        logger.info("채용공고 수집 중...")
        jobs = crawler.crawl_jobs(min_jobs=100)
        logger.info(f"총 {len(jobs)}개의 채용공고 수집 완료")
        
        # 수집된 데이터 샘플 확인
        if jobs:
            logger.info("\n첫 번째 채용공고 데이터 샘플:")
            for key, value in jobs[0].items():
                logger.info(f"{key}: {value}")
        
        # DB 저장
        logger.info("\nDB 저장 시작...")
        crawler.save_to_db(jobs)
        logger.info("DB 저장 완료")
        
        return True
        
    except Exception as e:
        logger.error(f"크롤링 실패: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_manual_crawling()
    if success:
        logger.info("수동 크롤링이 성공적으로 완료되었습니다.")
    else:
        logger.error("수동 크롤링 중 오류가 발생했습니다.") 