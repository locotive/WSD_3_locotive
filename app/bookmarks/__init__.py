from flask import Blueprint

bookmarks_bp = Blueprint('bookmarks', __name__)

from app.bookmarks import routes 