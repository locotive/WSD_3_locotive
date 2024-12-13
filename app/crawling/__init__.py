from flask import Blueprint
from flask_apscheduler import APScheduler
from pytz import timezone

crawling_bp = Blueprint('crawling', __name__)

# APScheduler 설정
scheduler_config = {
    'timezone': timezone('Asia/Seoul'),  # 명시적으로 타임존 설정
    'job_defaults': {
        'coalesce': False,
        'max_instances': 1
    }
}

scheduler = APScheduler()

def init_app(app):
    """크롤링 모듈 초기화"""
    from .routes import crawling_bp
    
    # APScheduler 설정 적용
    app.config['SCHEDULER_API_ENABLED'] = True
    app.config['SCHEDULER_TIMEZONE'] = 'Asia/Seoul'
    
    scheduler.init_app(app)
    scheduler.api_enabled = True
    
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
    
    # 스케줄러 시작
    scheduler.start()

from . import routes