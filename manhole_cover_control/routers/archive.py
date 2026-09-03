# -*- coding: utf-8 -*-
"""
功能 2：一井一档数字档案
=========================
为每一处井盖建立独立电子台账：基础信息、权属管理单位、运维履历、
全部维修更换历史记录；支持新增、编辑、多条件查询。
"""
import time
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

import database as db
from models import (MANHOLE_STATUSES, MANHOLE_TYPES, ManholeCreateReq,
                    ManholeUpdateReq, RepairReq)

router = APIRouter(prefix="/api/archive", tags=["2.一井一档数字档案"])

_UPDATABLE = ("location", "road_name", "district", "type", "owner_unit",
              "material", "install_date", "lat", "lng", "status", "remark")


def _gen_code(conn) -> str:
    year = time.strftime("%Y")
    n = conn.execute("SELECT COUNT(*) c FROM manholes WHERE code LIKE ?",
                     (f"JG-{year}-%",)).fetchone()["c"] + 1
    return f"JG-{year}-{n:03d}"


@router.get("", summary="井盖档案列表（多条件查询）")
def list_manholes(keyword: Optional[str] = Query(None, description="编号/位置/道路模糊匹配"),
                  district: Optional[str] = None, type: Optional[str] = None,
                  status: Optional[str] = None, owner_unit: Optional[str] = None,
                  page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    where, args = [], []
    if keyword:
        where.append("(code LIKE ? OR location LIKE ? OR road_name LIKE ?)")
        kw = f"%{keyword}%"
        args += [kw, kw, kw]
    for col, val in (("district", district), ("type", type),
                     ("status", status), ("owner_unit", owner_unit)):
        if val:
            where.append(f"{col}=?"); args.append(val)
    sql = ("SELECT m.*, (SELECT COUNT(*) FROM repair_history r WHERE r.manhole_id=m.id) repairs,"
           " (SELECT COUNT(*) FROM alarms a WHERE a.manhole_id=m.id) alarms"
           " FROM manholes m" +
           (" WHERE " + " AND ".join(where) if where else "") + " ORDER BY m.id")
    conn = db.get_conn()
    try:
        total = conn.execute(
            "SELECT COUNT(*) c FROM manholes m" +
            (" WHERE " + " AND ".join(where) if where else ""), args).fetchone()["c"]
        rows = db.rows_to_list(conn.execute(
            sql + " LIMIT ? OFFSET ?", args + [page_size, (page - 1) * page_size]))
        return {"total": total, "page": page, "page_size": page_size, "items": rows}
    finally:
        conn.close()


@router.get("/options", summary="下拉选项")
def options():
    conn = db.get_conn()
    try:
        districts = [r["district"] for r in conn.execute(
            "SELECT DISTINCT district FROM manholes ORDER BY district")]
        owners = [r["owner_unit"] for r in conn.execute(
            "SELECT DISTINCT owner_unit FROM manholes ORDER BY owner_unit")]
        return {"districts": districts, "owners": owners,
                "types": list(MANHOLE_TYPES), "statuses": list(MANHOLE_STATUSES)}
    finally:
        conn.close()


@router.get("/stats", summary="档案统计")
def stats():
    conn = db.get_conn()
    try:
        return {
            "by_district": db.rows_to_list(conn.execute(
                "SELECT district name, COUNT(*) value FROM manholes GROUP BY district")),
            "by_type": db.rows_to_list(conn.execute(
                "SELECT type name, COUNT(*) value FROM manholes GROUP BY type")),
            "by_status": db.rows_to_list(conn.execute(
                "SELECT status name, COUNT(*) value FROM manholes GROUP BY status")),
            "by_owner": db.rows_to_list(conn.execute(
                "SELECT owner_unit name, COUNT(*) value FROM manholes"
                " GROUP BY owner_unit ORDER BY value DESC")),
        }
    finally:
        conn.close()


@router.get("/{manhole_id}", summary="井盖档案详情（含履历）")
def detail(manhole_id: int):
    conn = db.get_conn()
    try:
        row = conn.execute("SELECT * FROM manholes WHERE id=?", (manhole_id,)).fetchone()
        if not row:
            raise HTTPException(404, f"井盖档案 {manhole_id} 不存在")
        repairs = db.rows_to_list(conn.execute(
            "SELECT * FROM repair_history WHERE manhole_id=? ORDER BY date DESC", (manhole_id,)))
        alarms = db.rows_to_list(conn.execute(
            "SELECT * FROM alarms WHERE manhole_id=? ORDER BY alarm_ts DESC LIMIT 20",
            (manhole_id,)))
        net = conn.execute("SELECT * FROM safety_nets WHERE manhole_id=?",
                           (manhole_id,)).fetchone()
        latest = conn.execute(
            "SELECT * FROM monitor_data WHERE manhole_id=? ORDER BY ts DESC LIMIT 1",
            (manhole_id,)).fetchone()
        return {"item": dict(row), "repairs": repairs, "alarms": alarms,
                "net": dict(net) if net else None,
                "latest_monitor": dict(latest) if latest else None}
    finally:
        conn.close()


@router.post("", summary="新增井盖档案（自动建档编号）")
def create(req: ManholeCreateReq):
    if req.type not in MANHOLE_TYPES:
        raise HTTPException(400, f"井盖类型应为：{'/'.join(MANHOLE_TYPES)}")
    conn = db.get_conn()
    try:
        code = _gen_code(conn)
        cur = conn.execute(
            "INSERT INTO manholes(code,location,road_name,district,type,owner_unit,material,"
            "install_date,lat,lng,status,remark,created_ts) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (code, req.location, req.road_name, req.district, req.type, req.owner_unit,
             req.material, req.install_date, req.lat, req.lng, "正常", req.remark,
             int(time.time() * 1000)))
        conn.commit()
        return {"ok": True, "id": cur.lastrowid, "code": code}
    finally:
        conn.close()


