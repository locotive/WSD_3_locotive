from flask import jsonify, request
import logging
import traceback

def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(error):
        # 스택 트레이스 로깅
        logging.error("=== Bad Request Error Trace ===")
        logging.error(f"Error Type: {type(error)}")
        logging.error(f"Error Message: {str(error)}")
        logging.error(f"Stack Trace: {traceback.format_exc()}")
        
        # 요청 정보 로깅
        logging.error("=== Request Information ===")
        logging.error(f"Path: {request.path}")
        logging.error(f"Method: {request.method}")
        logging.error(f"Headers: {dict(request.headers)}")
        logging.error(f"Args: {dict(request.args)}")
        logging.error(f"Form Data: {dict(request.form)}")
        
        # JSON 데이터가 있는 경우
        if request.is_json:
            try:
                logging.error(f"JSON Data: {request.get_json(force=True)}")
            except Exception as e:
                logging.error(f"Failed to parse JSON: {str(e)}")

        return jsonify({
            "status": "error",
            "message": str(error),
            "path": request.path,
            "method": request.method
        }), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            "status": "error",
            "message": "Unauthorized access"
        }), 401

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "status": "error",
            "message": "Resource not found"
        }), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        logging.error(f"Internal Server Error: {str(error)}")
        logging.error(traceback.format_exc())
        return jsonify({
            "status": "error",
            "message": "Internal server error"
        }), 500 