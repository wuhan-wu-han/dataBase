# -*- coding: utf-8 -*-
"""
功能 1：资产全景台账
====================
管网资产主数据管理：多条件筛选/关键词搜索/分页、五维度分类统计
（管径/材质/年代/权属/区域）、顶部汇总指标、CSV 导出、资产详情。
"""
import io
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

import database as db

router = APIRouter(prefix="/api/assets", tags=["1.资产全景台账"])

EXPORT_COLUMNS = [
    ("asset_code", "资产编号"), ("segment_name", "管段名称"), ("diameter", "管径"),
    ("material", "材质"), ("build_year", "建设年代"), ("owner_unit", "权属单位"),
    ("region", "所属区域"), ("length_m", "长度(米)"), ("pressure_level", "压力等级"),
    ("status", "当前状态"), ("location", "安装位置"), ("longitude", "经度"),
    ("latitude", "纬度"),
]


def _ownership_clear_clause():
    """权属清晰 = 产权/运维/监管三方均不为空。"""
    return ("COALESCE(o.property_unit,'')<>'' AND COALESCE(o.operation_unit,'')<>'' "
            "AND COALESCE(o.supervision_unit,'')<>''")


@router.get("", summary="资产明细列表（多条件筛选 + 搜索 + 分页）")
def list_assets(keyword: Optional[str] = Query(None, description="按资产编号/管段名称/位置模糊搜索"),
                diameter: Optional[str] = None, material: Optional[str] = None,
                owner_unit: Optional[str] = None, region: Optional[str] = None,
                status: Optional[str] = None,
                year_from: Optional[int] = Query(None, description="建设年代起"),
                year_to: Optional[int] = Query(None, description="建设年代止"),
                page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=200)):
    """支持按管径、材质、权属单位、区域、状态、年代区间组合筛选。"""
    where, args = ["1=1"], []
    if keyword:
        where.append("(asset_code LIKE ? OR segment_name LIKE ? OR location LIKE ?)")
        args += [f"%{keyword}%"] * 3
    for col, val in (("diameter", diameter), ("material", material), ("owner_unit", owner_unit),
                     ("region", region), ("status", status)):
        if val:
            where.append(f"{col}=?"); args.append(val)
    if year_from:
        where.append("build_year>=?"); args.append(year_from)
    if year_to:
        where.append("build_year<=?"); args.append(year_to)

    sql_where = " AND ".join(where)
    conn = db.get_conn()
    try:
        total = conn.execute(f"SELECT COUNT(*) c FROM assets WHERE {sql_where}", args).fetchone()["c"]
        rows = db.rows_to_list(conn.execute(
            f"SELECT * FROM assets WHERE {sql_where} ORDER BY id LIMIT ? OFFSET ?",
            args + [page_size, (page - 1) * page_size]))
        return {"total": total, "page": page, "page_size": page_size, "items": rows}
    finally:
        conn.close()


@router.get("/options", summary="筛选下拉选项")
def options():
    """供前端筛选器使用的可选值清单。"""
    conn = db.get_conn()
    try:
        def distinct(col):
            return [r[col] for r in conn.execute(
                f"SELECT DISTINCT {col} FROM assets ORDER BY {col}")]
        return {"diameters": distinct("diameter"), "materials": distinct("material"),
                "regions": distinct("region"), "owner_units": distinct("owner_unit"),
                "statuses": distinct("status"), "pressure_levels": distinct("pressure_level")}
    finally:
        conn.close()


