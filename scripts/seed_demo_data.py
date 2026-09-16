#!/usr/bin/env python3
"""Initialize repeatable defense/demo data without ELK.

The script is intentionally idempotent: it fills an empty feature table but never
overwrites rows that are already present. Existing databases should still be
backed up before running it.
"""

from __future__ import annotations

import json
import math
import random
import sqlite3
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GAS_DB = ROOT / "gas_risk_control" / "gas_risk.db"
PYTHON_ROOT = ROOT / "src" / "python"
NOW_MS = int(time.time() * 1000)
HOUR_MS = 3_600_000
DAY_MS = 24 * HOUR_MS
RNG = random.Random(20260914)


def count(conn: sqlite3.Connection, table: str) -> int:
    return conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]


def seed_gas_risk() -> dict[str, int]:
    sys.path.insert(0, str(ROOT / "gas_risk_control"))
    import database as gas_database  # type: ignore

    gas_database.init_db()
    conn = sqlite3.connect(GAS_DB)
    inserted: dict[str, int] = {}
    try:
        if count(conn, "alarms") == 0:
            rows = []
            messages = [
                (2, "燃气浓度 28.6%LEL，疑似微泄漏"),
                (1, "管内压力 1.16MPa 偏低"),
                (1, "振动 5.8mm/s，检测到施工扰动"),
                (2, "位移 28.4mm，存在地质灾害风险"),
            ]
            for i in range(16):
                level, message = messages[i % len(messages)]
                rows.append((NOW_MS - (16 - i) * 3 * HOUR_MS, i % 7 + 1, level, message))
            conn.executemany(
                "INSERT INTO alarms(ts_ms,sensor_id,level,content) VALUES(?,?,?,?)", rows
            )
            inserted["alarms"] = len(rows)

        if count(conn, "leak_records") == 0:
            rows = []
            for i, position in enumerate((8.2, 15.4, 22.1, 30.6, 38.3, 44.7)):
                method = "concentration" if i % 2 == 0 else "pressure_wave"
                detail = json.dumps(
                    {"source": "答辩演示", "affected_radius_m": 120 + i * 15},
                    ensure_ascii=False,
                )
                rows.append((NOW_MS - (6 - i) * DAY_MS, method, position, 0.86 + i * 0.018, detail))
            conn.executemany(
                "INSERT INTO leak_records(ts_ms,method,position_km,confidence,detail) VALUES(?,?,?,?,?)",
                rows,
            )
            inserted["leak_records"] = len(rows)

        if count(conn, "third_party_events") == 0:
            event_types = ("机械施工振动", "违规开挖", "重型车辆通行", "钻探作业")
            rows = []
            for i in range(12):
                distance = (i % 5) * 1.7 + 0.8
                intensity = 4.0 + i % 7
                score = min(99.0, intensity * 7.2 + max(0, 25 - distance * 3))
                level = "severe" if score >= 80 else "warning" if score >= 55 else "notice"
                rows.append(
                    (
                        NOW_MS - (12 - i) * 6 * HOUR_MS,
                        event_types[i % len(event_types)],
                        round(3.5 + i * 3.4, 1),
                        round(distance, 1),
                        intensity,
                        "管道保护区智能巡检发现的演示事件",
                        level,
                        round(score, 1),
                    )
                )
            conn.executemany(
                "INSERT INTO third_party_events(ts_ms,event_type,location_km,lateral_m,intensity,description,level,score) VALUES(?,?,?,?,?,?,?,?)",
                rows,
            )
            inserted["third_party_events"] = len(rows)

        users = conn.execute("SELECT id,user_type,baseline_m3h FROM gas_users ORDER BY id").fetchall()
        if count(conn, "meter_readings") == 0:
            reading_rows = []
            risk_rows = []
            for step in range(48):
                ts_ms = NOW_MS - (47 - step) * 30 * 60 * 1000
                for user_id, user_type, baseline in users:
                    flow = max(0.02, baseline * RNG.uniform(0.65, 1.35))
                    pressure = RNG.uniform(1.75, 2.35)
                    co_ppm = RNG.uniform(3, 24)
                    flame = 1
                    level = "normal"
                    reasons = ["各项指标正常"]
                    if step in (16, 32) and user_id in (1002, 2002):
                        co_ppm = 86 if user_id == 1002 else 235
                        level = "warning" if co_ppm < 200 else "severe"
                        reasons = [f"CO浓度 {co_ppm:.0f}ppm 超出安全范围"]
                    elif step == 40 and user_id == 1005:
                        flow = max(1.8, baseline * 4.8)
                        level = "severe"
                        reasons = ["流量异常偏大，疑似软管脱落或阀门未关"]
                    reading_rows.append((ts_ms, user_id, flow, pressure, co_ppm, flame, 1))
                    risk_rows.append((ts_ms, user_id, level, json.dumps(reasons, ensure_ascii=False)))
            conn.executemany(
                "INSERT INTO meter_readings(ts_ms,user_id,flow_m3h,pressure_kpa,co_ppm,flame,valve_open) VALUES(?,?,?,?,?,?,?)",
                reading_rows,
            )
            conn.executemany(
                "INSERT INTO user_risk_results(ts_ms,user_id,level,reasons) VALUES(?,?,?,?)",
                risk_rows,
            )
            inserted["meter_readings"] = len(reading_rows)
            inserted["user_risk_results"] = len(risk_rows)

        piles = conn.execute("SELECT id,rated_current_a FROM test_piles ORDER BY id").fetchall()
        if count(conn, "cathodic_data") == 0:
            rows = []
            for step in range(48):
                ts_ms = NOW_MS - (47 - step) * HOUR_MS
                for pile_id, rated_current in piles:
                    off_v = -0.98 + 0.035 * math.sin(step / 5 + pile_id)
                    if pile_id == 3 and 34 <= step <= 39:
                        off_v = -0.76 + RNG.uniform(-0.015, 0.015)
                    on_v = off_v - RNG.uniform(0.08, 0.16)
                    current = rated_current * RNG.uniform(0.78, 0.96)
                    rows.append((ts_ms, pile_id, round(on_v, 3), round(off_v, 3), round(current, 2)))
            conn.executemany(
                "INSERT INTO cathodic_data(ts_ms,pile_id,on_potential_v,off_potential_v,output_current_a) VALUES(?,?,?,?,?)",
                rows,
            )
            inserted["cathodic_data"] = len(rows)

        if count(conn, "emergency_events") == 0:
            event_specs = [
                (15.4, "leak_alarm", "severe", "executed", "V-03", "V-04"),
                (30.6, "manual", "warning", "restored", "V-06", "V-07"),
                (38.3, "leak_alarm", "severe", "planned", "V-07", "V-08"),
            ]
            command_total = 0
            for idx, (position, source, level, status, left, right) in enumerate(event_specs):
                ts_ms = NOW_MS - (3 - idx) * DAY_MS
                steps = [
                    {"seq": 1, "valve_id": left, "action": "close", "delay_s": 0},
                    {"seq": 2, "valve_id": right, "action": "close", "delay_s": 10},
                ]
                lo = math.floor(position / 5) * 5
                hi = math.ceil(position / 5) * 5
                plan = {
                    "steps": steps,
                    "isolation_segment": {
                        "from_km": lo,
                        "to_km": hi,
                        "length_km": hi - lo,
                        "affected_users_estimate": (hi - lo) * 120,
                        "valves_closed": [left, right],
                    },
                }
                isolation = None
                if status in ("executed", "restored"):
                    isolation = json.dumps(
                        {**plan["isolation_segment"], "result": "隔离完成，风险已受控"},
                        ensure_ascii=False,
                    )
                cur = conn.execute(
                    "INSERT INTO emergency_events(ts_ms,position_km,source,level,status,plan,isolation) VALUES(?,?,?,?,?,?,?)",
                    (ts_ms, position, source, level, status, json.dumps(plan, ensure_ascii=False), isolation),
                )
                for step in steps:
                    conn.execute(
                        "INSERT INTO valve_commands(ts_ms,event_id,valve_id,seq,action,delay_s,executed) VALUES(?,?,?,?,?,?,?)",
                        (ts_ms, cur.lastrowid, step["valve_id"], step["seq"], "close", step["delay_s"], 0 if status == "planned" else 1),
                    )
                    command_total += 1
            inserted["emergency_events"] = len(event_specs)
            inserted["valve_commands"] = command_total

        conn.commit()
    finally:
        conn.close()
    return inserted


