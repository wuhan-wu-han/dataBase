# -*- coding: utf-8 -*-
"""
确定性演示数据：
  - 12 处井盖档案（一井一档，5 区域 / 5 类型）
  - 36 期多维监测数据（12 井盖 × 3 期，其中 7 期异常）
  - 7 条告警 + 7 张工单（覆盖 待派发/已派发/处置中/已核验/已闭环 全阶段）
  - 1 起被盗事件：6 个异动轨迹点 + 公安联动记录
  - 10 张防坠网（含破损/维修/更换状态）+ 6 条运维记录
  - 8 条井盖维修更换履历
合计 90+ 条业务数据。
"""
import time

import database as db
from models import check_monitor

DISTRICTS = ["城东区", "城西区", "城南区", "城北区", "高新区"]
OWNERS = ["市政管理处", "水务集团", "排水公司", "供电公司", "电信运营商"]
BASE_LAT, BASE_LNG = 30.5200, 114.3500

# (位置, 道路, 区域, 类型, 权属, 材质, 安装日期)
_MANHOLES = [
    ("建设大道 12# 路灯旁", "建设大道", "城东区", "雨水", "市政管理处", "球墨铸铁", "2023-04-12"),
    ("建设大道与青华街交叉口", "建设大道", "城东区", "污水", "排水公司", "球墨铸铁", "2022-09-03"),
    ("滨河路 8# 公交站台", "滨河路", "城西区", "雨水", "市政管理处", "复合材料", "2024-01-20"),
    ("环城北路高架桥墩 B2", "环城北路", "城西区", "通信", "电信运营商", "钢纤维混凝土", "2021-11-08"),
    ("龙腾大道辅道 K3+210", "龙腾大道", "城南区", "雨水", "市政管理处", "球墨铸铁", "2023-06-15"),
    ("科技园路地铁 2 号口", "科技园路", "城南区", "电力", "供电公司", "复合材料", "2024-03-02"),
    ("中山路 45# 门店前", "中山路", "城北区", "污水", "排水公司", "球墨铸铁", "2022-05-19"),
    ("解放路人行横道东侧", "解放路", "城北区", "雨水", "市政管理处", "钢纤维混凝土", "2023-10-11"),
    ("青华街 8 号院门口", "青华街", "高新区", "污水", "排水公司", "球墨铸铁", "2021-07-27"),
    ("迎宾大道绿化带 K1+500", "迎宾大道", "高新区", "通信", "电信运营商", "复合材料", "2024-05-06"),
    ("文昌路小学段人行道", "文昌路", "高新区", "雨水", "市政管理处", "球墨铸铁", "2023-02-14"),
    ("科技园路西段检修井", "科技园路", "城南区", "燃气", "市政管理处", "球墨铸铁", "2022-12-01"),
]

# 最新一期异常画像：井盖序号 → 异常监测值（其余井盖为正常值）
_PROFILES = {
    2: {"displacement_mm": 12.5},
    3: {"tilt_deg": 18.5},
    5: {"damage": "破损"},
    6: {"damage": "轻微裂缝"},
    7: {"gas_ppm": 15.2},
    9: {"displacement_mm": 85.0},
    11: {"water_level_cm": 95.0},
}

# 告警/工单所处闭环阶段：井盖序号 → 阶段
_STAGES = {2: "已闭环", 3: "已核验", 5: "处置中", 6: "已派发",
           7: "待派发", 9: "处置中", 11: "已派发"}
_HANDLE = {"被盗异动": "公安报案", "有毒气体告警": "现场核查", "井盖破损": "更换"}
_ASSIGNEE = {2: "抢修一班", 3: "抢修二班", 5: "市政抢修班", 6: "抢修三班",
             7: None, 9: "抢修二班", 11: "抢修一班"}

# 防坠网：井盖序号 → (状态, 材质, 承载kg)；未列出的为默认已安装
_NETS = {1: ("已安装", "聚乙烯", 150), 2: ("已安装", "尼龙", 200),
         3: ("已安装", "聚乙烯", 150), 4: ("破损", "尼龙", 200),
         5: ("已安装", "不锈钢", 300), 6: ("已维修", "聚乙烯", 150),
         7: ("已安装", "尼龙", 200), 8: ("已更换", "不锈钢", 300),
         9: ("已安装", "聚乙烯", 150), 10: ("已安装", "尼龙", 200)}
