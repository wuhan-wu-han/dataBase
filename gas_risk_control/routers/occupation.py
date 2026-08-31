# -*- coding: utf-8 -*-
"""
功能 6：占压隐患管理
====================
建筑占压、重物堆压等隐患的台账管理（增删改查）与整改跟踪闭环：
    待下达 → 已下达 → 整改中 → 待验收 → 已闭环
每次整改动作写入跟踪日志，形成完整时间线，实现隐患闭环管理。
"""
import time

from fastapi import APIRouter, HTTPException, Query

import database as db
from models import OccupationCreateReq, OccupationUpdateReq, RectifyReq

router = APIRouter(prefix="/api/occupation", tags=["6.占压隐患管理"])

STATUSES = ["待下达", "已下达", "整改中", "待验收", "已闭环"]
TYPES = ["建筑占压", "重物堆压", "施工占压", "其他占压"]


@router.get("/records", summary="隐患台账查询")
def list_records(status: str = Query(None, description="按状态过滤"),
                 type: str = Query(None, alias="type", description="按类型过滤"),
                 risk_level: str = Query(None, description="按风险等级过滤")):
    """支持按状态/类型/风险等级过滤的台账列表。"""
    sql, args = "SELECT * FROM occupation_records WHERE 1=1", []
    if status:
        sql += " AND status=?"; args.append(status)
    if type:
        sql += " AND type=?"; args.append(type)
    if risk_level:
        sql += " AND risk_level=?"; args.append(risk_level)
    conn = db.get_conn()
    try:
        rows = db.rows_to_list(conn.execute(sql + " ORDER BY created_ts DESC", args))
        return {"records": rows, "statuses": STATUSES, "types": TYPES}
    finally:
        conn.close()


@router.post("/records", summary="新增隐患登记")
def create_record(req: OccupationCreateReq):
    """登记新发现的占压/堆压隐患，自动写入首条跟踪日志。"""
    if req.type not in TYPES:
        raise HTTPException(400, f"隐患类型应为：{'/'.join(TYPES)}")
    if req.risk_level not in ("高", "中", "低"):
        raise HTTPException(400, "风险等级应为：高/中/低")
    ts = int(time.time() * 1000)
    conn = db.get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO occupation_records(type,location_km,description,risk_level,status,"
            "responsible,deadline,created_ts) VALUES(?,?,?,?,?,?,?,?)",
            (req.type, req.location_km, req.description, req.risk_level, "待下达",
             req.responsible, req.deadline, ts))
        rid = cur.lastrowid
        conn.execute(
            "INSERT INTO rectification_logs(record_id,ts_ms,action,operator,status_to) VALUES(?,?,?,?,?)",
            (rid, ts, "隐患登记，纳入台账", "管理员", "待下达"))
        conn.commit()
        return {"id": rid, "ok": True}
    finally:
        conn.close()


@router.put("/records/{record_id}", summary="更新隐患信息")
def update_record(record_id: int, req: OccupationUpdateReq):
    """修改隐患描述/风险等级/责任人/期限（部分字段更新）。"""
    conn = db.get_conn()
    try:
        rec = conn.execute("SELECT * FROM occupation_records WHERE id=?", (record_id,)).fetchone()
        if not rec:
            raise HTTPException(404, f"隐患记录 {record_id} 不存在")
        fields = {k: v for k, v in req.model_dump().items() if v is not None}
        if fields.get("risk_level") and fields["risk_level"] not in ("高", "中", "低"):
            raise HTTPException(400, "风险等级应为：高/中/低")
        if fields:
            sets = ",".join(f"{k}=?" for k in fields)
            conn.execute(f"UPDATE occupation_records SET {sets} WHERE id=?",
                         (*fields.values(), record_id))
            conn.commit()
        return {"ok": True}
    finally:
        conn.close()


@router.post("/records/{record_id}/rectify", summary="记录整改动作（推进闭环）")
def rectify(record_id: int, req: RectifyReq):
    """
    记录一次整改动作并流转状态（如：下达整改通知书→已下达；
    现场清除堆土→整改中；验收合格→已闭环）。动作与状态变更进入时间线。
    """
    if req.status_to not in STATUSES:
        raise HTTPException(400, f"状态应为：{'/'.join(STATUSES)}")
    ts = int(time.time() * 1000)
    conn = db.get_conn()
    try:
        rec = conn.execute("SELECT * FROM occupation_records WHERE id=?", (record_id,)).fetchone()
        if not rec:
            raise HTTPException(404, f"隐患记录 {record_id} 不存在")
        conn.execute("UPDATE occupation_records SET status=? WHERE id=?", (req.status_to, record_id))
        conn.execute(
            "INSERT INTO rectification_logs(record_id,ts_ms,action,operator,status_to) VALUES(?,?,?,?,?)",
            (record_id, ts, req.action, req.operator, req.status_to))
        conn.commit()
        return {"ok": True, "record_id": record_id, "status": req.status_to}
    finally:
        conn.close()


@router.get("/records/{record_id}/timeline", summary="隐患整改时间线")
def timeline(record_id: int):
    """返回隐患详情 + 全部整改跟踪日志，展示闭环过程。"""
    conn = db.get_conn()
    try:
        rec = conn.execute("SELECT * FROM occupation_records WHERE id=?", (record_id,)).fetchone()
        if not rec:
            raise HTTPException(404, f"隐患记录 {record_id} 不存在")
        logs = db.rows_to_list(conn.execute(
            "SELECT ts_ms,action,operator,status_to FROM rectification_logs "
            "WHERE record_id=? ORDER BY ts_ms", (record_id,)))
        return {"record": dict(rec), "timeline": logs, "closed": rec["status"] == "已闭环"}
    finally:
        conn.close()


@router.get("/stats", summary="隐患统计分析")
def stats():
    """按类型、状态、风险等级统计，供图表展示。"""
    conn = db.get_conn()
    try:
        by_type = db.rows_to_list(conn.execute(
            "SELECT type name, COUNT(*) value FROM occupation_records GROUP BY type"))
        by_status = db.rows_to_list(conn.execute(
            "SELECT status name, COUNT(*) value FROM occupation_records GROUP BY status"))
        by_level = db.rows_to_list(conn.execute(
            "SELECT risk_level name, COUNT(*) value FROM occupation_records GROUP BY risk_level"))
        total = sum(r["value"] for r in by_status)
        closed = next((r["value"] for r in by_status if r["name"] == "已闭环"), 0)
        return {
            "by_type": by_type, "by_status": by_status, "by_level": by_level,
            "total": total, "closed": closed,
            "closure_rate_pct": round(closed / total * 100, 1) if total else 0.0,
        }
    finally:
        conn.close()
