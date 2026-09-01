#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据治理与中台服务子模块 - 数据模型与种子数据

内容：
1. 五大主数据：管网、设备、人员、组织机构、地理空间
2. 数据标准体系：传感数据/业务数据/交互接口编码规范
3. 数据质量规则：完整性/准确性/时效性/一致性校验规则
4. 时空数据引擎：拓扑关系、路径分析、缓冲区分析数据结构
5. 统一数据服务API：接口注册、权限、流量控制模型
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
# 数据标准体系 - 编码规范
# ==============================================================================

DATA_STANDARDS = {
    "SENSOR": {
        "code": "SENSOR",
        "name": "传感数据标准",
        "encoding_rule": "SB-{舱体代码}-{区段编号}-{传感器类型}-{序号}",
        "unit_standard": {
            "temperature": "℃",
            "humidity": "%RH",
            "pressure": "kPa",
            "gas_concentration": "ppm",
            "water_level": "mm",
            "flow_rate": "m³/h",
            "vibration": "mm/s",
        },
        "format_spec": {
            "timestamp": "ISO8601 (yyyy-MM-dd'T'HH:mm:ss+08:00)",
            "value_type": "float64",
            "quality_flag": "0=正常, 1=可疑, 2=异常, 3=维护中",
        },
        "sample_count": 1250000,
    },
    "BUSINESS": {
        "code": "BUSINESS",
        "name": "业务数据标准",
        "encoding_rule": "BZ-{模块代码}-{业务类型}-{年月}-{序号}",
        "unit_standard": {
            "alarm_level": "1=预警, 2=严重",
            "plan_status": "draft/active/deprecated",
            "device_status": "0=关机,1=待机,2=运行,3=预警,4=故障,5=急停,6=调试",
        },
        "format_spec": {
            "id_format": "大写字母-数字组合，长度8-20",
            "name_encoding": "UTF-8",
            "time_zone": "Asia/Shanghai (UTC+8)",
        },
        "sample_count": 85000,
    },
    "API": {
        "code": "API",
        "name": "交互接口标准",
        "encoding_rule": "API-{服务域}-{功能码}-{版本号}",
        "unit_standard": {
            "response_time": "ms",
            "data_size": "KB",
            "qps_limit": "次/秒",
        },
        "format_spec": {
            "protocol": "RESTful HTTPS",
            "auth": "Bearer Token + API Key",
            "response_format": "JSON (UTF-8)",
        },
        "sample_count": 24,
    },
}


# ==============================================================================
# 五大主数据 - 管网
# ==============================================================================

PIPELINE_TYPES = {
    "GS": "燃气管线",
    "WS": "给水管线",
    "EL": "电力电缆",
    "CO": "通信光缆",
    "HS": "热力管线",
    "DR": "排水管线",
}


def seed_pipelines() -> List[Dict[str, Any]]:
    """管网主数据种子"""
    pipelines = []
    segments = [
        ("GS", "Z01", "燃气主干管", "DN300", "PE", 2020, 850),
        ("GS", "Z02", "燃气分支管", "DN200", "PE", 2021, 620),
        ("GS", "Z03", "燃气入户管", "DN100", "PE", 2022, 380),
        ("WS", "Z01", "给水主干管", "DN400", "球墨铸铁", 2019, 920),
        ("WS", "Z02", "给水分支管", "DN200", "PE", 2021, 540),
        ("EL", "Z01", "10kV电力电缆", "YJV22-3×300", "铜芯", 2020, 1200),
        ("EL", "Z02", "低压电力电缆", "YJV-4×120", "铜芯", 2021, 680),
        ("CO", "Z01", "主干光缆", "GYTA-48B1", "单模48芯", 2019, 1500),
        ("CO", "Z02", "分支光缆", "GYTA-24B1", "单模24芯", 2022, 450),
        ("HS", "Z01", "热力供水管", "DN250", "无缝钢管", 2020, 780),
        ("HS", "Z02", "热力回水管", "DN250", "无缝钢管", 2020, 780),
        ("DR", "Z01", "雨水排水管", "DN500", "HDPE", 2021, 650),
    ]
    for i, (pType, zone, name, spec, material, year, length) in enumerate(segments):
        pipelines.append({
            "pipeline_id": "PL-%s-%s-%03d" % (pType, zone, i + 1),
            "pipeline_type": pType,
            "type_name": PIPELINE_TYPES[pType],
            "zone": zone,
            "name": name,
            "spec": spec,
            "material": material,
            "install_year": year,
            "length_m": length,
            "status": "running",
            "owner": _pipeline_owner(pType),
            "last_inspect": (datetime.now() - timedelta(days=30 + i * 5)).strftime("%Y-%m-%d"),
            "health_score": 85 + (i % 10),
        })
    return pipelines


