#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资产价值与成本管理子模块 - 数据模型与种子数据

内容：
1. 资产价值核算：原值、折旧、净值自动计算
2. 运维成本分析：按管段/区域统计运维、维修、改造费用
3. 全生命周期成本（LCC）分析：不同材质/方案的全周期成本对比
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
import random


def to_dict(model) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# =============================================================================
# 资产分类
# =============================================================================

ASSET_CATEGORIES = {
    "PIPE_SEGMENT": {"name": "管段", "depr_years": 30, "residual_rate": 0.05},
    "VALVE": {"name": "阀门", "depr_years": 15, "residual_rate": 0.05},
    "PUMP": {"name": "泵站设备", "depr_years": 20, "residual_rate": 0.10},
    "SENSOR": {"name": "传感器", "depr_years": 8, "residual_rate": 0.05},
    "ROBOT": {"name": "巡检机器人", "depr_years": 10, "residual_rate": 0.10},
    "ELECTRICAL": {"name": "电气设备", "depr_years": 15, "residual_rate": 0.05},
    "STRUCTURE": {"name": "土建结构", "depr_years": 50, "residual_rate": 0.02},
}

PIPE_MATERIALS = {
    "DUCTILE_IRON": {"name": "球墨铸铁", "unit_cost": 1200, "life_years": 50},
    "PE": {"name": "PE管", "unit_cost": 600, "life_years": 30},
    "STEEL": {"name": "钢管", "unit_cost": 1800, "life_years": 40},
    "CONCRETE": {"name": "混凝土管", "unit_cost": 800, "life_years": 45},
    "FRP": {"name": "玻璃钢管", "unit_cost": 1500, "life_years": 35},
}

REGIONS = ["城东片区", "城西片区", "城南片区", "城北片区", "开发区", "老城区"]

DEPR_METHODS = {
    "STRAIGHT_LINE": "直线法",
    "DOUBLE_DECLINING": "双倍余额递减法",
    "SUM_OF_YEARS": "年数总和法",
}


# =============================================================================
# Pydantic 请求模型
# =============================================================================

class AssetCreateRequest(BaseModel):
    name: str
    category: str
    region: str
    original_value: float
    install_date: str
    material: Optional[str] = None
    specs: Optional[str] = None


class CostRecordRequest(BaseModel):
    asset_id: str
    cost_type: str
    amount: float
    description: str
    record_date: Optional[str] = None


class LCCAnalysisRequest(BaseModel):
    project_name: str
    material_options: List[str]
    design_life: int
    discount_rate: float = 0.05
    annual_maintenance_rate: float = 0.02


# =============================================================================
# 种子数据生成
# =============================================================================

def seed_assets() -> List[Dict]:
    assets = []
    base_date = datetime(2020, 1, 1)

    pipe_segments = [
        ("城东主干管A段", "PIPE_SEGMENT", "城东片区", 850000, "DUCTILE_IRON", "DN800, L=500m"),
        ("城东主干管B段", "PIPE_SEGMENT", "城东片区", 620000, "PE", "DN600, L=380m"),
        ("城西供水主管", "PIPE_SEGMENT", "城西片区", 1200000, "STEEL", "DN1000, L=800m"),
        ("城西污水支管", "PIPE_SEGMENT", "城西片区", 380000, "PE", "DN400, L=250m"),
        ("城南热力管A", "PIPE_SEGMENT", "城南片区", 960000, "DUCTILE_IRON", "DN700, L=600m"),
        ("城南燃气管B", "PIPE_SEGMENT", "城南片区", 1100000, "STEEL", "DN500, L=450m"),
        ("城北雨水管", "PIPE_SEGMENT", "城北片区", 520000, "CONCRETE", "DN1200, L=700m"),
        ("开发区综合管沟", "PIPE_SEGMENT", "开发区", 2800000, "CONCRETE", "截面3x2.5m, L=1200m"),
        ("老城区给水管", "PIPE_SEGMENT", "老城区", 450000, "DUCTILE_IRON", "DN300, L=320m"),
        ("开发区中水管", "PIPE_SEGMENT", "开发区", 380000, "FRP", "DN400, L=280m"),
    ]

    for i, (name, cat, region, value, material, specs) in enumerate(pipe_segments):
        install_date = base_date + timedelta(days=random.randint(0, 1500))
        assets.append({
            "asset_id": f"AST-P{i+1:03d}",
            "name": name,
            "category": cat,
            "category_name": ASSET_CATEGORIES[cat]["name"],
            "region": region,
            "material": material,
            "material_name": PIPE_MATERIALS.get(material, {}).get("name", "-"),
            "specs": specs,
            "original_value": value,
            "install_date": install_date.strftime("%Y-%m-%d"),
            "depr_method": "STRAIGHT_LINE",
            "depr_years": ASSET_CATEGORIES[cat]["depr_years"],
            "residual_rate": ASSET_CATEGORIES[cat]["residual_rate"],
            "status": "在用",
            "created_at": install_date.strftime("%Y-%m-%d %H:%M:%S"),
        })

    equipment = [
        ("1#加压泵站", "PUMP", "城东片区", 1500000, "立式离心泵x3"),
        ("2#加压泵站", "PUMP", "城南片区", 1800000, "立式离心泵x4"),
        ("城东分区阀", "VALVE", "城东片区", 85000, "DN800电动蝶阀"),
        ("城西分区阀", "VALVE", "城西片区", 65000, "DN600电动蝶阀"),
        ("城南安全阀", "VALVE", "城南片区", 45000, "DN500弹簧式"),
        ("城北截流阀", "VALVE", "城北片区", 72000, "DN1200液压式"),
        ("SCADA主控柜", "ELECTRICAL", "开发区", 380000, "西门子S7-1500"),
        ("PLC远程站A", "ELECTRICAL", "城东片区", 120000, "AB ControlLogix"),
        ("巡检机器人A", "ROBOT", "开发区", 450000, "管廊巡检专用"),
        ("巡检机器人B", "ROBOT", "城东片区", 420000, "排水管网巡检"),
        ("水质监测站", "SENSOR", "城西片区", 280000, "多参数在线监测"),
        ("流量计组A", "SENSOR", "城东片区", 160000, "电磁流量计DN800"),
        ("流量计组B", "SENSOR", "城南片区", 140000, "超声波流量计DN600"),
        ("压力变送器组", "SENSOR", "城北片区", 95000, "罗斯蒙特3051x12"),
        ("气体检测器组", "SENSOR", "开发区", 180000, "四合一气体检测"),
    ]

    for i, (name, cat, region, value, specs) in enumerate(equipment):
        install_date = base_date + timedelta(days=random.randint(0, 1500))
        assets.append({
            "asset_id": f"AST-E{i+1:03d}",
            "name": name,
            "category": cat,
            "category_name": ASSET_CATEGORIES[cat]["name"],
            "region": region,
            "material": None,
            "material_name": "-",
            "specs": specs,
            "original_value": value,
            "install_date": install_date.strftime("%Y-%m-%d"),
            "depr_method": "STRAIGHT_LINE",
            "depr_years": ASSET_CATEGORIES[cat]["depr_years"],
            "residual_rate": ASSET_CATEGORIES[cat]["residual_rate"],
            "status": "在用",
            "created_at": install_date.strftime("%Y-%m-%d %H:%M:%S"),
        })

    return assets


