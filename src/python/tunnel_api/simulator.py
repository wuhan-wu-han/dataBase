# -*- coding: utf-8 -*-
"""
地下综合管廊管控子模块 - 实时数据模拟引擎

后台守护线程每 5 秒刷新一次数据（随机游走 + 事件注入），快照加锁读取。
注意：本模块依赖进程内全局状态，部署必须保持单 worker
（uvicorn main:app，不加 --workers），否则多进程间数据不一致。
"""

import json
import random
import threading
from collections import deque
from datetime import datetime

from .conflict import detect_conflicts
from .models import (
    ACCESS_GATES,
    BROADCAST_DEVICE,
    CABIN_CONFIGS,
    ENV_ALARM_CODES,
    ENV_ALARM_DESC,
    ENV_THRESHOLDS,
    INTRUSION_ZONES,
    LEVEL_NAMES,
    METRIC_INFO,
    METRIC_PRECISION,
    PIPELINE_LEDGER,
    PIPELINE_STATUS,
    PIPELINE_TYPES,
    SECURITY_ALARM_CODES,
    SENSOR_POINTS,
    SIM_BASELINES,
    ZONE_COUNT,
    ZONE_NAMES,
)

# ==============================================================================
# 模拟参数
# ==============================================================================

# 快照刷新周期（秒）
TUNNEL_REFRESH_SECONDS = 5

# 每点位每指标历史缓冲长度（帧）
HISTORY_MAX_POINTS = 720

# 告警列表最大保留条数
ALARM_MAX_COUNT = 200

# 门禁出入记录最大保留条数
ACCESS_MAX_COUNT = 50

# 每帧触发一次事件注入的概率
EVENT_INJECT_RATE = 0.15

# 每帧生成门禁出入记录的概率
ACCESS_EVENT_RATE = 0.12

# 每帧触发入侵检测事件的概率
INTRUSION_EVENT_RATE = 0.008

# 传感器离线概率参数
OFFLINE_RATE = 0.005
RECOVER_RATE = 0.2

# ==============================================================================
# 模块级状态
# ==============================================================================

_lock = threading.Lock()
_snapshot = None
_thread_started = False

# 传感器运行时状态：{sensor_id: {"values": {...}, "levels": {...}, "event": {...}, "online": True}}
_sensor_state = {}

# 历史趋势缓冲：{sensor_id: {metric: deque([(time, value), ...])}}
_history = {}

# 告警列表（新告警在前）与自增编号
_alarms = []
_alarm_seq = 0

# 管线台账（运行时副本，支持增改）
_pipelines = [dict(item) for item in PIPELINE_LEDGER]

# 安防状态
_security = {
    "in_tunnel_count": 5,
    "access_records": [],
    "intrusions": [],
    "broadcast": {"device_id": BROADCAST_DEVICE["device_id"],
                  "name": BROADCAST_DEVICE["name"],
                  "status": "在线", "volume": 60,
                  "last_test_time": ""},
}


