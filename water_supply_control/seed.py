# -*- coding: utf-8 -*-
"""供水管网精细化管控子模块 — 模拟数据播种（可重复执行，先清空再写入）"""
import os
import random
import time

from database import DB_PATH, get_conn, init_db

random.seed(42)

DAY = 86400000
NOW = int(time.time() * 1000)


def ts(days_ago, hour=9, minute=30):
    t = time.localtime(NOW / 1000 - days_ago * 86400)
    return int(time.mktime((t.tm_year, t.tm_mon, t.tm_mday, hour, minute, 0, 0, 0, -1)) * 1000)


def date_str(days_ago):
    return time.strftime("%Y-%m-%d", time.localtime(NOW / 1000 - days_ago * 86400))


PIPES = [
    ("PIPE001", "建设大道DN600主干管", "球墨铸铁", 600, 2400, "江汉区", "建设大道", 22.5, "2003-06-12"),
    ("PIPE002", "中山路DN400配水管", "灰铸铁", 400, 1800, "江汉区", "中山路", 24.0, "1998-04-20"),
    ("PIPE003", "滨江路DN800输水干管", "钢管", 800, 3200, "江岸区", "滨江路", 19.8, "2010-09-01"),
    ("PIPE004", "解放大道DN500主干管", "球墨铸铁", 500, 2600, "江岸区", "解放大道", 23.2, "2006-11-15"),
    ("PIPE005", "新华路DN300配水管", "灰铸铁", 300, 1200, "江汉区", "新华路", 25.1, "1995-07-08"),
    ("PIPE006", "二七路DN400配水管", "预应力砼", 400, 1500, "江岸区", "二七路", 21.6, "1992-03-25"),
    ("PIPE007", "青年路DN600主干管", "球墨铸铁", 600, 2100, "硚口区", "青年路", 26.4, "2012-05-18"),
    ("PIPE008", "武胜路DN300配水管", "PE", 300, 900, "硚口区", "武胜路", 27.0, "2018-08-30"),
    ("PIPE009", "汉阳大道DN500主干管", "球墨铸铁", 500, 2300, "汉阳区", "汉阳大道", 20.4, "2008-10-22"),
    ("PIPE010", "鹦鹉大道DN400配水管", "灰铸铁", 400, 1600, "汉阳区", "鹦鹉大道", 21.0, "1999-12-05"),
]

QUALITY_NODES = [
    ("QN01", "白鹤嘴水厂出厂水", "水厂", 1, None),
    ("QN02", "宗关泵站出水", "泵站", 2, 7),
    ("QN03", "建设大道管网水", "管网", 3, 1),
    ("QN04", "中山路管网水", "管网", 4, 2),
    ("QN05", "滨江路管网水", "管网", 5, 3),
    ("QN06", "阳光小区二次供水", "二次供水", 6, 1),
    ("QN07", "汉阳大道管网水", "管网", 7, 9),
    ("QN08", "终端用户龙头水", "终端用户", 8, 5),
]

STATIONS = [
    ("PS01", "宗关加压泵站", "硚口区", 32.0, 3, 0.42, 1200),
    ("PS02", "二七路加压泵站", "江岸区", 28.5, 2, 0.38, 900),
    ("PS03", "汉阳高区泵站", "汉阳区", 35.0, 3, 0.45, 1100),
    ("PS04", "青年路泵站", "硚口区", 30.0, 2, 0.36, 800),
]

DMAS = [
    ("DMA01", "江汉北片计量区", "江汉区", 26, 8600, 320, 6.5),
    ("DMA02", "江汉南片计量区", "江汉区", 22, 7200, 280, 9.8),
    ("DMA03", "江岸沿江计量区", "江岸区", 30, 9800, 410, 7.2),
    ("DMA04", "江岸二七计量区", "江岸区", 18, 5600, 230, 14.6),
    ("DMA05", "硚口宗关计量区", "硚口区", 24, 8100, 300, 8.4),
    ("DMA06", "汉阳钟家村计量区", "汉阳区", 21, 6900, 260, 11.2),
]

