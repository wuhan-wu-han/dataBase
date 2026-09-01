# -*- coding: utf-8 -*-
"""
地下综合管廊管控子模块 - 常量与数据模型

定义管廊舱室/区段结构、传感器点位布局、环境阈值规则、告警码、
管线台账初始数据、空间冲突规则参数与请求模型。

舱室划分（参考 GB 50838 城市综合管廊工程技术规范）：
    电力舱(EL) / 燃气舱(GS) / 水信舱(WS)，每舱 6 个区段（Z01~Z06）
传感器点位编码规则：
    GL-{舱码}{区段号}-{类型码}{序号}，如 GL-EL03-TH01
"""

from typing import Optional

from pydantic import BaseModel

# ==============================================================================
# 舱室 / 区段结构
# ==============================================================================

# 每舱区段数量
ZONE_COUNT = 6

# 舱室配置
CABIN_CONFIGS = [
    {"code": "EL", "name": "电力舱", "desc": "高压电缆舱室，重点监测温度与火情"},
    {"code": "GS", "name": "燃气舱", "desc": "独立燃气管线舱室，重点监测可燃/有毒气体"},
    {"code": "WS", "name": "水信舱", "desc": "供水管线与通信线缆舱室，重点监测积水液位"},
]

# 区段编码表：{1: "Z01", 2: "Z02", ...}
ZONE_NAMES = {i: "Z%02d" % i for i in range(1, ZONE_COUNT + 1)}

# ==============================================================================
# 传感器布局
# ==============================================================================

# 传感器类型信息：名称与采集指标
SENSOR_TYPE_INFO = {
    "TH": {"name": "温湿度传感器", "metrics": ["temperature", "humidity"]},
    "O2": {"name": "氧气探测器", "metrics": ["o2"]},
    "CO": {"name": "一氧化碳探测器", "metrics": ["co"]},
    "H2S": {"name": "硫化氢探测器", "metrics": ["h2s"]},
    "CH4": {"name": "甲烷探测器", "metrics": ["ch4"]},
    "WL": {"name": "积水液位计", "metrics": ["water_level"]},
    "SM": {"name": "烟雾探测器", "metrics": ["smoke"]},
}

# 各舱每区段部署的传感器类型
SENSOR_LAYOUT = {
    "EL": ["TH", "O2", "CO", "SM", "WL"],
    "GS": ["TH", "O2", "CH4", "H2S", "SM", "WL"],
    "WS": ["TH", "O2", "SM", "WL"],
}


def build_sensor_points():
    """按舱室布局生成全部传感器点位清单"""
    points = []
    for cabin in CABIN_CONFIGS:
        layout = SENSOR_LAYOUT[cabin["code"]]
        for zone in range(1, ZONE_COUNT + 1):
            for sensor_type in layout:
                points.append({
                    "sensor_id": "GL-%s%02d-%s01" % (cabin["code"], zone, sensor_type),
                    "cabin": cabin["code"],
                    "cabin_name": cabin["name"],
                    "zone": zone,
                    "zone_code": ZONE_NAMES[zone],
                    "sensor_type": sensor_type,
                    "sensor_name": SENSOR_TYPE_INFO[sensor_type]["name"],
                    "metrics": list(SENSOR_TYPE_INFO[sensor_type]["metrics"]),
                })
    return points


# 全部传感器点位（约 90 个：电力舱30 + 燃气舱36 + 水信舱24）
SENSOR_POINTS = build_sensor_points()

# ==============================================================================
# 环境指标元数据与阈值规则
# ==============================================================================

# 指标元数据：名称/单位/正常范围
METRIC_INFO = {
    "temperature": {"name": "温度", "unit": "℃", "normal_low": 5.0, "normal_high": 40.0},
    "humidity": {"name": "湿度", "unit": "%RH", "normal_low": 30.0, "normal_high": 85.0},
    "o2": {"name": "氧气浓度", "unit": "%VOL", "normal_low": 19.5, "normal_high": 23.5},
    "co": {"name": "一氧化碳", "unit": "ppm", "normal_low": 0.0, "normal_high": 24.0},
    "h2s": {"name": "硫化氢", "unit": "ppm", "normal_low": 0.0, "normal_high": 10.0},
    "ch4": {"name": "甲烷浓度", "unit": "%VOL", "normal_low": 0.0, "normal_high": 0.5},
    "water_level": {"name": "积水液位", "unit": "mm", "normal_low": 0.0, "normal_high": 100.0},
    "smoke": {"name": "烟雾指数", "unit": "", "normal_low": 0.0, "normal_high": 20.0},
}

