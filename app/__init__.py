from flask import Flask
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
from app.auth.routes import auth_bp
from app.jobs.routes import jobs_bp
from app.users.routes import user_bp
from app.applications.routes import applications_bp
from app.bookmarks.routes import bookmarks_bp
from app.common.error_handlers import register_error_handlers
from app.database import close_db
from app.config import Config
from app.companies.routes import companies_bp
from app.common.logging import setup_logger
from app.scheduler import init_scheduler

def create_app():
    app = Flask(__name__)
    CORS(app)

    # 로깅 설정
    setup_logger()
    
    # 스케줄러 시작
    init_scheduler()

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(jobs_bp, url_prefix='/jobs')
    app.register_blueprint(user_bp, url_prefix='/users')
    app.register_blueprint(applications_bp, url_prefix='/applications')
    app.register_blueprint(bookmarks_bp, url_prefix='/bookmarks')
    app.register_blueprint(companies_bp, url_prefix='/companies')

    # Register Swagger UI blueprint
    swaggerui_blueprint = get_swaggerui_blueprint(
        Config.SWAGGER_URL,
        Config.API_URL,
        config={
            'app_name': "Job API"
        }
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=Config.SWAGGER_URL)

    # Register error handlers
    register_error_handlers(app)

    # Teardown app context
    app.teardown_appcontext(close_db)

    return app 