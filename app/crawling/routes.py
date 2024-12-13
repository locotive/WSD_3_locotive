from flask import Blueprint, jsonify
from .saramin import SaraminCrawler
import asyncio
import logging
import random

crawling_bp = Blueprint('crawling', __name__)

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
def crawling_status():
    """크롤링 상태 확인 엔드포인트"""
    return jsonify({"status": "running"}), 200