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
                try:
                    response = f(*args, **kwargs)
                    if isinstance(response, tuple):
                        response = make_response(response[0]), response[1]
                    if not isinstance(response, Response):
                        response = make_response(response)
                    
                    response.headers['X-Content-Type-Options'] = 'nosniff'
                    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
                    response.headers['X-XSS-Protection'] = '1; mode=block'
                    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
                    response.headers['Content-Security-Policy'] = "default-src 'self'"
                    
                    return response
                except Exception as e:
                    logging.error(f"Security headers error: {str(e)}")
                    return jsonify({"status": "error", "message": str(e)}), 500
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
                            return make_response(jsonify({
                                "status": "error",
                                "message": "Invalid JSON data"
                            }), 400)
                        
                        # XSS 검사
                        if self.check_xss(data):
                            return make_response(jsonify({
                                "status": "error",
                                "message": "Potential XSS attack detected"
                            }), 400)
                        
                        # SQL Injection 검사
                        if self.check_sql_injection(data):
                            return make_response(jsonify({
                                "status": "error",
                                "message": "Potential SQL injection detected"
                            }), 400)
                        
                        # 입력 살균
                        sanitized_data = self.sanitize_input(data)
                        setattr(request, '_json', sanitized_data)

                    # URL 파라미터 검증
                    for key, value in request.args.items():
                        if self.check_xss(value) or self.check_sql_injection(value):
                            return make_response(jsonify({
                                "status": "error",
                                "message": "Invalid query parameter"
                            }), 400)

                    result = f(*args, **kwargs)
                    
                    # 결과가 튜플인 경우 (data, status_code)
                    if isinstance(result, tuple):
                        if len(result) == 2:
                            return make_response(jsonify(result[0]), result[1])
                        return result
                    
                    # 결과가 Response 객체인 경우
                    if isinstance(result, Response):
                        return result
                    
                    # 그 외의 경우
                    return make_response(jsonify(result), 200)

                except Exception as e:
                    logging.error(f"Request validation error: {str(e)}")
                    return make_response(jsonify({
                        "status": "error",
                        "message": str(e)
                    }), 500)
            return wrapped
        return decorator

# 싱글톤 인스턴스
security = SecurityMiddleware() 