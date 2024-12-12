from mysql.connector import pooling
from flask import g
from app.config import Config

db_pool = pooling.MySQLConnectionPool(pool_name="mypool", pool_size=5, **Config.DB_CONFIG)

def get_db():
    if 'db' not in g:
        g.db = db_pool.get_connection()
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close() 