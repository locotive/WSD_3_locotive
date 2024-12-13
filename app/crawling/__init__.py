from flask import Blueprint

crawling_bp = Blueprint('crawling', __name__)

from . import routes

def init_app(app):
    """크롤링 모듈 초기화"""
    from flask_apscheduler import APScheduler
    from .saramin import SaraminCrawler
    
    scheduler = APScheduler()
    scheduler.init_app(app)
    
    # 스케줄러 작업 정의
    @scheduler.task('cron', id='daily_crawling', hour=2)  # 매일 새벽 2시 실행
    def scheduled_crawling():
        with app.app_context():
            try:
                crawler = SaraminCrawler()
                jobs = crawler.crawl_jobs()
                saved_count = crawler.save_to_db(jobs)
                app.logger.info(f"Scheduled crawling completed: {saved_count} jobs saved")
            except Exception as e:
                app.logger.error(f"Scheduled crawling failed: {str(e)}")
    
    # 블루프린트 등록
    app.register_blueprint(crawling_bp, url_prefix='/crawling')
    
    # 스케줄러 시작
    scheduler.start() 