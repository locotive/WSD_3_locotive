from functools import wraps
from flask import request, jsonify
import re
import bleach

def validate_request():
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            try:
                # force=False, silent=True 옵션 추가
                data = request.get_json(force=False, silent=True)
                if data is None:
                    return jsonify({
                        "status": "error",
                        "message": "Invalid JSON data"
                    }), 400
                return f(*args, **kwargs)
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 400
        return wrapped
    return decorator

def sanitize_input():
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            try:
                # GET 파라미터 살균
                for key, value in request.args.items():
                    if isinstance(value, str):
                        request.args[key] = bleach.clean(value)

                # POST/PUT JSON 데이터 살균
                if request.is_json:
                    data = request.get_json(force=False, silent=True)
                    if data and isinstance(data, dict):
                        sanitized_data = {}
                        for key, value in data.items():
                            if isinstance(value, str):
                                sanitized_data[key] = bleach.clean(value)
                            else:
                                sanitized_data[key] = value
                        request.data = sanitized_data

                return f(*args, **kwargs)
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "message": f"Input sanitization failed: {str(e)}"
                }), 400
        return wrapped
    return decorator

def security_headers():
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            response = f(*args, **kwargs)
            # 보안 헤더 추가
            if hasattr(response, 'headers'):
                response.headers['Content-Security-Policy'] = "default-src 'self'"
                response.headers['X-Content-Type-Options'] = 'nosniff'
                response.headers['X-Frame-Options'] = 'DENY'
                response.headers['X-XSS-Protection'] = '1; mode=block'
            return response
        return wrapped
    return decorator

# security 객체 생성
class Security:
    def __init__(self):
        self.validate_request = validate_request
        self.sanitize_input = sanitize_input
        self.security_headers = security_headers

security = Security() 