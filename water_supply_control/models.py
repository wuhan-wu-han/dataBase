# -*- coding: utf-8 -*-
"""供水管网精细化管控子模块 — Pydantic 请求模型"""
from typing import Optional
from pydantic import BaseModel


class MonitorForm(BaseModel):
    pipe_id: int
    pressure_mpa: Optional[float] = None
    flow_m3h: Optional[float] = None
    level_cm: Optional[float] = None
    turbidity_ntu: Optional[float] = None
    residual_cl: Optional[float] = None
    deformation_mm: Optional[float] = None


class DmaRecordForm(BaseModel):
    dma_id: int
    date: str
    inflow_m3: float
    billed_m3: float
    night_min_flow_m3h: Optional[float] = None


class QualityForm(BaseModel):
    node_id: int
    turbidity_ntu: Optional[float] = None
    residual_cl: Optional[float] = None
    ph: Optional[float] = None


class PressurePlanForm(BaseModel):
    station_id: int
    period: str  # 早高峰 / 晚高峰 / 夜间低谷 / 日间平峰
    terrain_delta_m: Optional[float] = None


class SecondaryForm(BaseModel):
    unit_id: int
    level_pct: Optional[float] = None
    turbidity_ntu: Optional[float] = None
    residual_cl: Optional[float] = None
    disinfect_status: Optional[str] = None


class HydrantForm(BaseModel):
    location: str
    road_name: Optional[str] = None
    district: Optional[str] = None
    pipe_id: Optional[int] = None
    pressure_mpa: Optional[float] = None
    install_date: Optional[str] = None
    remark: Optional[str] = None


class HydrantTestForm(BaseModel):
    pressure_mpa: Optional[float] = None
    test_flow_ls: Optional[float] = None
    note: Optional[str] = None


class BurstHandleForm(BaseModel):
    status: str  # 风险预警 / 处置中 / 已关阀 / 已修复
