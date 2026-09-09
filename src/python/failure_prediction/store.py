#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""故障预报与寿命预测 —— SQLite 读写适配层

Java 侧 alarm-warning-service 从不启动，故由本模块在 Python :8000 上提供
/api/failure-predictions 数据。设备与故障概率为确定性种子（random.Random 固定种子），
首次访问时灌入空库，之后从库中读取，重启不丢。

接口字段用驼峰（deviceId / healthScore…），与前端 FailurePrediction.vue 严格对应；
库列用下划线，转换集中在 _to_camel()。
"""

import random
import traceback
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

try:                                                  # 从 src/python 目录启动
    from persistence import SessionLocal, init_db
    from persistence.failure_prediction_tables import FailurePrediction
except ImportError:                                   # 从仓库根目录以包路径启动
    from src.python.persistence import SessionLocal, init_db
    from src.python.persistence.failure_prediction_tables import FailurePrediction

SEED_KEY = 20260909

# 设备类型 → 设备编号前缀（城市安全生命线管网的典型监测对象）
_DEVICE_TYPES = [
    ("燃气调压箱", "GAS"),
    ("供水泵站", "WTR"),
    ("污水提升泵", "SEW"),
    ("供热换热站", "HEA"),
    ("管廊通风机", "TUN"),
    ("危化品储罐", "HAZ"),
    ("燃气管线阀门", "VLV"),
]

# 安塞区下辖街道/镇
_AREAS = [
    "真武洞街道", "金明街道", "白坪街道", "砖窑湾镇", "沿河湾镇",
    "王窑镇", "建华镇", "化子坪镇", "镰刀湾镇", "坪桥镇", "招安镇",
]


def _log_error(action: str, exc: Exception) -> None:
    print("[failure_prediction.store] %s 失败：%s" % (action, exc))
    traceback.print_exc()


def ensure_schema() -> None:
    """建表（幂等）"""
    init_db()


def _level_of(prob: float) -> str:
    if prob < 20:
        return "LOW"
    if prob < 40:
        return "MEDIUM"
    if prob < 60:
        return "HIGH"
    return "CRITICAL"


def _build_seed() -> List[Dict[str, Any]]:
    """生成 28 条确定性预测记录：故障概率驱动健康度/风险分/剩余寿命联动。"""
    rng = random.Random(SEED_KEY)
    base_time = datetime.now().replace(microsecond=0)
    records: List[Dict[str, Any]] = []
    seq_by_prefix: Dict[str, int] = {}

    for i in range(28):
        device_type, prefix = _DEVICE_TYPES[i % len(_DEVICE_TYPES)]
        seq_by_prefix[prefix] = seq_by_prefix.get(prefix, 0) + 1
        device_id = "%s-%03d" % (prefix, seq_by_prefix[prefix])
        area = _AREAS[rng.randrange(len(_AREAS))]

        # 故障概率：覆盖 LOW→CRITICAL 全区间，让环形图四档都有数据
        prob = round(rng.uniform(3.0, 95.0), 1)
        # 健康度与故障概率负相关；风险分正相关；剩余寿命负相关
        health = int(max(15, min(99, round(100 - prob * 0.82 + rng.uniform(-6, 6)))))
        risk = int(max(1, min(100, round(prob * 0.9 + rng.uniform(-5, 8)))))
        life = int(max(3, min(144, round((100 - prob) / 100 * 120 + rng.uniform(-6, 10)))))

        # 预测时间：最近 12 小时内错开，倒序展示时较新的在前
        at = base_time - timedelta(minutes=rng.randrange(0, 720))

        records.append({
            "device_id": device_id,
            "device_type": device_type,
            "area_id": area,
            "health_score": health,
            "risk_score": risk,
            "failure_probability": prob,
            "remaining_life_month": life,
            "prediction_level": _level_of(prob),
            "prediction_time": at.strftime("%Y-%m-%dT%H:%M:%S"),
        })
    return records


def seed_if_empty() -> None:
    """空库时灌入种子数据（幂等）。"""
    db = SessionLocal()
    try:
        if db.query(FailurePrediction).count() > 0:
            return
        for row in _build_seed():
            db.add(FailurePrediction(**row))
        db.commit()
    except Exception as exc:                          # noqa: BLE001
        db.rollback()
        _log_error("种子数据落库", exc)
    finally:
        db.close()


def _to_camel(row: FailurePrediction) -> Dict[str, Any]:
    return {
        "id": row.id,
        "deviceId": row.device_id,
        "deviceType": row.device_type,
        "areaId": row.area_id,
        "healthScore": row.health_score,
        "riskScore": row.risk_score,
        "failureProbability": row.failure_probability,
        "remainingLifeMonth": row.remaining_life_month,
        "predictionLevel": row.prediction_level,
        "predictionTime": row.prediction_time,
    }


def query_list(page: int = 1, size: int = 10,
               prediction_level: Optional[str] = None) -> Dict[str, Any]:
    """分页查询，返回 {records:[驼峰], total:N}。prediction_time 倒序（较新在前）。"""
    db = SessionLocal()
    try:
        q = db.query(FailurePrediction)
        if prediction_level:
            q = q.filter(FailurePrediction.prediction_level == prediction_level)
        total = q.count()
        rows = (q.order_by(FailurePrediction.prediction_time.desc(), FailurePrediction.id.desc())
                 .offset((page - 1) * size).limit(size).all())
        return {"records": [_to_camel(r) for r in rows], "total": total}
    finally:
        db.close()


def get_detail(prediction_id: int) -> Optional[Dict[str, Any]]:
    db = SessionLocal()
    try:
        row = db.query(FailurePrediction).filter(FailurePrediction.id == prediction_id).first()
        return _to_camel(row) if row else None
    finally:
        db.close()


def statistics() -> Dict[str, Any]:
    """统计卡片数据。highRiskCount = HIGH + CRITICAL（对应「高风险设备」语义）。"""
    db = SessionLocal()
    try:
        rows = db.query(FailurePrediction).all()
        total = len(rows)
        if total == 0:
            return {
                "totalDevices": 0, "highRiskCount": 0, "mediumRiskCount": 0,
                "lowRiskCount": 0, "avgHealthScore": "0.00", "avgRemainingLifeMonth": "0.00",
            }
        level_count = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        for r in rows:
            if r.prediction_level in level_count:
                level_count[r.prediction_level] += 1
        avg_health = sum(r.health_score or 0 for r in rows) / total
        avg_life = sum(r.remaining_life_month or 0 for r in rows) / total
        return {
            "totalDevices": total,
            "highRiskCount": level_count["HIGH"] + level_count["CRITICAL"],
            "mediumRiskCount": level_count["MEDIUM"],
            "lowRiskCount": level_count["LOW"],
            "avgHealthScore": "%.2f" % avg_health,
            "avgRemainingLifeMonth": "%.2f" % avg_life,
        }
    finally:
        db.close()


def generate() -> Optional[Dict[str, Any]]:
    """「生成预测」：刷新全部记录的预测时间为当前，返回故障概率最高的一台设备。

    无数据时返回 None（前端据此提示「无预警事件数据」）。
    """
    db = SessionLocal()
    try:
        rows = db.query(FailurePrediction).all()
        if not rows:
            return None
        now = datetime.now().replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%S")
        for r in rows:
            r.prediction_time = now
        db.commit()
        worst = max(rows, key=lambda r: (r.failure_probability or 0))
        return {
            "deviceId": worst.device_id,
            "deviceType": worst.device_type,
            "areaId": worst.area_id,
            "healthScore": worst.health_score,
            "riskScore": worst.risk_score,
            "failureProbability": worst.failure_probability,
            "remainingLifeMonth": worst.remaining_life_month,
            "predictionLevel": worst.prediction_level,
            "predictionTime": now,
        }
    except Exception as exc:                          # noqa: BLE001
        db.rollback()
        _log_error("生成预测", exc)
        return None
    finally:
        db.close()
