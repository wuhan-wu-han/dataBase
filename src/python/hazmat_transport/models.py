#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
危废/化学品输送管控子模块 - 数据模型与种子数据

内容：
1. 介质状态监测：危废介质压力、温度、流量、成分浓度
2. 输送路径合规校验：备案路径比对、改道/违规接驳告警
3. 全流程溯源管理：产生源→输送→处置端全链条追溯
4. 管段腐蚀余量评估：壁厚监测、剩余寿命预测
5. 环保合规台账：输送/处置/排放报表
6. 泄漏应急封堵：多级阀门级联关闭方案
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


def to_dict(model) -> Dict[str, Any]:
    """pydantic v1/v2 兼容的模型转 dict"""
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ==============================================================================
# 介质类型定义
# ==============================================================================

HAZMAT_MEDIA = {
    "ORG_SOLVENT": "有机溶剂废液",
    "ACID_BASE": "酸碱废液",
    "HEAVY_METAL": "重金属污泥",
    "TOXIC_GAS": "有毒气体",
    "FLAMMABLE": "易燃液体",
    "OXIDIZER": "氧化性物质",
}

MEDIA_UNITS = {
    "pressure": "MPa",
    "temperature": "℃",
    "flow_rate": "m³/h",
    "concentration": "mg/L",
    "wall_thickness": "mm",
}


def seed_media() -> List[Dict[str, Any]]:
    """危废介质监测种子数据"""
    media = []
    items = [
        ("MED-001", "ORG_SOLVENT", "甲苯废液", "HW06", "A厂-储罐区", 0.35, 28.5, 2.4, 1250),
        ("MED-002", "ORG_SOLVENT", "二甲苯废液", "HW06", "A厂-储罐区", 0.32, 27.8, 2.1, 980),
        ("MED-003", "ACID_BASE", "含铬废酸", "HW17", "B厂-酸洗车间", 0.45, 35.2, 1.8, 3200),
        ("MED-004", "ACID_BASE", "含镍碱性废液", "HW17", "B厂-电镀车间", 0.40, 32.1, 1.5, 2800),
        ("MED-005", "HEAVY_METAL", "含铅污泥", "HW31", "C厂-沉淀池", 0.28, 25.0, 0.8, 5600),
        ("MED-006", "HEAVY_METAL", "含镉污泥", "HW31", "C厂-沉淀池", 0.25, 24.5, 0.6, 4200),
        ("MED-007", "TOXIC_GAS", "硫化氢废气", "HW04", "D厂-反应车间", 0.15, 42.0, 120.0, 85),
        ("MED-008", "TOXIC_GAS", "氯气泄漏", "HW04", "D厂-氯碱车间", 0.18, 38.5, 95.0, 120),
        ("MED-009", "FLAMMABLE", "废矿物油", "HW08", "E厂-机修车间", 0.50, 30.0, 3.2, 450),
        ("MED-010", "FLAMMABLE", "废油漆渣", "HW12", "E厂-涂装车间", 0.48, 29.5, 2.8, 380),
        ("MED-011", "OXIDIZER", "废双氧水", "HW09", "F厂-氧化车间", 0.22, 26.0, 1.2, 15000),
        ("MED-012", "OXIDIZER", "高锰酸钾废液", "HW09", "F厂-水处理", 0.20, 25.5, 1.0, 8500),
    ]
    for mid, mtype, name, hw_code, source, pressure, temp, flow, conc in items:
        media.append({
            "media_id": mid,
            "media_type": mtype,
            "type_name": HAZMAT_MEDIA[mtype],
            "name": name,
            "hw_code": hw_code,
            "source": source,
            "pressure_mpa": pressure,
            "temperature_c": temp,
            "flow_rate_m3h": flow,
            "concentration_mgL": conc,
            "status": "normal" if conc < 5000 else "warning",
            "threshold_concentration": _threshold(mtype),
            "last_sample": (datetime.now() - timedelta(minutes=random_int(1, 30))).strftime("%Y-%m-%d %H:%M:%S"),
        })
    return media