def initialize_platform() -> Path:
    sys.path.insert(0, str(PYTHON_ROOT))
    from persistence import DB_PATH, init_db  # type: ignore
    from auth import seed_rbac  # type: ignore

    init_db()
    seed_rbac()
    # Importing the simulators invokes their existing idempotent seed loaders.
    import workorder.simulator  # noqa: F401
    import plan_api.simulator  # noqa: F401
    import data_governance.simulator  # noqa: F401
    import hazmat_transport.simulator  # noqa: F401
    import asset_cost.simulator  # noqa: F401
    path = Path(DB_PATH)
    seed_platform_activity(path)
    return path


def seed_platform_activity(path: Path) -> None:
    """Fill activity/history tables that the built-in master-data seeds leave empty."""
    conn = sqlite3.connect(path)
    try:
        now_text = time.strftime("%Y-%m-%d %H:%M:%S")
        if count(conn, "wo_dispatch_logs") == 0:
            orders = conn.execute(
                "SELECT order_id,assignee_id,assignee,created_at FROM wo_orders "
                "WHERE assignee_id IS NOT NULL LIMIT 10"
            ).fetchall()
            conn.executemany(
                "INSERT INTO wo_dispatch_logs(order_id,staff_id,staff_name,dispatched_at,method) VALUES(?,?,?,?,?)",
                [(o, sid, name, created or now_text, "智能派单") for o, sid, name, created in orders],
            )

        if count(conn, "ep_activations") == 0:
            plans = conn.execute(
                "SELECT plan_id,plan_name,category FROM ep_plans ORDER BY priority LIMIT 3"
            ).fetchall()
            for i, (plan_id, plan_name, category) in enumerate(plans, 1):
                activation_id = f"ACT-DEMO-{i:03d}"
                status = ("已完成", "执行中", "待启动")[i - 1]
                conn.execute(
                    "INSERT INTO ep_activations(activation_id,plan_id,plan_name,category,category_name,trigger,alarm_id,status,activated_at,finished_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (activation_id, plan_id, plan_name, category, "应急处置", "答辩演示告警自动匹配", f"ALM-DEMO-{i:03d}", status, now_text, now_text if i == 1 else None),
                )
                nodes = conn.execute(
                    "SELECT node_id,title,node_type FROM ep_flow_nodes WHERE plan_id=? ORDER BY seq LIMIT 4",
                    (plan_id,),
                ).fetchall()
                conn.executemany(
                    "INSERT INTO ep_activation_nodes(activation_id,node_id,title,node_type,status,finished_at) VALUES(?,?,?,?,?,?)",
                    [(activation_id, nid, title, ntype, "已完成" if i == 1 else "执行中" if j == 0 else "待执行", now_text if i == 1 else None) for j, (nid, title, ntype) in enumerate(nodes)],
                )

        if count(conn, "ep_live_matches") == 0:
            plan = conn.execute("SELECT plan_id,plan_name,category FROM ep_plans LIMIT 1").fetchone()
            if plan:
                best = {"plan_id": plan[0], "plan_name": plan[1], "score": 96, "reason": "风险类型和区域高度匹配"}
                alarm = {"alarm_id": "ALM-DEMO-001", "title": "燃气舱甲烷浓度严重超限", "level": 2, "location": "GS-Z03"}
                conn.execute(
                    "INSERT INTO ep_live_matches(match_id,time,alarm_id,alarm,category,category_name,best,candidates,fallback,fallback_message,auto_acked) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    ("MATCH-DEMO-001", now_text, "ALM-DEMO-001", json.dumps(alarm, ensure_ascii=False), plan[2], "燃气泄漏", json.dumps(best, ensure_ascii=False), json.dumps([best], ensure_ascii=False), 0, None, 1),
                )
                conn.execute(
                    "INSERT OR IGNORE INTO ep_matched_alarms(alarm_id,matched_at) VALUES(?,?)",
                    ("ALM-DEMO-001", now_text),
                )

        if count(conn, "tunnel_pipelines") == 0:
            pipeline_rows = []
            types = (("供水", "生活给水", 600, "球墨铸铁"), ("燃气", "天然气", 400, "无缝钢管"), ("电力", "10kV电缆", 180, "交联聚乙烯"), ("通信", "通信光缆", 80, "PE护套"))
            cabins = (("EL", "电力舱"), ("GS", "燃气舱"), ("WS", "水信舱"))
            for i in range(12):
                cabin, cabin_name = cabins[i % 3]
                ptype, medium, diameter, material = types[i % 4]
                zone = i % 6 + 1
                pipeline_rows.append((f"PL-DEMO-{i+1:03d}", cabin, cabin_name, zone, f"Z{zone:02d}", ptype, medium, diameter, material, "2021-06-01", "2021-09-01", "安塞市政设备公司", 1.6, 30, "maintenance" if i == 7 else "normal", 90, "2026-08-20", "2026-11-18", now_text))
            conn.executemany(
                "INSERT INTO tunnel_pipelines(pipeline_id,cabin,cabin_name,zone_code,zone,pipeline_type,medium,diameter_mm,material,install_date,commission_date,manufacturer,pressure_rating,design_life,status,inspection_interval_days,last_inspection,next_inspection,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                pipeline_rows,
            )

        if count(conn, "tunnel_alarms") < 12:
            alarm_rows = []
            metrics = (("ch4", "甲烷浓度", 1.3, "%VOL"), ("temperature", "温度", 43.5, "℃"), ("water_level", "积水液位", 128.0, "mm"), ("co", "一氧化碳", 31.0, "ppm"))
            for i in range(12):
                metric, metric_name, value, unit = metrics[i % 4]
                level = 2 if i % 5 == 0 else 1
                alarm_rows.append((f"TA-DEMO-{i+1:03d}", f"GL-GS{i%6+1:02d}-01", "sensor", ("GS", "EL", "WS")[i % 3], f"Z{i%6+1:02d}", metric, metric_name, value + i / 10, unit, level, "严重" if level == 2 else "预警", 51000 + i, f"{metric_name}超过安全阈值", "已处理" if i < 5 else "未处理", now_text if i < 5 else None, now_text))
            conn.executemany(
                "INSERT OR IGNORE INTO tunnel_alarms(alarm_id,source_id,source_type,cabin,zone_code,metric,metric_name,value,unit,level,severity,alarm_code,desc,status,ack_time,time) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                alarm_rows,
            )

        if count(conn, "tunnel_access_records") == 0:
            conn.executemany(
                "INSERT INTO tunnel_access_records(record_id,gate_id,gate_name,location,direction,person_id,person_name,authorized,time) VALUES(?,?,?,?,?,?,?,?,?)",
                [(f"AR-DEMO-{i+1:03d}", f"GATE-{i%4+1:02d}", f"{i%4+1}号门禁", f"综合管廊Z{i%6+1:02d}入口", "进" if i % 2 == 0 else "出", f"P-{100+i}", ("张巡检", "李维护", "王安全", "赵值班")[i % 4], 0 if i == 9 else 1, now_text) for i in range(16)],
            )

        if count(conn, "hazmat_emergency_logs") == 0:
            conn.executemany(
                "INSERT INTO hazmat_emergency_logs(log_id,route_id,leak_location,severity,valves_closed,total_response_time_sec,executed_at) VALUES(?,?,?,?,?,?,?)",
                [("HZ-EMG-001", "RT-001", "泵站P1出口", "high", 3, 8.6, now_text), ("HZ-EMG-002", "RT-003", "C厂输送支线", "medium", 2, 6.2, now_text), ("HZ-EMG-003", "RT-005", "泵站P10入口", "low", 2, 5.4, now_text)],
            )
        conn.commit()
    finally:
        conn.close()


def summarize_db(path: Path) -> dict[str, int]:
    conn = sqlite3.connect(path)
    try:
        tables = [
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        ]
        return {table: count(conn, table) for table in tables}
    finally:
        conn.close()


def main() -> None:
    gas_inserted = seed_gas_risk()
    platform_db = initialize_platform()
    print(json.dumps({
        "gas_risk_inserted": gas_inserted,
        "gas_risk_counts": summarize_db(GAS_DB),
        "platform_db": str(platform_db),
        "platform_counts": summarize_db(platform_db),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