# 阈值规则：预警/严重，高位超限或低位超限（氧气为低位告警）
ENV_THRESHOLDS = {
    "temperature": {"warn_high": 40.0, "crit_high": 50.0, "warn_low": None, "crit_low": None},
    "humidity": {"warn_high": 85.0, "crit_high": 95.0, "warn_low": None, "crit_low": None},
    "o2": {"warn_high": None, "crit_high": None, "warn_low": 19.5, "crit_low": 18.0},
    "co": {"warn_high": 24.0, "crit_high": 50.0, "warn_low": None, "crit_low": None},
    "h2s": {"warn_high": 10.0, "crit_high": 20.0, "warn_low": None, "crit_low": None},
    "ch4": {"warn_high": 1.0, "crit_high": 2.5, "warn_low": None, "crit_low": None},
    "water_level": {"warn_high": 100.0, "crit_high": 200.0, "warn_low": None, "crit_low": None},
    "smoke": {"warn_high": 20.0, "crit_high": 40.0, "warn_low": None, "crit_low": None},
}

# 模拟引擎基准值：(基准值, 随机游走步长, 物理下限, 物理上限)
SIM_BASELINES = {
    "temperature": (25.0, 0.6, -5.0, 60.0),
    "humidity": (60.0, 1.5, 20.0, 100.0),
    "o2": (20.9, 0.08, 14.0, 25.0),
    "co": (2.0, 0.5, 0.0, 80.0),
    "h2s": (1.0, 0.3, 0.0, 40.0),
    "ch4": (0.05, 0.02, 0.0, 5.0),
    "water_level": (20.0, 3.0, 0.0, 300.0),
    "smoke": (3.0, 1.0, 0.0, 100.0),
}

# 指标模拟值保留小数位
METRIC_PRECISION = {
    "temperature": 1, "humidity": 1, "o2": 2, "co": 1,
    "h2s": 2, "ch4": 3, "water_level": 1, "smoke": 1,
}

# ==============================================================================
# 告警码（5 位 51xxx 命名空间，与设备域 1001~4005 隔离）
# ==============================================================================

# 环境告警码：{(指标, 级别): 告警码}，级别 1=预警 2=严重
ENV_ALARM_CODES = {
    ("temperature", 1): 51001, ("temperature", 2): 51002,
    ("humidity", 1): 51011, ("humidity", 2): 51012,
    ("o2", 1): 51021, ("o2", 2): 51022,
    ("co", 1): 51031, ("co", 2): 51032,
    ("h2s", 1): 51041, ("h2s", 2): 51042,
    ("ch4", 1): 51051, ("ch4", 2): 51052,
    ("water_level", 1): 51061, ("water_level", 2): 51062,
    ("smoke", 1): 51071, ("smoke", 2): 51072,
}

# 环境告警描述：{(指标, 级别): 描述}
ENV_ALARM_DESC = {
    ("temperature", 1): "温度超预警阈值", ("temperature", 2): "温度严重超限，疑似火情",
    ("humidity", 1): "湿度超预警阈值", ("humidity", 2): "湿度严重超限",
    ("o2", 1): "氧气浓度偏低", ("o2", 2): "氧气浓度严重不足",
    ("co", 1): "一氧化碳超预警阈值", ("co", 2): "一氧化碳严重超标",
    ("h2s", 1): "硫化氢超预警阈值", ("h2s", 2): "硫化氢严重超标",
    ("ch4", 1): "甲烷浓度超预警阈值", ("ch4", 2): "甲烷浓度严重超标",
    ("water_level", 1): "积水液位超预警阈值", ("water_level", 2): "积水严重，需启动排水",
    ("smoke", 1): "检测到烟雾", ("smoke", 2): "烟雾浓度高，触发火情告警",
}

# 安防告警码
SECURITY_ALARM_CODES = {
    "unauthorized_access": 51801,
    "intrusion": 51802,
    "broadcast_fault": 51803,
}

# 告警级别名称
LEVEL_NAMES = {0: "正常", 1: "预警", 2: "严重"}

# ==============================================================================
# 管线台账
# ==============================================================================

# 管线类型
PIPELINE_TYPES = ["供水", "燃气", "电力", "通信"]

# 管线状态
PIPELINE_STATUS = ["在运", "检修", "停运"]

