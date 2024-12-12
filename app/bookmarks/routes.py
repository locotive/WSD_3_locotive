from flask import Blueprint, request, jsonify, g
from app.common.middleware import login_required
from app.bookmarks.models import Bookmark

bookmarks_bp = Blueprint('bookmarks', __name__)

@bookmarks_bp.route('/', methods=['POST'])
@login_required
def toggle_bookmark():
    data = request.get_json()
    if not data or 'posting_id' not in data:
        return jsonify({"message": "Posting ID is required"}), 400

    message, error = Bookmark.toggle_bookmark(g.current_user['user_id'], data['posting_id'])
    
    if error:
        return jsonify({"message": error}), 500

    return jsonify({"message": message})

@bookmarks_bp.route('/', methods=['GET'])
@login_required
def list_bookmarks():
    page = int(request.args.get('page', 1))
    sort = request.args.get('sort', 'desc')

    bookmarks = Bookmark.get_bookmarks(g.current_user['user_id'], page, sort)
    return jsonify(bookmarks) 