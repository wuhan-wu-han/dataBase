# -*- coding: utf-8 -*-
"""
功能 4：资产权属管理
====================
为每项资产明确三方责任：产权单位、运维单位、监管单位；
记录产权性质、产权证书、运维合同、责任边界与交接时间；
提供权属责任矩阵（单位 × 区域热力矩阵）、按区域/单位的权属分布统计，
并识别权属不清（产权/运维/监管任一缺失）的资产进行预警。
"""
from fastapi import APIRouter, HTTPException

import database as db
from models import OwnershipUpdateReq

router = APIRouter(prefix="/api/ownership", tags=["4.资产权属管理"])

CLEAR_COND = ("COALESCE(o.property_unit,'')<>'' AND COALESCE(o.operation_unit,'')<>'' "
              "AND COALESCE(o.supervision_unit,'')<>''")


def _matrix(conn, unit_col: str):
    """构建 单位 × 区域 的责任矩阵（热力图数据）。"""
    regions = [r["region"] for r in conn.execute(
        "SELECT DISTINCT region FROM assets ORDER BY region")]
    units = [r["u"] for r in conn.execute(
        f"SELECT DISTINCT {unit_col} u FROM ownership "
        f"WHERE COALESCE({unit_col},'')<>'' ORDER BY {unit_col}")]
    counts = {(r["u"], r["g"]): r["n"] for r in conn.execute(
        f"SELECT o.{unit_col} u, a.region g, COUNT(*) n FROM ownership o "
        f"JOIN assets a ON a.id=o.asset_id WHERE COALESCE(o.{unit_col},'')<>'' "
        f"GROUP BY o.{unit_col}, a.region")}
    values = []
    for i, u in enumerate(units):
        for j, g in enumerate(regions):
            n = counts.get((u, g), 0)
            if n:
                values.append([j, i, n])
    return {"rows": units, "columns": regions, "values": values}


@router.get("", summary="权属信息列表")
def list_ownership():
    """全部资产的权属记录（联查资产基础信息）。"""
    conn = db.get_conn()
    try:
        rows = db.rows_to_list(conn.execute(
            "SELECT o.*, a.asset_code, a.segment_name, a.region, a.status asset_status "
            "FROM ownership o JOIN assets a ON a.id=o.asset_id ORDER BY a.id"))
        for r in rows:
            r["is_clear"] = all([r["property_unit"], r["operation_unit"], r["supervision_unit"]])
        return {"items": rows}
    finally:
        conn.close()


@router.get("/matrix", summary="权属责任矩阵（产权/运维/监管 × 区域）")
def matrix():
    """三方责任矩阵：行=责任单位，列=区域，值=资产数量，供热力图展示。"""
    conn = db.get_conn()
    try:
        return {
            "property": _matrix(conn, "property_unit"),
            "operation": _matrix(conn, "operation_unit"),
            "supervision": _matrix(conn, "supervision_unit"),
        }
    finally:
        conn.close()


@router.get("/unclear", summary="权属不清资产预警")
def unclear():
    """识别产权/运维/监管任一缺失的资产，返回缺失项清单用于预警。"""
    conn = db.get_conn()
    try:
        rows = db.rows_to_list(conn.execute(
            "SELECT o.*, a.asset_code, a.segment_name, a.region, a.owner_unit "
            "FROM ownership o JOIN assets a ON a.id=o.asset_id "
            f"WHERE NOT ({CLEAR_COND}) ORDER BY a.id"))
        items = []
        for r in rows:
            missing = []
            if not r["property_unit"]:
                missing.append("产权单位")
            if not r["operation_unit"]:
                missing.append("运维单位")
            if not r["supervision_unit"]:
                missing.append("监管单位")
            items.append({**r, "missing": missing,
                          "missing_text": "、".join(missing)})
        return {"total": len(items), "items": items}
    finally:
        conn.close()


@router.get("/stats", summary="权属统计分析")
def stats():
    """产权性质分布、各单位承担数量、权属清晰率。"""
    conn = db.get_conn()
    try:
        total = conn.execute("SELECT COUNT(*) c FROM ownership").fetchone()["c"]
        clear = conn.execute(
            f"SELECT COUNT(*) c FROM ownership o WHERE {CLEAR_COND}").fetchone()["c"]
        by_nature = db.rows_to_list(conn.execute(
            "SELECT COALESCE(NULLIF(property_nature,''),'未登记') name, COUNT(*) value "
            "FROM ownership GROUP BY name"))
        return {
            "total": total, "clear": clear, "unclear": total - clear,
            "clear_rate_pct": round(clear / total * 100, 1) if total else 0,
            "by_nature": by_nature,
            "property_units": _unit_dist(conn, "property_unit"),
            "operation_units": _unit_dist(conn, "operation_unit"),
            "supervision_units": _unit_dist(conn, "supervision_unit"),
        }
    finally:
        conn.close()


def _unit_dist(conn, col):
    return db.rows_to_list(conn.execute(
        f"SELECT COALESCE(NULLIF({col},''),'（缺失）') name, COUNT(*) value "
        f"FROM ownership GROUP BY name ORDER BY value DESC"))


@router.get("/{asset_id}", summary="单资产权属详情")
def ownership_detail(asset_id: int):
    conn = db.get_conn()
    try:
        row = conn.execute(
            "SELECT o.*, a.asset_code, a.segment_name, a.region FROM ownership o "
            "JOIN assets a ON a.id=o.asset_id WHERE o.asset_id=?", (asset_id,)).fetchone()
        if not row:
            raise HTTPException(404, f"资产 {asset_id} 无权属记录")
        return dict(row)
    finally:
        conn.close()


@router.put("/{asset_id}", summary="更新/补录权属信息")
def update_ownership(asset_id: int, req: OwnershipUpdateReq):
    """对权属不清的资产进行补录修正（部分字段更新）。"""
    conn = db.get_conn()
    try:
        if not conn.execute("SELECT 1 FROM assets WHERE id=?", (asset_id,)).fetchone():
            raise HTTPException(404, f"资产 {asset_id} 不存在")
        fields = {k: v for k, v in req.model_dump().items() if v is not None}
        if not fields:
            raise HTTPException(400, "未提供任何待更新字段")
        exists = conn.execute("SELECT id FROM ownership WHERE asset_id=?", (asset_id,)).fetchone()
        if exists:
            sets = ",".join(f"{k}=?" for k in fields)
            conn.execute(f"UPDATE ownership SET {sets} WHERE asset_id=?",
                         (*fields.values(), asset_id))
        else:
            cols = ",".join(["asset_id", *fields.keys()])
            marks = ",".join(["?"] * (len(fields) + 1))
            conn.execute(f"INSERT INTO ownership({cols}) VALUES({marks})",
                         (asset_id, *fields.values()))
        conn.commit()
        return {"ok": True, "asset_id": asset_id}
    finally:
        conn.close()
