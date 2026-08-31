# -*- coding: utf-8 -*-
"""
models.py — Pydantic 请求/响应模型
==================================
所有对外接口的入参在此集中定义，字段注释会直接显示在 /docs 文档中。
"""
from typing import List, Optional

from pydantic import BaseModel, Field


# --------------------------- 1. 实时安全监测 ---------------------------
class SensorDataReport(BaseModel):
    """外部系统/网关上报的一帧毫秒级监测数据"""
    sensor_id: int = Field(..., description="监测站编号")
    ts_ms: Optional[int] = Field(None, description="毫秒时间戳，缺省取服务器当前时间")
    concentration_ppm: float = Field(..., description="燃气浓度 ppm")
    pressure_mpa: float = Field(..., description="管内压力 MPa")
    flow_m3h: float = Field(..., description="流量 m3/h")
    vibration_mms: float = Field(..., description="振动速度 mm/s")
    corrosion_mma: float = Field(..., description="腐蚀速率 mm/a")
    displacement_mm: float = Field(..., description="位移 mm")


class FaultInjectReq(BaseModel):
    """故障注入（演示用）"""
    sensor_id: int = Field(..., description="目标监测站")
    magnitude: float = Field(0.8, ge=0.1, le=1.0, description="故障强度 0.1~1.0")


# --------------------------- 2. 微泄漏精准定位 ---------------------------
class ConcentrationReading(BaseModel):
    position_km: float = Field(..., description="测点桩号 km")
    concentration_ppm: float = Field(..., description="测点浓度 ppm")


class LeakLocateReq(BaseModel):
    """浓度扩散模型反演定位入参"""
    readings: List[ConcentrationReading] = Field(..., min_length=2, description="沿线各测点浓度")
    background_ppm: float = Field(5.0, description="环境背景浓度")
    pipeline_length_km: float = Field(50.0, description="管线总长")


class PressureWaveReq(BaseModel):
    """压力波（负压波）时差法定位入参"""
    pipeline_length_km: float = Field(50.0, description="管线总长 km")
    wave_speed_m_s: float = Field(350.0, description="压力波传播速度 m/s")
    t_upstream_ms: float = Field(..., description="上游首站检测到负压波时刻（ms）")
    t_downstream_ms: float = Field(..., description="下游末站检测到负压波时刻（ms）")
    timing_error_ms: float = Field(5.0, description="两端时钟同步误差估计，用于不确定度")


# --------------------------- 3. 泄漏扩散仿真 ---------------------------
class DiffusionSimReq(BaseModel):
    """高斯烟羽扩散仿真入参"""
    leak_rate_kg_s: float = Field(2.0, gt=0, description="泄漏质量速率 kg/s")
    wind_speed_m_s: float = Field(3.0, ge=0.5, description="风速 m/s")
    wind_direction_deg: float = Field(0.0, description="风向（来向方位角，度）")
    pressure_kpa: float = Field(101.325, description="环境气压 kPa，影响气体密度与体积浓度")
    temperature_c: float = Field(20.0, description="环境温度 ℃")
    stability: str = Field("D", description="大气稳定度 A~F（A 不稳定~F 强稳定）")
    source_height_m: float = Field(0.5, ge=0, description="泄漏源有效高度 m")
    max_distance_m: float = Field(600.0, ge=100, le=5000, description="下风向仿真距离")
    grid_points: int = Field(100, ge=40, le=200, description="下风向网格数")


# --------------------------- 4. 第三方破坏预警 ---------------------------
class ThirdPartyEventReq(BaseModel):
    event_type: str = Field("机械施工振动", description="事件类型：机械施工振动/违规开挖/重型车辆通行/钻探作业/爆破作业")
    location_km: float = Field(..., description="沿管线桩号 km")
    lateral_m: float = Field(..., ge=0, description="距管道中心线水平距离 m")
    intensity: float = Field(5.0, ge=1, le=10, description="扰动强度 1~10")
    description: str = Field("", description="事件描述")


# --------------------------- 5. 用户端用气安全 ---------------------------
class UserAnomalyInjectReq(BaseModel):
    user_id: int = Field(..., description="用户编号")
    anomaly: str = Field("微泄漏", description="注入异常：微泄漏/熄火/CO超标/软管脱落")


# --------------------------- 6. 占压隐患管理 ---------------------------
class OccupationCreateReq(BaseModel):
    type: str = Field(..., description="隐患类型：建筑占压/重物堆压/施工占压/其他占压")
    location_km: float = Field(..., description="桩号 km")
    description: str = Field("", description="隐患描述")
    risk_level: str = Field("中", description="风险等级：高/中/低")
    responsible: str = Field("", description="责任单位/责任人")
    deadline: str = Field("", description="整改期限 YYYY-MM-DD")


class OccupationUpdateReq(BaseModel):
    description: Optional[str] = None
    risk_level: Optional[str] = None
    responsible: Optional[str] = None
    deadline: Optional[str] = None


class RectifyReq(BaseModel):
    action: str = Field(..., description="整改动作，如：下达整改通知书/现场清除堆土/拆除违建")
    operator: str = Field("管理员", description="经办人")
    status_to: str = Field(..., description="流转状态：待下达/已下达/整改中/待验收/已闭环")


# --------------------------- 7. 阴极保护监测 ---------------------------
class CathodicDataReq(BaseModel):
    pile_id: int = Field(..., description="测试桩编号")
    ts_ms: Optional[int] = Field(None, description="毫秒时间戳，缺省为当前时间")
    on_potential_v: float = Field(..., description="通电电位 V（CSE）")
    off_potential_v: float = Field(..., description="断电电位 V（CSE）")
    output_current_a: float = Field(..., description="恒电位仪输出电流 A")


# --------------------------- 8. 应急联动关阀 ---------------------------
class EmergencyTriggerReq(BaseModel):
    position_km: float = Field(..., description="泄漏/事故点桩号 km")
    source: str = Field("manual", description="触发来源：manual=人工 / leak_alarm=泄漏报警自动联动")
    level: str = Field("severe", description="事件级别：warning / severe")