def _pipeline_owner(pType: str) -> str:
    owners = {
        "GS": "武汉华润燃气",
        "WS": "武汉市水务集团",
        "EL": "武汉供电公司",
        "CO": "武汉电信/移动/联通",
        "HS": "武汉热力公司",
        "DR": "武汉市排水管理处",
    }
    return owners.get(pType, "未知")


# ==============================================================================
# 五大主数据 - 设备
# ==============================================================================

def seed_equipment() -> List[Dict[str, Any]]:
    """设备主数据种子"""
    equipment = []
    devices = [
        ("SEN-T01", "温度传感器", "PT100", "Z01-GS", "running", 98.5),
        ("SEN-T02", "温度传感器", "PT100", "Z01-WS", "running", 97.2),
        ("SEN-H01", "湿度传感器", "HMP110", "Z01-GS", "running", 96.8),
        ("SEN-G01", "甲烷检测仪", "GAX-CH4", "Z01-GS", "running", 99.1),
        ("SEN-G02", "CO检测仪", "GAX-CO", "Z02-GS", "running", 95.4),
        ("SEN-W01", "液位传感器", "ULC-100", "Z01-WS", "running", 94.6),
        ("SEN-S01", "烟感探测器", "JTY-GD", "Z01-EL", "running", 98.2),
        ("CAM-01", "高清摄像头", "DS-2CD", "Z01", "running", 99.5),
        ("CAM-02", "高清摄像头", "DS-2CD", "Z02", "running", 97.8),
        ("FAN-01", "事故风机", "BF-100", "Z01-GS", "standby", 92.3),
        ("FAN-02", "事故风机", "BF-100", "Z02-GS", "standby", 91.5),
        ("PMP-01", "排水泵", "WQ-50", "Z01-WS", "standby", 89.7),
        ("VLV-01", "电动切断阀", "DQW-200", "Z01-GS", "running", 96.1),
        ("VLV-02", "电动调节阀", "DQW-150", "Z01-HS", "running", 94.8),
        ("RTU-01", "远程终端单元", "RTU-200", "Z01", "running", 99.8),
    ]
    for dev_id, name, model, location, status, health in devices:
        equipment.append({
            "equipment_id": dev_id,
            "name": name,
            "model": model,
            "location": location,
            "status": status,
            "health_score": health,
            "install_date": (datetime.now() - timedelta(days=365 + hash(dev_id) % 365)).strftime("%Y-%m-%d"),
            "last_maintenance": (datetime.now() - timedelta(days=30 + hash(dev_id) % 60)).strftime("%Y-%m-%d"),
            "manufacturer": _equip_manufacturer(dev_id[:3]),
        })
    return equipment


def _equip_manufacturer(prefix: str) -> str:
    return {
        "SEN": "霍尼韦尔/西门子",
        "CAM": "海康威视",
        "FAN": "上海鼓风机厂",
        "PMP": "南方泵业",
        "VLV": "苏州纽威阀门",
        "RTU": "施耐德电气",
    }.get(prefix, "未知厂商")


# ==============================================================================
# 五大主数据 - 人员
# ==============================================================================

def seed_personnel() -> List[Dict[str, Any]]:
    """人员主数据种子"""
    personnel = [
        ("P001", "张建国", "监控中心值班长", "OPS", "active", "027-8800-0101"),
        ("P002", "李明华", "巡检班组长", "OPS", "active", "027-8800-0401"),
        ("P003", "王志强", "应急指挥专员", "MGT", "active", "027-8800-0103"),
        ("P004", "陈安平", "燃气抢修队长", "MAINT", "active", "027-8800-0201"),
        ("P005", "刘晓东", "电气工程师", "MAINT", "active", "027-8800-0702"),
        ("P006", "赵伟民", "数据分析师", "IT", "active", "027-8800-0901"),
        ("P007", "孙国庆", "安保队长", "SEC", "active", "027-8800-0301"),
        ("P008", "周建军", "系统管理员", "IT", "active", "027-8800-0902"),
        ("P009", "吴志刚", "运维工程师", "OPS", "leave", "027-8800-0402"),
        ("P010", "郑小红", "通报专员", "MGT", "active", "027-8800-0102"),
    ]
    result = []
    for p_id, name, role, dept, status, phone in personnel:
        result.append({
            "person_id": p_id,
            "name": name,
            "role": role,
            "department": dept,
            "dept_name": _dept_name(dept),
            "status": status,
            "phone": phone,
            "cert_level": _cert_level(role),
            "entry_date": (datetime.now() - timedelta(days=365 + hash(p_id) % 730)).strftime("%Y-%m-%d"),
        })
    return result


def _dept_name(dept: str) -> str:
    return {
        "OPS": "运维部",
        "MGT": "管理部",
        "MAINT": "抢修部",
        "IT": "信息中心",
        "SEC": "安保部",
    }.get(dept, "未知")


