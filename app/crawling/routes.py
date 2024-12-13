from flask import Blueprint, jsonify
from .saramin import SaraminCrawler
import logging

crawling_bp = Blueprint('crawling', __name__)

@crawling_bp.route('/manual', methods=['POST'])
def manual_crawling():
    try:
        crawler = SaraminCrawler()
        jobs = crawler.crawl_jobs(min_jobs=100)
        saved_count = crawler.save_to_db(jobs)
        
        return jsonify({
            "message": "크롤링 완료",
            "total_jobs": len(jobs),
            "saved_jobs": saved_count
        })
    except Exception as e:
        logging.error(f"수동 크롤링 실패: {str(e)}")
        return jsonify({"message": f"크롤링 실패: {str(e)}"}), 500