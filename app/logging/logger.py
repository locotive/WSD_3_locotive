import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import os
import json
from datetime import datetime
from flask import request, g
import traceback

class APILogger:
    def __init__(self):
        self.setup_loggers()
        
    def setup_loggers(self):
        # 로그 디렉토리 생성
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # API 요청 로거
        self.api_logger = logging.getLogger('api')
        self.api_logger.setLevel(logging.INFO)
        api_handler = TimedRotatingFileHandler(
            'logs/api.log',
            when='midnight',
            interval=1,
            backupCount=30
        )
        api_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.api_logger.addHandler(api_handler)
        
        # 에러 로거
        self.error_logger = logging.getLogger('error')
        self.error_logger.setLevel(logging.ERROR)
        error_handler = RotatingFileHandler(
            'logs/error.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=10
        )
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s\n%(exc_info)s'
        ))
        self.error_logger.addHandler(error_handler)
        
        # 성능 로거
        self.perf_logger = logging.getLogger('performance')
        self.perf_logger.setLevel(logging.INFO)
        perf_handler = TimedRotatingFileHandler(
            'logs/performance.log',
            when='H',
            interval=1,
            backupCount=24
        )
        perf_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(message)s'
        ))
        self.perf_logger.addHandler(perf_handler)

    def log_request(self):
        """API 요청 로깅"""
        request_data = {
            'endpoint': request.endpoint,
            'method': request.method,
            'path': request.path,
            'args': dict(request.args),
            'headers': dict(request.headers),
            'ip': request.remote_addr,
            'timestamp': datetime.now().isoformat()
        }
        
        if request.is_json:
            request_data['body'] = request.get_json()
            
        self.api_logger.info(json.dumps(request_data))

    def log_response(self, response):
        """API 응답 로깅"""
        response_data = {
            'endpoint': request.endpoint,
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            if response.is_json:
                response_data['body'] = response.get_json()
        except:
            pass
            
        self.api_logger.info(json.dumps(response_data))

    def log_error(self, error):
        """에러 로깅"""
        error_data = {
            'endpoint': request.endpoint,
            'method': request.method,
            'path': request.path,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'timestamp': datetime.now().isoformat()
        }
        
        self.error_logger.error(json.dumps(error_data))

    def log_performance(self, duration):
        """성능 로깅"""
        perf_data = {
            'endpoint': request.endpoint,
            'method': request.method,
            'path': request.path,
            'duration_ms': round(duration * 1000, 2),
            'timestamp': datetime.now().isoformat()
        }
        
        self.perf_logger.info(json.dumps(perf_data))

# 싱글톤 인스턴스
logger = APILogger() 