# -*- coding: utf-8 -*-
"""
功能 5：用户端用气安全
======================
面向居民/工商用户的燃气表数据做安全扫描，识别：
  - 熄火风险：火焰信号丢失但阀门仍开启、流量持续（未燃烧燃气外泄）
  - 微泄漏：  非用气时段持续小流量（0.01~0.10 m³/h 涓流）
  - 过流异常：流量远超基线（软管脱落/灶具阀忘关）
  - CO 超标：燃烧工况异常或通风不良
  - 表前压力异常
"""
import json
import random
import time

from fastapi import APIRouter, HTTPException, Query

import database as db
from models import UserAnomalyInjectReq

router = APIRouter(prefix="/api/user-safety", tags=["5.用户端用气安全"])

# 注入的异常（下次扫描生效一次）：{user_id: anomaly_type}
USER_ANOMALIES = {}


# ---------------------------------------------------------------------------
# 表数据模拟与风险识别
# ---------------------------------------------------------------------------
def _gen_reading(user: dict, anomaly: str = None) -> dict:
    """为单个用户生成一帧表具数据（正常工况或注入异常）。"""
    base = user["baseline_m3h"]
    hour = time.localtime().tm_hour
    using = (6 <= hour <= 9 or 16 <= hour <= 21) and random.random() < 0.7

    r = {
        "flow_m3h": round(base * random.uniform(0.7, 1.15), 3) if using else 0.0,
        "pressure_kpa": round(2.0 + random.uniform(-0.15, 0.15), 2),
        "co_ppm": round(random.uniform(0, 20), 1),
        "flame": 1,
        "valve_open": 1,
    }
    if anomaly == "微泄漏":
        r["flow_m3h"] = round(random.uniform(0.02, 0.07), 3)   # 持续涓流
    elif anomaly == "熄火":
        r["flow_m3h"] = round(base * random.uniform(0.8, 1.2), 3)
        r["flame"] = 0                                          # 无火焰但持续过气
    elif anomaly == "CO超标":
        r["co_ppm"] = round(random.uniform(80, 300), 1)
        if not using:
            r["flow_m3h"] = round(base * random.uniform(0.7, 1.0), 3)
    elif anomaly == "软管脱落":
        r["flow_m3h"] = round(base * random.uniform(3.0, 6.0), 2)
    return r


def _evaluate(user: dict, r: dict) -> tuple:
    """风险识别规则引擎。返回 (level, reasons[])。"""
    reasons, level = [], "normal"
    base = max(user["baseline_m3h"], 0.1)

    # 熄火：阀门开启、流量持续但火焰信号丢失 → 未燃烧燃气外泄，严重
    if r["flame"] == 0 and r["valve_open"] == 1 and r["flow_m3h"] > 0.02:
        level = "severe"
        reasons.append("熄火：火焰信号丢失但持续过气，存在燃气外泄风险")

    # 微泄漏：非用气时段持续小流量涓流
    if 0.01 < r["flow_m3h"] <= 0.10 and r["flame"] == 1:
        level = "warning" if level == "normal" else level
        reasons.append("疑似户内微泄漏：持续小流量涓流，建议入户安检")

    # 过流：远超基线（工商用户绝对阈值更高）
    over_limit = base * 2.5 if user["user_type"] == "居民" else base * 2.0
    if r["flow_m3h"] > max(over_limit, base + 1.0):
        level = "severe"
        reasons.append(f"流量异常偏大（{r['flow_m3h']:.2f}m³/h，基线 {base:.2f}），疑似软管脱落或阀门未关")

    # CO：燃烧工况/通风
    if r["co_ppm"] >= 200:
        level = "severe"
        reasons.append(f"CO 浓度 {r['co_ppm']:.0f}ppm 严重超标，立即通风并停用")
    elif r["co_ppm"] >= 50:
        level = "warning" if level == "normal" else level
        reasons.append(f"CO 浓度 {r['co_ppm']:.0f}ppm 偏高，燃烧工况异常")

    # 表前压力
    if r["pressure_kpa"] < 1.0:
        level = "warning" if level == "normal" else level
        reasons.append(f"表前压力 {r['pressure_kpa']:.2f}kPa 偏低")

    if not reasons:
        reasons.append("各项指标正常")
    return level, reasons


