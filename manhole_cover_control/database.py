# -*- coding: utf-8 -*-
"""
市政井盖全生命周期管控子模块 —— 数据库层
==========================================
SQLite（WAL 模式）九张业务表：
  - manholes         一井一档电子台账（基础信息/权属/位置/状态）
  - monitor_data     多维实时监测数据（倾角/位移/破损/水位/有毒气体）
  - alarms           风险告警记录（异常数据自动产生）
  - work_orders      隐患闭环处置工单（派发/上报/核验/销号）
  - move_tracks      被盗异动轨迹点（回放与定位追踪）
  - police_records   公安联动处置记录
  - safety_nets      防坠网台账（安装登记/状态）
  - net_maintains    防坠网运维记录（破损登记/维修/更换）
  - repair_history   井盖维修更换历史（运维履历）
"""
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manhole_cover.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS manholes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    location TEXT NOT NULL,
    road_name TEXT NOT NULL,
    district TEXT NOT NULL,
    type TEXT NOT NULL,
    owner_unit TEXT NOT NULL,
    material TEXT,
    install_date TEXT,
    lat REAL,
    lng REAL,
    status TEXT DEFAULT '正常',
    remark TEXT,
    created_ts INTEGER
);

CREATE TABLE IF NOT EXISTS monitor_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    manhole_id INTEGER NOT NULL,
    ts INTEGER NOT NULL,
    tilt_deg REAL,
    displacement_mm REAL,
    damage TEXT DEFAULT '完好',
    water_level_cm REAL,
    gas_ppm REAL,
    is_abnormal INTEGER DEFAULT 0,
    created_ts INTEGER
);
CREATE INDEX IF NOT EXISTS idx_monitor_manhole ON monitor_data(manhole_id, ts);

CREATE TABLE IF NOT EXISTS alarms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alarm_code TEXT UNIQUE NOT NULL,
    manhole_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    level TEXT NOT NULL,
    detail TEXT,
    alarm_ts INTEGER NOT NULL,
    status TEXT DEFAULT '待派发',
    created_ts INTEGER
);

CREATE TABLE IF NOT EXISTS work_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_code TEXT UNIQUE NOT NULL,
    alarm_id INTEGER,
    manhole_id INTEGER NOT NULL,
    handle_type TEXT,
    assignee TEXT,
    dispatch_ts INTEGER,
    status TEXT DEFAULT '待派发',
    report_info TEXT,
    report_ts INTEGER,
    verify_result TEXT,
    verify_ts INTEGER,
    close_ts INTEGER,
    created_ts INTEGER
);

CREATE TABLE IF NOT EXISTS move_tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    manhole_id INTEGER NOT NULL,
    ts INTEGER NOT NULL,
    lat REAL NOT NULL,
    lng REAL NOT NULL,
    speed_kmh REAL,
    note TEXT,
    created_ts INTEGER
);
CREATE INDEX IF NOT EXISTS idx_track_manhole ON move_tracks(manhole_id, ts);

CREATE TABLE IF NOT EXISTS police_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_no TEXT UNIQUE NOT NULL,
    manhole_id INTEGER NOT NULL,
    alarm_id INTEGER,
    police_unit TEXT,
    contact TEXT,
    report_ts INTEGER,
    status TEXT DEFAULT '已报案',
    result TEXT,
    created_ts INTEGER
);

CREATE TABLE IF NOT EXISTS safety_nets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    net_code TEXT UNIQUE NOT NULL,
    manhole_id INTEGER NOT NULL,
    install_date TEXT,
    material TEXT,
    load_kg REAL,
    net_status TEXT DEFAULT '已安装',
    last_check TEXT,
    next_check TEXT,
    repair_count INTEGER DEFAULT 0,
    remark TEXT,
    created_ts INTEGER
);

CREATE TABLE IF NOT EXISTS net_maintains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    net_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    date TEXT,
    detail TEXT,
    operator TEXT,
    created_ts INTEGER
);

CREATE TABLE IF NOT EXISTS repair_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    manhole_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    date TEXT,
    reason TEXT,
    detail TEXT,
    cost REAL,
    operator TEXT,
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
