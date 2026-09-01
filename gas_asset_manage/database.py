# -*- coding: utf-8 -*-
"""
database.py — SQLite 数据库访问层
================================
资产数字化台账子模块的表结构、连接管理与种子数据初始化。
表结构使用 CREATE TABLE IF NOT EXISTS，可重复执行。
"""
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gas_asset.db")


def get_conn() -> sqlite3.Connection:
    """获取 SQLite 连接（Row 字典风格访问；每请求独立连接，线程安全）。"""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def rows_to_list(rows):
    return [dict(r) for r in rows]


_SCHEMA = """
-- 资产主数据（全景台账）
CREATE TABLE IF NOT EXISTS assets (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_code     TEXT NOT NULL UNIQUE,   -- 资产编号
    segment_name   TEXT NOT NULL,          -- 管段名称
    diameter       TEXT NOT NULL,          -- 管径 DN
    material       TEXT NOT NULL,          -- 材质
    build_year     INTEGER NOT NULL,       -- 建设年代
    owner_unit     TEXT NOT NULL,          -- 权属（产权）单位
    region         TEXT NOT NULL,          -- 所属区域
    length_m       REAL NOT NULL,          -- 长度（米）
    pressure_level TEXT NOT NULL,          -- 压力等级
    status         TEXT NOT NULL,          -- 在役 / 停用 / 待报废
    location       TEXT,                   -- 安装位置描述
    longitude      REAL,                   -- 坐标
    latitude       REAL,
    created_ts     INTEGER NOT NULL
);

-- 全生命周期档案（采购→施工→运维→改造→报废）
CREATE TABLE IF NOT EXISTS lifecycle_records (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id    INTEGER NOT NULL REFERENCES assets(id),
    stage       TEXT NOT NULL,             -- 采购/施工/运维/改造/报废
    occurred_at TEXT NOT NULL,             -- 发生日期
    responsible TEXT,                      -- 责任单位/人
    description TEXT,                      -- 事件描述
    attachment  TEXT,                      -- 附件（合同/验收单/维修记录等）
    cost        REAL DEFAULT 0             -- 费用（元）
);
CREATE INDEX IF NOT EXISTS idx_lc_asset ON lifecycle_records(asset_id);

-- 盘点任务
CREATE TABLE IF NOT EXISTS inventory_tasks (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    task_code     TEXT NOT NULL UNIQUE,    -- 盘点单号
    method        TEXT NOT NULL,           -- 扫码盘点 / 巡检盘点
    scope         TEXT NOT NULL,           -- 盘点范围
    operator      TEXT NOT NULL,           -- 盘点人
    started_ts    INTEGER NOT NULL,
    finished_ts   INTEGER,
    status        TEXT NOT NULL DEFAULT '执行中',  -- 执行中/差异处理中/已完成
    matched_count INTEGER DEFAULT 0,       -- 账实一致数
    diff_count    INTEGER DEFAULT 0        -- 差异数
);

-- 盘点明细（账实核对结果与差异处理）
CREATE TABLE IF NOT EXISTS inventory_items (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id       INTEGER NOT NULL REFERENCES inventory_tasks(id),
    asset_id      INTEGER REFERENCES assets(id),  -- 盘盈项可为空
    asset_code    TEXT,                    -- 资产编号（盘盈时记录扫码所得）
    check_result  TEXT NOT NULL DEFAULT '待核对',  -- 待核对/一致/状态不符/盘亏/盘盈
    handle_status TEXT NOT NULL DEFAULT '待核对',  -- 待核对/无差异/待处理/补录/修正/报废
    remark        TEXT
);
CREATE INDEX IF NOT EXISTS idx_ii_task ON inventory_items(task_id);

-- 资产权属（三方责任：产权 / 运维 / 监管）
CREATE TABLE IF NOT EXISTS ownership (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id              INTEGER NOT NULL UNIQUE REFERENCES assets(id),
    property_unit         TEXT,            -- 产权单位
    property_nature       TEXT,            -- 产权性质：国有/集体/企业
    property_cert_no      TEXT,            -- 产权证书编号
    operation_unit        TEXT,            -- 运维单位
    operation_contract_no TEXT,            -- 运维合同编号
    supervision_unit      TEXT,            -- 监管单位
    responsibility_boundary TEXT,          -- 责任边界说明
    handover_at           TEXT             -- 交接时间
);
"""


def init_db():
    """建表并注入模拟数据（幂等）。"""
    conn = get_conn()
    try:
        conn.executescript(_SCHEMA)
        conn.commit()
    finally:
        conn.close()
