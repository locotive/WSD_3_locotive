from functools import wraps
from flask import request, abort, make_response, current_app, jsonify, Response
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
            return html.escape(data)
        elif isinstance(data, dict):
            return {k: self.sanitize_input(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_input(i) for i in data]
        return data

    def check_xss(self, data):
        """XSS 공격 탐지"""
        if isinstance(data, str):
            return bool(self.xss_pattern.search(data))
        elif isinstance(data, dict):
            return any(self.check_xss(v) for v in data.values())
        elif isinstance(data, list):
            return any(self.check_xss(i) for i in data)
        return False

    def check_sql_injection(self, data):
        """SQL Injection 탐지"""
        if isinstance(data, str):
            return bool(self.sql_pattern.search(data))
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
                response = f(*args, **kwargs)
                
                # 응답이 튜플인 경우
                if isinstance(response, tuple):
                    response_obj = response[0]
                    status = response[1]
                    if not isinstance(response_obj, Response):
                        response_obj = jsonify(response_obj)
                    response_obj.status_code = status
                else:
                    if not isinstance(response, Response):
                        response_obj = jsonify(response)
                        response_obj.status_code = 200
                    else:
                        response_obj = response
                
                # 보안 헤더 추가
                response_obj.headers['X-Content-Type-Options'] = 'nosniff'
                response_obj.headers['X-Frame-Options'] = 'SAMEORIGIN'
                response_obj.headers['X-XSS-Protection'] = '1; mode=block'
                response_obj.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
                response_obj.headers['Content-Security-Policy'] = "default-src 'self'"
                
                return response_obj
                
            return wrapped
        return decorator

    def validate_request(self):
        """요청 검증"""
        def decorator(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                try:
                    if request.is_json:
                        data = request.get_json(force=True, silent=True)
                        if data is None:
                            response = jsonify({
                                "status": "error",
                                "message": "Invalid JSON data"
                            })
                            response.status_code = 400
                            return response
                        
                        # XSS 검사
                        if self.check_xss(data):
                            response = jsonify({
                                "status": "error",
                                "message": "Potential XSS attack detected"
                            })
                            response.status_code = 400
                            return response

                    result = f(*args, **kwargs)
                    
                    # 응답이 이미 Response 객체인 경우
                    if isinstance(result, Response):
                        return result
                    
                    # 응답이 튜플인 경우 (data, status_code)
                    if isinstance(result, tuple):
                        data, status = result
                        response = jsonify(data)
                        response.status_code = status
                        return response
                    
                    # 그 외의 경우
                    response = jsonify(result)
                    response.status_code = 200
                    return response

                except Exception as e:
                    logging.error(f"Request validation error: {str(e)}")
                    response = jsonify({
                        "status": "error",
                        "message": str(e)
                    })
                    response.status_code = 500
                    return response
                
            return wrapped
        return decorator

# 싱글톤 인스턴스
security = SecurityMiddleware() 