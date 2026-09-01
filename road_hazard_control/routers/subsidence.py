# -*- coding: utf-8 -*-
"""
功能 2：道路沉降监测
=====================
多期沉降观测数据融合计算：按监测点留存历史记录，计算累计沉降量、
近期沉降速率与加速趋势，融合判定塌陷风险等级，并留存完整历史。
"""
import time
from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

import database as db
from models import SubsidenceRecordReq, fusion_risk

router = APIRouter(prefix="/api/subsidence", tags=["2.道路沉降监测"])


def _parse_date(s: str) -> date:
    try:
        return date.fromisoformat(s)
    except ValueError:
        raise HTTPException(400, f"日期格式应为 yyyy-MM-dd：{s}")


def compute_point_summaries(conn) -> list:
    """
    按监测点融合计算：累计沉降量、近三期速率（mm/月，按实际间隔折算）、
    是否加速（最新一期增量大于上一期）、塌陷风险等级与趋势描述。
    """
    points = conn.execute(
        "SELECT point_code, road_name, district, COUNT(*) n, MIN(measured_at) first_at,"
        " MAX(measured_at) last_at FROM subsidence_records GROUP BY point_code")
    out = []
    for p in points:
        recs = db.rows_to_list(conn.execute(
            "SELECT * FROM subsidence_records WHERE point_code=? ORDER BY measured_at",
            (p["point_code"],)))
        recent = recs[-3:]
        rate = 0.0
        if len(recent) >= 2:
            days = (_parse_date(recent[-1]["measured_at"]) -
                    _parse_date(recent[0]["measured_at"])).days
            delta_sum = sum(r["delta_mm"] for r in recent[1:])
            rate = round(delta_sum / max(days, 1) * 30, 1)
        accelerating = len(recs) >= 2 and recs[-1]["delta_mm"] > recs[-2]["delta_mm"]
        cumulative = recs[-1]["cumulative_mm"]
        level, trend = fusion_risk(cumulative, rate, accelerating)
        out.append({
            "point_code": p["point_code"], "road_name": p["road_name"],
            "district": p["district"], "record_count": p["n"],
            "first_measured": p["first_at"], "latest_measured": p["last_at"],
            "cumulative_mm": cumulative, "rate_mm_month": rate,
            "accelerating": accelerating, "risk_level": level, "trend": trend,
        })
    return out


@router.get("/points", summary="监测点融合风险总览")
def list_points(district: Optional[str] = None,
                risk_level: Optional[str] = None,
                keyword: Optional[str] = Query(None, description="点位/道路模糊匹配")):
    conn = db.get_conn()
    try:
        rows = compute_point_summaries(conn)
    finally:
        conn.close()
    if district:
        rows = [r for r in rows if r["district"] == district]
    if risk_level:
        rows = [r for r in rows if r["risk_level"] == risk_level]
    if keyword:
        rows = [r for r in rows if keyword in r["point_code"] or keyword in r["road_name"]]
    rows.sort(key=lambda r: r["cumulative_mm"], reverse=True)
    return {"total": len(rows), "items": rows}


@router.get("/history", summary="监测点历史观测记录")
def history(point_code: str = Query(..., description="监测点编号")):
    conn = db.get_conn()
    try:
        recs = db.rows_to_list(conn.execute(
            "SELECT * FROM subsidence_records WHERE point_code=? ORDER BY measured_at",
            (point_code,)))
    finally:
        conn.close()
    if not recs:
        raise HTTPException(404, f"监测点 {point_code} 无观测记录")
    return {"point_code": point_code, "records": recs}


@router.post("/records", summary="新增观测记录（自动累计与融合判定）")
def add_record(req: SubsidenceRecordReq):
    """
    录入本期沉降增量：自动累加到累计值；点位不存在时须携带道路与区域信息；
    观测日期必须晚于该点位最近一次观测。
    """
    measured = _parse_date(req.measured_at)
    conn = db.get_conn()
    try:
        last = conn.execute(
            "SELECT * FROM subsidence_records WHERE point_code=? ORDER BY measured_at DESC LIMIT 1",
            (req.point_code,)).fetchone()
        if last:
            if req.road_name and req.road_name != last["road_name"]:
                raise HTTPException(400, f"点位 {req.point_code} 属于 {last['road_name']}，道路不一致")
            if req.district and req.district != last["district"]:
                raise HTTPException(400, f"点位 {req.point_code} 属于 {last['district']}，区域不一致")
            if measured <= _parse_date(last["measured_at"]):
                raise HTTPException(400, f"观测日期须晚于最近一次观测 {last['measured_at']}")
            cumulative = round(last["cumulative_mm"] + req.delta_mm, 1)
            road, dist = last["road_name"], last["district"]
        else:
            if not req.road_name or not req.district:
                raise HTTPException(400, "新监测点首次录入须填写道路与区域")
            cumulative = round(req.delta_mm, 1)
            road, dist = req.road_name, req.district
        conn.execute(
            "INSERT INTO subsidence_records(point_code,road_name,district,measured_at,"
            "delta_mm,cumulative_mm,source,created_ts) VALUES(?,?,?,?,?,?,?,?)",
            (req.point_code, road, dist, req.measured_at, req.delta_mm,
             cumulative, req.source, int(time.time() * 1000)))
        conn.commit()
        return {"ok": True, "point_code": req.point_code,
                "cumulative_mm": cumulative}
    finally:
        conn.close()


@router.get("/options", summary="下拉选项（区域）")
def options():
    conn = db.get_conn()
    try:
        districts = [r["district"] for r in conn.execute(
            "SELECT DISTINCT district FROM subsidence_records ORDER BY district")]
        return {"districts": districts}
    finally:
        conn.close()


@router.get("/stats", summary="沉降监测统计")
def stats():
    """点位风险分布、区域分布与全网月度平均沉降趋势。"""
    conn = db.get_conn()
    try:
        points = compute_point_summaries(conn)
        by_risk, by_district = {}, {}
        for p in points:
            by_risk[p["risk_level"]] = by_risk.get(p["risk_level"], 0) + 1
            by_district[p["district"]] = by_district.get(p["district"], 0) + 1
        monthly = db.rows_to_list(conn.execute(
            "SELECT substr(measured_at,1,7) month, ROUND(AVG(delta_mm),2) avg_delta,"
            " ROUND(MAX(cumulative_mm),1) max_cum FROM subsidence_records"
            " GROUP BY month ORDER BY month"))
        return {
            "by_risk": [{"name": k, "value": v} for k, v in by_risk.items()],
            "by_district": [{"name": k, "value": v} for k, v in by_district.items()],
            "monthly": monthly,
        }
    finally:
        conn.close()