_NET_MAINTAINS = [
    (4, "破损登记", "2026-08-15", "巡查发现网体两处断裂", "王巡"),
    (6, "破损登记", "2026-07-02", "网绳磨损超限", "王巡"),
    (6, "维修", "2026-07-06", "更换磨损网绳，复检合格", "李修"),
    (8, "破损登记", "2026-06-20", "整体老化脆裂", "赵巡"),
    (8, "更换", "2026-06-24", "更换不锈钢防坠网，承载 300kg", "市政抢修班"),
    (4, "维修", "2026-08-28", "断裂处补接并加装卡扣", "李修"),
]

_REPAIRS = [
    (1, "维修", "2026-05-12", "井盖松动异响", "加装减震胶垫", 300, "抢修一班"),
    (2, "更换", "2026-08-25", "位移导致盖体变形", "更换球墨铸铁井盖", 1200, "抢修二班"),
    (3, "维修", "2026-07-02", "边缘破损", "修补焊接加固", 450, "抢修一班"),
    (5, "更换", "2026-06-18", "盖体破裂", "更换复合材料井盖", 980, "市政抢修班"),
    (7, "维修", "2026-04-30", "铰链松动", "更换铰链组件", 260, "抢修三班"),
    (9, "更换", "2026-03-22", "被盗后追回", "补装防盗型井盖", 1500, "抢修二班"),
    (10, "维修", "2026-08-08", "轻微裂缝", "裂缝封闭处理", 180, "抢修一班"),
    (12, "维修", "2026-07-27", "盖面磨损", "防滑纹补强", 220, "市政抢修班"),
]

DAY = 86400_000
HOUR = 3600_000