# 初始管线台账（预埋冲突数据用于演示空间冲突检测）：
#   PL-WS-002/003 —— 同舱段间距不足（间距规则）
#   PL-WS-001/002/005 在水信舱 Z01 —— 占位槽超限（容量规则）
#   PL-EL-004 —— 110kV 电力与燃气同舱（兼容性规则）
#   PL-GS-004 —— 燃气管线误登记在电力舱（兼容性规则）
PIPELINE_LEDGER = [
    {"pipeline_id": "PL-WS-001", "pipeline_type": "供水", "cabin": "WS",
     "zone_start": 1, "zone_end": 6, "diameter_mm": 800, "material": "球墨铸铁",
     "design_pressure": "1.0MPa", "lateral_pos": 0.8, "vertical_pos": 1,
     "status": "在运", "commission_date": "2024-03-15", "owner_unit": "市水务集团"},
    {"pipeline_id": "PL-WS-002", "pipeline_type": "通信", "cabin": "WS",
     "zone_start": 1, "zone_end": 4, "diameter_mm": 200, "material": "光缆桥架",
     "design_pressure": "", "lateral_pos": 1.5, "vertical_pos": 3,
     "status": "在运", "commission_date": "2024-05-20", "owner_unit": "移动运营商"},
    {"pipeline_id": "PL-WS-003", "pipeline_type": "通信", "cabin": "WS",
     "zone_start": 2, "zone_end": 5, "diameter_mm": 200, "material": "光缆桥架",
     "design_pressure": "", "lateral_pos": 1.55, "vertical_pos": 3,
     "status": "在运", "commission_date": "2024-08-02", "owner_unit": "联通运营商"},
    {"pipeline_id": "PL-WS-004", "pipeline_type": "供水", "cabin": "WS",
     "zone_start": 3, "zone_end": 6, "diameter_mm": 400, "material": "球墨铸铁",
     "design_pressure": "0.8MPa", "lateral_pos": 2.2, "vertical_pos": 1,
     "status": "在运", "commission_date": "2024-03-15", "owner_unit": "市水务集团"},
    {"pipeline_id": "PL-WS-005", "pipeline_type": "供水", "cabin": "WS",
     "zone_start": 1, "zone_end": 2, "diameter_mm": 1000, "material": "预应力钢筒混凝土",
     "design_pressure": "1.2MPa", "lateral_pos": 3.0, "vertical_pos": 1,
     "status": "在运", "commission_date": "2023-11-30", "owner_unit": "市水务集团"},
    {"pipeline_id": "PL-GS-001", "pipeline_type": "燃气", "cabin": "GS",
     "zone_start": 1, "zone_end": 3, "diameter_mm": 400, "material": "钢骨架聚乙烯",
     "design_pressure": "0.4MPa", "lateral_pos": 1.0, "vertical_pos": 2,
     "status": "在运", "commission_date": "2024-01-10", "owner_unit": "市燃气集团"},
    {"pipeline_id": "PL-GS-002", "pipeline_type": "燃气", "cabin": "GS",
     "zone_start": 4, "zone_end": 6, "diameter_mm": 300, "material": "钢骨架聚乙烯",
     "design_pressure": "0.2MPa", "lateral_pos": 1.2, "vertical_pos": 2,
     "status": "在运", "commission_date": "2024-01-10", "owner_unit": "市燃气集团"},
    {"pipeline_id": "PL-GS-003", "pipeline_type": "燃气", "cabin": "GS",
     "zone_start": 5, "zone_end": 6, "diameter_mm": 200, "material": "无缝钢管",
     "design_pressure": "0.2MPa", "lateral_pos": 2.5, "vertical_pos": 2,
     "status": "停运", "commission_date": "2024-06-18", "owner_unit": "市燃气集团"},
    {"pipeline_id": "PL-GS-004", "pipeline_type": "燃气", "cabin": "EL",
     "zone_start": 6, "zone_end": 6, "diameter_mm": 200, "material": "无缝钢管",
     "design_pressure": "0.2MPa", "lateral_pos": 2.8, "vertical_pos": 1,
     "status": "停运", "commission_date": "2023-09-01", "owner_unit": "市燃气集团"},
    {"pipeline_id": "PL-EL-001", "pipeline_type": "电力", "cabin": "EL",
     "zone_start": 1, "zone_end": 6, "diameter_mm": 300, "material": "XLPE电缆",
     "design_pressure": "110kV", "lateral_pos": 1.0, "vertical_pos": 2,
     "status": "在运", "commission_date": "2023-12-20", "owner_unit": "供电公司"},
    {"pipeline_id": "PL-EL-002", "pipeline_type": "电力", "cabin": "EL",
     "zone_start": 1, "zone_end": 6, "diameter_mm": 200, "material": "YJV电缆",
     "design_pressure": "10kV", "lateral_pos": 1.6, "vertical_pos": 2,
     "status": "在运", "commission_date": "2023-12-20", "owner_unit": "供电公司"},
    {"pipeline_id": "PL-EL-003", "pipeline_type": "电力", "cabin": "EL",
     "zone_start": 2, "zone_end": 5, "diameter_mm": 200, "material": "YJV电缆",
     "design_pressure": "10kV", "lateral_pos": 2.0, "vertical_pos": 3,
     "status": "检修", "commission_date": "2024-04-08", "owner_unit": "供电公司"},
    {"pipeline_id": "PL-EL-004", "pipeline_type": "电力", "cabin": "GS",
     "zone_start": 2, "zone_end": 3, "diameter_mm": 300, "material": "XLPE电缆",
     "design_pressure": "110kV", "lateral_pos": 2.0, "vertical_pos": 3,
     "status": "在运", "commission_date": "2025-02-11", "owner_unit": "供电公司"},
]

