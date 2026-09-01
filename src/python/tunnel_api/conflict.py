# -*- coding: utf-8 -*-
"""
地下综合管廊管控子模块 - 空间冲突检测引擎

对入廊管线台账执行三类规则检查，输出冲突清单：
1. 兼容性规则（硬规则）：燃气管线必须位于燃气舱；同舱段内禁止燃气与 110kV 及以上电力共存
2. 间距规则：同舱段内两两比较，水平/垂直净距不得小于类型对应的最小净距
3. 容量规则：每舱段按"占位槽"容量核算，管径折算槽位，占用超阈值即告警

纯函数设计，可独立调用；新增/编辑管线后由路由层即时重算。
"""

import re

from .models import (
    CABIN_SLOT_CAPACITY,
    CAPACITY_OVERLOAD_RATIO,
    MIN_CLEARANCE,
    SAME_TYPE_CLEARANCE,
    VERTICAL_CLEARANCE_PER_LEVEL,
    ZONE_COUNT,
)

# 高压电力判定阈值（kV）
HIGH_VOLTAGE_KV = 110

# 管径折算占位槽规则：(管径下限, 槽位数)
SLOT_RULES = [(800, 3), (400, 2)]


def get_voltage_kv(pipeline):
    """从设计压力字段解析电力管线的电压等级（kV），非电力或无法解析返回 0"""
    if pipeline.get("pipeline_type") != "电力":
        return 0
    matched = re.search(r"(\d+)\s*kV", str(pipeline.get("design_pressure", "")), re.IGNORECASE)
    return int(matched.group(1)) if matched else 0


def get_zones(pipeline):
    """展开管线占用的区段号列表（含端点，做合法性裁剪）"""
    start = max(1, int(pipeline.get("zone_start", 1)))
    end = min(ZONE_COUNT, int(pipeline.get("zone_end", start)))
    return list(range(start, end + 1))


def get_slot_count(pipeline):
    """按管径折算占位槽数量"""
    diameter = int(pipeline.get("diameter_mm", 0))
    for threshold, slots in SLOT_RULES:
        if diameter >= threshold:
            return slots
    return 1


def get_required_clearance(type_a, type_b):
    """查询两类管线之间的最小净距（米）"""
    if type_a == type_b:
        return SAME_TYPE_CLEARANCE
    return MIN_CLEARANCE.get(frozenset((type_a, type_b)), SAME_TYPE_CLEARANCE)


def estimate_clearance(pipe_a, pipe_b):
    """估算两条管线净距：同层取横向位置差，不同层按层位差折算"""
    if pipe_a.get("vertical_pos") == pipe_b.get("vertical_pos"):
        return abs(float(pipe_a.get("lateral_pos", 0)) - float(pipe_b.get("lateral_pos", 0)))
    level_diff = abs(int(pipe_a.get("vertical_pos", 1)) - int(pipe_b.get("vertical_pos", 1)))
    return level_diff * VERTICAL_CLEARANCE_PER_LEVEL


def check_compatibility(pipelines):
    """兼容性规则：燃气入错舱、燃气与高压电力同舱段"""
    conflicts = []
    for pipe in pipelines:
        if pipe.get("pipeline_type") == "燃气" and pipe.get("cabin") != "GS":
            conflicts.append({
                "conflict_type": "INCOMPATIBLE_CABIN",
                "severity": "严重",
                "cabin": pipe.get("cabin"),
                "zone": None,
                "pipeline_ids": [pipe.get("pipeline_id")],
                "message": "燃气管线 %s 位于非燃气舱（%s 舱），违反舱室兼容性要求"
                           % (pipe.get("pipeline_id"), pipe.get("cabin")),
            })

    # 按 (舱室, 区段) 分组检查燃气与高压电力共存
    grouped = {}
    for pipe in pipelines:
        for zone in get_zones(pipe):
            grouped.setdefault((pipe.get("cabin"), zone), []).append(pipe)
    for (cabin, zone), group in sorted(grouped.items()):
        gas_pipes = [p for p in group if p.get("pipeline_type") == "燃气"]
        hv_pipes = [p for p in group if get_voltage_kv(p) >= HIGH_VOLTAGE_KV]
        if gas_pipes and hv_pipes:
            conflicts.append({
                "conflict_type": "GAS_POWER_COEXIST",
                "severity": "严重",
                "cabin": cabin,
                "zone": zone,
                "pipeline_ids": [p.get("pipeline_id") for p in gas_pipes + hv_pipes],
                "message": "%s 舱 %s 区段内燃气管线与 %dkV 及以上电力管线共存"
                           % (cabin, "Z%02d" % zone, HIGH_VOLTAGE_KV),
            })
    return conflicts


def check_spacing(pipelines):
    """间距规则：同舱段内管线两两比较净距"""
    conflicts = []
    grouped = {}
    for pipe in pipelines:
        for zone in get_zones(pipe):
            grouped.setdefault((pipe.get("cabin"), zone), []).append(pipe)

    for (cabin, zone), group in sorted(grouped.items()):
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                pipe_a, pipe_b = group[i], group[j]
                clearance = estimate_clearance(pipe_a, pipe_b)
                required = get_required_clearance(pipe_a.get("pipeline_type"),
                                                  pipe_b.get("pipeline_type"))
                if clearance < required:
                    severity = "严重" if clearance < required * 0.5 else "一般"
                    conflicts.append({
                        "conflict_type": "SPACING_VIOLATION",
                        "severity": severity,
                        "cabin": cabin,
                        "zone": zone,
                        "pipeline_ids": [pipe_a.get("pipeline_id"), pipe_b.get("pipeline_id")],
                        "message": "%s 舱 %s 区段内 %s 与 %s 净距 %.2fm，小于最小净距 %.2fm"
                                   % (cabin, "Z%02d" % zone, pipe_a.get("pipeline_id"),
                                      pipe_b.get("pipeline_id"), clearance, required),
                    })
    return conflicts


def check_capacity(pipelines):
    """容量规则：每舱段占位槽占用超过容量阈值"""
    conflicts = []
    usage = {}
    for pipe in pipelines:
        for zone in get_zones(pipe):
            key = (pipe.get("cabin"), zone)
            usage[key] = usage.get(key, 0) + get_slot_count(pipe)

    for (cabin, zone), used in sorted(usage.items()):
        capacity = CABIN_SLOT_CAPACITY.get(cabin, 8)
        if used > capacity * CAPACITY_OVERLOAD_RATIO:
            severity = "严重" if used > capacity else "预警"
            conflicts.append({
                "conflict_type": "CAPACITY_OVERLOAD",
                "severity": severity,
                "cabin": cabin,
                "zone": zone,
                "pipeline_ids": [],
                "message": "%s 舱 %s 区段占位槽已用 %d/%d，超过 %.0f%% 预警线"
                           % (cabin, "Z%02d" % zone, used, capacity,
                              CAPACITY_OVERLOAD_RATIO * 100),
            })
    return conflicts


def detect_conflicts(pipelines):
    """执行全部规则检查，返回带编号的冲突清单"""
    raw = []
    raw.extend(check_compatibility(pipelines))
    raw.extend(check_spacing(pipelines))
    raw.extend(check_capacity(pipelines))
    for index, item in enumerate(raw):
        item["conflict_id"] = "CFT-%03d" % (index + 1)
    return raw
