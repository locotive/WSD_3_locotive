from flask import jsonify, request, current_app
from .saramin import SaraminCrawler
import asyncio
import logging
import random
import os
import json
from datetime import datetime
from . import crawling_bp, scheduler
from app.database import db
from .models import Job

@crawling_bp.route('/manual', methods=['POST'])
def manual_crawling():
    """수동 크롤링 엔드포인트"""
    logger = logging.getLogger('crawler')
    
    try:
        logger.info("수동 크롤링 시작")
        crawler = SaraminCrawler()
        
        # 비동기 크롤러 실행
        delay = random.uniform(10, 15)  # 5-8초에서 10-15초로 증가
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
        return jsonify({
            "status": "running" if scheduler.running else "stopped"
        })
    except Exception as e:
        current_app.logger.error(f"Failed to get crawling status: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@crawling_bp.route('/logs', methods=['GET'])
def get_crawling_logs():
    """크롤링 로그 조회"""
    try:
        # 쿼리 파라미터
        date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        level = request.args.get('level', 'INFO')
        
        # 로그 파일 경로
        log_dir = os.path.join(current_app.root_path, 'logs')
        log_file = os.path.join(log_dir, f'crawling_{date}.log')
        
        # 로그 디렉토리가 없으면 생성
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        logs = []
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line)
                        # 레벨 필터링
                        if level and log_entry.get('level') == level:
                            logs.append({
                                'timestamp': log_entry.get('timestamp'),
                                'level': log_entry.get('level'),
                                'message': log_entry.get('message'),
                                'details': log_entry.get('details', {})
                            })
                    except json.JSONDecodeError:
                        continue
        
        return jsonify({
            "status": "success",
            "data": logs
        })
    except Exception as e:
        current_app.logger.error(f"Failed to get crawling logs: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "크롤링 로그 조회 실패"
        }), 500