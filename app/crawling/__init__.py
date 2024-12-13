from flask import Blueprint
from flask_apscheduler import APScheduler
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
import os

# 타임존 환경 변수 설정
os.environ['TZ'] = 'Asia/Seoul'

crawling_bp = Blueprint('crawling', __name__)

# 스케줄러 설정
scheduler_config = {
    'SCHEDULER_TIMEZONE': pytz.timezone('Asia/Seoul'),
    'SCHEDULER_API_ENABLED': True,
    'SCHEDULER_JOB_DEFAULTS': {
        'coalesce': False,
        'max_instances': 1
    }
}

# 스케줄러 초기화
scheduler = APScheduler()

cache_timeouts = {
    # ... existing timeouts ...
    'get_crawling_status': 60,  # 1분
    'get_crawling_logs': 300    # 5분
}

def init_app(app):
    """크롤링 모듈 초기화"""
    from .routes import crawling_bp
    
    # APScheduler 설정 적용
    app.config.update(scheduler_config)
    
    try:
        # 스케줄러 초기화
        if not scheduler.running:
            scheduler.init_app(app)
            
            # 스케줄러 작업 정의
            @scheduler.task('cron', id='daily_crawling', hour=2)
            async def scheduled_crawling():
                with app.app_context():
                    try:
                        from .saramin import SaraminCrawler
                        crawler = SaraminCrawler()
                        saved_count = await crawler.crawl_jobs()
                        app.logger.info(f"Scheduled crawling completed: {saved_count} jobs saved")
                    except Exception as e:
                        app.logger.error(f"Scheduled crawling failed: {str(e)}")
            
            scheduler.start()
            app.logger.info("Scheduler started successfully")
    except Exception as e:
        app.logger.error(f"Failed to initialize scheduler: {str(e)}")
    
    # 블루프린트 등록
    app.register_blueprint(crawling_bp, url_prefix='/crawling')

from . import routes