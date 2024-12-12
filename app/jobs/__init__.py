from flask import Blueprint

jobs_bp = Blueprint('jobs', __name__)

from app.jobs import routes 