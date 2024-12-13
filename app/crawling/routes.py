from flask import Blueprint, jsonify
from .saramin import SaraminCrawler
import asyncio

crawling_bp = Blueprint('crawling', __name__)

@crawling_bp.route('/manual', methods=['POST'])
def manual_crawling():
    """수동 크롤링 엔드포인트"""
    try:
        crawler = SaraminCrawler()
        # 비동기 크롤러 실행
        asyncio.run(crawler.crawl_jobs())
        return jsonify({"message": "크롤링이 성공적으로 완료되었습니다."}), 200
    except Exception as e:
        return jsonify({"message": f"크롤링 실패: {str(e)}"}), 500

@crawling_bp.route('/status', methods=['GET'])
def crawling_status():
    """크롤링 상태 확인 엔드포인트"""
    return jsonify({"status": "running"}), 200