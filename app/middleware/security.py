from functools import wraps
from flask import request, abort, make_response, current_app, jsonify
import html
import re
from urllib.parse import urlparse
import hashlib
import time
import logging

class SecurityMiddleware:
    def __init__(self):
        self.xss_pattern = re.compile(r'<[^>]*script.*?>|javascript:|onerror=|onload=|eval\(.*?\)')
        self.sql_pattern = re.compile(r'\b(union|select|insert|update|delete|drop|--)\b', re.IGNORECASE)
        
    def sanitize_input(self, data):
        """입력 데이터 살균"""
        if isinstance(data, str):
            # HTML 이스케이프
            return html.escape(data)
        elif isinstance(data, dict):
            return {k: self.sanitize_input(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_input(i) for i in data]
        return data

    def check_xss(self, data):
        """XSS 공격 탐지"""
        if isinstance(data, str):
            if self.xss_pattern.search(data):
                return True
        elif isinstance(data, dict):
            return any(self.check_xss(v) for v in data.values())
        elif isinstance(data, list):
            return any(self.check_xss(i) for i in data)
        return False

    def check_sql_injection(self, data):
        """SQL Injection 탐지"""
        if isinstance(data, str):
            if self.sql_pattern.search(data):
                return True
        elif isinstance(data, dict):
            return any(self.check_sql_injection(v) for v in data.values())
        elif isinstance(data, list):
            return any(self.check_sql_injection(i) for i in data)
        return False

    def security_headers(self):
        """보안 헤더 추가"""
        def decorator(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                response = make_response(f(*args, **kwargs))
                
                # 보안 헤더 설정
                response.headers['X-Content-Type-Options'] = 'nosniff'
                response.headers['X-Frame-Options'] = 'SAMEORIGIN'
                response.headers['X-XSS-Protection'] = '1; mode=block'
                response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
                response.headers['Content-Security-Policy'] = "default-src 'self'"
                
                return response
            return wrapped
        return decorator

    def validate_request(self):
        """요청 검증"""
        def decorator(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                # JSON 데이터 검증
                if request.is_json:
                    data = request.get_json()
                    
                    # XSS 검사
                    if self.check_xss(data):
                        abort(400, description="Potential XSS attack detected")
                    
                    # SQL Injection 검사
                    if self.check_sql_injection(data):
                        abort(400, description="Potential SQL injection detected")
                    
                    # 입력 살균
                    sanitized_data = self.sanitize_input(data)
                    request._cached_json = sanitized_data

                # URL 파라미터 검증
                for key, value in request.args.items():
                    if self.check_xss(value) or self.check_sql_injection(value):
                        abort(400, description="Invalid query parameter")

                return f(*args, **kwargs)
            return wrapped
        return decorator

def validate_json():
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            try:
                if not request.is_json:
                    return jsonify({
                        "status": "error",
                        "code": "InvalidContentType",
                        "message": "Content-Type must be application/json"
                    }), 400
                
                # force=True를 사용하여 JSON 파싱 강제
                data = request.get_json(force=True)
                if data is None:
                    return jsonify({
                        "status": "error",
                        "code": "InvalidJSON",
                        "message": "Invalid JSON data"
                    }), 400
                    
                return f(*args, **kwargs)
                
            except Exception as e:
                logging.error(f"JSON validation error: {str(e)}")
                return jsonify({
                    "status": "error",
                    "code": type(e).__name__,
                    "message": str(e)
                }), 400
                
        return wrapped
    return decorator

# 싱글톤 인스턴스
security = SecurityMiddleware() 