# -*- coding: utf-8 -*-
"""供水管网精细化管控子模块 — SQLite 数据库连接与建表"""
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "water_supply.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS pipe (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    material TEXT,
    diameter_mm INTEGER,
    length_m REAL,
    district TEXT,
    road_name TEXT,
    terrain_elev_m REAL,
    lay_date TEXT,
    status TEXT DEFAULT '正常',
    remark TEXT
);

CREATE TABLE IF NOT EXISTS monitor_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pipe_id INTEGER NOT NULL,
    ts INTEGER NOT NULL,
    pressure_mpa REAL,
    flow_m3h REAL,
    level_cm REAL,
    turbidity_ntu REAL,
    residual_cl REAL,
    deformation_mm REAL,
    is_abnormal INTEGER DEFAULT 0,
    FOREIGN KEY (pipe_id) REFERENCES pipe(id)
);

CREATE TABLE IF NOT EXISTS alarm (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alarm_code TEXT NOT NULL UNIQUE,
    pipe_id INTEGER,
    source TEXT DEFAULT '管网',
    type TEXT NOT NULL,
    level TEXT NOT NULL,
    detail TEXT,
    alarm_ts INTEGER NOT NULL,
    status TEXT DEFAULT '待处理'
);

CREATE TABLE IF NOT EXISTS dma_zone (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    district TEXT,
    pipe_count INTEGER DEFAULT 0,
    user_count INTEGER DEFAULT 0,
    avg_flow_m3h REAL,
    night_min_flow_m3h REAL,
    leakage_rate_pct REAL,
    dark_leak_location TEXT,
    status TEXT DEFAULT '正常'
);

CREATE TABLE IF NOT EXISTS dma_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dma_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    inflow_m3 REAL,
    billed_m3 REAL,
    night_min_flow_m3h REAL,
    leakage_rate_pct REAL,
    FOREIGN KEY (dma_id) REFERENCES dma_zone(id)
);

CREATE TABLE IF NOT EXISTS quality_node (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    seq INTEGER NOT NULL,
    pipe_id INTEGER,
    turbidity_ntu REAL,
    residual_cl REAL,
    ph REAL,
    status TEXT DEFAULT '正常'
);

CREATE TABLE IF NOT EXISTS quality_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id INTEGER NOT NULL,
    ts INTEGER NOT NULL,
    turbidity_ntu REAL,
    residual_cl REAL,
    ph REAL,
    is_abnormal INTEGER DEFAULT 0,
    FOREIGN KEY (node_id) REFERENCES quality_node(id)
);

CREATE TABLE IF NOT EXISTS pump_station (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    district TEXT,
    supply_elev_m REAL,
    pump_count INTEGER DEFAULT 2,
    current_pressure_mpa REAL,
    rated_flow_m3h REAL,
    status TEXT DEFAULT '运行'
);

CREATE TABLE IF NOT EXISTS pressure_plan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    station_id INTEGER NOT NULL,
    period TEXT NOT NULL,
    terrain_delta_m REAL,
    current_pressure_mpa REAL,
    target_pressure_mpa REAL,
    energy_save_pct REAL,
    burst_risk_reduce TEXT,
    status TEXT DEFAULT '已生成',
    created_ts INTEGER NOT NULL,
    FOREIGN KEY (station_id) REFERENCES pump_station(id)
);

CREATE TABLE IF NOT EXISTS secondary_unit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    community TEXT NOT NULL,
    district TEXT,
    tank_count INTEGER DEFAULT 1,
    level_pct REAL,
    turbidity_ntu REAL,
    residual_cl REAL,
    disinfect_status TEXT DEFAULT '正常',
    status TEXT DEFAULT '正常',
    last_check TEXT
);

CREATE TABLE IF NOT EXISTS hydrant (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    location TEXT NOT NULL,
    road_name TEXT,
    district TEXT,
    pipe_id INTEGER,
    pressure_mpa REAL,
    test_flow_ls REAL,
    last_test_ts INTEGER,
    install_date TEXT,
    status TEXT DEFAULT '正常',
    remark TEXT
);

CREATE TABLE IF NOT EXISTS hydrant_event (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hydrant_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    ts INTEGER NOT NULL,
    detail TEXT,
    status TEXT DEFAULT '已处理',
    FOREIGN KEY (hydrant_id) REFERENCES hydrant(id)
);

CREATE TABLE IF NOT EXISTS burst_case (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pipe_id INTEGER NOT NULL,
    risk_score REAL,
    risk_level TEXT,
    predict_detail TEXT,
    affected_users INTEGER DEFAULT 0,
    affected_area TEXT,
    status TEXT DEFAULT '风险预警',
    created_ts INTEGER NOT NULL,
    FOREIGN KEY (pipe_id) REFERENCES pipe(id)
);

CREATE TABLE IF NOT EXISTS burst_valve (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL,
    valve_code TEXT NOT NULL,
    position TEXT,
    order_no INTEGER DEFAULT 0,
    is_selected INTEGER DEFAULT 1,
    FOREIGN KEY (case_id) REFERENCES burst_case(id)
);
"""


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = get_conn()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