def _threshold(mtype: str) -> float:
    return {
        "ORG_SOLVENT": 2000,
        "ACID_BASE": 5000,
        "HEAVY_METAL": 8000,
        "TOXIC_GAS": 200,
        "FLAMMABLE": 1000,
        "OXIDIZER": 20000,
    }.get(mtype, 1000)


def random_int(a: int, b: int) -> int:
    import random
    return random.randint(a, b)


# ==============================================================================
# 输送路径
# ==============================================================================

def seed_routes() -> List[Dict[str, Any]]:
    """备案输送路径种子数据"""
    routes = []
    items = [
        ("RT-001", "A厂-储罐区", "处置中心-北区", "HW06", 12.5, "approved",
         [("A厂-储罐区", 0), ("泵站P1", 3.2), ("泵站P2", 7.8), ("处置中心-北区", 12.5)]),
        ("RT-002", "B厂-酸洗车间", "处置中心-南区", "HW17", 8.3, "approved",
         [("B厂-酸洗车间", 0), ("泵站P3", 2.5), ("泵站P4", 5.6), ("处置中心-南区", 8.3)]),
        ("RT-003", "C厂-沉淀池", "处置中心-北区", "HW31", 15.2, "approved",
         [("C厂-沉淀池", 0), ("泵站P5", 4.0), ("泵站P6", 9.5), ("泵站P7", 12.8), ("处置中心-北区", 15.2)]),
        ("RT-004", "D厂-反应车间", "处置中心-东区", "HW04", 6.8, "approved",
         [("D厂-反应车间", 0), ("泵站P8", 2.2), ("泵站P9", 4.5), ("处置中心-东区", 6.8)]),
        ("RT-005", "E厂-机修车间", "处置中心-南区", "HW08", 10.5, "approved",
         [("E厂-机修车间", 0), ("泵站P10", 3.5), ("泵站P11", 7.2), ("处置中心-南区", 10.5)]),
        ("RT-006", "F厂-氧化车间", "处置中心-东区", "HW09", 9.0, "approved",
         [("F厂-氧化车间", 0), ("泵站P12", 3.0), ("泵站P13", 6.5), ("处置中心-东区", 9.0)]),
        ("RT-007", "A厂-储罐区", "处置中心-北区", "HW06", 14.0, "deviated",
         [("A厂-储罐区", 0), ("泵站P1", 3.2), ("未备案接驳点X", 6.5), ("处置中心-北区", 14.0)]),
        ("RT-008", "B厂-酸洗车间", "处置中心-南区", "HW17", 10.5, "deviated",
         [("B厂-酸洗车间", 0), ("泵站P3", 2.5), ("未备案接驳点Y", 6.8), ("处置中心-南区", 10.5)]),
    ]
    for rid, src, dst, hw_code, dist, status, waypoints in items:
        routes.append({
            "route_id": rid,
            "source": src,
            "destination": dst,
            "hw_code": hw_code,
            "distance_km": dist,
            "status": status,
            "waypoints": waypoints,
            "approved_date": (datetime.now() - timedelta(days=random_int(30, 180))).strftime("%Y-%m-%d"),
            "valid_until": (datetime.now() + timedelta(days=random_int(60, 365))).strftime("%Y-%m-%d"),
            "carrier": _carrier(rid),
        })
    return routes


def _carrier(rid: str) -> str:
    carriers = {
        "RT-001": "武汉绿源环保运输",
        "RT-002": "湖北危废物流",
        "RT-003": "武汉绿源环保运输",
        "RT-004": "华中危废转运",
        "RT-005": "湖北危废物流",
        "RT-006": "华中危废转运",
        "RT-007": "未知承运商",
        "RT-008": "未知承运商",
    }
    return carriers.get(rid, "未知")


# ==============================================================================
# 全流程溯源记录
# ==============================================================================

