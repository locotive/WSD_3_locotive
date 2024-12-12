from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from .saramin import SaraminCrawler
import logging

class CrawlingScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.crawler = SaraminCrawler()
        self.logger = logging.getLogger('scheduler')

    def start(self):
        """스케줄러 시작"""
        # 매일 자정에 크롤링 실행
        self.scheduler.add_job(
            self._daily_crawl,
            trigger=CronTrigger(hour=0, minute=0),
            id='daily_crawling'
        )
        
        self.scheduler.start()
        self.logger.info("크롤링 스케줄러 시작")

    def _daily_crawl(self):
        """일일 크롤링 작업"""
        try:
            jobs = self.crawler.crawl_jobs(min_jobs=100)
            self.crawler.save_to_db(jobs)
            self.logger.info(f"일일 크롤링 완료: {len(jobs)}개 수집")
        except Exception as e:
            self.logger.error(f"일일 크롤링 실패: {str(e)}")

    def stop(self):
        """스케줄러 정지"""
        self.scheduler.shutdown()
        self.logger.info("크롤링 스케줄러 정지")

# 싱글톤 인스턴스
scheduler = CrawlingScheduler() 