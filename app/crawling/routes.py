from flask import jsonify, request, current_app
from .saramin import SaraminCrawler
import asyncio
import logging
import random
import os
import json
from datetime import datetime
from . import crawling_bp, scheduler
from app.database import get_db
from .models import Job

@crawling_bp.route('/manual', methods=['POST'])
def manual_crawling():
    """수동 크롤링 엔드포인트"""
    logger = logging.getLogger('crawler')
    
    try:
        logger.info("수동 크롤링 시작")
        crawler = SaraminCrawler()
        
        # 비동기 크롤러 실행
        delay = random.uniform(10, 15)
        saved_count = asyncio.run(crawler.crawl_jobs())
        
        logger.info(f"크롤링 완료: {saved_count}개의 채용공고 저장됨")
        return jsonify({
            "message": "크롤링이 성공적으로 완료되었습니다.",
            "saved_count": saved_count
        }), 200
        
    except Exception as e:
        logger.error(f"크롤링 실패: {str(e)}", exc_info=True)
        return jsonify({
            "message": f"크롤링 실패: {str(e)}",
            "error_details": str(e.__class__.__name__)
        }), 500

@crawling_bp.route('/status', methods=['GET'])
def get_crawling_status():
    """크롤링 상태 조회"""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        # 최근 크롤링 상태 조회
        cursor.execute("""
            SELECT status, created_at 
            FROM crawling_status 
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        status = cursor.fetchone()
        
        return jsonify({
            "status": status['status'] if status else "unknown",
            "last_update": status['created_at'].isoformat() if status else None
        })
    except Exception as e:
        current_app.logger.error(f"Failed to get crawling status: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    finally:
        cursor.close()

@crawling_bp.route('/logs', methods=['GET'])
def get_crawling_logs():
    """크롤링 로그 조회"""
    try:
        date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        level = request.args.get('level', 'INFO')
        
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        # 로그 조회 쿼리
        cursor.execute("""
            SELECT timestamp, level, message, details
            FROM crawling_logs
            WHERE DATE(timestamp) = %s
            AND level = %s
            ORDER BY timestamp DESC
        """, (date, level))
        
        logs = cursor.fetchall()
        
        return jsonify({
            "status": "success",
            "data": [{
                'timestamp': log['timestamp'].isoformat(),
                'level': log['level'],
                'message': log['message'],
                'details': json.loads(log['details']) if log['details'] else {}
            } for log in logs]
        })
    except Exception as e:
        current_app.logger.error(f"Failed to get crawling logs: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "크롤링 로그 조회 실패"
        }), 500
    finally:
        cursor.close()