SECONDS = [
    ("SEC01", "阳光小区二次供水", "江汉区", 2),
    ("SEC02", "金色雅园二次供水", "江汉区", 2),
    ("SEC03", "百步亭花园二次供水", "江岸区", 3),
    ("SEC04", "汉口春天二次供水", "硚口区", 2),
    ("SEC05", "世贸锦绣长江二次供水", "汉阳区", 2),
    ("SEC06", "福星惠誉二次供水", "江岸区", 1),
]

HYDRANTS = [
    ("XH0001", "建设大道与新华路交叉口东50m", "建设大道", "江汉区", 1),
    ("XH0002", "中山路协和医院门前", "中山路", "江汉区", 2),
    ("XH0003", "滨江路江滩公园西门", "滨江路", "江岸区", 3),
    ("XH0004", "解放大道二七纪念馆旁", "解放大道", "江岸区", 4),
    ("XH0005", "新华路菜市场北侧", "新华路", "江汉区", 5),
    ("XH0006", "二七路头道街口", "二七路", "江岸区", 6),
    ("XH0007", "青年路机场河桥边", "青年路", "硚口区", 7),
    ("XH0008", "武胜路凯德广场东侧", "武胜路", "硚口区", 8),
    ("XH0009", "汉阳大道钟家村站台", "汉阳大道", "汉阳区", 9),
    ("XH0010", "鹦鹉大道拦江路口", "鹦鹉大道", "汉阳区", 10),
]


