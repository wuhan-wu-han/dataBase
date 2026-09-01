# -*- coding: utf-8 -*-
"""
database.py — SQLite 数据库访问层
================================
- 提供数据库连接、建表、种子数据初始化
- 所有表结构使用 CREATE TABLE IF NOT EXISTS，可重复执行
"""
import os
import sqlite3

# 数据库文件位于本模块同目录下
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gas_risk.db")


def get_conn() -> sqlite3.Connection:
    """获取一个 SQLite 连接（行以字典风格访问）。每次请求独立连接，天然线程安全。"""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def rows_to_list(rows):
    """将 sqlite3.Row 列表转为普通 dict 列表，便于 JSON 序列化。"""
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# 建表
# ---------------------------------------------------------------------------
_SCHEMA = """
-- 监测站（集成传感器：浓度/压力/流量/振动/腐蚀/位移）
CREATE TABLE IF NOT EXISTS sensors (
    id           INTEGER PRIMARY KEY,
    name         TEXT NOT NULL,
    position_km  REAL NOT NULL,          -- 桩号（沿管线公里数）
    type         TEXT DEFAULT 'integrated',
    status       TEXT DEFAULT 'normal'   -- normal / fault / offline
);

-- 毫秒级实时监测数据
CREATE TABLE IF NOT EXISTS monitoring_data (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_id         INTEGER NOT NULL,
    ts_ms             INTEGER NOT NULL,      -- 毫秒时间戳
    concentration_ppm REAL,                  -- 燃气浓度 ppm（甲烷 LEL=50000ppm=5%VOL）
    pressure_mpa      REAL,                  -- 管内压力 MPa
    flow_m3h          REAL,                  -- 流量 m3/h
    vibration_mms     REAL,                  -- 振动速度 mm/s
    corrosion_mma     REAL,                  -- 腐蚀速率 mm/a
    displacement_mm   REAL                   -- 位移（地质沉降/形变）mm
);
CREATE INDEX IF NOT EXISTS idx_md_sensor_ts ON monitoring_data(sensor_id, ts_ms);

-- 报警记录
CREATE TABLE IF NOT EXISTS alarms (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_ms     INTEGER NOT NULL,
    sensor_id INTEGER,
    level     INTEGER NOT NULL,   -- 1=预警 2=严重
    content   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_alarm_ts ON alarms(ts_ms);

-- 泄漏定位记录
CREATE TABLE IF NOT EXISTS leak_records (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_ms      INTEGER NOT NULL,
    method     TEXT NOT NULL,     -- concentration=浓度扩散模型 pressure_wave=压力波
    position_km REAL NOT NULL,
    confidence REAL,
    detail     TEXT               -- JSON 附加信息
);

-- 第三方施工事件
CREATE TABLE IF NOT EXISTS third_party_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_ms       INTEGER NOT NULL,
    event_type  TEXT NOT NULL,    -- 机械施工振动/违规开挖/重型车辆通行/钻探作业/爆破作业
    location_km REAL NOT NULL,
    lateral_m   REAL NOT NULL,    -- 与管道中心线的水平距离（米）
    intensity   REAL,             -- 扰动强度 1~10
    description TEXT,
    level       TEXT NOT NULL,    -- severe/warning/notice
    score       REAL
);

-- 燃气用户
CREATE TABLE IF NOT EXISTS gas_users (
    id            INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    user_type     TEXT NOT NULL,      -- 居民/工商
    address       TEXT,
    baseline_m3h  REAL                -- 典型用气流量基线
);

-- 用户用气数据（每次安全扫描产生一条快照）
CREATE TABLE IF NOT EXISTS meter_readings (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_ms      INTEGER NOT NULL,
    user_id    INTEGER NOT NULL,
    flow_m3h   REAL,              -- 当前流量
    pressure_kpa REAL,            -- 表前压力
    co_ppm     REAL,              -- 一氧化碳浓度
    flame      INTEGER,           -- 1=火焰正常 0=熄火/无火焰信号
    valve_open INTEGER            -- 1=阀门开启
);

-- 用户风险识别结果
CREATE TABLE IF NOT EXISTS user_risk_results (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_ms     INTEGER NOT NULL,
    user_id   INTEGER NOT NULL,
    level     TEXT NOT NULL,      -- normal/warning/severe
    reasons   TEXT                -- JSON 数组：风险原因
);

-- 占压隐患台账
CREATE TABLE IF NOT EXISTS occupation_records (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    type        TEXT NOT NULL,        -- 建筑占压/重物堆压/施工占压/其他占压
    location_km REAL NOT NULL,
    description TEXT,
    risk_level  TEXT NOT NULL,        -- 高/中/低
    status      TEXT NOT NULL DEFAULT '待下达',  -- 待下达/已下达/整改中/待验收/已闭环
    responsible TEXT,                 -- 责任人/责任单位
    deadline    TEXT,                 -- 整改期限
    created_ts  INTEGER NOT NULL
);

-- 占压隐患整改跟踪日志（闭环管理）
CREATE TABLE IF NOT EXISTS rectification_logs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id  INTEGER NOT NULL,
    ts_ms      INTEGER NOT NULL,
    action     TEXT NOT NULL,
    operator   TEXT,
    status_to  TEXT
);

-- 阴极保护测试桩
CREATE TABLE IF NOT EXISTS test_piles (
    id             INTEGER PRIMARY KEY,
    name           TEXT NOT NULL,
    position_km    REAL NOT NULL,
    rated_current_a REAL             -- 恒电位仪额定输出电流
);

-- 阴极保护监测数据
CREATE TABLE IF NOT EXISTS cathodic_data (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_ms            INTEGER NOT NULL,
    pile_id          INTEGER NOT NULL,
    on_potential_v   REAL,           -- 通电电位（相对 Cu/CuSO4 参比）
    off_potential_v  REAL,           -- 断电（瞬间去极化）电位，评价准则依据
    output_current_a REAL            -- 恒电位仪输出电流
);
CREATE INDEX IF NOT EXISTS idx_cd_pile_ts ON cathodic_data(pile_id, ts_ms);

-- 管线阀门（应急联动执行对象）
CREATE TABLE IF NOT EXISTS valves (
    id          TEXT PRIMARY KEY,
    position_km REAL NOT NULL,
    diameter_mm INTEGER,
    status      TEXT DEFAULT 'open'  -- open=开启 closed=关闭
);

-- 应急联动事件
CREATE TABLE IF NOT EXISTS emergency_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_ms       INTEGER NOT NULL,
    position_km REAL NOT NULL,       -- 泄漏/事故点桩号
    source      TEXT NOT NULL,       -- manual=人工触发 leak_alarm=泄漏报警联动
    level       TEXT NOT NULL,       -- warning/severe
    status      TEXT NOT NULL,       -- planned/executed/restored
    plan        TEXT,                -- JSON 关阀级联方案
    isolation   TEXT                 -- JSON 隔离段评估结果
);

-- 阀门操作指令记录
CREATE TABLE IF NOT EXISTS valve_commands (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_ms      INTEGER NOT NULL,
    event_id   INTEGER,
    valve_id   TEXT NOT NULL,
    seq        INTEGER NOT NULL,
    action     TEXT NOT NULL,        -- close/open
    delay_s    INTEGER,
    executed   INTEGER DEFAULT 0
);
"""


