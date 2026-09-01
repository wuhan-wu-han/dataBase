# -*- coding: utf-8 -*-
"""
道路地下隐患防控子模块 —— 数据库层
====================================
SQLite（WAL 模式）三张业务表：
  - cavities               地下空洞台账（雷达/渗漏数据与风险分级）
  - subsidence_records     道路沉降多期观测记录（按监测点留存历史）
  - construction_assess    施工影响评估档案（土体/管网安全评分）
"""
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "road_hazard.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS cavities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    road_name TEXT NOT NULL,
    district TEXT NOT NULL,
    location TEXT,
    radar_velocity REAL,
    radar_area REAL,
    leakage_index REAL,
    cavity_volume REAL,
    depth_m REAL,
    risk_score INTEGER,
    risk_level TEXT,
    status TEXT DEFAULT '监测中',
    found_at TEXT,
    remark TEXT,
    created_ts INTEGER
);

CREATE TABLE IF NOT EXISTS subsidence_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    point_code TEXT NOT NULL,
    road_name TEXT NOT NULL,
    district TEXT NOT NULL,
    measured_at TEXT NOT NULL,
    delta_mm REAL NOT NULL,
    cumulative_mm REAL NOT NULL,
    source TEXT DEFAULT '水准测量',
    created_ts INTEGER
);
CREATE INDEX IF NOT EXISTS idx_subs_point ON subsidence_records(point_code, measured_at);

CREATE TABLE IF NOT EXISTS construction_assess (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT NOT NULL,
    construction_unit TEXT NOT NULL,
    road_name TEXT NOT NULL,
    district TEXT NOT NULL,
    work_type TEXT NOT NULL,
    excavation_depth REAL,
    distance_to_pipe REAL,
    start_date TEXT,
    plan_days INTEGER,
    soil_score INTEGER,
    pipe_score INTEGER,
    overall_score INTEGER,
    risk_level TEXT,
    measures TEXT,
    assessor TEXT,
    assessed_at TEXT,
    created_ts INTEGER
);
"""


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def rows_to_list(rows) -> list:
    return [dict(r) for r in rows]


def init_db() -> None:
    conn = get_conn()
    try:
        conn.executescript(_SCHEMA)
        conn.commit()
    finally:
        conn.close()
