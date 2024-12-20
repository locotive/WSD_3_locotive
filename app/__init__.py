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
from app.middleware.rate_limit import api_rate_limit
from app.cache.redis_cache import cache
from app.middleware.security import security
from app.logging.logger import logger
from app.monitoring.metrics import metrics
from prometheus_client import make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from app.crawling import scheduler
from app.crawling.routes import crawling_bp
from app.resumes.routes import resumes_bp
from .crawling import init_app as init_crawling
import time
import atexit
import yaml
import json
import os
from functools import wraps
import logging

def create_app():
    app = Flask(__name__,
        static_url_path='/static',
        static_folder='static'
    )
    
    # Config 적용
    app.config.from_object(Config)
    
    # 환경 변수에서 직접 로드 (백업)
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    
    # CORS 설정 수정
    CORS(app, resources={
        r"/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })

    # 로깅 설정
    setup_logger()
    
    # 애플리케이션 종료 시 스케줄러 정지
    atexit.register(scheduler.shutdown)

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
    app.register_blueprint(resumes_bp)

    # 먼저 swagger.json 생성
    swagger_data = {
        "openapi": "3.0.0",
        "info": {
            "title": "Job Board API",
            "version": "1.0.0",
            "description": """
# 채용 플랫폼 API 문서

## 인증 방식
- Bearer Token 인증 사용
- /auth/login에서 발급받은 access_token을 Authorization 헤더에 포함
- 예: Authorization: Bearer <access_token>

## 공통 에러 코드
- 400: 잘못된 요청
- 401: 인증 실패
- 403: 권한 없음
- 404: 리소스 없음
- 409: 충돌 (중복 등)
- 500: 서버 에러

## 응답 형식
성공 응답:
```json
{
    "status": "success",
    "data": { ... }
}
```

에러 응답:
```json
{
    "status": "error",
    "message": "에러 메시지"
}
```
            """
        },
        "paths": {},
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                }
            },
            "schemas": {},
            "responses": {
                "UnauthorizedError": {
                    "description": "인증 실패",
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/Error"
                            }
                        }
                    }
                }
            }
        }
    }
    
    # YAML 파일 병합
    yaml_files = [
        'auth.yml', 
        'jobs.yml', 
        'applications.yml', 
        'bookmarks.yml', 
        'resumes.yml',
        'crawling.yml'
    ]
    for yaml_file in yaml_files:
        file_path = os.path.join('app', 'docs', yaml_file)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f)
                
                # paths 병합
                if 'paths' in yaml_data:
                    for path, operations in yaml_data['paths'].items():
                        if path not in swagger_data['paths']:
                            swagger_data['paths'][path] = {}
                        swagger_data['paths'][path].update(operations)
                
                # components 병합
                if 'components' in yaml_data:
                    for component_type, components in yaml_data['components'].items():
                        if component_type not in swagger_data['components']:
                            swagger_data['components'][component_type] = {}
                        swagger_data['components'][component_type].update(components)
                
                # tags 병합 (중복 제거)
                if 'tags' in yaml_data:
                    existing_tags = {tag['name']: tag for tag in swagger_data.get('tags', [])}
                    for tag in yaml_data['tags']:
                        existing_tags[tag['name']] = tag
                    swagger_data['tags'] = list(existing_tags.values())
    
    # static 디렉토리 생성 및 파일 저장
    os.makedirs('app/static', exist_ok=True)
    with open('app/static/swagger.json', 'w', encoding='utf-8') as f:
        json.dump(swagger_data, f, ensure_ascii=False, indent=2)
    
    # 그 다음 Swagger UI Blueprint 등록
    SWAGGER_URL = '/api/docs'
    API_URL = '/static/swagger.json'
    
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            'app_name': "Job Board API"
        }
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
    
    @app.before_request
    def before_request():
        # GET 요청의 경우 Content-Type 헤더 제거
        if request.method == 'GET' and 'Content-Type' in request.headers:
            del request.headers['Content-Type']
        
        g.start_time = time.time()
        logger.log_request()
        logging.info(f"[Request] Headers: {dict(request.headers)}")
        metrics.update_memory_metrics()

    # cache_timeouts 정의
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

    @app.after_request
    def after_request(response):
        # 메트릭스 업데이트
        metrics.update_request_metrics(request, response.status_code)
        
        # 응답 시간 기록
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            metrics.update_latency_metrics(request.endpoint, duration)
            logger.log_performance(duration * 1000)
        
        # 응답 로깅
        logger.log_response(response)
        
        return response

    @app.errorhandler(Exception)
    def handle_error(error):
        # 에러 상세 로깅
        logging.error(f"[Error Handler] Exception type: {type(error).__name__}")
        logging.error(f"[Error Handler] Error message: {str(error)}")
        logging.error(f"[Error Handler] Request path: {request.path}")
        logging.error(f"[Error Handler] Request method: {request.method}")
        logging.error(f"[Error Handler] Request headers: {dict(request.headers)}")
        
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
        
        # Bad Request 에러인 경우 추가 정보 로깅
        if getattr(error, 'code', 500) == 400:
            logging.error(f"[Error Handler] Bad Request details:")
            logging.error(f"[Error Handler] Request data: {request.get_data()}")
            if request.is_json:
                logging.error(f"[Error Handler] JSON data: {request.get_json(silent=True)}")
        
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

    # 크롤링 모듈 초기화
    init_crawling(app)

    return app 