def _calc_depr(original_value, depr_years, residual_rate, method, years_elapsed):
    residual = original_value * residual_rate
    depreciable = original_value - residual

    if method == "STRAIGHT_LINE":
        annual = depreciable / depr_years
        accum = min(annual * years_elapsed, depreciable)
        return round(accum, 2), round(annual, 2), round(original_value - accum, 2)

    elif method == "DOUBLE_DECLINING":
        rate = 2.0 / depr_years
        book = original_value
        accum = 0
        annual_list = []
        for y in range(1, min(years_elapsed, depr_years) + 1):
            dep = book * rate
            if book - dep < residual:
                dep = book - residual
            accum += dep
            annual_list.append(round(dep, 2))
            book -= dep
        avg_annual = round(accum / min(years_elapsed, depr_years), 2) if years_elapsed > 0 else 0
        return round(accum, 2), avg_annual, round(original_value - accum, 2)

    elif method == "SUM_OF_YEARS":
        soy_sum = depr_years * (depr_years + 1) / 2
        accum = 0
        for y in range(1, min(years_elapsed, depr_years) + 1):
            frac = (depr_years - y + 1) / soy_sum
            accum += depreciable * frac
        accum = min(accum, depreciable)
        annual = round(depreciable / depr_years, 2)
        return round(accum, 2), annual, round(original_value - accum, 2)

    return 0, 0, original_value


def calc_asset_values(assets: List[Dict], ref_date: Optional[str] = None) -> List[Dict]:
    ref = datetime.strptime(ref_date, "%Y-%m-%d") if ref_date else datetime.now()
    result = []
    for a in assets:
        install = datetime.strptime(a["install_date"], "%Y-%m-%d")
        years_elapsed = max(0, (ref - install).days / 365.25)
        accum, annual, net = _calc_depr(
            a["original_value"], a["depr_years"], a["residual_rate"],
            a["depr_method"], years_elapsed
        )
        item = {**a}
        item["accumulated_depr"] = accum
        item["annual_depr"] = annual
        item["net_value"] = net
        item["years_elapsed"] = round(years_elapsed, 1)
        item["depr_pct"] = round(accum / (a["original_value"] - a["original_value"] * a["residual_rate"]) * 100, 1) if a["original_value"] > 0 else 0
        if years_elapsed >= a["depr_years"]:
            item["status"] = "已提足"
        elif net <= 0:
            item["status"] = "已报废"
        result.append(item)
    return result


