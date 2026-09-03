#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""共享持久化层包：SQLite + SQLAlchemy

用法：
    from persistence import SessionLocal, init_db
    init_db()          # 幂等建表（首次启动时灌入种子由业务模块自行完成）
"""

from .database import (
    DB_PATH,
    Base,
    SessionLocal,
    engine,
    from_json,
    get_db,
    init_db,
    to_json,
)

__all__ = [
    "DB_PATH",
    "Base",
    "SessionLocal",
    "engine",
    "to_json",
    "from_json",
    "init_db",
    "get_db",
]
