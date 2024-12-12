from functools import wraps
import time
from flask import request, jsonify, g
import redis
import os

# Redis 연결 설정
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=0,
    decode_responses=True
)

def rate_limit(requests=100, window=60):
    """
    Rate limiting 데코레이터
    :param requests: 허용되는 최대 요청 수
    :param window: 시간 윈도우 (초)
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # API 키나 IP 주소로 식별
            identifier = request.headers.get('X-API-KEY') or request.remote_addr
            
            # Redis 키 생성
            key = f'rate_limit:{identifier}'
            
            try:
                # 현재 요청 수 가져오기
                current = redis_client.get(key)
                
                if current is None:
                    # 새로운 키 설정
                    redis_client.setex(key, window, 1)
                else:
                    current = int(current)
                    if current >= requests:
                        return jsonify({
                            "status": "error",
                            "message": "Rate limit exceeded",
                            "code": "RATE_LIMIT_EXCEEDED"
                        }), 429
                    
                    # 요청 수 증가
                    redis_client.incr(key)
                
                # 남은 요청 수를 헤더에 포함
                response = f(*args, **kwargs)
                remaining = requests - (int(redis_client.get(key) or 0))
                
                # 응답이 튜플인 경우 (응답, 상태 코드)
                if isinstance(response, tuple):
                    response_obj, status_code = response
                    headers = {
                        'X-RateLimit-Limit': str(requests),
                        'X-RateLimit-Remaining': str(remaining),
                        'X-RateLimit-Reset': str(redis_client.ttl(key))
                    }
                    return response_obj, status_code, headers
                
                # 일반 응답인 경우
                return response, 200, {
                    'X-RateLimit-Limit': str(requests),
                    'X-RateLimit-Remaining': str(remaining),
                    'X-RateLimit-Reset': str(redis_client.ttl(key))
                }
                
            except redis.RedisError:
                # Redis 에러 시 기본적으로 요청 허용
                return f(*args, **kwargs)
                
        return wrapped
    return decorator

# 엔드포인트별 다른 rate limit 설정
def api_rate_limit():
    """API 엔드포인트별 rate limit 설정"""
    endpoint = request.endpoint
    
    # 엔드포인트별 rate limit 설정
    limits = {
        'list_jobs': (200, 60),  # 채용공고 목록: 200req/1min
        'search_jobs': (100, 60),  # 검색: 100req/1min
        'apply_job': (30, 60),   # 지원: 30req/1min
        'register_user': (10, 60) # 회원가입: 10req/1min
    }
    
    # 기본값
    default_limit = (100, 60)  # 100req/1min
    
    requests, window = limits.get(endpoint, default_limit)
    return rate_limit(requests=requests, window=window) 