# -*- coding: utf-8 -*-
"""
seed.py — 内置模拟数据
======================
生成 60 条覆盖不同管径/材质/年代/权属/区域的资产记录，
并配套生成生命周期档案、权属信息与盘点任务，无需连接真实系统。
数据生成使用固定随机种子，保证多次初始化结果一致（幂等：已有数据时跳过）。
"""
import random
import time

import database as db

REGIONS = ["城东区", "城西区", "城南区", "城北区", "高新区"]
REGION_CODE = {"城东区": "CD", "城西区": "CX", "城南区": "CN", "城北区": "CB", "高新区": "GX"}

DIAMETERS = ["DN100", "DN150", "DN200", "DN300", "DN400", "DN500"]
MATERIALS = ["钢管", "PE管", "铸铁管", "球墨铸铁管"]
PRESSURES = ["高压", "次高压", "中压", "低压"]

PROPERTY_UNITS = ["天信燃气集团", "城投燃气公司", "中油管道公司", "蓝星燃气公司"]
OPERATION_UNITS = ["天信运维中心", "城东运维站", "城西运维站", "外委运维A公司"]
SUPERVISION_UNITS = ["市住建局", "市应急管理局", "区安监站"]
NATURES = ["国有", "集体", "企业"]

STREETS = [
    "滨河路", "建设大道", "解放路", "中山路", "人民大街",
    "科技园路", "环城北路", "望江路", "青华街", "龙腾大道",
]


def _pick_material(year: int) -> str:
    """按建设年代选择符合行业演进的材质。"""
    if year <= 2000:
        return random.choice(["铸铁管", "钢管"])
    if year <= 2008:
        return random.choice(["钢管", "铸铁管", "球墨铸铁管"])
    return random.choice(["PE管", "钢管", "球墨铸铁管"])


def _gen_assets(conn, now_ms):
    assets = []
    region_seq = {r: 0 for r in REGIONS}
    for i in range(60):
        region = REGIONS[i % len(REGIONS)]
        year = random.choice(list(range(1992, 2024)))
        material = _pick_material(year)
        diameter = random.choice(DIAMETERS)
        # 老旧铸铁管更可能待报废/停用
        age = 2026 - year
        r = random.random()
        if material == "铸铁管" and age > 25 and r < 0.45:
            status = "待报废"
        elif r < 0.07:
            status = "停用"
        elif r < 0.14:
            status = "待报废"
        else:
            status = "在役"

        region_seq[region] += 1
        code = f"GX-{REGION_CODE[region]}-{year}-{region_seq[region]:04d}"
        street = random.choice(STREETS)
        asset = {
            "asset_code": code,
            "segment_name": f"{street}{random.choice(['中段', '东段', '西段', '南段', '北段'])}燃气管道",
            "diameter": diameter,
            "material": material,
            "build_year": year,
            "owner_unit": random.choice(PROPERTY_UNITS),
            "region": region,
            "length_m": round(random.uniform(200, 3200), 1),
            "pressure_level": random.choices(PRESSURES, weights=[8, 15, 60, 17])[0],
            "status": status,
            "location": f"{region}{street}{random.randint(1, 200)}号沿线",
            "longitude": round(104.00 + random.uniform(0, 0.18), 6),
            "latitude": round(30.60 + random.uniform(0, 0.14), 6),
            "created_ts": now_ms,
        }
        assets.append(asset)
    conn.executemany(
        "INSERT INTO assets(asset_code,segment_name,diameter,material,build_year,owner_unit,"
        "region,length_m,pressure_level,status,location,longitude,latitude,created_ts)"
        " VALUES(:asset_code,:segment_name,:diameter,:material,:build_year,:owner_unit,"
        ":region,:length_m,:pressure_level,:status,:location,:longitude,:latitude,:created_ts)",
        assets)
    return db.rows_to_list(conn.execute("SELECT * FROM assets ORDER BY id"))


def _gen_lifecycle(conn, assets):
    """采购→施工→运维（多次）→（改造）→（报废申请）全流程档案。"""
    rows = []
    for a in assets:
        year = a["build_year"]
        rows.append((a["id"], "采购", f"{year - 1}-06-18", f"{a['owner_unit']}物资部",
                     f"采购 {a['diameter']} {a['material']} 管材 {a['length_m']:.0f} 米，签订采购合同",
                     f"采购合同-{a['asset_code']}.pdf", round(a["length_m"] * random.uniform(80, 260), 0)))
        rows.append((a["id"], "施工", f"{year}-03-25", f"{a['owner_unit']}工程部",
                     f"管段敷设施工完成并通过竣工验收，焊口/接口检测合格",
                     f"竣工验收单-{a['asset_code']}.pdf", round(a["length_m"] * random.uniform(120, 320), 0)))
        # 运维记录 1~3 条
        for k in range(random.randint(1, 3)):
            y = min(year + 3 + k * random.randint(2, 5), 2025)
            rows.append((a["id"], "运维", f"{y}-{random.randint(3, 11):02d}-{random.randint(1, 28):02d}",
                         random.choice(OPERATION_UNITS),
                         random.choice(["年度巡检完成，防腐层检测合格", "阴极保护电位测试，保护效果正常",
                                        "发现轻微锈蚀，做补口防腐处理", "阀门保养与泄漏检测，未见异常",
                                        "第三方施工监护，管线安全"]),
                         f"维修巡检记录-{a['asset_code']}-{y}.pdf",
                         round(random.uniform(800, 26000), 0)))
        # 约 30% 资产有改造记录
        if random.random() < 0.3 and year < 2015:
            y = min(year + random.randint(10, 18), 2025)
            rows.append((a["id"], "改造", f"{y}-05-12", f"{a['owner_unit']}工程部",
                         "老旧管段更新改造，更换老化阀门与补偿器",
                         f"改造方案与验收-{a['asset_code']}.pdf", round(a["length_m"] * random.uniform(150, 400), 0)))
        # 待报废资产附报废评估/申请
        if a["status"] == "待报废":
            rows.append((a["id"], "报废", "2026-04-10", f"{a['owner_unit']}资产部",
                         "管龄超限且腐蚀评级为 D 级，提交报废评估与置换申请",
                         f"报废评估报告-{a['asset_code']}.pdf", round(random.uniform(5000, 20000), 0)))
    conn.executemany(
        "INSERT INTO lifecycle_records(asset_id,stage,occurred_at,responsible,description,attachment,cost)"
        " VALUES(?,?,?,?,?,?,?)", rows)


