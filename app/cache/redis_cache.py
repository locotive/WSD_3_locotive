import redis
import json
from functools import wraps
from flask import request
import os
from datetime import timedelta

class RedisCache:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=1,  # Rate limiting과 다른 DB 사용
            decode_responses=True
        )

    def cache_response(self, timeout=300):  # 기본 5분
        def decorator(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                # 캐시 키 생성 (URL + 쿼리 파라미터)
                cache_key = f"cache:{request.path}:{request.query_string.decode()}"
                
                # GET 요청만 캐시
                if request.method != 'GET':
                    return f(*args, **kwargs)

                # 캐시된 데이터 확인
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)

                # 원본 함수 실행
                result = f(*args, **kwargs)
                
                # 결과 캐싱
                if result:
                    self.redis_client.setex(
                        cache_key,
                        timeout,
                        json.dumps(result)
                    )
                
                return result
            return wrapped
        return decorator

    def invalidate_cache(self, pattern="*"):
        """특정 패턴의 캐시 삭제"""
        for key in self.redis_client.scan_iter(f"cache:{pattern}"):
            self.redis_client.delete(key)

    def get_cache_size(self):
        """전체 캐시 크기 확인"""
        return len(list(self.redis_client.scan_iter("cache:*")))

# 싱글톤 인스턴스 생성
cache = RedisCache() 