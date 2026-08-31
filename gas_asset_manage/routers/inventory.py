# -*- coding: utf-8 -*-
"""
功能 3：资产盘点
================
支持两种盘点方式：
  - 扫码盘点：前端模拟扫码，逐个录入资产编号核对（/scan）；
  - 巡检盘点：按区域/管段批量核对（/patrol）。

流程：生成盘点任务 → 执行盘点（账实核对）→ 标记差异 →
      差异处理（补录/修正/报废）→ 盘点完成。
"""
import time
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

import database as db
from models import InventoryTaskCreateReq, ItemHandleReq, ScanCheckReq

router = APIRouter(prefix="/api/inventory", tags=["3.资产盘点"])

DIFF_RESULTS = ("状态不符", "盘亏", "盘盈")   # 差异核对结果
HANDLE_CHOICES = ("补录", "修正", "报废")     # 差异处理方式


def _task_or_404(conn, task_id):
    task = conn.execute("SELECT * FROM inventory_tasks WHERE id=?", (task_id,)).fetchone()
    if not task:
        raise HTTPException(404, f"盘点任务 {task_id} 不存在")
    return task


def _gen_task_code(conn):
    today = time.strftime("%Y%m%d")
    n = conn.execute("SELECT COUNT(*) c FROM inventory_tasks WHERE task_code LIKE ?",
                     (f"PD-{today}-%",)).fetchone()["c"] + 1
    return f"PD-{today}-{n:02d}"


@router.get("/tasks", summary="盘点任务列表")
def list_tasks(limit: int = Query(50, ge=1, le=200)):
    conn = db.get_conn()
    try:
        rows = db.rows_to_list(conn.execute(
            "SELECT * FROM inventory_tasks ORDER BY id DESC LIMIT ?", (limit,)))
        return {"tasks": rows}
    finally:
        conn.close()


@router.post("/tasks", summary="生成盘点任务")
def create_task(req: InventoryTaskCreateReq):
    """
    生成盘点任务并按范围（区域）圈定资产，生成待核对明细。
    盘点方式：扫码盘点 / 巡检盘点。
    """
    if req.method not in ("扫码盘点", "巡检盘点"):
        raise HTTPException(400, "盘点方式应为：扫码盘点 / 巡检盘点")
    ts = int(time.time() * 1000)
    conn = db.get_conn()
    try:
        if req.scope_region:
            assets = conn.execute("SELECT * FROM assets WHERE region=?", (req.scope_region,)).fetchall()
        else:
            assets = conn.execute("SELECT * FROM assets").fetchall()
        if not assets:
            raise HTTPException(400, f"范围「{req.scope}」内没有可盘点资产")
        cur = conn.execute(
            "INSERT INTO inventory_tasks(task_code,method,scope,operator,started_ts,status)"
            " VALUES(?,?,?,?,?,?)",
            (_gen_task_code(conn), req.method, req.scope, req.operator, ts, "执行中"))
        task_id = cur.lastrowid
        conn.executemany(
            "INSERT INTO inventory_items(task_id,asset_id,asset_code,check_result,handle_status)"
            " VALUES(?,?,?,?,?)",
            [(task_id, a["id"], a["asset_code"], "待核对", "待核对") for a in assets])
        conn.commit()
        return {"ok": True, "task_id": task_id, "item_count": len(assets)}
    finally:
        conn.close()


@router.get("/tasks/{task_id}", summary="盘点任务详情（含明细）")
def task_detail(task_id: int):
    conn = db.get_conn()
    try:
        task = _task_or_404(conn, task_id)
        items = db.rows_to_list(conn.execute(
            "SELECT i.*, a.segment_name, a.region, a.status asset_status, a.diameter "
            "FROM inventory_items i LEFT JOIN assets a ON a.id=i.asset_id "
            "WHERE i.task_id=? ORDER BY i.id", (task_id,)))
        return {"task": dict(task), "items": items}
    finally:
        conn.close()


def _apply_result(conn, item_id, asset, found: bool):
    """
    账实核对判定：
      - 巡检未找到现场管段 → 盘亏；
      - 台账状态为停用但现场仍在运行（模拟：id 可被 5 整除）→ 状态不符；
      - 其余 → 一致。
    """
    if not found:
        result, handle = "盘亏", "待处理"
    elif asset["status"] == "停用" and asset["id"] % 5 == 0:
        result, handle = "状态不符", "待处理"
    else:
        result, handle = "一致", "无差异"
    conn.execute("UPDATE inventory_items SET check_result=?, handle_status=? WHERE id=?",
                 (result, handle, item_id))
    if result in DIFF_RESULTS:
        conn.execute("UPDATE inventory_tasks SET status='差异处理中' WHERE id=?",
                     (conn.execute("SELECT task_id FROM inventory_items WHERE id=?",
                                   (item_id,)).fetchone()["task_id"],))
    return result


