# -*- coding: utf-8 -*-
"""
simulator.py — 毫秒级实时数据模拟引擎
=====================================
生产环境中本模块由 SCADA / IoT 网关的真实数据上报替代；
演示环境中由一个后台守护线程为每个监测站持续生成毫秒级监测数据
（浓度、压力、流量、振动、腐蚀速率、位移），并做阈值报警评估。

支持故障注入，用于演示报警→定位→应急联动的完整闭环：
    set_leak(sensor_id, magnitude)  模拟管道微泄漏（浓度陡升+压力下降）
    set_third_party_disturbance(sensor_id, magnitude)  模拟第三方施工振动
    clear_faults()                  清除全部注入故障
"""
import math
import random
import threading
import time

import database as db

# ---------------------------------------------------------------------------
# 报警阈值配置
# ---------------------------------------------------------------------------
LEL_PPM = 50000.0          # 甲烷爆炸下限 = 5%VOL = 50000 ppm
THRESHOLDS = {
    "lel_pct_warning": 5.0,     # %LEL ≥5 预警
    "lel_pct_severe": 25.0,     # %LEL ≥25 严重（疑似泄漏）
    "pressure_low": 1.2,        # MPa 低压报警
    "pressure_high": 2.0,       # MPa 高压报警
    "flow_dev_pct": 15.0,       # 流量偏离基线百分比
    "vibration_warning": 4.0,   # mm/s
    "vibration_severe": 10.0,
    "corrosion_warning": 0.05,  # mm/a
    "corrosion_severe": 0.10,
    "displacement_warning": 10.0,   # mm
    "displacement_severe": 25.0,
}

# 各指标基准值与随机游走噪声幅度
BASELINES = {
    "concentration_ppm": 3.0,
    "pressure_mpa": 1.6,
    "flow_m3h": 1200.0,
    "vibration_mms": 0.4,
    "corrosion_mma": 0.018,
    "displacement_mm": 2.0,
}
NOISE = {
    "concentration_ppm": 1.0,
    "pressure_mpa": 0.015,
    "flow_m3h": 30.0,
    "vibration_mms": 0.12,
    "corrosion_mma": 0.003,
    "displacement_mm": 0.5,
}

# 故障注入状态（全局共享，线程安全由 GIL 保证简单读写）
INJECTIONS = {"leak": None, "tpd": None}

_stop = threading.Event()
_thread = None
_state = {}            # sensor_id -> 上一时刻各指标值（随机游走用）
_last_alarm = {}       # (sensor_id, level) -> 上次报警毫秒时间戳（节流）


# ---------------------------------------------------------------------------
# 故障注入接口（被 /api/monitoring/simulate-* 调用）
# ---------------------------------------------------------------------------
def set_leak(sensor_id: int, magnitude: float = 0.8):
    """注入泄漏：magnitude 0~1，决定浓度升高幅度与压降。"""
    INJECTIONS["leak"] = {"sensor_id": sensor_id, "magnitude": max(0.1, min(1.0, magnitude)),
                          "start_ts": int(time.time() * 1000)}


def set_third_party_disturbance(sensor_id: int, magnitude: float = 0.8):
    """注入第三方施工振动扰动。"""
    INJECTIONS["tpd"] = {"sensor_id": sensor_id, "magnitude": max(0.1, min(1.0, magnitude)),
                         "start_ts": int(time.time() * 1000)}


def clear_faults():
    INJECTIONS["leak"] = None
    INJECTIONS["tpd"] = None


def current_faults():
    return {k: v for k, v in INJECTIONS.items() if v}


# ---------------------------------------------------------------------------
# 数据生成与报警评估
# ---------------------------------------------------------------------------
def _next_value(prev: float, base: float, noise: float) -> float:
    """均值回归随机游走：围绕基准值小幅波动，模拟真实传感器噪声。"""
    v = prev + random.gauss(0, noise * 0.35) + (base - prev) * 0.06
    return max(v, 0.0)


def _apply_fault_effects(sensor: dict, row: dict):
    """把注入故障叠加到该监测站数据上（按与故障点距离高斯衰减）。"""
    leak = INJECTIONS["leak"]
    if leak:
        d = abs(sensor["position_km"] - _sensor_pos(leak["sensor_id"]))
        m = leak["magnitude"]
        # 浓度：故障点最高约 1500ppm*m，随距离 σ=1.5km 高斯衰减
        row["concentration_ppm"] += 1500.0 * m * math.exp(-d * d / (2 * 1.5 ** 2))
        # 压力：故障点压降约 0.25MPa*m
        row["pressure_mpa"] -= 0.25 * m * math.exp(-d * d / (2 * 2.0 ** 2))
        row["pressure_mpa"] = max(row["pressure_mpa"], 0.3)
    tpd = INJECTIONS["tpd"]
    if tpd:
        d = abs(sensor["position_km"] - _sensor_pos(tpd["sensor_id"]))
        row["vibration_mms"] += 12.0 * tpd["magnitude"] * math.exp(-d * d / (2 * 1.0 ** 2))


_sensor_pos_cache = {}


def _sensor_pos(sensor_id: int) -> float:
    if not _sensor_pos_cache:
        conn = db.get_conn()
        try:
            for r in conn.execute("SELECT id, position_km FROM sensors"):
                _sensor_pos_cache[r["id"]] = r["position_km"]
        finally:
            conn.close()
    return _sensor_pos_cache.get(sensor_id, 0.0)