def seed():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
    conn = get_conn()

    # ---- 管道 ----
    for code, name, mat, dia, ln, dist, road, elev, lay in PIPES:
        conn.execute(
            "INSERT INTO pipe(code,name,material,diameter_mm,length_m,district,road_name,"
            "terrain_elev_m,lay_date,status) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (code, name, mat, dia, ln, dist, road, elev, lay, "正常"))

    # ---- 监测记录：每管6条（近6天） ----
    for pid in range(1, 11):
        for d in range(6):
            pr = round(random.uniform(0.18, 0.55), 2)
            ab = []
            if pid == 2 and d == 0:
                pr = 0.62; ab.append("高压")
            if pid == 5 and d == 0:
                pr = 0.12; ab.append("低压")
            turb = round(random.uniform(0.2, 0.8), 2)
            rcl = round(random.uniform(0.08, 0.3), 2)
            if pid == 6 and d == 0:
                turb = 1.6; ab.append("浊度")
            conn.execute(
                "INSERT INTO monitor_record(pipe_id,ts,pressure_mpa,flow_m3h,level_cm,"
                "turbidity_ntu,residual_cl,deformation_mm,is_abnormal) VALUES (?,?,?,?,?,?,?,?,?)",
                (pid, ts(d, random.randint(8, 18)), pr, round(random.uniform(120, 600), 1),
                 round(random.uniform(40, 90), 1), turb, rcl,
                 round(random.uniform(0.5, 6.5) if pid == 2 else random.uniform(0.3, 3), 1),
                 1 if ab else 0))

    # ---- 告警 ----
    alarms = [
        (1, "管网", "高压告警", "高", "管道压力0.62MPa，超安全上限0.6MPa，存在爆管隐患", 0, "待处理"),
        (5, "管网", "低压告警", "中", "管道压力0.12MPa，低于服务下限0.15MPa", 0, "待处理"),
        (6, "管网", "浊度超标", "中", "浊度1.6NTU，超国标1NTU", 0, "待处理"),
        (2, "管网", "管道形变", "高", "管道形变6.2mm，超阈值5mm", 1, "待处理"),
        (None, "DMA分区", "漏损告警", "高", "DMA04漏损率14.6%超管控线12%，疑似暗漏", 1, "待处理"),
        (None, "二次供水", "二供告警", "高", "百步亭花园水箱液位15%过低，存在断水风险", 2, "待处理"),
        (3, "消防栓", "消防栓告警", "中", "出水流量32L/s异常偏大，疑似盗用消防用水", 2, "已处理"),
        (4, "管网", "低压告警", "中", "管道压力0.14MPa，低于服务下限0.15MPa", 3, "已处理"),
        (None, "水质溯源", "余氯不足", "中", "余氯0.03mg/L低于国标0.05mg/L；疑似问题管段：中山路DN400配水管(PIPE002)", 3, "已处理"),
        (7, "管网", "高压告警", "高", "管道压力0.61MPa，超安全上限0.6MPa", 4, "已处理"),
    ]
    for i, (pid, src, atype, level, detail, d, st) in enumerate(alarms):
        conn.execute(
            "INSERT INTO alarm(alarm_code,pipe_id,source,type,level,detail,alarm_ts,status)"
            " VALUES (?,?,?,?,?,?,?,?)",
            ("AL%04d" % (i + 1), pid, src, atype, level, detail, ts(d, 10 + i % 8), st))

    # ---- DMA 分区 + 7日记录 ----
    for code, name, dist, pcnt, ucnt, flow, night in DMAS:
        rate = round(random.uniform(6, 15), 1) if code in ("DMA04", "DMA06") else round(random.uniform(5, 10), 1)
        if code == "DMA04":
            rate = 14.6
        conn.execute(
            "INSERT INTO dma_zone(code,name,district,pipe_count,user_count,avg_flow_m3h,"
            "night_min_flow_m3h,leakage_rate_pct,dark_leak_location,status) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (code, name, dist, pcnt, ucnt, flow, night, rate,
             "二七路DN400管段K0+350处" if code == "DMA04" else None,
             "漏损偏高" if rate > 12 else "正常"))
    for zid in range(1, 7):
        for d in range(7):
            inflow = round(random.uniform(5000, 9000), 1)
            rate = round(random.uniform(5, 15) if zid == 4 else random.uniform(5, 11), 2)
            conn.execute(
                "INSERT INTO dma_record(dma_id,date,inflow_m3,billed_m3,night_min_flow_m3h,"
                "leakage_rate_pct) VALUES (?,?,?,?,?,?)",
                (zid, date_str(d), inflow, round(inflow * (1 - rate / 100), 1),
                 round(random.uniform(4, 11) if zid == 4 else random.uniform(3, 8), 1), rate))

    # ---- 水质节点 + 记录 ----
    for code, name, kind, seq, pid in QUALITY_NODES:
        conn.execute(
            "INSERT INTO quality_node(code,name,kind,seq,pipe_id,turbidity_ntu,residual_cl,ph,status)"
            " VALUES (?,?,?,?,?,?,?,?,?)",
            (code, name, kind, seq, pid, round(random.uniform(0.2, 0.7), 2),
             round(random.uniform(0.1, 0.3), 2), round(random.uniform(6.8, 7.6), 1), "正常"))
    for nid in range(1, 9):
        for d in range(5):
            conn.execute(
                "INSERT INTO quality_record(node_id,ts,turbidity_ntu,residual_cl,ph,is_abnormal)"
                " VALUES (?,?,?,?,?,?)",
                (nid, ts(d, 8 + nid % 6), round(random.uniform(0.2, 0.9), 2),
                 round(random.uniform(0.06, 0.3), 2), round(random.uniform(6.6, 7.8), 1), 0))

    # ---- 泵站 + 调度方案 ----
    for code, name, dist, elev, pc, pr, rf in STATIONS:
        conn.execute(
            "INSERT INTO pump_station(code,name,district,supply_elev_m,pump_count,"
            "current_pressure_mpa,rated_flow_m3h,status) VALUES (?,?,?,?,?,?,?,?)",
            (code, name, dist, elev, pc, pr, rf, "运行"))
    plans = [
        (1, "夜间低谷", 6.4, 0.42, 0.36, 14.3, "由中降至低", "已执行"),
        (1, "早高峰", 6.4, 0.36, 0.40, 5.2, "维持低风险", "已执行"),
        (2, "夜间低谷", 5.7, 0.38, 0.32, 15.8, "由中降至低", "已生成"),
        (3, "晚高峰", 7.0, 0.45, 0.48, 4.1, "维持中风险", "已生成"),
        (4, "夜间低谷", 6.0, 0.36, 0.31, 13.9, "由中降至低", "已生成"),
        (2, "日间平峰", 5.7, 0.32, 0.33, 2.8, "维持低风险", "已执行"),
    ]
    for sid, period, td, cur, tgt, es, br, st in plans:
        conn.execute(
            "INSERT INTO pressure_plan(station_id,period,terrain_delta_m,current_pressure_mpa,"
            "target_pressure_mpa,energy_save_pct,burst_risk_reduce,status,created_ts)"
            " VALUES (?,?,?,?,?,?,?,?,?)",
            (sid, period, td, cur, tgt, es, br, st, ts(random.randint(0, 5), 14)))

    # ---- 二次供水 ----
    for code, comm, dist, tc in SECONDS:
        lv = round(random.uniform(35, 90), 1)
        st = "正常"
        if code == "SEC03":
            lv = 15.0; st = "告警"
        conn.execute(
            "INSERT INTO secondary_unit(code,community,district,tank_count,level_pct,"
            "turbidity_ntu,residual_cl,disinfect_status,status,last_check) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (code, comm, dist, tc, lv, round(random.uniform(0.2, 0.7), 2),
             round(random.uniform(0.08, 0.25), 2), "正常", st, date_str(random.randint(0, 3))))

    # ---- 消防栓 + 事件 ----
    for code, loc, road, dist, pid in HYDRANTS:
        st = "正常"
        pr = round(random.uniform(0.15, 0.35), 2)
        if code == "XH0005":
            pr = 0.08; st = "告警"
        conn.execute(
            "INSERT INTO hydrant(code,location,road_name,district,pipe_id,pressure_mpa,"
            "test_flow_ls,last_test_ts,install_date,status) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (code, loc, road, dist, pid, pr, round(random.uniform(8, 25), 1),
             ts(random.randint(1, 20), 10), "201%d-0%d-1%d" % (random.randint(0, 9), random.randint(1, 9), random.randint(0, 9)), st))
    for hid in range(1, 11):
        conn.execute(
            "INSERT INTO hydrant_event(hydrant_id,type,ts,detail,status) VALUES (?,?,?,?,?)",
            (hid, "出水测试", ts(random.randint(1, 15), 9), "例行季度出水测试", "已处理"))
    conn.execute(
        "INSERT INTO hydrant_event(hydrant_id,type,ts,detail,status) VALUES (?,?,?,?,?)",
        (3, "盗用告警", ts(2, 22), "夜间流量异常，疑似盗用消防用水", "已处理"))
    conn.execute(
        "INSERT INTO hydrant_event(hydrant_id,type,ts,detail,status) VALUES (?,?,?,?,?)",
        (5, "低压告警", ts(1, 8), "水压0.08MPa不足，影响消防取水", "待处理"))

    # ---- 爆管案例 + 关阀方案 ----
    bursts = [
        (2, 78.5, "高", "管龄28年(灰铸铁材质)评分28 + 运行压力0.62MPa评分31，综合风险78.5", 1280, "江汉区中山路沿线", "风险预警"),
        (6, 66.2, "高", "管龄34年(预应力砼材质)评分34 + 运行压力0.35MPa评分18，综合风险66.2", 960, "江岸区二七路沿线", "处置中"),
        (5, 52.4, "中", "管龄31年(灰铸铁材质)评分31 + 运行压力0.12MPa评分6，综合风险52.4", 640, "江汉区新华路沿线", "风险预警"),
        (10, 45.8, "中", "管龄27年(灰铸铁材质)评分27 + 运行压力0.30MPa评分15，综合风险45.8", 820, "汉阳区鹦鹉大道沿线", "已修复"),
    ]
    for pid, score, level, detail, users, area, st in bursts:
        cur = conn.execute(
            "INSERT INTO burst_case(pipe_id,risk_score,risk_level,predict_detail,"
            "affected_users,affected_area,status,created_ts) VALUES (?,?,?,?,?,?,?,?)",
            (pid, score, level, detail, users, area, st, ts(random.randint(0, 4), 16)))
        cid = cur.lastrowid
        p = conn.execute("SELECT code,name,road_name FROM pipe WHERE id=?", (pid,)).fetchone()
        for no, (suffix, pos) in enumerate([
            ("A", "%s上游端阀门" % p["name"]),
            ("B", "%s下游端阀门" % p["name"]),
            ("C", "%s连通支管阀门" % (p["road_name"] or "主干"))], 1):
            conn.execute(
                "INSERT INTO burst_valve(case_id,valve_code,position,order_no,is_selected)"
                " VALUES (?,?,?,?,1)", (cid, "FV%s-%s" % (p["code"], suffix), pos, no))

    conn.commit()
    conn.close()
    print("seed done ->", DB_PATH)


if __name__ == "__main__":
    seed()
