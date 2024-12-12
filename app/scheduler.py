from apscheduler.schedulers.background import BackgroundScheduler
from app.crawling.saramin import SaraminCrawler
import logging

logger = logging.getLogger(__name__)

def crawl_and_save():
    """크롤링 실행 및 저장"""
    try:
        crawler = SaraminCrawler()
        jobs = crawler.crawl_jobs()
        crawler.save_to_db(jobs)
        logger.info(f"Successfully crawled and saved {len(jobs)} jobs")
    except Exception as e:
        logger.error(f"Crawling job failed: {str(e)}")

def init_scheduler():
    """스케줄러 초기화 및 시작"""
    scheduler = BackgroundScheduler()
    
    # 매일 자정에 실행
    scheduler.add_job(
        crawl_and_save,
        'cron',
        hour=0,
        minute=0
    )
    
    # 즉시 한 번 실행
    scheduler.add_job(crawl_and_save)
    
    scheduler.start()