@router.get("/summary", summary="顶部汇总指标")
def summary():
    """
    大屏顶部统计卡：资产总数、总长度、在役数、待报废数、
    盘点完成率（已完成任务/总任务）、权属清晰率（三方齐全的资产占比）。
    """
    conn = db.get_conn()
    try:
        total = conn.execute("SELECT COUNT(*) c, COALESCE(SUM(length_m),0) len FROM assets").fetchone()
        sc = lambda s: conn.execute("SELECT COUNT(*) c FROM assets WHERE status=?", (s,)).fetchone()["c"]
        tasks = conn.execute("SELECT COUNT(*) t, SUM(status='已完成') f FROM inventory_tasks").fetchone()
        clear = conn.execute(
            f"SELECT COUNT(*) c FROM assets a JOIN ownership o ON o.asset_id=a.id WHERE {_ownership_clear_clause()}"
        ).fetchone()["c"]
        return {
            "total_assets": total["c"],
            "total_length_km": round(total["len"] / 1000, 2),
            "in_service": sc("在役"),
            "suspended": sc("停用"),
            "pending_disposal": sc("待报废"),
            "task_count": tasks["t"],
            "task_finished": tasks["f"] or 0,
            "inventory_completion_rate": round((tasks["f"] or 0) / tasks["t"] * 100, 1) if tasks["t"] else 0,
            "ownership_clear": clear,
            "ownership_clear_rate": round(clear / total["c"] * 100, 1) if total["c"] else 0,
        }
    finally:
        conn.close()


def _group(conn, col, label_fn=None):
    """按维度分组统计数量与长度（公里），供五维分类图表使用。"""
    rows = conn.execute(
        f"SELECT {col} name, COUNT(*) value, ROUND(SUM(length_m)/1000.0, 2) length_km "
        f"FROM assets GROUP BY {col} ORDER BY value DESC").fetchall()
    out = [{"name": label_fn(r["name"]) if label_fn else r["name"],
            "value": r["value"], "length_km": r["length_km"]} for r in rows]
    return out


@router.get("/stats", summary="五维分类统计（管径/材质/年代/权属/区域）")
def stats():
    conn = db.get_conn()
    try:
        return {
            "by_diameter": _group(conn, "diameter"),
            "by_material": _group(conn, "material"),
            "by_decade": _group(conn, "build_year/10*10", lambda v: f"{v}年代"),
            "by_owner": _group(conn, "owner_unit"),
            "by_region": _group(conn, "region"),
            "by_pressure": _group(conn, "pressure_level"),
            "by_status": _group(conn, "status"),
        }
    finally:
        conn.close()


@router.get("/export", summary="导出资产台账 CSV")
def export(keyword: Optional[str] = None, diameter: Optional[str] = None,
           material: Optional[str] = None, owner_unit: Optional[str] = None,
           region: Optional[str] = None, status: Optional[str] = None):
    """按当前筛选条件导出 CSV（带 BOM，Excel 可直接打开中文）。"""
    where, args = ["1=1"], []
    if keyword:
        where.append("(asset_code LIKE ? OR segment_name LIKE ? OR location LIKE ?)")
        args += [f"%{keyword}%"] * 3
    for col, val in (("diameter", diameter), ("material", material),
                     ("owner_unit", owner_unit), ("region", region), ("status", status)):
        if val:
            where.append(f"{col}=?"); args.append(val)
    conn = db.get_conn()
    try:
        rows = db.rows_to_list(conn.execute(
            f"SELECT * FROM assets WHERE {' AND '.join(where)} ORDER BY id", args))
    finally:
        conn.close()

    buf = io.StringIO()
    buf.write("\ufeff")  # UTF-8 BOM：兼容 Excel 中文
    buf.write(",".join(h for _, h in EXPORT_COLUMNS) + "\n")
    for r in rows:
        buf.write(",".join(str(r.get(k, "")) for k, _ in EXPORT_COLUMNS) + "\n")
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=asset_ledger.csv"})


@router.get("/{asset_id}", summary="资产详情（含权属与生命周期概要）")
def asset_detail(asset_id: int):
    conn = db.get_conn()
    try:
        asset = conn.execute("SELECT * FROM assets WHERE id=?", (asset_id,)).fetchone()
        if not asset:
            raise HTTPException(404, f"资产 {asset_id} 不存在")
        own = conn.execute("SELECT * FROM ownership WHERE asset_id=?", (asset_id,)).fetchone()
        stages = db.rows_to_list(conn.execute(
            "SELECT stage, COUNT(*) n, COALESCE(SUM(cost),0) cost FROM lifecycle_records "
            "WHERE asset_id=? GROUP BY stage", (asset_id,)))
        return {"asset": dict(asset), "ownership": dict(own) if own else None,
                "lifecycle_summary": stages}
    finally:
        conn.close()