def _cert_level(role: str) -> str:
    if "指挥" in role or "队长" in role:
        return "高级"
    if "工程师" in role or "组长" in role:
        return "中级"
    return "初级"


# ==============================================================================
# 五大主数据 - 组织机构
# ==============================================================================

def seed_organizations() -> List[Dict[str, Any]]:
    """组织机构主数据种子"""
    return [
        {"org_id": "ORG-001", "name": "管廊监控中心", "type": "internal", "parent": None,
         "staff_count": 12, "duty": "24小时监控值守、告警处置调度"},
        {"org_id": "ORG-002", "name": "运维管理部", "type": "internal", "parent": "ORG-001",
         "staff_count": 25, "duty": "日常巡检、设备维护、环境管理"},
        {"org_id": "ORG-003", "name": "应急指挥办公室", "type": "internal", "parent": "ORG-001",
         "staff_count": 8, "duty": "应急预案管理、演练组织、事故复盘"},
        {"org_id": "ORG-004", "name": "武汉华润燃气", "type": "external", "parent": None,
         "staff_count": 45, "duty": "燃气管线运维、抢修"},
        {"org_id": "ORG-005", "name": "武汉市水务集团", "type": "external", "parent": None,
         "staff_count": 38, "duty": "给水管线运维"},
        {"org_id": "ORG-006", "name": "武汉供电公司", "type": "external", "parent": None,
         "staff_count": 52, "duty": "电力电缆运维、调度"},
        {"org_id": "ORG-007", "name": "消防救援站", "type": "external", "parent": None,
         "staff_count": 30, "duty": "火灾扑救、抢险救援"},
        {"org_id": "ORG-008", "name": "信息中心", "type": "internal", "parent": "ORG-001",
         "staff_count": 10, "duty": "系统运维、数据治理、接口管理"},
    ]


# ==============================================================================
# 五大主数据 - 地理空间
# ==============================================================================

def seed_geo_spaces() -> List[Dict[str, Any]]:
    """地理空间主数据种子"""
    return [
        {"geo_id": "GEO-CABIN-01", "name": "综合管廊主体", "type": "cabin",
         "center": [30.5728, 114.2688], "bbox": [114.265, 30.570, 114.275, 30.576],
         "area_sqm": 12500, "zones": ["Z01", "Z02", "Z03"]},
        {"geo_id": "GEO-ZONE-01", "name": "Z01区段", "type": "zone",
         "center": [30.5735, 114.2680], "bbox": [114.265, 30.572, 114.270, 30.575],
         "area_sqm": 4200, "cabins": ["GS", "WS", "EL"]},
        {"geo_id": "GEO-ZONE-02", "name": "Z02区段", "type": "zone",
         "center": [30.5728, 114.2700], "bbox": [114.268, 30.571, 114.273, 30.574],
         "area_sqm": 4100, "cabins": ["GS", "HS", "CO"]},
        {"geo_id": "GEO-ZONE-03", "name": "Z03区段", "type": "zone",
         "center": [30.5720, 114.2720], "bbox": [114.270, 30.570, 114.275, 30.573],
         "area_sqm": 4200, "cabins": ["EL", "CO", "DR"]},
        {"geo_id": "GEO-ENTRY-01", "name": "1号出入口", "type": "entry",
         "center": [30.5738, 114.2675], "bbox": [114.267, 30.573, 114.268, 30.574],
         "area_sqm": 25, "zone": "Z01"},
        {"geo_id": "GEO-ENTRY-02", "name": "2号出入口", "type": "entry",
         "center": [30.5725, 114.2710], "bbox": [114.270, 30.572, 114.271, 30.573],
         "area_sqm": 25, "zone": "Z02"},
        {"geo_id": "GEO-ENTRY-03", "name": "3号出入口（通风口）", "type": "entry",
         "center": [30.5718, 114.2725], "bbox": [114.272, 30.571, 114.273, 30.572],
         "area_sqm": 30, "zone": "Z03"},
    ]


# ==============================================================================
# 数据质量规则
# ==============================================================================

