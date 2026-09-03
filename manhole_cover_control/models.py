# -*- coding: utf-8 -*-
"""Pydantic 请求模型与告警判定规则（井盖多维监测阈值）。"""
from typing import Optional

from pydantic import BaseModel, Field

# ---------------- 枚举 ----------------
MANHOLE_TYPES = ("雨水", "污水", "通信", "电力", "燃气")
MANHOLE_STATUSES = ("正常", "告警", "处置中", "被盗", "维修中")
DAMAGE_LEVELS = ("完好", "轻微裂缝", "破损")
ALARM_STATUSES = ("待派发", "已派发", "处置中", "已核验", "已闭环")
ORDER_STATUSES = ("待派发", "处置中", "待核验", "已核验", "已闭环")
HANDLE_TYPES = ("维修", "更换", "现场核查", "公安报案")
NET_STATUSES = ("已安装", "破损", "已维修", "已更换")
NET_MAINTAIN_TYPES = ("破损登记", "维修", "更换")
POLICE_STATUSES = ("已报案", "已立案", "侦破中", "已追回")

# ---------------- 监测告警阈值 ----------------
TILT_LIMIT = 15.0        # 倾角 °
DISP_LIMIT = 10.0        # 位移 mm（异动）
DISP_THEFT_LIMIT = 30.0  # 位移 mm（判定被盗异动）
WATER_LIMIT = 80.0       # 井下水位 cm
GAS_LIMIT = 10.0         # 有毒气体 ppm（H2S 复合）


def check_monitor(tilt_deg: Optional[float], displacement_mm: Optional[float],
                  damage: Optional[str], water_level_cm: Optional[float],
                  gas_ppm: Optional[float]) -> list:
    """
    多维监测数据 → 告警列表 [{type, level, detail}]：
      - 位移 >= 30mm       → 被盗异动（高）；>= 10mm → 位移异常（中）
      - 倾角 >= 15°        → 倾角异常（高）
      - 破损               → 井盖破损（高）；轻微裂缝 → 轻微裂缝（低）
      - 水位 >= 80cm       → 水位告警（中）
      - 有毒气体 >= 10ppm  → 有毒气体告警（高）
    """
    out = []
    if displacement_mm is not None:
        if displacement_mm >= DISP_THEFT_LIMIT:
            out.append({"type": "被盗异动", "level": "高",
                        "detail": f"位移 {displacement_mm}mm，疑似井盖被盗"})
        elif displacement_mm >= DISP_LIMIT:
            out.append({"type": "位移异常", "level": "中",
                        "detail": f"位移 {displacement_mm}mm，超过阈值 {DISP_LIMIT}mm"})
    if tilt_deg is not None and tilt_deg >= TILT_LIMIT:
        out.append({"type": "倾角异常", "level": "高",
                    "detail": f"倾角 {tilt_deg}°，超过阈值 {TILT_LIMIT}°"})
    if damage == "破损":
        out.append({"type": "井盖破损", "level": "高", "detail": "监测到井盖破损"})
    elif damage == "轻微裂缝":
        out.append({"type": "轻微裂缝", "level": "低", "detail": "井盖表面轻微裂缝"})
    if water_level_cm is not None and water_level_cm >= WATER_LIMIT:
        out.append({"type": "水位告警", "level": "中",
                    "detail": f"井下水位 {water_level_cm}cm，超过阈值 {WATER_LIMIT}cm"})
    if gas_ppm is not None and gas_ppm >= GAS_LIMIT:
        out.append({"type": "有毒气体告警", "level": "高",
                    "detail": f"有毒气体 {gas_ppm}ppm，超过阈值 {GAS_LIMIT}ppm"})
    return out


# ---------------- 请求模型 ----------------
class MonitorDataReq(BaseModel):
    manhole_id: int
    ts: Optional[int] = Field(None, description="采集时间戳 ms，缺省取当前时间")
    tilt_deg: Optional[float] = Field(None, ge=0)
    displacement_mm: Optional[float] = Field(None, ge=0)
    damage: Optional[str] = Field(None, description=" ".join(DAMAGE_LEVELS))
    water_level_cm: Optional[float] = Field(None, ge=0)
    gas_ppm: Optional[float] = Field(None, ge=0)


class ManholeCreateReq(BaseModel):
    location: str
    road_name: str
    district: str
    type: str = Field(..., description=" ".join(MANHOLE_TYPES))
    owner_unit: str = Field(..., description="权属管理单位")
    material: Optional[str] = None
    install_date: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    remark: Optional[str] = None


class ManholeUpdateReq(BaseModel):
    location: Optional[str] = None
    road_name: Optional[str] = None
    district: Optional[str] = None
    type: Optional[str] = None
    owner_unit: Optional[str] = None
    material: Optional[str] = None
    install_date: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    status: Optional[str] = None
    remark: Optional[str] = None


class RepairReq(BaseModel):
    type: str = Field(..., description="维修 / 更换")
    date: str
    reason: Optional[str] = None
    detail: Optional[str] = None
    cost: Optional[float] = Field(None, ge=0)
    operator: Optional[str] = None


class DispatchReq(BaseModel):
    assignee: str = Field(..., description="运维班组/负责人")
    handle_type: str = Field("维修", description=" ".join(HANDLE_TYPES))


class ReportReq(BaseModel):
    report_info: str = Field(..., min_length=2, description="现场处置情况上报")


class VerifyReq(BaseModel):
    passed: bool
    verify_result: str = Field(..., description="核验结论")


class TrackReq(BaseModel):
    manhole_id: int
    ts: Optional[int] = None
    lat: float
    lng: float
    speed_kmh: Optional[float] = Field(None, ge=0)
    note: Optional[str] = None


class PoliceReq(BaseModel):
    manhole_id: int
    alarm_id: Optional[int] = None
    police_unit: str
    contact: str
    case_no: Optional[str] = None
    status: str = "已报案"
    result: Optional[str] = None


class NetCreateReq(BaseModel):
    manhole_id: int
    install_date: Optional[str] = None
    material: Optional[str] = Field(None, description="聚乙烯/尼龙/不锈钢")
    load_kg: Optional[float] = Field(None, ge=0, description="承载能力 kg")
    next_check: Optional[str] = None
    remark: Optional[str] = None


class NetMaintainReq(BaseModel):
    type: str = Field(..., description=" ".join(NET_MAINTAIN_TYPES))
    date: str
    detail: Optional[str] = None
    operator: Optional[str] = None
