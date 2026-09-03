# -*- coding: utf-8 -*-
"""
功能 5：防坠网台账管理
=======================
管理防坠网安装登记、破损记录、维修更换的完整运维台账：
登记 → 巡检发现破损 → 维修/更换 → 复检，状态与运维记录联动。
"""
import time
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

import database as db
from models import NET_MAINTAIN_TYPES, NetCreateReq, NetMaintainReq

router = APIRouter(prefix="/api/safety-net", tags=["5.防坠网台账管理"])


def _gen_code(conn) -> str:
    year = time.strftime("%Y")
    n = conn.execute("SELECT COUNT(*) c FROM safety_nets WHERE net_code LIKE ?",
                     (f"FZ-{year}-%",)).fetchone()["c"] + 1
    return f"FZ-{year}-{n:03d}"


def _net_or_404(conn, net_id):
    row = conn.execute("SELECT * FROM safety_nets WHERE id=?", (net_id,)).fetchone()
    if not row:
        raise HTTPException(404, f"防坠网 {net_id} 不存在")
    return row


@router.get("", summary="防坠网台账列表")
def list_nets(net_status: Optional[str] = None, district: Optional[str] = None,
              keyword: Optional[str] = Query(None, description="网编号/井盖编号/位置"),
              page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    where, args = [], []
    if net_status:
        where.append("n.net_status=?"); args.append(net_status)
    if district:
        where.append("m.district=?"); args.append(district)
    if keyword:
        where.append("(n.net_code LIKE ? OR m.code LIKE ? OR m.location LIKE ?)")
        kw = f"%{keyword}%"
        args += [kw, kw, kw]
    sql = ("SELECT n.*, m.code manhole_code, m.location, m.road_name, m.district"
           " FROM safety_nets n JOIN manholes m ON m.id=n.manhole_id" +
           (" WHERE " + " AND ".join(where) if where else "") + " ORDER BY n.id")
    conn = db.get_conn()
    try:
        rows = db.rows_to_list(conn.execute(sql, args))
        return {"total": len(rows), "page": page, "page_size": page_size,
                "items": rows[(page - 1) * page_size: page * page_size]}
    finally:
        conn.close()


@router.get("/stats", summary="防坠网统计")
def stats():
    conn = db.get_conn()
    try:
        by_status = db.rows_to_list(conn.execute(
            "SELECT net_status name, COUNT(*) value FROM safety_nets GROUP BY net_status"))
        today = time.strftime("%Y-%m-%d")
        overdue = conn.execute(
            "SELECT COUNT(*) c FROM safety_nets WHERE next_check IS NOT NULL AND next_check<?",
            (today,)).fetchone()["c"]
        maintains = conn.execute("SELECT COUNT(*) c FROM net_maintains").fetchone()["c"]
        return {"by_status": by_status, "overdue_check": overdue,
                "maintain_total": maintains,
                "cover_rate_pct": round(conn.execute(
                    "SELECT COUNT(*) c FROM safety_nets").fetchone()["c"] /
                    max(conn.execute("SELECT COUNT(*) c FROM manholes").fetchone()["c"], 1)
                    * 100, 1)}
    finally:
        conn.close()


@router.get("/{net_id}", summary="防坠网详情（含运维记录）")
def detail(net_id: int):
    conn = db.get_conn()
    try:
        net = _net_or_404(conn, net_id)
        maintains = db.rows_to_list(conn.execute(
            "SELECT * FROM net_maintains WHERE net_id=? ORDER BY date", (net_id,)))
        m = conn.execute("SELECT code, location, road_name, district FROM manholes WHERE id=?",
                         (net["manhole_id"],)).fetchone()
        return {"item": dict(net), "maintains": maintains,
                "manhole": dict(m) if m else None}
    finally:
        conn.close()


@router.post("", summary="防坠网安装登记")
def create(req: NetCreateReq):
    conn = db.get_conn()
    try:
        if not conn.execute("SELECT 1 FROM manholes WHERE id=?", (req.manhole_id,)).fetchone():
            raise HTTPException(404, f"井盖 {req.manhole_id} 不存在")
        exists = conn.execute("SELECT 1 FROM safety_nets WHERE manhole_id=? AND net_status<>'已更换'",
                              (req.manhole_id,)).fetchone()
        if exists:
            raise HTTPException(400, "该井盖已登记防坠网，请勿重复安装登记")
        code = _gen_code(conn)
        cur = conn.execute(
            "INSERT INTO safety_nets(net_code,manhole_id,install_date,material,load_kg,"
            "net_status,last_check,next_check,repair_count,remark,created_ts)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (code, req.manhole_id, req.install_date or time.strftime("%Y-%m-%d"),
             req.material, req.load_kg, "已安装",
             time.strftime("%Y-%m-%d"), req.next_check, 0, req.remark,
             int(time.time() * 1000)))
        conn.commit()
        return {"ok": True, "id": cur.lastrowid, "net_code": code}
    finally:
        conn.close()


@router.post("/{net_id}/maintain", summary="登记运维记录（破损/维修/更换）")
def maintain(net_id: int, req: NetMaintainReq):
    """
    破损登记 → 台账状态置「破损」；维修/更换 → 状态置「已维修/已更换」，
    维修次数 +1，并刷新最近检查日期。
    """
    if req.type not in NET_MAINTAIN_TYPES:
        raise HTTPException(400, f"运维类型应为：{'/'.join(NET_MAINTAIN_TYPES)}")
    conn = db.get_conn()
    try:
        net = _net_or_404(conn, net_id)
        cur = conn.execute(
            "INSERT INTO net_maintains(net_id,type,date,detail,operator,created_ts)"
            " VALUES(?,?,?,?,?,?)",
            (net_id, req.type, req.date, req.detail, req.operator, int(time.time() * 1000)))
        if req.type == "破损登记":
            conn.execute("UPDATE safety_nets SET net_status='破损' WHERE id=?", (net_id,))
        else:
            new_status = "已维修" if req.type == "维修" else "已更换"
            conn.execute("UPDATE safety_nets SET net_status=?, repair_count=repair_count+1,"
                         " last_check=? WHERE id=?", (new_status, req.date, net_id))
        conn.commit()
        return {"ok": True, "id": cur.lastrowid, "net_status":
                "破损" if req.type == "破损登记" else ("已维修" if req.type == "维修" else "已更换")}
    finally:
        conn.close()