def seed() -> None:
    conn = db.get_conn()
    try:
        if conn.execute("SELECT COUNT(*) c FROM manholes").fetchone()["c"]:
            return  # 已播种，幂等返回
        now = int(time.time() * 1000)
        day = time.strftime("%Y%m%d")

        # ---- 1. 井盖档案 ----
        for i, (loc, road, dist, mtype, owner, mat, idate) in enumerate(_MANHOLES, 1):
            conn.execute(
                "INSERT INTO manholes(code,location,road_name,district,type,owner_unit,material,"
                "install_date,lat,lng,status,remark,created_ts) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (f"JG-2026-{i:03d}", loc, road, dist, mtype, owner, mat, idate,
                 round(BASE_LAT + 0.004 * i, 4), round(BASE_LNG + 0.006 * i, 4),
                 "正常", None, now - 60 * DAY))

        # ---- 2. 监测数据（每井盖 3 期）----
        abnormal_latest = {}
        for i in range(1, 13):
            for k, off in enumerate((2 * DAY, DAY, 2 * HOUR)):
                base = {"tilt_deg": round(1.0 + 0.15 * i, 1), "displacement_mm": round(0.5 + 0.1 * i, 1),
                        "damage": "完好", "water_level_cm": round(25 + 2 * i, 1),
                        "gas_ppm": round(1.0 + 0.1 * i, 1)}
                if k == 2 and i in _PROFILES:
                    base.update(_PROFILES[i])
                    abnormal_latest[i] = base
                conn.execute(
                    "INSERT INTO monitor_data(manhole_id,ts,tilt_deg,displacement_mm,damage,"
                    "water_level_cm,gas_ppm,is_abnormal,created_ts) VALUES(?,?,?,?,?,?,?,?,?)",
                    (i, now - off, base["tilt_deg"], base["displacement_mm"], base["damage"],
                     base["water_level_cm"], base["gas_ppm"],
                     1 if k == 2 and i in _PROFILES else 0, now - off))

        # ---- 3. 告警 + 工单（按闭环阶段展开）----
        seq = 0
        for i, values in sorted(abnormal_latest.items()):
            hits = check_monitor(values["tilt_deg"], values["displacement_mm"],
                                 values["damage"], values["water_level_cm"], values["gas_ppm"])
            stage = _STAGES[i]
            for h in hits:
                seq += 1
                alarm_status = {"待派发": "待派发", "已派发": "已派发", "处置中": "处置中",
                                "已核验": "已核验", "已闭环": "已闭环"}[stage]
                alarm_ts = now - 2 * HOUR
                conn.execute(
                    "INSERT INTO alarms(alarm_code,manhole_id,type,level,detail,alarm_ts,status,created_ts)"
                    " VALUES(?,?,?,?,?,?,?,?)",
                    (f"GJ-{day}-{seq:02d}", i, h["type"], h["level"], h["detail"],
                     alarm_ts, alarm_status, alarm_ts))
                alarm_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

                # 井盖状态联动
                if h["type"] == "被盗异动":
                    m_status = "被盗"
                elif stage == "已闭环":
                    m_status = "正常"
                elif stage == "待派发":
                    m_status = "告警"
                else:
                    m_status = "处置中"
                conn.execute("UPDATE manholes SET status=? WHERE id=?", (m_status, i))

                order_status = {"待派发": "待派发", "已派发": "处置中", "处置中": "待核验",
                                "已核验": "已核验", "已闭环": "已闭环"}[stage]
                handle = _HANDLE.get(h["type"], "维修")
                assignee = _ASSIGNEE.get(i)
                dispatch_ts = alarm_ts + HOUR if order_status != "待派发" else None
                report_info, report_ts = None, None
                verify_result, verify_ts = None, None
                close_ts = None
                if order_status in ("待核验", "已核验", "已闭环"):
                    report_info = {"被盗异动": "现场核查确认井盖缺失，已联动公安报案并设置围挡",
                                   }.get(h["type"], "现场完成处置，隐患排除，申请核验")
                    report_ts = alarm_ts + 5 * HOUR
                if order_status in ("已核验", "已闭环"):
                    verify_result = "整改合格，现场复核通过"
                    verify_ts = alarm_ts + 8 * HOUR
                if order_status == "已闭环":
                    close_ts = alarm_ts + 9 * HOUR
                conn.execute(
                    "INSERT INTO work_orders(order_code,alarm_id,manhole_id,handle_type,assignee,"
                    "dispatch_ts,status,report_info,report_ts,verify_result,verify_ts,close_ts,created_ts)"
                    " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (f"GD-{day}-{seq:02d}", alarm_id, i, handle, assignee, dispatch_ts,
                     order_status, report_info, report_ts, verify_result, verify_ts,
                     close_ts, alarm_ts))

                # ---- 4. 被盗事件：轨迹 + 公安联动 ----
                if h["type"] == "被盗异动":
                    lat = conn.execute("SELECT lat,lng FROM manholes WHERE id=?",
                                       (i,)).fetchone()
                    lat0, lng0 = lat["lat"], lat["lng"]
                    notes = ["异动起点（原位偏移）", "沿青华街向北移动", "进入文昌路",
                             "货车车厢疑似装载", "停靠废品回收站", "轨迹终点（定位锁定）"]
                    for k, note in enumerate(notes):
                        conn.execute(
                            "INSERT INTO move_tracks(manhole_id,ts,lat,lng,speed_kmh,note,created_ts)"
                            " VALUES(?,?,?,?,?,?,?)",
                            (i, alarm_ts + k * 20 * 60000,
                             round(lat0 + 0.0018 * k, 5), round(lng0 + 0.0026 * k, 5),
                             round(18 + 6 * k, 1), note, alarm_ts + k * 20 * 60000))
                    conn.execute(
                        "INSERT INTO police_records(case_no,manhole_id,alarm_id,police_unit,contact,"
                        "report_ts,status,result,created_ts) VALUES(?,?,?,?,?,?,?,?,?)",
                        (f"GA-{day}-{seq:02d}", i, alarm_id, "高新区分局刑侦大队",
                         "刘警官 027-8866xxxx", alarm_ts + 3 * HOUR, "已立案",
                         "已调取沿线监控，锁定嫌疑车辆", alarm_ts + 3 * HOUR))

        # ---- 5. 防坠网台账 ----
        for mid, (nstat, mat, load) in sorted(_NETS.items()):
            conn.execute(
                "INSERT INTO safety_nets(net_code,manhole_id,install_date,material,load_kg,"
                "net_status,last_check,next_check,repair_count,remark,created_ts)"
                " VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (f"FZ-2026-{mid:03d}", mid, "2026-05-10", mat, load, nstat,
                 "2026-08-20", "2026-11-20",
                 1 if nstat in ("已维修", "已更换") else 0,
                 None if nstat == "已安装" else f"{nstat}，待复查", now - 30 * DAY))
        for net_mid, mtype, mdate, detail, op in _NET_MAINTAINS:
            net_id = conn.execute("SELECT id FROM safety_nets WHERE manhole_id=?",
                                  (net_mid,)).fetchone()["id"]
            conn.execute(
                "INSERT INTO net_maintains(net_id,type,date,detail,operator,created_ts)"
                " VALUES(?,?,?,?,?,?)", (net_id, mtype, mdate, detail, op, now - 20 * DAY))

        # ---- 6. 维修更换履历 ----
        for mid, rtype, rdate, reason, detail, cost, op in _REPAIRS:
            conn.execute(
                "INSERT INTO repair_history(manhole_id,type,date,reason,detail,cost,operator,created_ts)"
                " VALUES(?,?,?,?,?,?,?,?)", (mid, rtype, rdate, reason, detail, cost, op,
                                              now - 15 * DAY))

        conn.commit()
    finally:
        conn.close()