@router.post("/scan", summary="全网用气安全扫描")
def scan():
    """
    对全部用户采集一帧表具数据并执行风险识别，
    结果写入历史（供曲线追溯）。演示环境中表具数据由本模块模拟生成。
    """
    ts = int(time.time() * 1000)
    conn = db.get_conn()
    try:
        users = db.rows_to_list(conn.execute("SELECT * FROM gas_users ORDER BY id"))
        results = []
        counts = {"normal": 0, "warning": 0, "severe": 0}
        for u in users:
            anomaly = USER_ANOMALIES.pop(u["id"], None)  # 注入的异常仅生效一次
            r = _gen_reading(u, anomaly)
            conn.execute(
                "INSERT INTO meter_readings(ts_ms,user_id,flow_m3h,pressure_kpa,co_ppm,flame,valve_open)"
                " VALUES(?,?,?,?,?,?,?)",
                (ts, u["id"], r["flow_m3h"], r["pressure_kpa"], r["co_ppm"], r["flame"], r["valve_open"]))
            level, reasons = _evaluate(u, r)
            conn.execute("INSERT INTO user_risk_results(ts_ms,user_id,level,reasons) VALUES(?,?,?,?)",
                         (ts, u["id"], level, json.dumps(reasons, ensure_ascii=False)))
            counts[level] += 1
            results.append({**u, **r, "level": level, "reasons": reasons,
                            "anomaly_injected": anomaly})
        conn.commit()
        return {"ts_ms": ts, "summary": counts, "results": results}
    finally:
        conn.close()


@router.get("/users", summary="用户清单及最近一次风险评估")
def users():
    """返回全部用户，附最近一次扫描的风险级别与原因。"""
    conn = db.get_conn()
    try:
        users = db.rows_to_list(conn.execute("SELECT * FROM gas_users ORDER BY id"))
        for u in users:
            last = conn.execute(
                "SELECT * FROM user_risk_results WHERE user_id=? ORDER BY id DESC LIMIT 1",
                (u["id"],)).fetchone()
            u["last_level"] = last["level"] if last else "unknown"
            u["last_reasons"] = json.loads(last["reasons"]) if last else ["尚未扫描"]
            u["last_ts_ms"] = last["ts_ms"] if last else None
        return {"users": users}
    finally:
        conn.close()


@router.get("/history", summary="单用户表具数据历史")
def history(user_id: int = Query(...), limit: int = Query(50, ge=1, le=500)):
    """该用户最近 N 次扫描的流量/压力/CO 曲线数据。"""
    conn = db.get_conn()
    try:
        if not conn.execute("SELECT 1 FROM gas_users WHERE id=?", (user_id,)).fetchone():
            raise HTTPException(404, f"用户 {user_id} 不存在")
        rows = db.rows_to_list(conn.execute(
            "SELECT ts_ms,flow_m3h,pressure_kpa,co_ppm,flame FROM meter_readings "
            "WHERE user_id=? ORDER BY id DESC LIMIT ?", (user_id, limit)))
        return {"user_id": user_id, "points": list(reversed(rows))}
    finally:
        conn.close()


@router.post("/simulate-anomaly", summary="注入用户端异常（演示）")
def simulate_anomaly(req: UserAnomalyInjectReq):
    """
    为指定用户注入异常工况（微泄漏/熄火/CO超标/软管脱落），
    下一次 /scan 时生效并应被识别。
    """
    if req.anomaly not in ("微泄漏", "熄火", "CO超标", "软管脱落"):
        raise HTTPException(400, "异常类型应为：微泄漏/熄火/CO超标/软管脱落")
    conn = db.get_conn()
    try:
        if not conn.execute("SELECT 1 FROM gas_users WHERE id=?", (req.user_id,)).fetchone():
            raise HTTPException(404, f"用户 {req.user_id} 不存在")
    finally:
        conn.close()
    USER_ANOMALIES[req.user_id] = req.anomaly
    return {"ok": True, "msg": f"已为用户 {req.user_id} 注入「{req.anomaly}」，请点击“立即扫描”查看识别结果"}
