#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地下综合管廊环境监测数据生成脚本

功能：
1. 生成模拟的管廊环境时序传感数据（电力舱/燃气舱/水信舱 × 6 区段）
2. 覆盖温湿度、氧气、一氧化碳、硫化氢、甲烷、积水液位、烟雾等指标
3. 随机注入 3%~5% 越限数据并映射到 51xxx 告警码命名空间
4. 数据信封与设备域 device_sensor 对齐，可直接进入 Kafka→Hive→Spark→ES 管道

使用示例：
    python generate_tunnel_logs.py --count 50000 --output data/logs

依赖：
    除复用 tunnel_api/models.py 常量外无第三方依赖
"""

import argparse
import importlib.util
import json
import os
import random
from datetime import datetime, timedelta


# ==============================================================================
# 复用管廊模块常量（直接按文件加载，避免触发 tunnel_api/__init__ 启动模拟器）
# ==============================================================================

_MODELS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "tunnel_api", "models.py"
)
_spec = importlib.util.spec_from_file_location("tunnel_models", _MODELS_PATH)
_models = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_models)

SENSOR_POINTS = _models.SENSOR_POINTS
ENV_THRESHOLDS = _models.ENV_THRESHOLDS
SIM_BASELINES = _models.SIM_BASELINES
METRIC_PRECISION = _models.METRIC_PRECISION
ENV_ALARM_CODES = _models.ENV_ALARM_CODES
ENV_ALARM_DESC = _models.ENV_ALARM_DESC

# 越限数据注入概率（目标告警占比 3%~5%）
ANOMALY_RATE = 0.04


def evaluate_level(metric, value):
    """按阈值规则判定级别：0 正常 / 1 预警 / 2 严重（与模拟引擎一致）"""
    rule = ENV_THRESHOLDS.get(metric)
    if not rule:
        return 0
    if rule.get("crit_high") is not None and value >= rule["crit_high"]:
        return 2
    if rule.get("warn_high") is not None and value >= rule["warn_high"]:
        return 1
    if rule.get("crit_low") is not None and value <= rule["crit_low"]:
        return 2
    if rule.get("warn_low") is not None and value <= rule["warn_low"]:
        return 1
    return 0


def gen_normal_value(metric):
    """在基准值附近生成不越限的正常值"""
    base, step, lo, hi = SIM_BASELINES[metric]
    rule = ENV_THRESHOLDS[metric]
    if metric == "o2":
        margin = base - rule["warn_low"]
        value = base + random.uniform(-0.6, 0.6) * margin
    else:
        warn = rule.get("warn_high")
        if warn is None:
            value = base + random.uniform(-step * 2, step * 2)
        else:
            margin = warn - base
            value = base + random.uniform(-0.8, 0.8) * margin if margin > 0 \
                else base + random.uniform(-step * 2, step * 2)
    return max(lo, min(hi, value))


def gen_anomaly_value(metric, level):
    """生成越过预警/严重阈值的异常值"""
    rule = ENV_THRESHOLDS[metric]
    _, _, lo, hi = SIM_BASELINES[metric]
    if metric == "o2":
        warn, crit = rule["warn_low"], rule["crit_low"]
        if level == 1:
            value = random.uniform(crit + 0.1, warn - 0.05)
        else:
            value = random.uniform(lo, crit - 0.05)
    else:
        warn, crit = rule["warn_high"], rule["crit_high"]
        if level == 1:
            value = random.uniform(warn + 0.05, max(warn + 0.1, crit - 0.05))
        else:
            value = random.uniform(crit + 0.05, hi * 0.98)
    return max(lo, min(hi, value))


def metric_stress(metric, value):
    """将指标值归一化为压力系数 [0,1]：0 完全正常，1 达到/超过严重阈值"""
    rule = ENV_THRESHOLDS[metric]
    base = SIM_BASELINES[metric][0]
    if metric == "o2":
        warn, crit = rule["warn_low"], rule["crit_low"]
        if value >= base:
            return 0.0
        if value >= warn:
            span = base - warn
            return 0.1 * (base - value) / span if span > 0 else 0.0
        if value >= crit:
            span = warn - crit
            return 0.1 + 0.5 * (warn - value) / span if span > 0 else 0.6
        return min(1.0, 0.6 + (crit - value) * 0.2)
    warn = rule.get("warn_high")
    crit = rule.get("crit_high")
    if warn is None:
        return 0.0
    if value <= base:
        return 0.0
    if value <= warn:
        span = warn - base
        return 0.1 * (value - base) / span if span > 0 else 0.0
    if crit is None:
        return 0.1
    if value <= crit:
        span = crit - warn
        return 0.1 + 0.5 * (value - warn) / span if span > 0 else 0.6
    return min(1.0, 0.6 + (value - crit) * 0.05)


def generate_health_score(metric_values):
    """按最大偏离度折算环境健康分（0-100）"""
    stress = 0.0
    for metric, value in metric_values.items():
        stress = max(stress, metric_stress(metric, value))
    return max(10, min(100, int(100 - stress * 85)))


def generate_log_entry(point, base_time, index):
    """
    生成单条管廊环境监测记录

    Args:
        point (dict): 传感器点位（来自 SENSOR_POINTS）
        base_time (datetime): 基准时间（当日零点）
        index (int): 该点位的采样序号（5 秒间隔）

    Returns:
        dict: 单条日志记录
    """
    timestamp = base_time + timedelta(seconds=index * 5)

    inject_anomaly = random.random() < ANOMALY_RATE
    metric_values = {}
    target_metric = None
    if inject_anomaly:
        target_metric = random.choice(point["metrics"])
        target_level = 1 if random.random() < 0.7 else 2
    for metric in point["metrics"]:
        if inject_anomaly and metric == target_metric:
            raw = gen_anomaly_value(metric, target_level)
        else:
            raw = gen_normal_value(metric)
        metric_values[metric] = round(raw, METRIC_PRECISION.get(metric, 2))

    # 判定级别（取各指标最高）
    level = 0
    worst_metric = None
    for metric, value in metric_values.items():
        lv = evaluate_level(metric, value)
        if lv > level:
            level = lv
            worst_metric = metric

    alarm_code = 0
    alarm_desc = "正常"
    if level > 0 and worst_metric:
        alarm_code = ENV_ALARM_CODES.get((worst_metric, level), 0)
        alarm_desc = ENV_ALARM_DESC.get((worst_metric, level), "环境异常")

    health_score = generate_health_score(metric_values)

    return {
        "device_id": point["sensor_id"],
        "device_type": point["sensor_name"],
        "cabin": point["cabin"],
        "cabin_name": point["cabin_name"],
        "zone": point["zone_code"],
        "workshop": "%s-%s" % (point["cabin_name"], point["zone_code"]),
        "event_timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        "params": metric_values,
        "level": level,
        "alarm_code": alarm_code,
        "alarm_desc": alarm_desc,
        "health_score": health_score,
        "ts": int(timestamp.timestamp() * 1000),
    }


def generate_logs(count, output_dir):
    """
    生成指定数量的管廊环境监测数据

    Args:
        count (int): 记录数量
        output_dir (str): 输出目录

    Returns:
        str: 生成的日志文件路径
    """
    os.makedirs(output_dir, exist_ok=True)

    point_count = len(SENSOR_POINTS)
    print("传感器点位：共 %d 个" % point_count)
    cabin_stat = {}
    for p in SENSOR_POINTS:
        cabin_stat[p["cabin_name"]] = cabin_stat.get(p["cabin_name"], 0) + 1
    for name, cnt in cabin_stat.items():
        print("  - %s: %d 个点位" % (name, cnt))

    base_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    filename = "tunnel_sensor_%s.log" % base_time.strftime("%Y%m%d")
    filepath = os.path.join(output_dir, filename)

    print("\n开始生成 %s 条管廊监测数据..." % format(count, ","))
    print("输出文件: %s" % filepath)

    alarm_total = 0
    batch_size = 1000
    batches = (count + batch_size - 1) // batch_size

    with open(filepath, "w", encoding="utf-8") as f:
        for batch in range(batches):
            start_idx = batch * batch_size
            end_idx = min((batch + 1) * batch_size, count)
            batch_logs = []
            for i in range(start_idx, end_idx):
                point = SENSOR_POINTS[i % point_count]
                entry = generate_log_entry(point, base_time, i // point_count)
                if entry["alarm_code"] != 0:
                    alarm_total += 1
                batch_logs.append(json.dumps(entry, ensure_ascii=False))
            f.write("\n".join(batch_logs) + "\n")

            if (batch + 1) % 10 == 0 or batch == batches - 1:
                progress = ((batch + 1) / batches) * 100
                print("进度: %.1f%% (%s/%s 条记录)"
                      % (progress, format(end_idx, ","), format(count, ",")))

    file_size = os.path.getsize(filepath)
    ratio = (alarm_total / count * 100) if count else 0
    print("✓ 数据生成完成！")
    print("  文件路径: %s" % filepath)
    print("  文件大小: %.2f MB" % (file_size / 1024 / 1024))
    print("  记录数量: %s" % format(count, ","))
    print("  告警记录: %s 条 (%.2f%%)" % (format(alarm_total, ","), ratio))

    return filepath


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="地下综合管廊环境监测数据生成器")
    parser.add_argument("--count", type=int, default=100000,
                        help="生成记录数量，默认100000")
    parser.add_argument("--output", type=str, default="data/logs",
                        help="输出目录，默认为 data/logs")

    args = parser.parse_args()
    generate_logs(args.count, args.output)


if __name__ == "__main__":
    main()