def seed_traceability() -> List[Dict[str, Any]]:
    """溯源记录种子数据"""
    records = []
    sources = ["A厂-储罐区", "B厂-酸洗车间", "C厂-沉淀池", "D厂-反应车间", "E厂-机修车间", "F厂-氧化车间"]
    destinations = ["处置中心-北区", "处置中心-南区", "处置中心-东区"]
    carriers = ["武汉绿源环保运输", "湖北危废物流", "华中危废转运"]
    hw_codes = ["HW06", "HW17", "HW31", "HW04", "HW08", "HW09"]
    statuses = ["completed", "completed", "completed", "in_transit", "pending"]

    for i in range(20):
        src = sources[i % len(sources)]
        dst = destinations[i % len(destinations)]
        carrier = carriers[i % len(carriers)]
        hw = hw_codes[i % len(hw_codes)]
        status = statuses[i % len(statuses)]
        volume = round(random_int(50, 500) + random_int(0, 99) / 100, 2)

        records.append({
            "trace_id": "TR-%04d" % (i + 1),
            "media_name": _media_name(hw),
            "hw_code": hw,
            "source": src,
            "destination": dst,
            "carrier": carrier,
            "volume_m3": volume,
            "status": status,
            "generate_time": (datetime.now() - timedelta(days=random_int(1, 30), hours=random_int(0, 23))).strftime("%Y-%m-%d %H:%M:%S"),
            "dispatch_time": (datetime.now() - timedelta(days=random_int(0, 29), hours=random_int(0, 23))).strftime("%Y-%m-%d %H:%M:%S") if status != "pending" else "",
            "arrive_time": (datetime.now() - timedelta(days=random_int(0, 28), hours=random_int(0, 23))).strftime("%Y-%m-%d %H:%M:%S") if status == "completed" else "",
            "disposal_result": _disposal_result(status),
            "manifest_no": "MF-2026-%05d" % (i + 1001),
        })
    return records


def _media_name(hw: str) -> str:
    names = {
        "HW06": "有机溶剂废液",
        "HW17": "酸碱废液",
        "HW31": "重金属污泥",
        "HW04": "有毒气体",
        "HW08": "废矿物油",
        "HW09": "氧化性废液",
    }
    return names.get(hw, "未知危废")


def _disposal_result(status: str) -> str:
    if status == "completed":
        return random_int(0, 1) == 0 and "达标处置" or "部分处置"
    if status == "in_transit":
        return "运输中"
    return "待处置"


# ==============================================================================
# 管段腐蚀数据
# ==============================================================================

