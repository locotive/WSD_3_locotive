from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
from app.auth.routes import auth_bp
from app.jobs.routes import jobs_bp
from app.users.routes import user_bp
from app.applications.routes import applications_bp
from app.bookmarks.routes import bookmarks_bp
from app.common.error_handlers import register_error_handlers
from app.database import close_db
from app.config import Config
from app.companies.routes import companies_bp
from app.common.logging import setup_logger
from app.crawling.scheduler import scheduler
from app.middleware.rate_limit import api_rate_limit
from app.cache.redis_cache import cache
from app.middleware.security import security
from app.logging.logger import logger
from app.monitoring.metrics import metrics
from prometheus_client import make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from app.crawling.scheduler import scheduler
import time
import atexit

def create_app():
    app = Flask(__name__,
        static_url_path='/static',
        static_folder='../static'
    )
    CORS(app)

    # 로깅 설정
    setup_logger()
    
    # 스케줄러 시작
    @app.before_first_request
    def start_scheduler():
        scheduler.start()

    # 애플리케이션 종료 시 스케줄러 정지
    atexit.register(scheduler.stop)

    # Prometheus 메트릭 엔드포인트 추가
    app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
        '/metrics': make_wsgi_app()
    })

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(jobs_bp, url_prefix='/jobs')
    app.register_blueprint(user_bp, url_prefix='/users')
    app.register_blueprint(applications_bp, url_prefix='/applications')
    app.register_blueprint(bookmarks_bp, url_prefix='/bookmarks')
    app.register_blueprint(companies_bp, url_prefix='/companies')

    # Register Swagger UI blueprint
    SWAGGER_URL = '/api/docs'
    API_URL = '/static/swagger.json'
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={'app_name': "Job API"}
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    @app.before_request
    def before_request():
        # 요청 시작 시간 저장
        g.start_time = time.time()
        # 요청 로깅
        logger.log_request()
        
        # 메모리 메트릭 업데이트
        metrics.update_memory_metrics()

    # 미들웨어 전역 적용
    @app.before_request
    def apply_middleware():
        if request.path.startswith(('/api/docs', '/static', '/metrics')):
            return

        endpoint = app.view_functions.get(request.endpoint)
        if not endpoint:
            return

        # 메트릭 추적 추가
        endpoint = metrics.track_request()(endpoint)
        
        # 보안 미들웨어 적용
        endpoint = security.validate_request()(endpoint)
        endpoint = security.security_headers()(endpoint)
        
        # Rate Limiting 적용
        endpoint = api_rate_limit()(endpoint)
        
        # 캐시 적용 (GET 요청만)
        if request.method == 'GET':
            cache_timeouts = {
                'list_jobs': 300,
                'get_job_detail': 600,
                'list_companies': 1800,
                'get_company_detail': 1800,
                'get_tech_stacks': 3600,
                'get_locations': 3600,
                'get_tech_trends': 86400,
                'get_location_trends': 86400
            }
            timeout = cache_timeouts.get(request.endpoint, 300)
            endpoint = cache.cache_response(timeout=timeout)(endpoint)

        app.view_functions[request.endpoint] = endpoint

    @app.after_request
    def after_request(response):
        # 메트릭스 업데이트
        metrics.update_request_metrics(request, response.status_code)
        
        # 응답 시간 기록
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            metrics.update_latency_metrics(request.endpoint, duration)
            logger.log_performance(duration * 1000)  # ms로 변환
        
        # 응답 로깅
        logger.log_response(response)  # request 인자 제거
        
        # DB 커넥션 풀 메트릭스 업데이트
        try:
            metrics.update_db_metrics(db_pool.pool_size)
        except:
            pass  # DB 메트릭스 업데이트 실패 시 무시
        
        return response

    @app.errorhandler(Exception)
    def handle_error(error):
        # 에러 로깅
        logger.log_error(error)
        
        # 에러 메트릭 업데이트
        if hasattr(g, 'error_counts'):
            g.error_counts[request.endpoint] = g.error_counts.get(request.endpoint, 0) + 1
            metrics.update_error_metrics(
                request.endpoint,
                g.error_counts[request.endpoint],
                metrics.request_count.labels(
                    method=request.method,
                    endpoint=request.endpoint,
                    status='500'
                )._value.get()
            )
        
        # 에러 응답
        return jsonify({
            "status": "error",
            "message": str(error),
            "code": type(error).__name__
        }), getattr(error, 'code', 500)

    # Register error handlers
    register_error_handlers(app)

    # Teardown app context
    app.teardown_appcontext(close_db)

    return app 