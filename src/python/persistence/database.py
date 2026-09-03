#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""共享持久化层 —— SQLite + SQLAlchemy

供 workorder / plan_api 等子模块复用。数据库文件默认落在 src/python/data/platform.db，
可用环境变量 PLATFORM_DB_PATH 覆盖（便于测试时指向临时库）。
"""

import json
import os
import sqlite3

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))      # .../src/python/persistence
_PYTHON_DIR = os.path.dirname(_MODULE_DIR)                      # .../src/python

DB_PATH = os.environ.get("PLATFORM_DB_PATH",
                         os.path.join(_PYTHON_DIR, "data", "platform.db"))
_parent = os.path.dirname(DB_PATH)
if _parent:
    os.makedirs(_parent, exist_ok=True)

# check_same_thread=False：FastAPI 线程池复用同一连接
engine = create_engine("sqlite:///" + DB_PATH.replace("\\", "/"),
                       connect_args={"check_same_thread": False},
                       pool_pre_ping=True)


@event.listens_for(engine, "connect")
def _configure_sqlite(dbapi_conn, _record):
    """WAL + busy_timeout：后台刷新线程与请求线程并发写时不抛 database is locked"""
    if isinstance(dbapi_conn, sqlite3.Connection):
        dbapi_conn.execute("PRAGMA journal_mode=WAL")
        dbapi_conn.execute("PRAGMA busy_timeout=5000")
        dbapi_conn.execute("PRAGMA foreign_keys=ON")


SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()


def to_json(value) -> str:
    """嵌套结构（数组 / 对象）落 JSON 文本列"""
    return json.dumps(value if value is not None else [], ensure_ascii=False)


def from_json(raw, default=None):
    """JSON 文本列还原；脏数据回退为默认值而不是让整页 500"""
    if raw is None or raw == "":
        return default if default is not None else []
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return default if default is not None else []


def init_db():
    """建表（幂等）。需先让模型模块完成注册。"""
    try:
        from . import workorder_tables, plan_tables          # 作为包导入
    except ImportError:
        import workorder_tables, plan_tables                 # 作为顶层模块导入
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI 依赖注入用"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    print("SQLite 已就绪：%s" % DB_PATH)