@router.post("/tasks/{task_id}/scan", summary="扫码盘点：核对单件资产")
def scan_check(task_id: int, req: ScanCheckReq):
    """
    模拟扫码：录入资产编号后核对该资产。
    编号不在任务范围内 → 400；台账中不存在该编号 → 记为盘盈（有物无账）。
    """
    conn = db.get_conn()
    try:
        task = _task_or_404(conn, task_id)
        if task["status"] == "已完成":
            raise HTTPException(400, "该盘点任务已完成，不能再核对")

        item = conn.execute("SELECT * FROM inventory_items WHERE task_id=? AND asset_code=?",
                            (task_id, req.asset_code)).fetchone()
        if item:
            if item["check_result"] != "待核对":
                raise HTTPException(400, f"资产 {req.asset_code} 已核对过（{item['check_result']}）")
            asset = conn.execute("SELECT * FROM assets WHERE id=?", (item["asset_id"],)).fetchone()
            result = _apply_result(conn, item["id"], asset, found=True)
        else:
            exists = conn.execute("SELECT 1 FROM assets WHERE asset_code=?", (req.asset_code,)).fetchone()
            if exists:
                raise HTTPException(400, f"资产 {req.asset_code} 不在本任务盘点范围内")
            # 台账中不存在 → 盘盈（现场有物、账上无记录）
            conn.execute(
                "INSERT INTO inventory_items(task_id,asset_id,asset_code,check_result,handle_status,remark)"
                " VALUES(?,?,?,?,?,?)", (task_id, None, req.asset_code, "盘盈", "待处理", "扫码发现账外资产"))
            conn.execute("UPDATE inventory_tasks SET status='差异处理中' WHERE id=?", (task_id,))
            result = "盘盈"
        conn.commit()
        return {"ok": True, "asset_code": req.asset_code, "check_result": result}
    finally:
        conn.close()


@router.post("/tasks/{task_id}/patrol", summary="巡检盘点：批量核对")
def patrol_check(task_id: int):
    """按区域/管段批量核对全部待核对资产（模拟现场巡检结果）。"""
    conn = db.get_conn()
    try:
        task = _task_or_404(conn, task_id)
        if task["status"] == "已完成":
            raise HTTPException(400, "该盘点任务已完成，不能再核对")
        pending = db.rows_to_list(conn.execute(
            "SELECT i.*, a.* FROM inventory_items i JOIN assets a ON a.id=i.asset_id "
            "WHERE i.task_id=? AND i.check_result='待核对'", (task_id,)))
        results = {"一致": 0, "盘亏": 0, "状态不符": 0}
        for it in pending:
            found = not (it["asset_id"] % 9 == 4)   # 模拟现场未找到
            r = _apply_result(conn, it["id"], it, found)
            results[r] = results.get(r, 0) + 1
        conn.commit()
        return {"ok": True, "checked": len(pending), "results": results}
    finally:
        conn.close()


@router.put("/items/{item_id}", summary="差异处理（补录/修正/报废）")
def handle_item(item_id: int, req: ItemHandleReq):
    """
    对差异项做闭环处理：
      - 补录：盘盈资产补充录入台账；
      - 修正：修正台账状态/属性信息；
      - 报废：关联资产转入待报废状态。
    """
    if req.handle_status not in HANDLE_CHOICES:
        raise HTTPException(400, f"处理方式应为：{'/'.join(HANDLE_CHOICES)}")
    conn = db.get_conn()
    try:
        item = conn.execute("SELECT * FROM inventory_items WHERE id=?", (item_id,)).fetchone()
        if not item:
            raise HTTPException(404, f"盘点明细 {item_id} 不存在")
        if item["check_result"] not in DIFF_RESULTS:
            raise HTTPException(400, "仅差异项（状态不符/盘亏/盘盈）需要处理")
        conn.execute("UPDATE inventory_items SET handle_status=?, remark=? WHERE id=?",
                     (req.handle_status, req.remark or item["remark"], item_id))
        # 报废处理：联动更新资产状态
        if req.handle_status == "报废" and item["asset_id"]:
            conn.execute("UPDATE assets SET status='待报废' WHERE id=?", (item["asset_id"],))
        conn.commit()
        return {"ok": True, "item_id": item_id, "handle_status": req.handle_status}
    finally:
        conn.close()


