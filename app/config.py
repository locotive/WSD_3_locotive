import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

class Config:
    # Database configuration
    DB_CONFIG = {
        "host": os.getenv('DB_HOST', '113.198.66.75'),
        "user": os.getenv('DB_USER', 'myuser'),
        "password": os.getenv('DB_PASSWORD', 'mypassword'),
        "database": os.getenv('DB_NAME', 'mydb'),
        "port": int(os.getenv('DB_PORT', 13102))
    }

    # JWT configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60
    REFRESH_TOKEN_EXPIRE_DAYS = 7

    # Swagger configuration
    SWAGGER_URL = '/api/docs'
    API_URL = '/static/swagger.json'