# ==============================================================================
# 空间冲突检测规则参数
# ==============================================================================

# 不同类型管线最小水平净距（米）
MIN_CLEARANCE = {
    frozenset(("燃气", "电力")): 0.5,
    frozenset(("燃气", "供水")): 0.3,
    frozenset(("燃气", "通信")): 0.3,
    frozenset(("电力", "通信")): 0.2,
    frozenset(("电力", "供水")): 0.2,
    frozenset(("供水", "通信")): 0.15,
}

# 同类型管线最小净距（米）
SAME_TYPE_CLEARANCE = 0.1

# 支架层位差折算的垂直净距（米/层）
VERTICAL_CLEARANCE_PER_LEVEL = 0.6

# 每舱每区段占位槽容量
CABIN_SLOT_CAPACITY = {"EL": 8, "GS": 6, "WS": 8}

# 容量预警比例（占用超过容量×该比例即告警）
CAPACITY_OVERLOAD_RATIO = 0.8

# 冲突类型显示名
CONFLICT_TYPE_NAMES = {
    "INCOMPATIBLE_CABIN": "舱室兼容性冲突",
    "GAS_POWER_COEXIST": "燃气与高压电力同舱",
    "SPACING_VIOLATION": "管线间距不足",
    "CAPACITY_OVERLOAD": "区段容量超限",
}

# ==============================================================================
# 安防设施
# ==============================================================================

# 门禁点位
ACCESS_GATES = [
    {"gate_id": "ACC-001", "name": "东端主入口", "location": "电力舱 Z01"},
    {"gate_id": "ACC-002", "name": "西端逃生出口", "location": "水信舱 Z06"},
    {"gate_id": "ACC-003", "name": "1号通风井检修口", "location": "燃气舱 Z03"},
]

# 入侵检测防区
INTRUSION_ZONES = [
    {"zone_id": "DF-001", "name": "东端地面通风口"},
    {"zone_id": "DF-002", "name": "西端投料口"},
    {"zone_id": "DF-003", "name": "2号逃生出口"},
]

# 应急广播设备
BROADCAST_DEVICE = {"device_id": "BC-001", "name": "管廊应急广播系统", "zone_coverage": "全舱段"}

# ==============================================================================
# 请求模型（枚举与范围校验在路由层手工执行，兼容 pydantic v1/v2）
# ==============================================================================


class PipelineCreateRequest(BaseModel):
    """新增管线请求"""
    pipeline_type: str
    cabin: str
    zone_start: int
    zone_end: int
    diameter_mm: int
    material: str = ""
    design_pressure: str = ""
    lateral_pos: float
    vertical_pos: int
    status: str = "在运"
    owner_unit: str = ""


class PipelineUpdateRequest(BaseModel):
    """更新管线请求（全部可选）"""
    pipeline_type: Optional[str] = None
    cabin: Optional[str] = None
    zone_start: Optional[int] = None
    zone_end: Optional[int] = None
    diameter_mm: Optional[int] = None
    material: Optional[str] = None
    design_pressure: Optional[str] = None
    lateral_pos: Optional[float] = None
    vertical_pos: Optional[int] = None
    status: Optional[str] = None
    owner_unit: Optional[str] = None


class AccessRecordRequest(BaseModel):
    """门禁出入登记请求"""
    gate_id: str
    direction: str
    person_id: str
    person_name: str = ""
    authorized: bool = True