def now_str():
    """当前时间字符串"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def sanitize(payload):
    """序列化净化：确保所有数值为原生类型（防 numpy 等类型导致序列化 500）"""
    return json.loads(json.dumps(payload, default=lambda o: float(o) if isinstance(o, float) else o))


# ==============================================================================
# 阈值判定与告警
# ==============================================================================


def evaluate_level(metric, value):
    """按阈值规则判定级别：0 正常 / 1 预警 / 2 严重"""
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


def create_alarm(source_id, cabin, zone_code, metric, value, level, desc_override=None):
    """构造一条告警记录并加入列表（返回记录）"""
    global _alarm_seq
    _alarm_seq += 1
    info = METRIC_INFO.get(metric, {"name": metric, "unit": ""})
    alarm = {
        "alarm_id": "ALM-GL-%05d" % _alarm_seq,
        "source_id": source_id,
        "source_type": "sensor",
        "cabin": cabin,
        "zone_code": zone_code,
        "metric": metric,
        "metric_name": info["name"],
        "value": value,
        "unit": info["unit"],
        "level": level,
        "severity": LEVEL_NAMES.get(level, "预警"),
        "alarm_code": ENV_ALARM_CODES.get((metric, level), 0),
        "desc": desc_override or ENV_ALARM_DESC.get((metric, level), "环境指标异常"),
        "status": "未处理",
        "time": now_str(),
    }
    _alarms.insert(0, alarm)
    del _alarms[ALARM_MAX_COUNT:]
    return alarm


# ==============================================================================
# 单帧推进
# ==============================================================================


def init_sensor_state():
    """初始化传感器运行时状态（基准值附近小幅扰动）"""
    for point in SENSOR_POINTS:
        values = {}
        for metric in point["metrics"]:
            baseline, step, low, high = SIM_BASELINES[metric]
            values[metric] = round(baseline + random.uniform(-step * 3, step * 3), 4)
        _sensor_state[point["sensor_id"]] = {
            "values": values,
            "levels": {m: 0 for m in point["metrics"]},
            "event": None,
            "online": True,
        }
        _history[point["sensor_id"]] = {m: deque(maxlen=HISTORY_MAX_POINTS)
                                        for m in point["metrics"]}


def inject_event():
    """按概率随机挑选一个点位注入越限事件（持续若干帧后自然回落）"""
    if random.random() >= EVENT_INJECT_RATE:
        return
    point = random.choice(SENSOR_POINTS)
    state = _sensor_state.get(point["sensor_id"])
    if not state or not state["online"]:
        return
    metric = random.choice(point["metrics"])
    rule = ENV_THRESHOLDS[metric]
    if rule.get("crit_high") is not None:
        target = rule["crit_high"] * random.uniform(1.05, 1.3)
    else:
        target = rule["crit_low"] * random.uniform(0.8, 0.92)
    state["event"] = {"metric": metric, "target": target,
                      "frames_left": random.randint(12, 30)}


def walk_metric(metric, value, event):
    """单指标单帧演进：事件中逼近目标值，平时均值回归随机游走"""
    baseline, step, low, high = SIM_BASELINES[metric]
    if event and event["metric"] == metric and event["frames_left"] > 0:
        value += (event["target"] - value) * 0.25
        event["frames_left"] -= 1
    else:
        value += (baseline - value) * 0.05 + random.uniform(-step, step)
    return min(high, max(low, value))


def advance_sensor(point):
    """推进单个点位一帧，返回其指标明细与新增告警列表"""
    state = _sensor_state[point["sensor_id"]]
    new_alarms = []
    metrics_detail = {}
    worst_level = 0

    for metric in point["metrics"]:
        value = walk_metric(metric, state["values"][metric], state["event"])
        state["values"][metric] = value
        level = evaluate_level(metric, value)
        prev_level = state["levels"][metric]
        if level > prev_level and level > 0:
            alarm = create_alarm(point["sensor_id"], point["cabin"],
                                 point["zone_code"], metric,
                                 round(value, METRIC_PRECISION[metric]), level)
            new_alarms.append(alarm)
        state["levels"][metric] = level
        worst_level = max(worst_level, level)
        _history[point["sensor_id"]][metric].append(
            (now_str(), round(value, METRIC_PRECISION[metric])))
        metrics_detail[metric] = {
            "name": METRIC_INFO[metric]["name"],
            "value": round(value, METRIC_PRECISION[metric]),
            "unit": METRIC_INFO[metric]["unit"],
            "level": level,
        }

    # 离线状态随机翻转（低概率离线，离线后较快恢复）
    if state["online"] and random.random() < OFFLINE_RATE:
        state["online"] = False
    elif not state["online"] and random.random() < RECOVER_RATE:
        state["online"] = True

    detail = {
        "sensor_id": point["sensor_id"],
        "sensor_name": point["sensor_name"],
        "sensor_type": point["sensor_type"],
        "cabin": point["cabin"],
        "cabin_name": point["cabin_name"],
        "zone": point["zone"],
        "zone_code": point["zone_code"],
        "online": state["online"],
        "level": worst_level if state["online"] else 0,
        "metrics": metrics_detail,
    }
    return detail


# ==============================================================================
# 安防模拟
# ==============================================================================

SURNAMES = ["张", "王", "李", "赵", "刘", "陈", "杨", "黄", "周", "吴"]


def advance_security():
    """推进安防状态一帧：门禁出入、入侵检测"""
    sec = _security

    # 门禁出入事件
    if random.random() < ACCESS_EVENT_RATE:
        if sec["in_tunnel_count"] <= 1:
            direction = "进"
        elif sec["in_tunnel_count"] >= 12:
            direction = "出"
        else:
            direction = random.choice(["进", "出"])
        authorized = random.random() < 0.9
        gate = random.choice(ACCESS_GATES)
        record = {
            "record_id": "ACR-%s-%04d" % (datetime.now().strftime("%H%M%S"),
                                           random.randint(0, 9999)),
            "gate_id": gate["gate_id"],
            "gate_name": gate["name"],
            "location": gate["location"],
            "direction": direction,
            "person_id": "RY-%03d" % random.randint(100, 999),
            "person_name": random.choice(SURNAMES) + "某",
            "authorized": authorized,
            "time": now_str(),
        }
        sec["access_records"].insert(0, record)
        del sec["access_records"][ACCESS_MAX_COUNT:]
        sec["in_tunnel_count"] += 1 if direction == "进" else -1
        if not authorized:
            alarm = create_alarm(gate["gate_id"], "", gate["location"],
                                 "access", 0, 1,
                                 desc_override="门禁未授权人员刷卡（%s）" % gate["name"])
            alarm["alarm_code"] = SECURITY_ALARM_CODES["unauthorized_access"]
            alarm["source_type"] = "gate"
            alarm["metric_name"] = "门禁"

    # 入侵检测事件
    if random.random() < INTRUSION_EVENT_RATE:
        zone = random.choice(INTRUSION_ZONES)
        sec["intrusions"].insert(0, {
            "intrusion_id": "INT-%s-%03d" % (datetime.now().strftime("%H%M%S"),
                                              random.randint(0, 999)),
            "zone_id": zone["zone_id"],
            "zone_name": zone["name"],
            "level": "预警",
            "status": "未处理",
            "time": now_str(),
        })
        del sec["intrusions"][20:]


# ==============================================================================
# 快照构建
# ==============================================================================


def build_cabin_summary(env_realtime):
    """按舱室汇总：健康分、告警点位、区段最差级别（供剖面态势图）"""
    cabins = []
    zone_levels = {}
    for detail in env_realtime:
        key = (detail["cabin"], detail["zone"])
        cur = zone_levels.get(key, {"level": 0, "metric": None})
        if detail["online"] and detail["level"] > cur["level"]:
            worst_metric = max(detail["metrics"].items(),
                               key=lambda kv: kv[1]["level"])[0] \
                if detail["metrics"] else None
            cur = {"level": detail["level"], "metric": worst_metric}
        zone_levels[key] = cur

    for cabin in CABIN_CONFIGS:
        cabin_details = [d for d in env_realtime if d["cabin"] == cabin["code"]]
        warn_count = sum(1 for d in cabin_details if d["online"] and d["level"] == 1)
        crit_count = sum(1 for d in cabin_details if d["online"] and d["level"] == 2)
        health_score = max(0, 100 - warn_count * 5 - crit_count * 15)
        zones = []
        for zone in range(1, ZONE_COUNT + 1):
            info = zone_levels.get((cabin["code"], zone), {"level": 0, "metric": None})
            zones.append({"zone_code": ZONE_NAMES[zone], "level": info["level"],
                          "worst_metric": info["metric"]})
        cabins.append({"code": cabin["code"], "name": cabin["name"],
                       "desc": cabin["desc"], "health_score": health_score,
                       "warn_count": warn_count, "crit_count": crit_count,
                       "zones": zones})
    return cabins


def build_overview(env_realtime, cabins):
    """构建大屏总览 KPI"""
    total = len(env_realtime)
    online = sum(1 for d in env_realtime if d["online"])
    o2_values = [d["metrics"]["o2"]["value"] for d in env_realtime
                 if d["online"] and "o2" in d["metrics"]]
    unhandled = sum(1 for a in _alarms if a["status"] == "未处理")
    cabin_scores = [c["health_score"] for c in cabins]
    return {
        "total_sensors": total,
        "online_sensors": online,
        "online_rate": round(online / total, 4) if total else 0,
        "alarms_today": len(_alarms),
        "unhandled_alarms": unhandled,
        "env_health_score": round(sum(cabin_scores) / len(cabin_scores), 1)
        if cabin_scores else 100,
        "cabin_health": {c["code"]: c["health_score"] for c in cabins},
        "o2_min": min(o2_values) if o2_values else None,
        "in_tunnel_count": _security["in_tunnel_count"],
        "conflict_count": len(detect_conflicts(_pipelines)),
        "pipeline_count": len(_pipelines),
        "broadcast_status": _security["broadcast"]["status"],
        "update_time": now_str(),
    }


def build_snapshot():
    """生成整份快照并做序列化净化"""
    env_realtime = [advance_sensor(point) for point in SENSOR_POINTS]
    cabins = build_cabin_summary(env_realtime)
    snapshot = {
        "overview": build_overview(env_realtime, cabins),
        "cabins": cabins,
        "env_realtime": env_realtime,
        "alarms": list(_alarms),
        "security": {
            "in_tunnel_count": _security["in_tunnel_count"],
            "gates": list(ACCESS_GATES),
            "access_records": list(_security["access_records"]),
            "intrusions": list(_security["intrusions"]),
            "broadcast": dict(_security["broadcast"]),
        },
    }
    return sanitize(snapshot)


def refresh_loop():
    """后台刷新循环（守护线程入口）"""
    while True:
        try:
            inject_event()
            advance_security()
            snapshot = build_snapshot()
            global _snapshot
            with _lock:
                _snapshot = snapshot
        except Exception as exc:  # 模拟失败不阻断服务
            print("⚠ 管廊模拟引擎刷新失败: %s" % exc)
        threading.Event().wait(TUNNEL_REFRESH_SECONDS)


def get_snapshot():
    """获取当前快照（首帧惰性生成，传感器状态未初始化时自动兜底）"""
    global _snapshot
    with _lock:
        if not _sensor_state:
            init_sensor_state()
        if _snapshot is None:
            _snapshot = build_snapshot()
        return _snapshot


# ==============================================================================
# 对外操作接口（路由层调用）
# ==============================================================================


def get_trend(sensor_id, points=60):
    """获取单点位历史趋势（按指标返回序列）"""
    point = next((p for p in SENSOR_POINTS if p["sensor_id"] == sensor_id), None)
    if point is None:
        return None
    count = min(max(points, 10), HISTORY_MAX_POINTS)
    series = []
    for metric in point["metrics"]:
        frames = list(_history.get(sensor_id, {}).get(metric, []))[-count:]
        series.append({
            "metric": metric,
            "name": METRIC_INFO[metric]["name"],
            "unit": METRIC_INFO[metric]["unit"],
            "times": [f[0] for f in frames],
            "values": [f[1] for f in frames],
        })
    return {"sensor_id": sensor_id, "sensor_name": point["sensor_name"],
            "cabin": point["cabin"], "zone_code": point["zone_code"],
            "series": series}


def acknowledge_alarm(alarm_id):
    """确认告警（标记为已处理），返回告警记录或 None"""
    with _lock:
        for alarm in _alarms:
            if alarm["alarm_id"] == alarm_id:
                alarm["status"] = "已处理"
                return dict(alarm)
    return None


def get_pipelines():
    """获取管线台账副本"""
    with _lock:
        return [dict(p) for p in _pipelines]


def add_pipeline(data):
    """新增管线，自动生成编号（PL-{舱码}-{序号}）"""
    with _lock:
        cabin = data["cabin"]
        prefix = "PL-%s-" % cabin
        max_seq = 0
        for pipe in _pipelines:
            # 只按编号前缀扫描：管线舱室字段可能与编号前缀不一致（如误登记数据）
            if pipe["pipeline_id"].startswith(prefix):
                try:
                    max_seq = max(max_seq, int(pipe["pipeline_id"].split("-")[-1]))
                except ValueError:
                    continue
        pipeline = dict(data)
        pipeline["pipeline_id"] = "PL-%s-%03d" % (cabin, max_seq + 1)
        pipeline["commission_date"] = datetime.now().strftime("%Y-%m-%d")
        _pipelines.append(pipeline)
        return dict(pipeline)


def update_pipeline(pipeline_id, data):
    """局部更新管线字段，返回更新后的记录或 None"""
    with _lock:
        for pipe in _pipelines:
            if pipe["pipeline_id"] == pipeline_id:
                pipe.update({k: v for k, v in data.items() if v is not None})
                return dict(pipe)
    return None


def register_access(record_data):
    """手动登记一条门禁出入记录（模拟刷卡），联动在廊人数"""
    with _lock:
        gate = next((g for g in ACCESS_GATES if g["gate_id"] == record_data["gate_id"]), None)
        record = {
            "record_id": "ACR-%s-%04d" % (datetime.now().strftime("%H%M%S"),
                                           random.randint(0, 9999)),
            "gate_id": record_data["gate_id"],
            "gate_name": gate["name"] if gate else record_data["gate_id"],
            "location": gate["location"] if gate else "",
            "direction": record_data["direction"],
            "person_id": record_data["person_id"],
            "person_name": record_data.get("person_name") or "某",
            "authorized": record_data.get("authorized", True),
            "time": now_str(),
        }
        _security["access_records"].insert(0, record)
        del _security["access_records"][ACCESS_MAX_COUNT:]
        _security["in_tunnel_count"] += 1 if record["direction"] == "进" else -1
        _security["in_tunnel_count"] = max(0, _security["in_tunnel_count"])
        return dict(record)


def test_broadcast():
    """触发应急广播自检"""
    with _lock:
        _security["broadcast"]["status"] = "在线"
        _security["broadcast"]["last_test_time"] = now_str()
        return dict(_security["broadcast"])


# ==============================================================================
# 引擎启动
# ==============================================================================


def start_simulator():
    """启动后台刷新线程（幂等，异常兜底不阻断主服务）"""
    global _thread_started
    if _thread_started:
        return
    try:
        init_sensor_state()
        thread = threading.Thread(target=refresh_loop, name="tunnel-simulator", daemon=True)
        thread.start()
        _thread_started = True
        print("✓ 管廊模拟引擎已启动（%d 个点位，%d 秒刷新）"
              % (len(SENSOR_POINTS), TUNNEL_REFRESH_SECONDS))
    except Exception as exc:
        print("⚠ 管廊模拟引擎启动失败: %s（接口将退化为静态数据）" % exc)
