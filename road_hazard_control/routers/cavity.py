# -*- coding: utf-8 -*-
"""
功能 1：地下空洞风险评估
=========================
录入地质雷达探测与渗漏检测数据，自动计算风险评分并判定低/中/高风险，
支持空洞台账的新增、修改、查询与统计。
"""
import time
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

import database as db
from models import CAVITY_STATUSES, RISK_LEVELS, CavityCreateReq, CavityUpdateReq, calc_cavity_risk

router = APIRouter(prefix="/api/cavity", tags=["1.地下空洞风险评估"])

# 字段白名单（PUT 部分更新用）
_UPDATABLE = ("road_name", "district", "location", "radar_velocity", "radar_area",
              "leakage_index", "cavity_volume", "depth_m", "status", "found_at", "remark")


def _gen_code(conn) -> str:
    year = time.strftime("%Y")
    n = conn.execute("SELECT COUNT(*) c FROM cavities WHERE code LIKE ?",
                     (f"KD-{year}-%",)).fetchone()["c"] + 1
    return f"KD-{year}-{n:03d}"


@router.get("", summary="空洞台账列表")
def list_cavities(keyword: Optional[str] = Query(None, description="编号/道路/位置模糊匹配"),
                  district: Optional[str] = None,
                  risk_level: Optional[str] = None,
                  status: Optional[str] = None,
                  page: int = Query(1, ge=1),
                  page_size: int = Query(20, ge=1, le=100)):
    where, args = [], []
    if keyword:
        where.append("(code LIKE ? OR road_name LIKE ? OR location LIKE ?)")
        kw = f"%{keyword}%"
        args += [kw, kw, kw]
    if district:
        where.append("district=?"); args.append(district)
    if risk_level:
        where.append("risk_level=?"); args.append(risk_level)
    if status:
        where.append("status=?"); args.append(status)
    sql = "SELECT * FROM cavities" + (
        " WHERE " + " AND ".join(where) if where else "") + " ORDER BY risk_score DESC, id DESC"
    conn = db.get_conn()
    try:
        total = conn.execute("SELECT COUNT(*) c FROM" + sql[len("SELECT * FROM"):], args).fetchone()["c"]
        rows = db.rows_to_list(conn.execute(
            sql + " LIMIT ? OFFSET ?", args + [page_size, (page - 1) * page_size]))
        return {"total": total, "page": page, "page_size": page_size, "items": rows}
    finally:
        conn.close()


@router.get("/options", summary="下拉选项（区域/状态/工法）")
def options():
    conn = db.get_conn()
    try:
        districts = [r["district"] for r in conn.execute(
            "SELECT DISTINCT district FROM cavities ORDER BY district")]
        roads = [r["road_name"] for r in conn.execute(
            "SELECT DISTINCT road_name FROM cavities ORDER BY road_name")]
        return {"districts": districts, "roads": roads,
                "risk_levels": list(RISK_LEVELS), "statuses": list(CAVITY_STATUSES)}
    finally:
        conn.close()


@router.get("/stats", summary="空洞风险统计")
def stats():
    conn = db.get_conn()
    try:
        by_risk = db.rows_to_list(conn.execute(
            "SELECT risk_level name, COUNT(*) value FROM cavities GROUP BY risk_level"))
        by_district = db.rows_to_list(conn.execute(
            "SELECT district name, COUNT(*) value FROM cavities GROUP BY district ORDER BY value DESC"))
        by_status = db.rows_to_list(conn.execute(
            "SELECT status name, COUNT(*) value FROM cavities GROUP BY status"))
        return {"by_risk": by_risk, "by_district": by_district, "by_status": by_status}
    finally:
        conn.close()


@router.get("/{cavity_id}", summary="空洞详情")
def detail(cavity_id: int):
    conn = db.get_conn()
    try:
        row = conn.execute("SELECT * FROM cavities WHERE id=?", (cavity_id,)).fetchone()
        if not row:
            raise HTTPException(404, f"空洞记录 {cavity_id} 不存在")
        return {"item": dict(row)}
    finally:
        conn.close()


@router.post("", summary="新增空洞（自动风险评估）")
def create(req: CavityCreateReq):
    """录入雷达与渗漏数据，自动计算风险评分与等级后入库。"""
    if req.status not in CAVITY_STATUSES:
        raise HTTPException(400, f"状态应为：{'/'.join(CAVITY_STATUSES)}")
    score, level = calc_cavity_risk(req.radar_area, req.leakage_index, req.cavity_volume)
    conn = db.get_conn()
    try:
        code = _gen_code(conn)
        cur = conn.execute(
            "INSERT INTO cavities(code,road_name,district,location,radar_velocity,radar_area,"
            "leakage_index,cavity_volume,depth_m,risk_score,risk_level,status,found_at,remark,created_ts)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (code, req.road_name, req.district, req.location, req.radar_velocity,
             req.radar_area, req.leakage_index, req.cavity_volume, req.depth_m,
             score, level, req.status, req.found_at, req.remark, int(time.time() * 1000)))
        conn.commit()
        return {"ok": True, "id": cur.lastrowid, "code": code,
                "risk_score": score, "risk_level": level}
    finally:
        conn.close()


@router.put("/{cavity_id}", summary="修改空洞信息（自动重算风险）")
def update(cavity_id: int, req: CavityUpdateReq):
    """部分字段更新；探测数据变化时自动重新计算风险评分与等级。"""
    if req.status is not None and req.status not in CAVITY_STATUSES:
        raise HTTPException(400, f"状态应为：{'/'.join(CAVITY_STATUSES)}")
    conn = db.get_conn()
    try:
        old = conn.execute("SELECT * FROM cavities WHERE id=?", (cavity_id,)).fetchone()
        if not old:
            raise HTTPException(404, f"空洞记录 {cavity_id} 不存在")
        data = req.model_dump(exclude_none=True)
        if not data:
            raise HTTPException(400, "没有需要更新的字段")
        merged = {**dict(old), **data}
        score, level = calc_cavity_risk(merged["radar_area"] or 0,
                                        merged["leakage_index"] or 0,
                                        merged["cavity_volume"] or 0)
        sets = [f"{k}=?" for k in data if k in _UPDATABLE]
        args = [v for k, v in data.items() if k in _UPDATABLE]
        sets += ["risk_score=?", "risk_level=?"]
        args += [score, level, cavity_id]
        conn.execute(f"UPDATE cavities SET {', '.join(sets)} WHERE id=?", args)
        conn.commit()
        return {"ok": True, "id": cavity_id, "risk_score": score, "risk_level": level}
    finally:
        conn.close()
