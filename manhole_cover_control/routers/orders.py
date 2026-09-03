# -*- coding: utf-8 -*-
"""
功能 3：隐患闭环处置流程
=========================
完整业务闭环：
  隐患发现告警 → 自动生成派发运维工单 → 现场处置信息上报
  → 整改结果核验 → 隐患闭环销号归档
工单状态机：待派发 → 处置中 → 待核验 → 已核验 → 已闭环
（核验不通过退回处置中重新上报；告警与井盖状态全程联动）
"""
import time
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

import database as db
from models import DispatchReq, HANDLE_TYPES, ReportReq, VerifyReq

router = APIRouter(prefix="/api/orders", tags=["3.隐患闭环处置"])

_JOIN = ("SELECT o.*, a.alarm_code, a.type alarm_type, a.level alarm_level, a.detail alarm_detail,"
         " m.code, m.location, m.road_name, m.district FROM work_orders o"
         " LEFT JOIN alarms a ON a.id=o.alarm_id"
         " JOIN manholes m ON m.id=o.manhole_id")


def _order_or_404(conn, order_id):
    row = conn.execute("SELECT * FROM work_orders WHERE id=?", (order_id,)).fetchone()
    if not row:
        raise HTTPException(404, f"工单 {order_id} 不存在")
    return row


def _sync_alarm(conn, alarm_id, status):
    if alarm_id:
        conn.execute("UPDATE alarms SET status=? WHERE id=?", (status, alarm_id))


@router.get("", summary="运维工单列表")
def list_orders(status: Optional[str] = None, handle_type: Optional[str] = None,
                keyword: Optional[str] = Query(None, description="工单号/井盖编号/位置"),
                page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    where, args = [], []
    if status:
        where.append("o.status=?"); args.append(status)
    if handle_type:
        where.append("o.handle_type=?"); args.append(handle_type)
    if keyword:
        where.append("(o.order_code LIKE ? OR m.code LIKE ? OR m.location LIKE ?)")
        kw = f"%{keyword}%"
        args += [kw, kw, kw]
    sql = _JOIN + (" WHERE " + " AND ".join(where) if where else "") + \
        " ORDER BY o.created_ts DESC"
    conn = db.get_conn()
    try:
        rows = db.rows_to_list(conn.execute(sql, args))
        return {"total": len(rows), "page": page, "page_size": page_size,
                "items": rows[(page - 1) * page_size: page * page_size]}
    finally:
        conn.close()


@router.get("/stats", summary="工单统计与闭环率")
def stats():
    conn = db.get_conn()
    try:
        by_status = db.rows_to_list(conn.execute(
            "SELECT status name, COUNT(*) value FROM work_orders GROUP BY status"))
        total = conn.execute("SELECT COUNT(*) c FROM work_orders").fetchone()["c"]
        closed = conn.execute(
            "SELECT COUNT(*) c FROM work_orders WHERE status='已闭环'").fetchone()["c"]
        avg_ms = conn.execute(
            "SELECT AVG(close_ts-created_ts) v FROM work_orders WHERE close_ts IS NOT NULL"
        ).fetchone()["v"]
        return {"by_status": by_status, "total": total, "closed": closed,
                "close_rate_pct": round(closed / total * 100, 1) if total else 0,
                "avg_close_hours": round(avg_ms / 3600000, 1) if avg_ms else 0}
    finally:
        conn.close()


@router.get("/{order_id}", summary="工单详情（闭环流程时间线）")
def detail(order_id: int):
    conn = db.get_conn()
    try:
        row = conn.execute(
            _JOIN + " WHERE o.id=?", (order_id,)).fetchone()
        if not row:
            raise HTTPException(404, f"工单 {order_id} 不存在")
        return {"item": dict(row)}
    finally:
        conn.close()


@router.post("/{order_id}/dispatch", summary="派发工单（指定班组与处置方式）")
def dispatch(order_id: int, req: DispatchReq):
    if req.handle_type not in HANDLE_TYPES:
        raise HTTPException(400, f"处置方式应为：{'/'.join(HANDLE_TYPES)}")
    conn = db.get_conn()
    try:
        o = _order_or_404(conn, order_id)
        if o["status"] != "待派发":
            raise HTTPException(400, f"仅待派发工单可派发（当前：{o['status']}）")
        ts = int(time.time() * 1000)
        conn.execute("UPDATE work_orders SET status='处置中', assignee=?, handle_type=?,"
                     " dispatch_ts=? WHERE id=?", (req.assignee, req.handle_type, ts, order_id))
        _sync_alarm(conn, o["alarm_id"], "已派发")
        conn.execute("UPDATE manholes SET status='处置中' WHERE id=? AND status='告警'",
                     (o["manhole_id"],))
        conn.commit()
        return {"ok": True, "id": order_id, "status": "处置中"}
    finally:
        conn.close()


@router.post("/{order_id}/report", summary="现场处置信息上报")
def report(order_id: int, req: ReportReq):
    conn = db.get_conn()
    try:
        o = _order_or_404(conn, order_id)
        if o["status"] != "处置中":
            raise HTTPException(400, f"仅处置中工单可上报（当前：{o['status']}）")
        ts = int(time.time() * 1000)
        conn.execute("UPDATE work_orders SET status='待核验', report_info=?, report_ts=?"
                     " WHERE id=?", (req.report_info, ts, order_id))
        _sync_alarm(conn, o["alarm_id"], "处置中")
        conn.commit()
        return {"ok": True, "id": order_id, "status": "待核验"}
    finally:
        conn.close()


@router.post("/{order_id}/verify", summary="整改结果核验")
def verify(order_id: int, req: VerifyReq):
    conn = db.get_conn()
    try:
        o = _order_or_404(conn, order_id)
        if o["status"] != "待核验":
            raise HTTPException(400, f"仅待核验工单可核验（当前：{o['status']}）")
        ts = int(time.time() * 1000)
        if req.passed:
            conn.execute("UPDATE work_orders SET status='已核验', verify_result=?,"
                         " verify_ts=? WHERE id=?", (req.verify_result, ts, order_id))
            _sync_alarm(conn, o["alarm_id"], "已核验")
            status = "已核验"
        else:
            # 核验不通过：退回处置中，需重新上报
            conn.execute("UPDATE work_orders SET status='处置中', verify_result=?,"
                         " verify_ts=? WHERE id=?", (req.verify_result, ts, order_id))
            _sync_alarm(conn, o["alarm_id"], "已派发")
            status = "处置中"
        conn.commit()
        return {"ok": True, "id": order_id, "status": status}
    finally:
        conn.close()


@router.post("/{order_id}/close", summary="隐患闭环销号归档")
def close(order_id: int):
    conn = db.get_conn()
    try:
        o = _order_or_404(conn, order_id)
        if o["status"] != "已核验":
            raise HTTPException(400, f"仅已核验工单可闭环销号（当前：{o['status']}）")
        ts = int(time.time() * 1000)
        conn.execute("UPDATE work_orders SET status='已闭环', close_ts=? WHERE id=?",
                     (ts, order_id))
        _sync_alarm(conn, o["alarm_id"], "已闭环")
        conn.execute("UPDATE manholes SET status='正常' WHERE id=?"
                     " AND status IN ('告警','处置中','维修中')", (o["manhole_id"],))
        conn.commit()
        return {"ok": True, "id": order_id, "status": "已闭环"}
    finally:
        conn.close()