def seed_pipe_segments() -> List[Dict[str, Any]]:
    """管段腐蚀评估种子数据"""
    segments = []
    items = [
        ("PS-001", "RT-001", "碳钢", 8.0, 0.12, 2018, "A厂-泵站P1"),
        ("PS-002", "RT-001", "碳钢", 8.0, 0.15, 2018, "泵站P1-泵站P2"),
        ("PS-003", "RT-001", "不锈钢", 6.0, 0.05, 2020, "泵站P2-处置中心"),
        ("PS-004", "RT-002", "碳钢", 8.0, 0.18, 2017, "B厂-泵站P3"),
        ("PS-005", "RT-002", "碳钢", 8.0, 0.20, 2017, "泵站P3-泵站P4"),
        ("PS-006", "RT-002", "碳钢", 8.0, 0.16, 2019, "泵站P4-处置中心"),
        ("PS-007", "RT-003", "碳钢", 10.0, 0.10, 2019, "C厂-泵站P5"),
        ("PS-008", "RT-003", "碳钢", 10.0, 0.14, 2019, "泵站P5-泵站P6"),
        ("PS-009", "RT-003", "碳钢", 10.0, 0.11, 2020, "泵站P6-泵站P7"),
        ("PS-010", "RT-003", "碳钢", 10.0, 0.13, 2020, "泵站P7-处置中心"),
        ("PS-011", "RT-004", "不锈钢", 6.0, 0.04, 2021, "D厂-泵站P8"),
        ("PS-012", "RT-004", "不锈钢", 6.0, 0.06, 2021, "泵站P8-泵站P9"),
        ("PS-013", "RT-004", "不锈钢", 6.0, 0.05, 2021, "泵站P9-处置中心"),
        ("PS-014", "RT-005", "碳钢", 8.0, 0.22, 2016, "E厂-泵站P10"),
        ("PS-015", "RT-005", "碳钢", 8.0, 0.25, 2016, "泵站P10-泵站P11"),
        ("PS-016", "RT-005", "碳钢", 8.0, 0.19, 2018, "泵站P11-处置中心"),
        ("PS-017", "RT-006", "碳钢", 8.0, 0.08, 2022, "F厂-泵站P12"),
        ("PS-018", "RT-006", "碳钢", 8.0, 0.09, 2022, "泵站P12-泵站P13"),
        ("PS-019", "RT-006", "碳钢", 8.0, 0.07, 2022, "泵站P13-处置中心"),
    ]
    for psid, route_id, material, orig_thickness, corrosion_rate, year, location in items:
        age = datetime.now().year - year
        current_thickness = round(max(orig_thickness - corrosion_rate * age, 1.0), 2)
        remaining_life = round((current_thickness - 2.0) / corrosion_rate, 1) if corrosion_rate > 0 else 999
        risk_level = "low" if remaining_life > 15 else ("medium" if remaining_life > 8 else "high")
        segments.append({
            "segment_id": psid,
            "route_id": route_id,
            "material": material,
            "original_thickness_mm": orig_thickness,
            "current_thickness_mm": current_thickness,
            "corrosion_rate_mm_year": corrosion_rate,
            "install_year": year,
            "location": location,
            "remaining_life_years": remaining_life,
            "risk_level": risk_level,
            "last_inspect": (datetime.now() - timedelta(days=random_int(10, 90))).strftime("%Y-%m-%d"),
            "next_inspect": (datetime.now() + timedelta(days=random_int(30, 180))).strftime("%Y-%m-%d"),
        })
    return segments


# ==============================================================================
# 环保合规台账
# ==============================================================================

def seed_compliance_ledger() -> List[Dict[str, Any]]:
    """环保合规台账种子数据"""
    ledger = []
    categories = ["transport", "disposal", "emission"]
    cat_names = {"transport": "输送台账", "disposal": "处置台账", "emission": "排放台账"}
    factories = ["A厂", "B厂", "C厂", "D厂", "E厂", "F厂"]
    hw_codes = ["HW06", "HW17", "HW31", "HW04", "HW08", "HW09"]

    for i in range(18):
        cat = categories[i % 3]
        factory = factories[i % len(factories)]
        hw = hw_codes[i % len(hw_codes)]
        volume = round(random_int(100, 2000) + random_int(0, 99) / 100, 2)
        compliant = random_int(0, 4) != 0  # 80% compliant

        ledger.append({
            "ledger_id": "LED-%04d" % (i + 1),
            "category": cat,
            "category_name": cat_names[cat],
            "factory": factory,
            "hw_code": hw,
            "media_name": _media_name(hw),
            "volume_m3": volume,
            "report_period": (datetime.now() - timedelta(days=random_int(1, 90))).strftime("%Y-%m"),
            "compliant": compliant,
            "issue_count": 0 if compliant else random_int(1, 5),
            "inspector": _inspector(i),
            "filing_date": (datetime.now() - timedelta(days=random_int(1, 60))).strftime("%Y-%m-%d"),
        })
    return ledger


def _inspector(idx: int) -> str:
    names = ["王环保", "李监测", "张督查", "陈审核", "刘检查", "赵验收"]
    return names[idx % len(names)]


# ==============================================================================
# 应急阀门
# ==============================================================================