@router.post("/tasks/{task_id}/finish", summary="完成盘点任务")
def finish_task(task_id: int):
    """
    校验：无待核对项、差异项均已处理。通过后写入账实一致数/差异数并归档。
    """
    conn = db.get_conn()
    try:
        _task_or_404(conn, task_id)
        unchecked = conn.execute(
            "SELECT COUNT(*) c FROM inventory_items WHERE task_id=? AND check_result='待核对'",
            (task_id,)).fetchone()["c"]
        if unchecked:
            raise HTTPException(400, f"仍有 {unchecked} 项未核对，不能完成盘点")
        unhandled = conn.execute(
            "SELECT COUNT(*) c FROM inventory_items WHERE task_id=? AND handle_status='待处理'",
            (task_id,)).fetchone()["c"]
        if unhandled:
            raise HTTPException(400, f"仍有 {unhandled} 项差异未处理，不能完成盘点")

        matched = conn.execute(
            "SELECT COUNT(*) c FROM inventory_items WHERE task_id=? AND check_result='一致'",
            (task_id,)).fetchone()["c"]
        diff = conn.execute(
            "SELECT COUNT(*) c FROM inventory_items WHERE task_id=? AND check_result IN ('状态不符','盘亏','盘盈')",
            (task_id,)).fetchone()["c"]
        conn.execute(
            "UPDATE inventory_tasks SET status='已完成', finished_ts=?, matched_count=?, diff_count=? "
            "WHERE id=?", (int(time.time() * 1000), matched, diff, task_id))
        conn.commit()
        return {"ok": True, "task_id": task_id, "matched_count": matched, "diff_count": diff}
    finally:
        conn.close()


@router.get("/diff", summary="盘点差异清单与处理跟踪")
def diff_list(task_id: Optional[int] = Query(None),
              handle_status: Optional[str] = Query(None, description="按处理状态过滤")):
    """跨任务的差异清单（状态不符/盘亏/盘盈），可按任务与处理状态过滤。"""
    where, args = ["i.check_result IN ('状态不符','盘亏','盘盈')"], []
    if task_id:
        where.append("i.task_id=?"); args.append(task_id)
    if handle_status:
        where.append("i.handle_status=?"); args.append(handle_status)
    conn = db.get_conn()
    try:
        rows = db.rows_to_list(conn.execute(
            "SELECT i.*, t.task_code, t.method, t.operator, a.segment_name, a.region, "
            "a.status asset_status FROM inventory_items i "
            "JOIN inventory_tasks t ON t.id=i.task_id "
            "LEFT JOIN assets a ON a.id=i.asset_id WHERE " + " AND ".join(where) +
            " ORDER BY i.id DESC", args))
        return {"diffs": rows, "total": len(rows)}
    finally:
        conn.close()


@router.get("/stats", summary="盘点统计（差异处理状态分布）")
def stats():
    """差异处理状态分布与任务完成情况，供大屏图表使用。"""
    conn = db.get_conn()
    try:
        by_handle = db.rows_to_list(conn.execute(
            "SELECT handle_status name, COUNT(*) value FROM inventory_items "
            "WHERE check_result IN ('状态不符','盘亏','盘盈') GROUP BY handle_status"))
        by_result = db.rows_to_list(conn.execute(
            "SELECT check_result name, COUNT(*) value FROM inventory_items "
            "WHERE check_result<>'待核对' GROUP BY check_result"))
        tasks = db.rows_to_list(conn.execute(
            "SELECT id, task_code, method, scope, operator, status, matched_count, diff_count,"
            " started_ts, finished_ts FROM inventory_tasks ORDER BY id DESC LIMIT 10"))
        total_items = conn.execute(
            "SELECT COUNT(*) c FROM inventory_items WHERE check_result<>'待核对'").fetchone()["c"]
        matched = conn.execute(
            "SELECT COUNT(*) c FROM inventory_items WHERE check_result='一致'").fetchone()["c"]
        return {
            "by_handle_status": by_handle,
            "by_check_result": by_result,
            "recent_tasks": tasks,
            "match_rate_pct": round(matched / total_items * 100, 1) if total_items else 0,
        }
    finally:
        conn.close()
