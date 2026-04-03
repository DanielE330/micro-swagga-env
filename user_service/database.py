import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

DATABASE_URL = os.getenv('DATABASE_URL')

# Auto-create database if not exists
_db_name = DATABASE_URL.rsplit('/', 1)[-1]
_base_url = DATABASE_URL.rsplit('/', 1)[0] + '/postgres'
_conn = psycopg2.connect(_base_url)
_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
_cur = _conn.cursor()
_cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (_db_name,))
if not _cur.fetchone():
    try:
        _cur.execute(f'CREATE DATABASE "{_db_name}"')
    except psycopg2.errors.DuplicateDatabase:
        pass
_cur.close()
_conn.close()

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()