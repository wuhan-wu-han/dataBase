# -*- coding: utf-8 -*-
"""
功能 2：全生命周期档案
======================
为每项资产建立 采购 → 施工 → 运维 → 改造 → 报废 的全流程时间线档案。
每个阶段记录：阶段名称、发生时间、责任单位/人、事件描述、附件、费用。
支持按资产查看完整时间线，支持新增/编辑各阶段记录。
"""
from fastapi import APIRouter, HTTPException, Query

import database as db
from models import STAGES, LifecycleCreateReq, LifecycleUpdateReq

router = APIRouter(prefix="/api/lifecycle", tags=["2.全生命周期档案"])


@router.get("/stages", summary="生命周期阶段定义")
def stages():
    """返回标准阶段顺序，供前端时间线/分布图使用。"""
    return {"stages": list(STAGES)}


@router.get("/{asset_id}", summary="资产全生命周期时间线")
def timeline(asset_id: int):
    """按时间正序返回该资产全部阶段记录，并汇总各阶段费用。"""
    conn = db.get_conn()
    try:
        asset = conn.execute("SELECT id, asset_code, segment_name FROM assets WHERE id=?",
                             (asset_id,)).fetchone()
        if not asset:
            raise HTTPException(404, f"资产 {asset_id} 不存在")
        records = db.rows_to_list(conn.execute(
            "SELECT * FROM lifecycle_records WHERE asset_id=? ORDER BY occurred_at, id",
            (asset_id,)))
        total_cost = sum(r["cost"] or 0 for r in records)
        return {"asset": dict(asset), "records": records,
                "record_count": len(records), "total_cost": round(total_cost, 0)}
    finally:
        conn.close()


@router.get("", summary="生命周期记录查询（可按阶段过滤）")
def list_records(stage: str = Query(None, description="按阶段过滤"),
                 asset_id: int = Query(None), limit: int = Query(200, ge=1, le=1000)):
    """返回生命周期记录（联查资产编号），供分布图与明细使用。"""
    where, args = ["1=1"], []
    if stage:
        where.append("l.stage=?"); args.append(stage)
    if asset_id:
        where.append("l.asset_id=?"); args.append(asset_id)
    conn = db.get_conn()
    try:
        rows = db.rows_to_list(conn.execute(
            "SELECT l.*, a.asset_code, a.segment_name FROM lifecycle_records l "
            "JOIN assets a ON a.id=l.asset_id WHERE " + " AND ".join(where) +
            " ORDER BY l.occurred_at DESC LIMIT ?", args + [limit]))
        return {"records": rows}
    finally:
        conn.close()


@router.post("", summary="新增生命周期记录")
def create_record(req: LifecycleCreateReq):
    """为资产新增一条阶段记录（如一次维修、一次改造）。"""
    if req.stage not in STAGES:
        raise HTTPException(400, f"阶段应为：{'/'.join(STAGES)}")
    conn = db.get_conn()
    try:
        if not conn.execute("SELECT 1 FROM assets WHERE id=?", (req.asset_id,)).fetchone():
            raise HTTPException(404, f"资产 {req.asset_id} 不存在")
        cur = conn.execute(
            "INSERT INTO lifecycle_records(asset_id,stage,occurred_at,responsible,description,attachment,cost)"
            " VALUES(?,?,?,?,?,?,?)",
            (req.asset_id, req.stage, req.occurred_at, req.responsible,
             req.description, req.attachment, req.cost))
        conn.commit()
        return {"ok": True, "id": cur.lastrowid}
    finally:
        conn.close()


@router.put("/{record_id}", summary="编辑生命周期记录")
def update_record(record_id: int, req: LifecycleUpdateReq):
    """部分字段更新；若修改阶段需仍属于标准阶段。"""
    conn = db.get_conn()
    try:
        rec = conn.execute("SELECT * FROM lifecycle_records WHERE id=?", (record_id,)).fetchone()
        if not rec:
            raise HTTPException(404, f"记录 {record_id} 不存在")
        fields = {k: v for k, v in req.model_dump().items() if v is not None}
        if "stage" in fields and fields["stage"] not in STAGES:
            raise HTTPException(400, f"阶段应为：{'/'.join(STAGES)}")
        if fields:
            sets = ",".join(f"{k}=?" for k in fields)
            conn.execute(f"UPDATE lifecycle_records SET {sets} WHERE id=?",
                         (*fields.values(), record_id))
            conn.commit()
        return {"ok": True}
    finally:
        conn.close()