def init_db():
    """建表并写入演示种子数据（幂等：已有数据时跳过）。"""
    conn = get_conn()
    try:
        conn.executescript(_SCHEMA)
        _seed(conn)
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 种子数据：一条 0~50km 高压主干管线，配套监测站/阀门/测试桩/用户
# ---------------------------------------------------------------------------
def _seed(conn: sqlite3.Connection):
    if conn.execute("SELECT COUNT(*) c FROM sensors").fetchone()["c"] == 0:
        sensors = [
            (1, "1#监测站", 2.0), (2, "2#监测站", 8.0), (3, "3#监测站", 15.0),
            (4, "4#监测站", 22.0), (5, "5#监测站", 30.0), (6, "6#监测站", 38.0),
            (7, "7#监测站", 45.0),
        ]
        conn.executemany("INSERT INTO sensors(id,name,position_km) VALUES(?,?,?)", sensors)

    if conn.execute("SELECT COUNT(*) c FROM valves").fetchone()["c"] == 0:
        valves = [(f"V-{i:02d}", float(i * 5), 800) for i in range(11)]  # 每 5km 一台截断阀
        conn.executemany("INSERT INTO valves(id,position_km,diameter_mm) VALUES(?,?,?)", valves)

    if conn.execute("SELECT COUNT(*) c FROM test_piles").fetchone()["c"] == 0:
        piles = [(1, "TP-01", 5.0, 10.0), (2, "TP-02", 15.0, 10.0), (3, "TP-03", 25.0, 12.0),
                 (4, "TP-04", 35.0, 12.0), (5, "TP-05", 45.0, 10.0)]
        conn.executemany("INSERT INTO test_piles(id,name,position_km,rated_current_a) VALUES(?,?,?,?)", piles)

    if conn.execute("SELECT COUNT(*) c FROM gas_users").fetchone()["c"] == 0:
        users = [
            (1001, "幸福小区 3-201", "居民", "幸福小区3栋", 0.4),
            (1002, "幸福小区 5-602", "居民", "幸福小区5栋", 0.4),
            (1003, "和平里 12-301", "居民", "和平里12栋", 0.3),
            (1004, "和平里 8-102", "居民", "和平里8栋", 0.3),
            (1005, "滨江苑 2-1801", "居民", "滨江苑2栋", 0.4),
            (1006, "阳光花园 9-502", "居民", "阳光花园9栋", 0.35),
            (2001, "华联超市熟食区", "工商", "商业中心A座", 2.5),
            (2002, "川菜居饭店", "工商", "美食街12号", 3.0),
            (2003, "机关食堂", "工商", "行政中心3号楼", 2.0),
        ]
        conn.executemany("INSERT INTO gas_users(id,name,user_type,address,baseline_m3h) VALUES(?,?,?,?,?)", users)

    if conn.execute("SELECT COUNT(*) c FROM occupation_records").fetchone()["c"] == 0:
        import time
        now_ms = int(time.time() * 1000)
        records = [
            ("建筑占压", 12.5, "临建板房占压管道中心线上方，距管顶 0.8m", "高", "整改中",
             "城建三公司", "2026-09-15", now_ms - 86400000 * 20),
            ("重物堆压", 27.3, "渣土堆高约 3m，堆压管道上方约 40m 范围", "中", "已下达",
             "市政道路项目部", "2026-09-30", now_ms - 86400000 * 8),
            ("施工占压", 33.8, "旋挖钻机在管道保护范围内作业", "高", "待下达",
             "待确认", "", now_ms - 86400000 * 1),
            ("建筑占压", 41.2, "围墙基础距管道水平距离 2.1m", "低", "已闭环",
             "园区物业", "", now_ms - 86400000 * 60),
        ]
        for r in records:
            cur = conn.execute(
                "INSERT INTO occupation_records(type,location_km,description,risk_level,status,responsible,deadline,created_ts)"
                " VALUES(?,?,?,?,?,?,?,?)", r)
            conn.execute(
                "INSERT INTO rectification_logs(record_id,ts_ms,action,operator,status_to) VALUES(?,?,?,?,?)",
                (cur.lastrowid, r[7], "隐患登记，纳入台账", "巡检员", r[4]))