def _gen_ownership(conn, assets):
    """约 10% 资产权属信息不完整（产权/运维/监管任一缺失），用于预警演示。"""
    for idx, a in enumerate(assets):
        prop = a["owner_unit"]
        oper = random.choice(OPERATION_UNITS)
        supv = random.choice(SUPERVISION_UNITS)
        nature = random.choice(NATURES)
        cert = f"房燃证字[{a['build_year']}]第{1000 + idx}号"
        contract = f"YW-{a['build_year']}-{200 + idx}"
        boundary = f"以阀门井为界：阀前（含阀门）由{oper}负责，阀后由用户侧负责；监管责任归{supv}"
        handover = f"{a['build_year']}-{random.randint(4, 10):02d}-01"

        # 制造权属不清样本：6 条分别缺失不同字段
        if idx % 17 == 5:
            prop, cert = "", ""          # 缺产权
        elif idx % 17 == 9:
            oper, contract = "", ""      # 缺运维
        elif idx % 17 == 13:
            supv = ""                    # 缺监管
        elif idx % 17 == 16:
            prop, oper, supv = "", "", ""  # 三方皆缺

        conn.execute(
            "INSERT INTO ownership(asset_id,property_unit,property_nature,property_cert_no,"
            "operation_unit,operation_contract_no,supervision_unit,responsibility_boundary,handover_at)"
            " VALUES(?,?,?,?,?,?,?,?,?)",
            (a["id"], prop, nature, cert, oper, contract, supv, boundary, handover))


def _gen_inventory(conn, assets, now_ms):
    """两个已完成任务 + 一个执行中任务，含差异与处理状态。"""
    def make_task(code, method, scope, operator, started, finished, status, pick_ids):
        conn.execute(
            "INSERT INTO inventory_tasks(task_code,method,scope,operator,started_ts,finished_ts,status,"
            "matched_count,diff_count) VALUES(?,?,?,?,?,?,?,?,?)",
            (code, method, scope, operator, started, finished, status, 0, 0))
        tid = conn.execute("SELECT last_insert_rowid() id").fetchone()["id"]
        matched = diff = 0
        for aid in pick_ids:
            a = next(x for x in assets if x["id"] == aid)
            if aid % 9 == 4:
                result, handle, remark = "盘亏", "待处理", "现场未找到该管段标识，疑似台账坐标偏差"
                diff += 1
            elif a["status"] == "停用" and aid % 5 == 0:
                result, handle, remark = "状态不符", "修正", "现场实际仍在运行，台账状态需修正"
                diff += 1
            elif aid % 11 == 6:
                result, handle, remark = "状态不符", "补录", "新增支管未在台账中，需补录"
                diff += 1
            else:
                result, handle, remark = "一致", "无差异", ""
                matched += 1
            conn.execute(
                "INSERT INTO inventory_items(task_id,asset_id,asset_code,check_result,handle_status,remark)"
                " VALUES(?,?,?,?,?,?)", (tid, aid, a["asset_code"], result, handle, remark))
        conn.execute("UPDATE inventory_tasks SET matched_count=?, diff_count=? WHERE id=?",
                     (matched, diff, tid))

    day = 86400000
    ids_a = [a["id"] for a in assets[:24]]
    ids_b = [a["id"] for a in assets[24:46]]
    ids_c = [a["id"] for a in assets[46:]]
    make_task("PD-20260510-01", "巡检盘点", "城东区·城西区 全部在役管段", "张巡检",
              now_ms - 100 * day, now_ms - 98 * day, "已完成", ids_a)
    make_task("PD-20260720-01", "扫码盘点", "高新区 重点管段", "李盘点",
              now_ms - 30 * day, now_ms - 29 * day, "已完成", ids_b)
    make_task("PD-20260828-01", "巡检盘点", "城南区·城北区 老旧铸铁管段", "王核查",
              now_ms - 2 * day, None, "差异处理中", ids_c)


def seed():
    """初始化全部模拟数据（已有资产数据时跳过）。"""
    conn = db.get_conn()
    try:
        if conn.execute("SELECT COUNT(*) c FROM assets").fetchone()["c"] > 0:
            return
        random.seed(20260831)
        now_ms = int(time.time() * 1000)
        assets = _gen_assets(conn, now_ms)
        _gen_lifecycle(conn, assets)
        _gen_ownership(conn, assets)
        _gen_inventory(conn, assets, now_ms)
        conn.commit()
    finally:
        conn.close()
