# -*- coding: utf-8 -*-
"""
功能 4：被盗追踪管理
=====================
保存井盖异常移动数据（位移传感 + 定位上报），支持移动轨迹回放、
最新位置定位追踪，并留存公安联动处置记录（报案/立案/追回全流程）。
"""
import time
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

import database as db
from models import POLICE_STATUSES, PoliceReq, TrackReq

router = APIRouter(prefix="/api/theft", tags=["4.被盗追踪管理"])


def _manhole_or_404(conn, manhole_id):
    row = conn.execute("SELECT * FROM manholes WHERE id=?", (manhole_id,)).fetchone()
    if not row:
        raise HTTPException(404, f"井盖 {manhole_id} 不存在")
    return row


@router.get("/cases", summary="被盗案件列表")
def cases():
    """发生过被盗异动告警的井盖案件（含轨迹点数与公安记录）。"""
    conn = db.get_conn()
    try:
        rows = db.rows_to_list(conn.execute(
            "SELECT a.id alarm_id, a.alarm_code, a.alarm_ts, a.status alarm_status,"
            " m.id manhole_id, m.code, m.location, m.road_name, m.district, m.status,"
            " (SELECT COUNT(*) FROM move_tracks t WHERE t.manhole_id=m.id) track_points,"
            " (SELECT p.case_no FROM police_records p WHERE p.manhole_id=m.id"
            "   ORDER BY p.id DESC LIMIT 1) case_no,"
            " (SELECT p.status FROM police_records p WHERE p.manhole_id=m.id"
            "   ORDER BY p.id DESC LIMIT 1) police_status"
            " FROM alarms a JOIN manholes m ON m.id=a.manhole_id"
            " WHERE a.type='被盗异动' ORDER BY a.alarm_ts DESC"))
        return {"cases": rows, "total": len(rows)}
    finally:
        conn.close()


@router.get("/tracks", summary="异动轨迹回放（按时间排序）")
def tracks(manhole_id: int = Query(...)):
    conn = db.get_conn()
    try:
        m = _manhole_or_404(conn, manhole_id)
        rows = db.rows_to_list(conn.execute(
            "SELECT * FROM move_tracks WHERE manhole_id=? ORDER BY ts", (manhole_id,)))
        return {"manhole": {"id": m["id"], "code": m["code"], "location": m["location"],
                            "lat": m["lat"], "lng": m["lng"], "status": m["status"]},
                "tracks": rows, "total": len(rows)}
    finally:
        conn.close()


@router.post("/tracks", summary="上报异动轨迹点")
def add_track(req: TrackReq):
    ts = req.ts or int(time.time() * 1000)
    conn = db.get_conn()
    try:
        _manhole_or_404(conn, req.manhole_id)
        cur = conn.execute(
            "INSERT INTO move_tracks(manhole_id,ts,lat,lng,speed_kmh,note,created_ts)"
            " VALUES(?,?,?,?,?,?,?)",
            (req.manhole_id, ts, req.lat, req.lng, req.speed_kmh, req.note, ts))
        conn.commit()
        return {"ok": True, "id": cur.lastrowid}
    finally:
        conn.close()


@router.get("/locate/{manhole_id}", summary="最新位置定位追踪")
def locate(manhole_id: int):
    conn = db.get_conn()
    try:
        m = _manhole_or_404(conn, manhole_id)
        last = conn.execute(
            "SELECT * FROM move_tracks WHERE manhole_id=? ORDER BY ts DESC LIMIT 1",
            (manhole_id,)).fetchone()
        if last:
            return {"manhole_id": manhole_id, "code": m["code"], "status": m["status"],
                    "lat": last["lat"], "lng": last["lng"], "ts": last["ts"],
                    "speed_kmh": last["speed_kmh"], "note": last["note"],
                    "source": "轨迹定位"}
        return {"manhole_id": manhole_id, "code": m["code"], "status": m["status"],
                "lat": m["lat"], "lng": m["lng"], "ts": None,
                "speed_kmh": None, "note": None, "source": "档案原位"}
    finally:
        conn.close()


@router.get("/police", summary="公安联动处置记录")
def police_list(manhole_id: Optional[int] = Query(None),
                status: Optional[str] = Query(None)):
    where, args = [], []
    if manhole_id:
        where.append("p.manhole_id=?"); args.append(manhole_id)
    if status:
        where.append("p.status=?"); args.append(status)
    conn = db.get_conn()
    try:
        rows = db.rows_to_list(conn.execute(
            "SELECT p.*, m.code, m.location, m.road_name FROM police_records p"
            " JOIN manholes m ON m.id=p.manhole_id" +
            (" WHERE " + " AND ".join(where) if where else "") +
            " ORDER BY p.report_ts DESC", args))
        return {"records": rows, "total": len(rows)}
    finally:
        conn.close()


@router.post("/police", summary="新增公安联动记录（报案）")
def add_police(req: PoliceReq):
    if req.status not in POLICE_STATUSES:
        raise HTTPException(400, f"状态应为：{'/'.join(POLICE_STATUSES)}")
    conn = db.get_conn()
    try:
        _manhole_or_404(conn, req.manhole_id)
        case_no = req.case_no
        if not case_no:
            n = conn.execute("SELECT COUNT(*) c FROM police_records").fetchone()["c"] + 1
            case_no = f"GA-{time.strftime('%Y%m%d')}-{n:02d}"
        cur = conn.execute(
            "INSERT INTO police_records(case_no,manhole_id,alarm_id,police_unit,contact,"
            "report_ts,status,result,created_ts) VALUES(?,?,?,?,?,?,?,?,?)",
            (case_no, req.manhole_id, req.alarm_id, req.police_unit, req.contact,
             int(time.time() * 1000), req.status, req.result, int(time.time() * 1000)))
        conn.commit()
        return {"ok": True, "id": cur.lastrowid, "case_no": case_no}
    finally:
        conn.close()


@router.put("/police/{record_id}", summary="更新公安处置进展")
def update_police(record_id: int, status: Optional[str] = None, result: Optional[str] = None):
    if status and status not in POLICE_STATUSES:
        raise HTTPException(400, f"状态应为：{'/'.join(POLICE_STATUSES)}")
    conn = db.get_conn()
    try:
        rec = conn.execute("SELECT * FROM police_records WHERE id=?", (record_id,)).fetchone()
        if not rec:
            raise HTTPException(404, f"公安记录 {record_id} 不存在")
        sets, args = [], []
        if status:
            sets.append("status=?"); args.append(status)
            # 追回后井盖状态联动恢复
            if status == "已追回":
                conn.execute("UPDATE manholes SET status='维修中' WHERE id=? AND status='被盗'",
                             (rec["manhole_id"],))
        if result:
            sets.append("result=?"); args.append(result)
        if not sets:
            raise HTTPException(400, "没有需要更新的内容")
        conn.execute(f"UPDATE police_records SET {', '.join(sets)} WHERE id=?",
                     args + [record_id])
        conn.commit()
        return {"ok": True, "id": record_id}
    finally:
        conn.close()
