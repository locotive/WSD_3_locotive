from flask import Blueprint, jsonify
from .saramin import SaraminCrawler
import logging

crawling_bp = Blueprint('crawling', __name__)

@crawling_bp.route('/manual', methods=['POST'])
def manual_crawling():
    try:
        crawler = SaraminCrawler()
        jobs = crawler.crawl_jobs()
        if jobs:
            saved_count = crawler.save_to_db(jobs)
            return jsonify({
                'message': f'크롤링 완료: {len(jobs)}개 수집, {saved_count}개 저장'
            }), 200
        else:
            return jsonify({
                'message': '크롤링 실패: 수집된 데이터 없음'
            }), 400
    except Exception as e:
        logging.error(f'수동 크롤링 실패: {str(e)}')
        return jsonify({
            'message': f'크롤링 실패: {str(e)}'
        }), 500