def evaluate_alarm(sensor: dict, row: dict):
    """
    阈值报警评估。返回 (level, content)：level 0=正常 1=预警 2=严重。
    """
    t = THRESHOLDS
    msgs, level = [], 0

    lel = row["concentration_ppm"] / LEL_PPM * 100.0
    if lel >= t["lel_pct_severe"]:
        level = 2
        msgs.append(f"燃气浓度 {lel:.1f}%LEL，疑似泄漏")
    elif lel >= t["lel_pct_warning"]:
        level = max(level, 1)
        msgs.append(f"燃气浓度 {lel:.1f}%LEL 升高")

    if row["pressure_mpa"] < t["pressure_low"]:
        level = max(level, 2 if row["pressure_mpa"] < 1.0 else 1)
        msgs.append(f"压力 {row['pressure_mpa']:.2f}MPa 偏低（疑似泄漏压降）")
    elif row["pressure_mpa"] > t["pressure_high"]:
        level = max(level, 1)
        msgs.append(f"压力 {row['pressure_mpa']:.2f}MPa 偏高")

    dev = abs(row["flow_m3h"] - BASELINES["flow_m3h"]) / BASELINES["flow_m3h"] * 100
    if dev > t["flow_dev_pct"]:
        level = max(level, 1)
        msgs.append(f"流量偏离基线 {dev:.0f}%")

    if row["vibration_mms"] >= t["vibration_severe"]:
        level = max(level, 2)
        msgs.append(f"振动 {row['vibration_mms']:.1f}mm/s，疑似第三方施工破坏")
    elif row["vibration_mms"] >= t["vibration_warning"]:
        level = max(level, 1)
        msgs.append(f"振动 {row['vibration_mms']:.1f}mm/s 升高")

    if row["corrosion_mma"] >= t["corrosion_severe"]:
        level = max(level, 1)
        msgs.append(f"腐蚀速率 {row['corrosion_mma']:.3f}mm/a 超标")
    elif row["corrosion_mma"] >= t["corrosion_warning"]:
        level = max(level, 1)
        msgs.append(f"腐蚀速率 {row['corrosion_mma']:.3f}mm/a 偏高")

    if row["displacement_mm"] >= t["displacement_severe"]:
        level = max(level, 2)
        msgs.append(f"位移 {row['displacement_mm']:.1f}mm，地质灾害风险")
    elif row["displacement_mm"] >= t["displacement_warning"]:
        level = max(level, 1)
        msgs.append(f"位移 {row['displacement_mm']:.1f}mm 增大")

    return level, "；".join(msgs)


def _generate_step(conn, sensors, ts_ms: int):
    """为所有监测站生成一个时刻的数据并落库，返回触发的报警条数。"""
    n_alarm = 0
    for s in sensors:
        sid = s["id"]
        prev = _state.get(sid) or {k: v for k, v in BASELINES.items()}
        row = {}
        for k in BASELINES:
            base = BASELINES[k]
            # 第三方振动注入时，抑制均值回归，保持高振动状态
            row[k] = _next_value(prev[k], base, NOISE[k])
        _apply_fault_effects(dict(s), row)
        _state[sid] = row

        conn.execute(
            "INSERT INTO monitoring_data(sensor_id,ts_ms,concentration_ppm,pressure_mpa,"
            "flow_m3h,vibration_mms,corrosion_mma,displacement_mm) VALUES(?,?,?,?,?,?,?,?)",
            (sid, ts_ms, row["concentration_ppm"], row["pressure_mpa"], row["flow_m3h"],
             row["vibration_mms"], row["corrosion_mma"], row["displacement_mm"]))

        level, content = evaluate_alarm(s, row)
        if level > 0:
            key = (sid, level)
            last = _last_alarm.get(key, 0)
            # 同站同级报警 60 秒内只记录一次，避免刷屏
            if ts_ms - last > 60000 or level > _recent_max_level(sid, ts_ms):
                conn.execute("INSERT INTO alarms(ts_ms,sensor_id,level,content) VALUES(?,?,?,?)",
                             (ts_ms, sid, level, content))
                _last_alarm[key] = ts_ms
                n_alarm += 1
    return n_alarm


def _recent_max_level(sensor_id: int, ts_ms: int) -> int:
    return max((l for (sid, l), t in _last_alarm.items() if sid == sensor_id and ts_ms - t < 60000), default=0)


# ---------------------------------------------------------------------------
# 后台线程
# ---------------------------------------------------------------------------
def _loop():
    """每秒为全部监测站写入一帧毫秒级数据。"""
    while not _stop.is_set():
        try:
            conn = db.get_conn()
            try:
                sensors = db.rows_to_list(conn.execute("SELECT * FROM sensors").fetchall())
                _generate_step(conn, sensors, int(time.time() * 1000))
                conn.commit()
            finally:
                conn.close()
        except Exception as e:  # 守护线程不允许崩溃
            print(f"[simulator] 数据生成异常: {e}")
        _stop.wait(1.0)


def start():
    """启动模拟线程（幂等）。"""
    global _thread
    if _thread and _thread.is_alive():
        return
    _stop.clear()
    _thread = threading.Thread(target=_loop, name="data-simulator", daemon=True)
    _thread.start()


def stop():
    _stop.set()


def seed_history(hours: float = 2.0, step_s: int = 5):
    """
    启动时补录历史数据，使前端一打开就有完整曲线。
    """
    conn = db.get_conn()
    try:
        cnt = conn.execute("SELECT COUNT(*) c FROM monitoring_data").fetchone()["c"]
        if cnt > len(BASELINES) * 100:  # 已有足够数据
            return
        sensors = db.rows_to_list(conn.execute("SELECT * FROM sensors").fetchall())
        end = int(time.time() * 1000)
        start_ms = end - int(hours * 3600 * 1000)
        for ts in range(start_ms, end, step_s * 1000):
            _generate_step(conn, sensors, ts)
        conn.commit()
    finally:
        conn.close()