def seed_cost_records() -> List[Dict]:
    records = []
    cost_types = ["日常运维", "定期维修", "应急维修", "技改更换", "能耗费用", "人工费用"]
    descriptions = {
        "日常运维": ["管道冲洗", "阀门保养", "设备巡检", "清淤作业", "防腐补涂"],
        "定期维修": ["泵机大修", "阀门更换密封", "电气预防性试验", "传感器校准"],
        "应急维修": ["爆管抢修", "阀门卡死更换", "泵机故障抢修", "传感器损坏更换"],
        "技改更换": ["老旧管段更换", "设备升级改造", "控制系统改造", "防腐层整体翻新"],
        "能耗费用": ["泵站电费", "照明电费", "监控系统电费"],
        "人工费用": ["运维人员工资", "外包服务费", "技术咨询费"],
    }

    asset_ids = [f"AST-P{i:03d}" for i in range(1, 11)] + [f"AST-E{i:03d}" for i in range(1, 16)]

    for i in range(120):
        ct = random.choice(cost_types)
        asset_id = random.choice(asset_ids)
        cat = "PIPE_SEGMENT" if asset_id.startswith("AST-P") else random.choice(["PUMP", "VALVE", "SENSOR", "ROBOT", "ELECTRICAL"])
        region_map = {
            "AST-P001": "城东片区", "AST-P002": "城东片区", "AST-P003": "城西片区",
            "AST-P004": "城西片区", "AST-P005": "城南片区", "AST-P006": "城南片区",
            "AST-P007": "城北片区", "AST-P008": "开发区", "AST-P009": "老城区", "AST-P010": "开发区",
        }
        region = region_map.get(asset_id, random.choice(REGIONS))

        base_amount = {
            "日常运维": (2000, 15000),
            "定期维修": (5000, 50000),
            "应急维修": (10000, 80000),
            "技改更换": (30000, 200000),
            "能耗费用": (3000, 20000),
            "人工费用": (5000, 30000),
        }
        lo, hi = base_amount[ct]
        amount = round(random.uniform(lo, hi), 2)

        date = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 600))
        records.append({
            "record_id": f"COST-{i+1:04d}",
            "asset_id": asset_id,
            "cost_type": ct,
            "amount": amount,
            "description": random.choice(descriptions[ct]),
            "region": region,
            "record_date": date.strftime("%Y-%m-%d"),
            "approved": random.random() > 0.1,
            "created_at": date.strftime("%Y-%m-%d %H:%M:%S"),
        })

    return records


def seed_lcc_analyses() -> List[Dict]:
    analyses = [
        {
            "analysis_id": "LCC-001",
            "project_name": "城东主干管更换工程",
            "design_life": 50,
            "discount_rate": 0.05,
            "options": [
                {"material": "DUCTILE_IRON", "material_name": "球墨铸铁", "initial_cost": 850000,
                 "annual_maintenance": 12000, "annual_energy": 0, "replacement_cost": 0,
                 "disposal_cost": -5000, "total_lcc": 0, "npv": 0},
                {"material": "PE", "material_name": "PE管", "initial_cost": 520000,
                 "annual_maintenance": 18000, "annual_energy": 0, "replacement_cost": 180000,
                 "disposal_cost": -2000, "total_lcc": 0, "npv": 0},
                {"material": "STEEL", "material_name": "钢管", "initial_cost": 1100000,
                 "annual_maintenance": 25000, "annual_energy": 0, "replacement_cost": 0,
                 "disposal_cost": -15000, "total_lcc": 0, "npv": 0},
            ],
            "recommended": None,
            "created_at": "2025-06-15 10:30:00",
        },
        {
            "analysis_id": "LCC-002",
            "project_name": "开发区综合管沟建设",
            "design_life": 60,
            "discount_rate": 0.04,
            "options": [
                {"material": "CONCRETE", "material_name": "混凝土结构", "initial_cost": 3500000,
                 "annual_maintenance": 35000, "annual_energy": 12000, "replacement_cost": 0,
                 "disposal_cost": 0, "total_lcc": 0, "npv": 0},
                {"material": "STEEL", "material_name": "钢结构", "initial_cost": 4200000,
                 "annual_maintenance": 50000, "annual_energy": 15000, "replacement_cost": 0,
                 "disposal_cost": -80000, "total_lcc": 0, "npv": 0},
                {"material": "FRP", "material_name": "玻璃钢 composite", "initial_cost": 3800000,
                 "annual_maintenance": 20000, "annual_energy": 10000, "replacement_cost": 0,
                 "disposal_cost": -30000, "total_lcc": 0, "npv": 0},
            ],
            "recommended": None,
            "created_at": "2025-08-20 14:00:00",
        },
    ]

    for a in analyses:
        rate = a["discount_rate"]
        life = a["design_life"]
        for opt in a["options"]:
            npv = opt["initial_cost"]
            for y in range(1, life + 1):
                annual = opt["annual_maintenance"] + opt["annual_energy"]
                npv += annual / ((1 + rate) ** y)
                if y == 25 and opt["replacement_cost"] > 0:
                    npv += opt["replacement_cost"] / ((1 + rate) ** y)
            npv += opt["disposal_cost"] / ((1 + rate) ** life)
            opt["npv"] = round(npv, 2)
            opt["total_lcc"] = opt["npv"]

        best = min(a["options"], key=lambda x: x["npv"])
        a["recommended"] = best["material"]

    return analyses