QUALITY_RULES = {
    "COMPLETENESS": {
        "code": "COMPLETENESS",
        "name": "完整性校验",
        "description": "检查数据字段是否缺失、空值比例",
        "threshold": 0.95,
        "check_items": [
            {"field": "sensor_value", "rule": "NOT NULL", "weight": 0.3},
            {"field": "timestamp", "rule": "NOT NULL", "weight": 0.3},
            {"field": "device_id", "rule": "NOT NULL", "weight": 0.2},
            {"field": "quality_flag", "rule": "IN (0,1,2,3)", "weight": 0.2},
        ],
    },
    "ACCURACY": {
        "code": "ACCURACY",
        "name": "准确性校验",
        "description": "检查数据值是否在合理范围内",
        "threshold": 0.98,
        "check_items": [
            {"field": "temperature", "rule": "BETWEEN -40 AND 150", "unit": "℃"},
            {"field": "humidity", "rule": "BETWEEN 0 AND 100", "unit": "%RH"},
            {"field": "ch4_concentration", "rule": "BETWEEN 0 AND 100000", "unit": "ppm"},
            {"field": "water_level", "rule": "BETWEEN 0 AND 5000", "unit": "mm"},
        ],
    },
    "TIMELINESS": {
        "code": "TIMELINESS",
        "name": "时效性校验",
        "description": "检查数据时间戳是否在允许延迟范围内",
        "threshold": 0.90,
        "check_items": [
            {"metric": "sensor_data", "max_delay_sec": 60},
            {"metric": "alarm_event", "max_delay_sec": 10},
            {"metric": "device_status", "max_delay_sec": 30},
        ],
    },
    "CONSISTENCY": {
        "code": "CONSISTENCY",
        "name": "一致性校验",
        "description": "检查跨表/跨源数据的一致性",
        "threshold": 0.99,
        "check_items": [
            {"check": "设备ID参照完整性", "source": "sensor_data", "ref": "equipment_master"},
            {"check": "区段编码一致性", "source": "pipeline_master", "ref": "geo_zone"},
            {"check": "时间戳时区一致性", "rule": "ALL UTC+8"},
        ],
    },
}


# ==============================================================================
# 统一数据服务API注册
# ==============================================================================

def seed_api_services() -> List[Dict[str, Any]]:
    """统一数据服务API种子"""
    return [
        {"api_id": "API-GOV-001", "name": "主数据查询服务", "domain": "governance",
         "endpoint": "/governance/master/{type}", "method": "GET",
         "qps_limit": 100, "auth_required": True, "status": "active",
         "call_count_24h": 12580, "avg_response_ms": 45},
        {"api_id": "API-GOV-002", "name": "数据质量报告服务", "domain": "governance",
         "endpoint": "/governance/quality/report", "method": "GET",
         "qps_limit": 50, "auth_required": True, "status": "active",
         "call_count_24h": 3420, "avg_response_ms": 120},
        {"api_id": "API-GOV-003", "name": "时空分析服务", "domain": "governance",
         "endpoint": "/governance/spatial/analyze", "method": "POST",
         "qps_limit": 30, "auth_required": True, "status": "active",
         "call_count_24h": 890, "avg_response_ms": 280},
        {"api_id": "API-TUN-001", "name": "管廊监测数据服务", "domain": "tunnel",
         "endpoint": "/tunnel/sensor/current", "method": "GET",
         "qps_limit": 200, "auth_required": True, "status": "active",
         "call_count_24h": 45600, "avg_response_ms": 35},
        {"api_id": "API-TUN-002", "name": "管廊告警查询服务", "domain": "tunnel",
         "endpoint": "/tunnel/alarm/list", "method": "GET",
         "qps_limit": 100, "auth_required": True, "status": "active",
         "call_count_24h": 8920, "avg_response_ms": 55},
        {"api_id": "API-PLN-001", "name": "预案匹配服务", "domain": "plan",
         "endpoint": "/plan/match", "method": "POST",
         "qps_limit": 50, "auth_required": True, "status": "active",
         "call_count_24h": 1250, "avg_response_ms": 180},
        {"api_id": "API-PLN-002", "name": "预案列表服务", "domain": "plan",
         "endpoint": "/plan/plans", "method": "GET",
         "qps_limit": 100, "auth_required": False, "status": "active",
         "call_count_24h": 5680, "avg_response_ms": 42},
        {"api_id": "API-DEV-001", "name": "设备状态服务", "domain": "device",
         "endpoint": "/analysis/device_status", "method": "GET",
         "qps_limit": 150, "auth_required": False, "status": "active",
         "call_count_24h": 28900, "avg_response_ms": 38},
    ]


# ==============================================================================
# Pydantic 请求模型
# ==============================================================================

class QualityCheckRequest(BaseModel):
    """数据质量校验请求"""
    data_type: str = "sensor"
    sample_size: int = 1000
    rules: Optional[List[str]] = None


class SpatialAnalyzeRequest(BaseModel):
    """时空分析请求"""
    analyze_type: str = "buffer"
    geometry: Optional[Dict[str, Any]] = None
    zone: Optional[str] = None
    radius_m: float = 100.0
    layer: Optional[str] = None


class ApiRegisterRequest(BaseModel):
    """API注册请求"""
    api_name: str
    domain: str
    endpoint: str
    method: str = "GET"
    qps_limit: int = 100
    auth_required: bool = True


class MasterDataQueryRequest(BaseModel):
    """主数据查询请求"""
    data_type: str
    filters: Optional[Dict[str, Any]] = None
    page: int = 1
    page_size: int = 20
