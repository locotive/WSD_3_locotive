from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps
from flask import request, g
import psutil

class APIMetrics:
    def __init__(self):
        # 요청 카운터
        self.request_count = Counter(
            'api_requests_total',
            'Total number of API requests',
            ['method', 'endpoint', 'status']
        )
        
        # 응답 시간 히스토그램
        self.request_latency = Histogram(
            'api_request_latency_seconds',
            'Request latency in seconds',
            ['method', 'endpoint'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
        )
        
        # 활성 요청 수 게이지
        self.active_requests = Gauge(
            'api_active_requests',
            'Number of active requests',
            ['method']
        )
        
        # 캐시 히트율 게이지
        self.cache_hit_ratio = Gauge(
            'api_cache_hit_ratio',
            'Cache hit ratio',
            ['endpoint']
        )
        
        # 에러율 게이지
        self.error_rate = Gauge(
            'api_error_rate',
            'API error rate',
            ['endpoint']
        )
        
        # DB 연결 풀 사용량
        self.db_pool_usage = Gauge(
            'api_db_pool_usage',
            'Database connection pool usage'
        )
        
        # 메모리 사용량
        self.memory_usage = Gauge(
            'api_memory_usage_bytes',
            'Memory usage in bytes'
        )

    def update_request_metrics(self, request, status_code=200):
        """요청 메트릭스 업데이트"""
        endpoint = request.endpoint or 'unknown'
        self.request_count.labels(
            method=request.method,
            endpoint=endpoint,
            status=status_code
        ).inc()

    def track_request(self):
        """요청 추적"""
        def decorator(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                method = request.method
                endpoint = request.endpoint or 'unknown'
                
                # 활성 요청 증가
                self.active_requests.labels(method=method).inc()
                
                start_time = time.time()
                try:
                    response = f(*args, **kwargs)
                    status = response.status_code
                except Exception as e:
                    status = 500
                    raise
                finally:
                    # 요청 카운터 증가
                    self.request_count.labels(
                        method=method,
                        endpoint=endpoint,
                        status=status
                    ).inc()
                    
                    # 응답 시간 기록
                    self.request_latency.labels(
                        method=method,
                        endpoint=endpoint
                    ).observe(time.time() - start_time)
                    
                    # 활성 요청 감소
                    self.active_requests.labels(method=method).dec()
                    
                return response
            return wrapped
        return decorator

    def update_cache_metrics(self, endpoint, hit):
        """캐시 메트릭 업데이트"""
        self.cache_hit_ratio.labels(endpoint=endpoint).set(
            1.0 if hit else 0.0
        )

    def update_error_metrics(self, endpoint, error_count, total_count):
        """에러율 메트릭 업데이트"""
        if total_count > 0:
            error_rate = error_count / total_count
            self.error_rate.labels(endpoint=endpoint).set(error_rate)

    def update_db_metrics(self, pool_size):
        """DB 메트릭 업데이트"""
        self.db_pool_usage.set(pool_size)

    def update_memory_metrics(self):
        """메모리 사용량 메트릭 업데이트"""
        process = psutil.Process()
        memory_info = process.memory_info()
        self.memory_usage.set(memory_info.rss)

    def update_latency_metrics(self, endpoint, duration):
        """지연 시간 메트릭스 업데이트"""
        if endpoint:
            self.request_latency.labels(
                method=request.method,
                endpoint=endpoint
            ).observe(duration)

# 싱글톤 인스턴스
metrics = APIMetrics() 