@router.put("/{manhole_id}", summary="编辑井盖档案")
def update(manhole_id: int, req: ManholeUpdateReq):
    if req.type is not None and req.type not in MANHOLE_TYPES:
        raise HTTPException(400, f"井盖类型应为：{'/'.join(MANHOLE_TYPES)}")
    if req.status is not None and req.status not in MANHOLE_STATUSES:
        raise HTTPException(400, f"状态应为：{'/'.join(MANHOLE_STATUSES)}")
    data = req.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(400, "没有需要更新的字段")
    conn = db.get_conn()
    try:
        old = conn.execute("SELECT * FROM manholes WHERE id=?", (manhole_id,)).fetchone()
        if not old:
            raise HTTPException(404, f"井盖档案 {manhole_id} 不存在")
        sets = [f"{k}=?" for k in data if k in _UPDATABLE]
        args = [v for k, v in data.items() if k in _UPDATABLE]
        if not sets:
            raise HTTPException(400, "没有可更新字段")
        conn.execute(f"UPDATE manholes SET {', '.join(sets)} WHERE id=?",
                     args + [manhole_id])
        conn.commit()
        return {"ok": True, "id": manhole_id}
    finally:
        conn.close()


@router.post("/{manhole_id}/repairs", summary="登记维修/更换履历")
def add_repair(manhole_id: int, req: RepairReq):
    if req.type not in ("维修", "更换"):
        raise HTTPException(400, "履历类型应为：维修 / 更换")
    conn = db.get_conn()
    try:
        if not conn.execute("SELECT 1 FROM manholes WHERE id=?", (manhole_id,)).fetchone():
            raise HTTPException(404, f"井盖档案 {manhole_id} 不存在")
        cur = conn.execute(
            "INSERT INTO repair_history(manhole_id,type,date,reason,detail,cost,operator,created_ts)"
            " VALUES(?,?,?,?,?,?,?,?)",
            (manhole_id, req.type, req.date, req.reason, req.detail, req.cost,
             req.operator, int(time.time() * 1000)))
        # 更换井盖后默认恢复正常状态（维修中 → 正常）
        if req.type == "更换":
            conn.execute("UPDATE manholes SET status='正常' WHERE id=? AND status='维修中'",
                         (manhole_id,))
        conn.commit()
        return {"ok": True, "id": cur.lastrowid}
    finally:
        conn.close()