def seed_emergency_valves() -> List[Dict[str, Any]]:
    """应急阀门种子数据"""
    valves = []
    items = [
        ("VLV-E01", "RT-001", "A厂-出口", "电动切断阀", "DQW-200", "normal", 1, 0.5),
        ("VLV-E02", "RT-001", "泵站P1-入口", "电动切断阀", "DQW-200", "normal", 1, 0.8),
        ("VLV-E03", "RT-001", "泵站P2-出口", "电动切断阀", "DQW-150", "normal", 2, 1.2),
        ("VLV-E04", "RT-002", "B厂-出口", "电动切断阀", "DQW-200", "normal", 1, 0.4),
        ("VLV-E05", "RT-002", "泵站P3-入口", "电动切断阀", "DQW-200", "normal", 1, 0.9),
        ("VLV-E06", "RT-002", "泵站P4-出口", "电动切断阀", "DQW-150", "normal", 2, 1.5),
        ("VLV-E07", "RT-003", "C厂-出口", "电动切断阀", "DQW-250", "normal", 1, 0.6),
        ("VLV-E08", "RT-003", "泵站P5-入口", "电动切断阀", "DQW-250", "normal", 1, 1.0),
        ("VLV-E09", "RT-003", "泵站P6-出口", "电动切断阀", "DQW-200", "normal", 2, 1.8),
        ("VLV-E10", "RT-003", "泵站P7-出口", "电动切断阀", "DQW-200", "normal", 3, 2.2),
        ("VLV-E11", "RT-004", "D厂-出口", "电动切断阀", "DQW-150", "normal", 1, 0.3),
        ("VLV-E12", "RT-004", "泵站P8-入口", "电动切断阀", "DQW-150", "normal", 1, 0.7),
        ("VLV-E13", "RT-004", "泵站P9-出口", "电动切断阀", "DQW-150", "normal", 2, 1.1),
        ("VLV-E14", "RT-005", "E厂-出口", "电动切断阀", "DQW-200", "normal", 1, 0.5),
        ("VLV-E15", "RT-005", "泵站P10-入口", "电动切断阀", "DQW-200", "normal", 1, 1.0),
        ("VLV-E16", "RT-005", "泵站P11-出口", "电动切断阀", "DQW-150", "normal", 2, 1.6),
        ("VLV-E17", "RT-006", "F厂-出口", "电动切断阀", "DQW-200", "normal", 1, 0.4),
        ("VLV-E18", "RT-006", "泵站P12-入口", "电动切断阀", "DQW-200", "normal", 1, 0.8),
        ("VLV-E19", "RT-006", "泵站P13-出口", "电动切断阀", "DQW-150", "normal", 2, 1.3),
        ("VLV-E20", "RT-007", "未备案接驳点X-入口", "手动切断阀", "DQW-150", "alert", 1, 0.0),
    ]
    for vid, route_id, location, vtype, model, status, cascade_level, response_sec in items:
        valves.append({
            "valve_id": vid,
            "route_id": route_id,
            "location": location,
            "valve_type": vtype,
            "model": model,
            "status": status,
            "cascade_level": cascade_level,
            "response_time_sec": response_sec,
            "last_test": (datetime.now() - timedelta(days=random_int(5, 60))).strftime("%Y-%m-%d"),
            "auto_close": cascade_level <= 2,
        })
    return valves


# ==============================================================================
# Pydantic 请求模型
# ==============================================================================

class RouteCheckRequest(BaseModel):
    """路径合规校验请求"""
    route_id: str
    current_position: Optional[str] = None
    waypoint: Optional[str] = None


class TraceQueryRequest(BaseModel):
    """溯源查询请求"""
    trace_id: Optional[str] = None
    hw_code: Optional[str] = None
    source: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None


class CorrosionEvalRequest(BaseModel):
    """腐蚀评估请求"""
    segment_id: Optional[str] = None
    route_id: Optional[str] = None
    risk_level: Optional[str] = None


class EmergencyActionRequest(BaseModel):
    """泄漏应急请求"""
    route_id: str
    leak_location: Optional[str] = None
    severity: str = "medium"


class ComplianceReportRequest(BaseModel):
    """合规报表请求"""
    category: Optional[str] = None
    factory: Optional[str] = None
    period: Optional[str] = None
