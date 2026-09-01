# -*- coding: utf-8 -*-
"""
功能 1：实时安全监测
====================
燃气浓度、压力、流量、振动、腐蚀速率、位移六类指标的毫秒级数据
监测接口：测点列表、实时最新值、历史曲线、报警记录、外部上报、故障注入。
"""
import time

from fastapi import APIRouter, HTTPException, Query

import database as db
import simulator
from models import FaultInjectReq, SensorDataReport

router = APIRouter(prefix="/api/monitoring", tags=["1.实时安全监测"])

_FIELDS = ("concentration_ppm", "pressure_mpa", "flow_m3h",
           "vibration_mms", "corrosion_mma", "displacement_mm")


@router.get("/sensors", summary="监测站列表")
def list_sensors():
    """返回全部监测站（集成传感器）的桩号与状态。"""
    conn = db.get_conn()
    try:
        return db.rows_to_list(conn.execute("SELECT * FROM sensors ORDER BY position_km"))
    finally:
        conn.close()


@router.get("/realtime", summary="实时最新数据（全部测站）")
def realtime(sensor_id: int = Query(None, description="仅查指定测站")):
    """
    每个测站最新一帧毫秒级数据，并附带 %LEL（爆炸下限百分比）与报警级别。
    数据由模拟线程每秒写入，前端每 2~3 秒轮询即可呈现实时效果。
    """
    conn = db.get_conn()
    try:
        sql = ("SELECT m.*, s.name, s.position_km FROM monitoring_data m "
               "JOIN (SELECT sensor_id, MAX(ts_ms) mx FROM monitoring_data GROUP BY sensor_id) t "
               "ON m.sensor_id=t.sensor_id AND m.ts_ms=t.mx "
               "JOIN sensors s ON s.id=m.sensor_id")
        if sensor_id is not None:
            sql += f" WHERE m.sensor_id={int(sensor_id)}"
        rows = db.rows_to_list(conn.execute(sql + " ORDER BY s.position_km"))
        for r in rows:
            # %LEL = ppm / 50000 * 100（甲烷 LEL=5%VOL=50000ppm）
            r["lel_pct"] = round(r["concentration_ppm"] / simulator.LEL_PPM * 100, 3)
            level, content = simulator.evaluate_alarm({"position_km": r["position_km"]}, r)
            r["alarm_level"], r["alarm_content"] = level, content
        return {"ts_ms": int(time.time() * 1000), "faults": simulator.current_faults(), "data": rows}
    finally:
        conn.close()


@router.get("/history", summary="历史曲线数据")
def history(sensor_id: int = Query(..., description="测站编号"),
            minutes: int = Query(15, ge=1, le=240, description="回溯分钟数")):
    """返回指定测站最近 N 分钟的全部测点，供前端绘制实时趋势曲线。"""
    conn = db.get_conn()
    try:
        since = int(time.time() * 1000) - minutes * 60000
        rows = db.rows_to_list(conn.execute(
            "SELECT ts_ms,concentration_ppm,pressure_mpa,flow_m3h,vibration_mms,"
            "corrosion_mma,displacement_mm FROM monitoring_data "
            "WHERE sensor_id=? AND ts_ms>=? ORDER BY ts_ms", (sensor_id, since)))
        for r in rows:
            r["lel_pct"] = round(r["concentration_ppm"] / simulator.LEL_PPM * 100, 3)
        return {"sensor_id": sensor_id, "minutes": minutes, "points": rows}
    finally:
        conn.close()


@router.get("/alarms", summary="实时报警记录")
def alarms(limit: int = Query(30, ge=1, le=200, description="返回条数")):
    """最近报警（按时间倒序），含报警级别与测站名。"""
    conn = db.get_conn()
    try:
        rows = db.rows_to_list(conn.execute(
            "SELECT a.*, s.name sensor_name FROM alarms a "
            "LEFT JOIN sensors s ON s.id=a.sensor_id ORDER BY a.ts_ms DESC LIMIT ?", (limit,)))
        return {"alarms": rows}
    finally:
        conn.close()


@router.post("/data", summary="外部数据上报（毫秒级）")
def report_data(item: SensorDataReport):
    """
    供外部 SCADA/网关上报一帧数据。真实项目中此接口由 IoT 平台高频调用，
    演示环境由后台模拟线程代替。上报后立即做阈值报警评估。
    """
    ts = item.ts_ms or int(time.time() * 1000)
    conn = db.get_conn()
    try:
        sensor = conn.execute("SELECT * FROM sensors WHERE id=?", (item.sensor_id,)).fetchone()
        if not sensor:
            raise HTTPException(404, f"测站 {item.sensor_id} 不存在")
        conn.execute(
            "INSERT INTO monitoring_data(sensor_id,ts_ms,concentration_ppm,pressure_mpa,"
            "flow_m3h,vibration_mms,corrosion_mma,displacement_mm) VALUES(?,?,?,?,?,?,?,?)",
            (item.sensor_id, ts, item.concentration_ppm, item.pressure_mpa, item.flow_m3h,
             item.vibration_mms, item.corrosion_mma, item.displacement_mm))
        level, content = simulator.evaluate_alarm(dict(sensor), item.model_dump())
        if level > 0:
            conn.execute("INSERT INTO alarms(ts_ms,sensor_id,level,content) VALUES(?,?,?,?)",
                         (ts, item.sensor_id, level, content))
        conn.commit()
        return {"ok": True, "ts_ms": ts, "alarm_level": level, "alarm_content": content}
    finally:
        conn.close()


@router.post("/simulate-leak", summary="注入泄漏故障（演示）")
def simulate_leak(req: FaultInjectReq):
    """向指定测站注入泄漏：浓度陡升、压力下降，可触发报警→定位→应急联动完整流程。"""
    simulator.set_leak(req.sensor_id, req.magnitude)
    return {"ok": True, "msg": f"已向 {req.sensor_id}#测站注入强度 {req.magnitude} 的泄漏"}


@router.post("/simulate-disturbance", summary="注入第三方施工振动（演示）")
def simulate_disturbance(req: FaultInjectReq):
    """向指定测站注入第三方施工振动扰动。"""
    simulator.set_third_party_disturbance(req.sensor_id, req.magnitude)
    return {"ok": True, "msg": f"已向 {req.sensor_id}#测站注入强度 {req.magnitude} 的施工振动"}


@router.post("/clear-faults", summary="清除全部注入故障（演示）")
def clear_faults():
    simulator.clear_faults()
    return {"ok": True, "msg": "已恢复正常工况"}
