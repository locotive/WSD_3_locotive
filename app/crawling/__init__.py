from flask import Blueprint
from flask_apscheduler import APScheduler
from pytz import timezone
from apscheduler.schedulers.background import BackgroundScheduler

crawling_bp = Blueprint('crawling', __name__)

# 스케줄러 설정
scheduler_config = {
    'apscheduler.timezone': 'Asia/Seoul',
    'apscheduler.job_defaults.coalesce': False,
    'apscheduler.job_defaults.max_instances': 1
}

# 스케줄러 초기화
scheduler = APScheduler(scheduler=BackgroundScheduler(timezone='Asia/Seoul'))

def init_app(app):
    """크롤링 모듈 초기화"""
    from .routes import crawling_bp
    
    # APScheduler 설정 적용
    app.config.update(scheduler_config)
    
    # 스케줄러 작업 정의
    @scheduler.task('cron', id='daily_crawling', hour=2)
    def scheduled_crawling():
        with app.app_context():
            try:
                from .saramin import SaraminCrawler
                crawler = SaraminCrawler()
                jobs = crawler.crawl_jobs()
                saved_count = crawler.save_to_db(jobs)
                app.logger.info(f"Scheduled crawling completed: {saved_count} jobs saved")
            except Exception as e:
                app.logger.error(f"Scheduled crawling failed: {str(e)}")
    
    # 블루프린트 등록
    app.register_blueprint(crawling_bp, url_prefix='/crawling')
    
    # 스케줄러 초기화 및 시작 (app.app_context() 내에서)
    if not scheduler.running:
        scheduler.init_app(app)
        scheduler.api_enabled = True
        scheduler.start()

from . import routes