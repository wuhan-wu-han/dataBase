# -*- coding: utf-8 -*-
"""Pydantic 请求模型与风险判定逻辑（地下空洞 / 道路沉降 / 施工影响）。"""
from typing import Optional

from pydantic import BaseModel, Field

# ---------------- 通用枚举 ----------------
RISK_LEVELS = ("低风险", "中风险", "高风险")
CAVITY_STATUSES = ("监测中", "处置中", "已处置")
WORK_TYPES = ("明挖", "顶管", "打桩", "定向钻", "非开挖修复")


# ---------------- 1. 地下空洞 ----------------
def calc_cavity_risk(radar_area: float, leakage_index: float,
                     cavity_volume: float) -> tuple[int, str]:
    """
    空洞风险评分（0-100）：
      - 雷达异常区面积（m²）：>=8 → 40 分；>=4 → 30；>=1.5 → 18；其余 6
      - 渗漏指数（0-10）：   >=6 → 30 分；>=3 → 20；>=1 → 10；其余 0
      - 估算体积（m³）：     >=10 → 30 分；>=3 → 20；>=1 → 10；其余 0
    分级：>=60 高风险；>=35 中风险；其余 低风险。
    """
    if radar_area >= 8:
        score = 40
    elif radar_area >= 4:
        score = 30
    elif radar_area >= 1.5:
        score = 18
    else:
        score = 6
    if leakage_index >= 6:
        score += 30
    elif leakage_index >= 3:
        score += 20
    elif leakage_index >= 1:
        score += 10
    if cavity_volume >= 10:
        score += 30
    elif cavity_volume >= 3:
        score += 20
    elif cavity_volume >= 1:
        score += 10
    level = "高风险" if score >= 60 else ("中风险" if score >= 35 else "低风险")
    return score, level


class CavityCreateReq(BaseModel):
    road_name: str
    district: str
    location: Optional[str] = None
    radar_velocity: Optional[float] = Field(None, description="雷达波速 m/s")
    radar_area: float = Field(..., ge=0, description="雷达异常区面积 m²")
    leakage_index: float = Field(0, ge=0, le=10, description="渗漏指数 0-10")
    cavity_volume: float = Field(0, ge=0, description="估算空洞体积 m³")
    depth_m: Optional[float] = Field(None, ge=0)
    status: str = "监测中"
    found_at: Optional[str] = None
    remark: Optional[str] = None


class CavityUpdateReq(BaseModel):
    road_name: Optional[str] = None
    district: Optional[str] = None
    location: Optional[str] = None
    radar_velocity: Optional[float] = None
    radar_area: Optional[float] = None
    leakage_index: Optional[float] = None
    cavity_volume: Optional[float] = None
    depth_m: Optional[float] = None
    status: Optional[str] = None
    found_at: Optional[str] = None
    remark: Optional[str] = None


# ---------------- 2. 道路沉降 ----------------
def fusion_risk(cumulative_mm: float, rate_mm_month: float,
                accelerating: bool) -> tuple[str, str]:
    """
    多期沉降融合判定：
      高风险（塌陷风险）：累计 >= 50mm 或 近三月速率 >= 6mm/月
      中风险（快速发展）：累计 >= 30mm 或 近三月速率 >= 3mm/月
      低风险（缓慢发展）：累计 >= 15mm 或 近三月速率 >= 1.2mm/月
      其余为稳定。近期加速时趋势描述追加“且呈加速趋势”。
    """
    if cumulative_mm >= 50 or rate_mm_month >= 6:
        level = "高风险"
    elif cumulative_mm >= 30 or rate_mm_month >= 3:
        level = "中风险"
    elif cumulative_mm >= 15 or rate_mm_month >= 1.2:
        level = "低风险"
    else:
        level = "低风险"
    if level == "低风险" and cumulative_mm < 15 and rate_mm_month < 1.2:
        trend = "稳定"
    elif level == "低风险":
        trend = "缓慢发展"
    elif level == "中风险":
        trend = "快速发展"
    else:
        trend = "塌陷风险"
    if accelerating:
        trend += "（加速）"
    return level, trend


class SubsidenceRecordReq(BaseModel):
    point_code: str
    road_name: Optional[str] = None
    district: Optional[str] = None
    measured_at: str = Field(..., description="观测日期 yyyy-MM-dd")
    delta_mm: float = Field(..., description="本期沉降量 mm")
    source: str = "水准测量"


# ---------------- 3. 施工影响评估 ----------------
_WORK_WEIGHT = {"明挖": 1.0, "顶管": 0.8, "打桩": 0.9, "定向钻": 0.6, "非开挖修复": 0.5}


def calc_construction_risk(work_type: str, excavation_depth: float,
                           distance_to_pipe: float) -> tuple[int, int, int, str]:
    """
    施工影响评估：
      - 土体风险 = 开挖深度 × 9 × 工法权重（封顶 100）
      - 管网风险 = 与管线距离分档（<1.5m→90；<3m→65；<6m→40；其余 15）× 工法权重
      - 综合评分 = 0.5×土体 + 0.5×管网
    分级：>=60 高风险；>=35 中风险；其余 低风险。
    """
    w = _WORK_WEIGHT.get(work_type, 0.8)
    soil_score = min(100, round(excavation_depth * 9 * w))
    if distance_to_pipe < 1.5:
        base = 90
    elif distance_to_pipe < 3:
        base = 65
    elif distance_to_pipe < 6:
        base = 40
    else:
        base = 15
    pipe_score = min(100, round(base * w))
    overall = round(0.5 * soil_score + 0.5 * pipe_score)
    level = "高风险" if overall >= 60 else ("中风险" if overall >= 35 else "低风险")
    return soil_score, pipe_score, overall, level


class ConstructionCreateReq(BaseModel):
    project_name: str
    construction_unit: str
    road_name: str
    district: str
    work_type: str = Field(..., description=" ".join(WORK_TYPES))
    excavation_depth: float = Field(..., ge=0, description="开挖/作业深度 m")
    distance_to_pipe: float = Field(..., ge=0, description="距最近管线距离 m")
    start_date: Optional[str] = None
    plan_days: Optional[int] = Field(None, ge=1)
    measures: Optional[str] = None
    assessor: Optional[str] = None
    assessed_at: Optional[str] = None
