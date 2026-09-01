# -*- coding: utf-8 -*-
"""
功能 3：施工影响评估
=====================
录入施工项目信息（工法、开挖深度、与管线距离等），自动评估对周边
土体与地下管网的安全风险，形成评估档案并可检索统计。
"""
import time
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

import database as db
from models import RISK_LEVELS, WORK_TYPES, ConstructionCreateReq, calc_construction_risk

router = APIRouter(prefix="/api/construction", tags=["3.施工影响评估"])


@router.get("", summary="施工评估档案列表")
def list_assess(keyword: Optional[str] = Query(None, description="项目/道路/施工单位模糊匹配"),
                district: Optional[str] = None,
                risk_level: Optional[str] = None,
                work_type: Optional[str] = None,
                page: int = Query(1, ge=1),
                page_size: int = Query(20, ge=1, le=100)):
    where, args = [], []
    if keyword:
        where.append("(project_name LIKE ? OR road_name LIKE ? OR construction_unit LIKE ?)")
        kw = f"%{keyword}%"
        args += [kw, kw, kw]
    if district:
        where.append("district=?"); args.append(district)
    if risk_level:
        where.append("risk_level=?"); args.append(risk_level)
    if work_type:
        where.append("work_type=?"); args.append(work_type)
    sql = "SELECT * FROM construction_assess" + (
        " WHERE " + " AND ".join(where) if where else "") + " ORDER BY overall_score DESC, id DESC"
    conn = db.get_conn()
    try:
        total = conn.execute("SELECT COUNT(*) c FROM" + sql[len("SELECT * FROM"):], args).fetchone()["c"]
        rows = db.rows_to_list(conn.execute(
            sql + " LIMIT ? OFFSET ?", args + [page_size, (page - 1) * page_size]))
        return {"total": total, "page": page, "page_size": page_size, "items": rows}
    finally:
        conn.close()


@router.get("/options", summary="下拉选项（区域/工法）")
def options():
    conn = db.get_conn()
    try:
        districts = [r["district"] for r in conn.execute(
            "SELECT DISTINCT district FROM construction_assess ORDER BY district")]
        return {"districts": districts, "work_types": list(WORK_TYPES),
                "risk_levels": list(RISK_LEVELS)}
    finally:
        conn.close()


@router.get("/stats", summary="施工风险统计")
def stats():
    conn = db.get_conn()
    try:
        by_risk = db.rows_to_list(conn.execute(
            "SELECT risk_level name, COUNT(*) value FROM construction_assess GROUP BY risk_level"))
        by_work = db.rows_to_list(conn.execute(
            "SELECT work_type name, COUNT(*) value FROM construction_assess GROUP BY work_type"))
        by_district = db.rows_to_list(conn.execute(
            "SELECT district name, COUNT(*) value FROM construction_assess"
            " GROUP BY district ORDER BY value DESC"))
        return {"by_risk": by_risk, "by_work_type": by_work, "by_district": by_district}
    finally:
        conn.close()


@router.get("/{assess_id}", summary="评估档案详情")
def detail(assess_id: int):
    conn = db.get_conn()
    try:
        row = conn.execute("SELECT * FROM construction_assess WHERE id=?", (assess_id,)).fetchone()
        if not row:
            raise HTTPException(404, f"评估档案 {assess_id} 不存在")
        return {"item": dict(row)}
    finally:
        conn.close()


@router.post("", summary="新增施工评估（自动评分）")
def create(req: ConstructionCreateReq):
    """录入施工信息，自动计算土体/管网/综合评分与风险等级后建档。"""
    if req.work_type not in WORK_TYPES:
        raise HTTPException(400, f"工法应为：{'/'.join(WORK_TYPES)}")
    soil, pipe, overall, level = calc_construction_risk(
        req.work_type, req.excavation_depth, req.distance_to_pipe)
    conn = db.get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO construction_assess(project_name,construction_unit,road_name,district,"
            "work_type,excavation_depth,distance_to_pipe,start_date,plan_days,soil_score,pipe_score,"
            "overall_score,risk_level,measures,assessor,assessed_at,created_ts)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (req.project_name, req.construction_unit, req.road_name, req.district, req.work_type,
             req.excavation_depth, req.distance_to_pipe, req.start_date, req.plan_days,
             soil, pipe, overall, level, req.measures, req.assessor,
             req.assessed_at or time.strftime("%Y-%m-%d"), int(time.time() * 1000)))
        conn.commit()
        return {"ok": True, "id": cur.lastrowid,
                "soil_score": soil, "pipe_score": pipe,
                "overall_score": overall, "risk_level": level}
    finally:
        conn.close()
