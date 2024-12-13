from mysql.connector import pooling
from flask import g
from app.config import Config

# MySQL 연결 풀 생성
db_pool = pooling.MySQLConnectionPool(pool_name="mypool", pool_size=5, **Config.DB_CONFIG)

def get_db():
    if 'db' not in g:
        g.db = db_pool.get_connection()
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_app(app):
    app.teardown_appcontext(close_db)