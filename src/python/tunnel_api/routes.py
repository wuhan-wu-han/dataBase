# -*- coding: utf-8 -*-
"""
地下综合管廊管控子模块 - API 路由

前缀 /tunnel，覆盖五个接口域：
    总览（overview/cabins）、环境监测（env）、告警（alarms）、
    管线管理（pipelines，含空间冲突检测）、安防（security）、工作流（workflow）

所有入参做枚举/范围校验，非法输入返回 422；资源不存在返回 404。
"""

import os
import subprocess
import sys
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File

from . import simulator as sim
from . import store as tstore
from .conflict import detect_conflicts
from .models import (
    ACCESS_GATES,
    CABIN_CONFIGS,
    ENV_THRESHOLDS,
    LEVEL_NAMES,
    METRIC_INFO,
    PIPELINE_STATUS,
    PIPELINE_TYPES,
    AccessRecordRequest,
    PipelineCreateRequest,
    PipelineUpdateRequest,
    ZONE_COUNT,
)

router = APIRouter(prefix="/tunnel", tags=["管廊管控"])

# 合法舱室代码
VALID_CABINS = {cabin["code"] for cabin in CABIN_CONFIGS}

# 项目根目录（本文件位于 src/python/tunnel_api/，上溯四层）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

# 管廊数据管道工作流状态
workflow_status = {
    "running": False,
    "current_step": "",
    "progress": 0,
    "message": "等待执行",
    "start_time": "",
    "error": None,
}

# 管道各步骤（名称, 命令, 超时秒, 进度）
WORKFLOW_TIMEOUT = 900


# ==============================================================================
# 参数校验辅助
# ==============================================================================


def validate_cabin(cabin):
    """校验舱室代码"""
    if cabin is not None and cabin not in VALID_CABINS:
        raise HTTPException(status_code=422,
                            detail="cabin 必须是 %s 之一" % "/".join(sorted(VALID_CABINS)))
    return cabin


def normalize_zone(zone):
    """归一化区段参数：'Z03' / '3' / 3 均转为整数 3"""
    if zone is None or zone == "":
        return None
    text = str(zone).upper().lstrip("Z")
    if not text.isdigit() or not 1 <= int(text) <= ZONE_COUNT:
        raise HTTPException(status_code=422,
                            detail="zone 必须是 Z01~Z%02d 或 1~%d" % (ZONE_COUNT, ZONE_COUNT))
    return int(text)


def validate_pipeline_fields(data):
    """校验管线字段（新增时全量，更新时仅校验非空字段）"""
    if data.get("pipeline_type") is not None and data["pipeline_type"] not in PIPELINE_TYPES:
        raise HTTPException(status_code=422,
                            detail="pipeline_type 必须是 %s 之一" % "/".join(PIPELINE_TYPES))
    if data.get("cabin") is not None and data["cabin"] not in VALID_CABINS:
        raise HTTPException(status_code=422,
                            detail="cabin 必须是 %s 之一" % "/".join(sorted(VALID_CABINS)))
    if data.get("status") is not None and data["status"] not in PIPELINE_STATUS:
        raise HTTPException(status_code=422,
                            detail="status 必须是 %s 之一" % "/".join(PIPELINE_STATUS))
    for key in ("zone_start", "zone_end"):
        if data.get(key) is not None and not 1 <= int(data[key]) <= ZONE_COUNT:
            raise HTTPException(status_code=422, detail="%s 必须在 1~%d" % (key, ZONE_COUNT))
    if data.get("zone_start") is not None and data.get("zone_end") is not None \
            and int(data["zone_start"]) > int(data["zone_end"]):
        raise HTTPException(status_code=422, detail="zone_start 不得大于 zone_end")
    if data.get("diameter_mm") is not None and int(data["diameter_mm"]) <= 0:
        raise HTTPException(status_code=422, detail="diameter_mm 必须为正整数")
    if data.get("lateral_pos") is not None and float(data["lateral_pos"]) < 0:
        raise HTTPException(status_code=422, detail="lateral_pos 不得为负")
    if data.get("vertical_pos") is not None and not 1 <= int(data["vertical_pos"]) <= 4:
        raise HTTPException(status_code=422, detail="vertical_pos 必须在 1~4（支架层位）")


# ==============================================================================
# 总览域
# ==============================================================================


@router.get("/overview", summary="管廊总览KPI")
def get_overview():
    return sim.get_snapshot()["overview"]


@router.get("/cabins", summary="舱室/区段结构与状态")
def get_cabins():
    return sim.get_snapshot()["cabins"]


# ==============================================================================
# 环境监测域
# ==============================================================================


@router.get("/env/realtime", summary="环境实时监测")
def get_env_realtime(cabin: str = None, zone: str = None, metric: str = None):
    """全部点位最新值，可按舱室/区段/指标过滤"""
    validate_cabin(cabin)
    zone_num = normalize_zone(zone)
    if metric is not None and metric not in METRIC_INFO:
        raise HTTPException(status_code=422,
                            detail="metric 必须是 %s 之一" % "/".join(METRIC_INFO))

    result = []
    for detail in sim.get_snapshot()["env_realtime"]:
        if cabin and detail["cabin"] != cabin:
            continue
        if zone_num and detail["zone"] != zone_num:
            continue
        item = dict(detail)
        if metric:
            if metric not in item["metrics"]:
                continue
            item["metrics"] = {metric: item["metrics"][metric]}
        result.append(item)
    return {"total": len(result), "sensors": result}


@router.get("/env/trend", summary="点位历史趋势")
def get_env_trend(sensor_id: str, points: int = 60):
    """单点位历史趋势（按指标返回时间序列）"""
    if not 10 <= points <= 720:
        raise HTTPException(status_code=422, detail="points 必须在 10~720")
    trend = sim.get_trend(sensor_id, points)
    if trend is None:
        raise HTTPException(status_code=404, detail="传感器点位不存在: %s" % sensor_id)
    return trend


@router.get("/env/thresholds", summary="环境阈值规则")
def get_env_thresholds():
    return {"metrics": METRIC_INFO, "thresholds": ENV_THRESHOLDS, "levels": LEVEL_NAMES}


# ==============================================================================
# 告警域
# ==============================================================================


@router.get("/alarms", summary="告警列表（分页）")
def get_alarms(page: int = 1, page_size: int = 20, cabin: str = None, status: str = None, metric: str = None):
    """告警列表（默认按时间倒序，支持级别/舱室/状态过滤）"""
    validate_cabin(cabin)
    if status is not None and status not in ("未处理", "处理中", "已处理"):
        raise HTTPException(status_code=422, detail="status 必须是 未处理/处理中/已处理")
    result = tstore.list_alarms(page, page_size, cabin or "", status or "", metric or "")
    return {"data": result["data"], "total": result["total"]}


@router.get("/alarms/stats", summary="告警统计")
def get_alarm_stats():
    """按严重度/指标/舱室三维统计"""
    alarms = sim.get_snapshot()["alarms"]
    by_severity, by_metric, by_cabin = {}, {}, {}
    for alarm in alarms:
        by_severity[alarm["severity"]] = by_severity.get(alarm["severity"], 0) + 1
        by_metric[alarm["metric_name"]] = by_metric.get(alarm["metric_name"], 0) + 1
        cabin_key = alarm["cabin"] or "公共区域"
        by_cabin[cabin_key] = by_cabin.get(cabin_key, 0) + 1
    return {
        "total": len(alarms),
        "unhandled": sum(1 for a in alarms if a["status"] == "未处理"),
        "by_severity": [{"name": k, "count": v} for k, v in by_severity.items()],
        "by_metric": sorted(({"name": k, "count": v} for k, v in by_metric.items()),
                            key=lambda x: x["count"], reverse=True),
        "by_cabin": [{"name": k, "count": v} for k, v in by_cabin.items()],
    }


@router.post("/alarms/{alarm_id}/ack", summary="确认告警")
def acknowledge_alarm(alarm_id: str):
    """将告警标记为已处理"""
    alarm = sim.acknowledge_alarm(alarm_id)
    if alarm is None:
        # Try store layer as fallback
        existing = tstore.get_alarm(alarm_id)
        if existing is None:
            raise HTTPException(status_code=404, detail="告警不存在: %s" % alarm_id)
        updated = tstore.update_alarm(alarm_id, {"status": "已处理"})
        return {"status": "success", "message": "告警已确认", "alarm": updated}
    return {"status": "success", "message": "告警已确认", "alarm": alarm}


# ==============================================================================
# 管线管理域
# ==============================================================================


@router.get("/pipelines", summary="管线台账（分页）")
def get_pipelines(page: int = 1, page_size: int = 20, pipeline_type: str = None, cabin: str = None, status: str = None):
    """管线台账列表，可按类型/舱室/状态过滤"""
    validate_cabin(cabin)
    if pipeline_type is not None and pipeline_type not in PIPELINE_TYPES:
        raise HTTPException(status_code=422,
                            detail="pipeline_type 必须是 %s 之一" % "/".join(PIPELINE_TYPES))
    result = tstore.list_pipelines(page, page_size, cabin or "", pipeline_type or "", status or "")
    return {"data": result["data"], "total": result["total"]}


@router.get("/pipelines/{pipeline_id}", summary="管线详情")
def get_pipeline_detail(pipeline_id: str):
    pipeline = tstore.get_pipeline(pipeline_id)
    if pipeline is None:
        raise HTTPException(status_code=404, detail="管线不存在: %s" % pipeline_id)
    return pipeline


@router.post("/pipelines", summary="新增管线")
def create_pipeline(request: PipelineCreateRequest):
    """新增入廊管线，自动编号并即时重算冲突"""
    data = request.model_dump() if hasattr(request, "model_dump") else request.dict()
    validate_pipeline_fields(data)
    # Auto-generate pipeline_id like the old sim.add_pipeline
    cabin = data["cabin"]
    prefix = "PL-%s-" % cabin
    existing_pipes = [p for p in sim.get_pipelines() if p["pipeline_id"].startswith(prefix)]
    max_seq = 0
    for pipe in existing_pipes:
        try:
            max_seq = max(max_seq, int(pipe["pipeline_id"].split("-")[-1]))
        except ValueError:
            continue
    data["pipeline_id"] = "PL-%s-%03d" % (cabin, max_seq + 1)
    data["commission_date"] = datetime.now().strftime("%Y-%m-%d")
    pipeline = tstore.create_pipeline(data)
    # Also sync into in-memory list for conflict detection
    sim_sync = dict(data)
    sim._pipelines.append(sim_sync)
    conflicts = detect_conflicts(sim.get_pipelines())
    related = [c for c in conflicts if pipeline["pipeline_id"] in c["pipeline_ids"]]
    return {"status": "success", "pipeline": pipeline,
            "conflict_count": len(conflicts), "related_conflicts": related}


@router.put("/pipelines/{pipeline_id}", summary="更新管线")
def update_pipeline(pipeline_id: str, request: PipelineUpdateRequest):
    """局部更新管线字段"""
    data = {k: v for k, v in
            (request.model_dump() if hasattr(request, "model_dump") else request.dict()).items()
            if v is not None}
    merged = tstore.get_pipeline(pipeline_id)
    if merged is None:
        raise HTTPException(status_code=404, detail="管线不存在: %s" % pipeline_id)
    merged.update(data)
    validate_pipeline_fields(merged)
    updated = tstore.update_pipeline(pipeline_id, data)
    if updated is None:
        raise HTTPException(status_code=404, detail="管线不存在: %s" % pipeline_id)
    return {"status": "success", "pipeline": updated,
            "conflict_count": len(detect_conflicts(sim.get_pipelines()))}


@router.delete("/pipelines/{pipeline_id}", summary="删除管线")
def delete_pipeline(pipeline_id: str):
    if not tstore.delete_pipeline(pipeline_id):
        raise HTTPException(status_code=404, detail="管线不存在: %s" % pipeline_id)
    return {"message": "管线已删除"}


@router.get("/pipelines/conflicts", summary="空间冲突检测")
def get_pipeline_conflicts():
    """当前台账的全量冲突检测结果"""
    conflicts = detect_conflicts(sim.get_pipelines())
    return {"total": len(conflicts), "conflicts": conflicts}


@router.post("/pipelines/conflicts/precheck", summary="拟入廊冲突预判")
def precheck_pipeline_conflicts(request: PipelineCreateRequest):
    """提交拟入廊管线信息，返回与现有管线的冲突预判（不实际写入）"""
    data = request.model_dump() if hasattr(request, "model_dump") else request.dict()
    validate_pipeline_fields(data)
    candidate = dict(data)
    candidate["pipeline_id"] = "PL-PRECHECK"
    conflicts = detect_conflicts(sim.get_pipelines() + [candidate])
    related = [c for c in conflicts if "PL-PRECHECK" in c["pipeline_ids"]]
    return {"candidate": candidate, "related_conflicts": related,
            "conflict_count": len(related)}


# ==============================================================================
# 安防域
# ==============================================================================


@router.get("/security/overview", summary="安防总览")
def get_security_overview():
    security = sim.get_snapshot()["security"]
    return {
        "in_tunnel_count": security["in_tunnel_count"],
        "gates": security["gates"],
        "broadcast": security["broadcast"],
        "intrusion_count": len(security["intrusions"]),
        "unhandled_intrusions": sum(1 for i in security["intrusions"]
                                    if i["status"] == "未处理"),
        "today_access_count": len(security["access_records"]),
    }


@router.get("/security/access", summary="门禁出入记录（分页）")
def get_access_records(page: int = 1, page_size: int = 20, gate_id: str = "", person_id: str = ""):
    result = tstore.list_access_records(page, page_size, gate_id, person_id)
    return {"data": result["data"], "total": result["total"]}


@router.post("/security/access", summary="登记出入记录")
def create_access_record(request: AccessRecordRequest):
    """手动登记一条门禁出入记录（模拟刷卡），自动联动在廊人数"""
    if request.gate_id not in {g["gate_id"] for g in ACCESS_GATES}:
        raise HTTPException(status_code=422,
                            detail="gate_id 必须是 %s 之一"
                                   % "/".join(g["gate_id"] for g in ACCESS_GATES))
    if request.direction not in ("进", "出"):
        raise HTTPException(status_code=422, detail="direction 必须是 进 或 出")
    if not request.person_id or len(request.person_id) > 32:
        raise HTTPException(status_code=422, detail="person_id 不能为空且长度≤32")
    record = sim.register_access(request.model_dump()
                                 if hasattr(request, "model_dump") else request.dict())
    return {"status": "success", "record": record}


@router.get("/security/intrusions", summary="入侵检测告警")
def get_intrusions(limit: int = 20):
    if not 1 <= limit <= 100:
        raise HTTPException(status_code=422, detail="limit 必须在 1~100")
    intrusions = sim.get_snapshot()["security"]["intrusions"][:limit]
    return {"total": len(intrusions), "intrusions": intrusions}


@router.get("/security/broadcast", summary="应急广播状态")
def get_broadcast():
    return sim.get_snapshot()["security"]["broadcast"]


@router.post("/security/broadcast/test", summary="广播自检")
def test_broadcast():
    broadcast = sim.test_broadcast()
    return {"status": "success", "message": "广播自检完成", "broadcast": broadcast}


# ==============================================================================
# 工作流域（管廊大数据管道编排）
# ==============================================================================


def run_tunnel_pipeline(count, output_dir):
    """后台执行管廊数据管道：生成 → 加载Hive → ETL → Kafka"""
    date_tag = datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(output_dir, "tunnel_sensor_%s.log" % date_tag)
    steps = [
        ("数据生成", 15, [sys.executable,
                          os.path.join(PROJECT_ROOT, "src", "python",
                                       "generate_tunnel_logs.py"),
                          "--count", str(count), "--output", output_dir]),
        ("加载到Hive", 40, ["bash", os.path.join(PROJECT_ROOT, "scripts",
                                                "load_tunnel_data_to_hive.sh")]),
        ("ETL分析", 70, ["bash", os.path.join(PROJECT_ROOT, "scripts",
                                              "etl_tunnel.sh")]),
        ("发送到Kafka", 90, [sys.executable,
                             os.path.join(PROJECT_ROOT, "src", "python",
                                          "tunnel_kafka_producer.py"),
                             "--input", log_file, "--speed", "10"]),
    ]
    try:
        for name, progress, command in steps:
            workflow_status["current_step"] = name
            workflow_status["progress"] = progress
            workflow_status["message"] = "正在执行: %s" % name
            result = subprocess.run(command, capture_output=True, text=True,
                                    timeout=WORKFLOW_TIMEOUT, cwd=PROJECT_ROOT)
            if result.returncode != 0:
                raise RuntimeError("%s 失败: %s" % (name, result.stderr[-500:]))
        workflow_status["current_step"] = "完成"
        workflow_status["progress"] = 100
        workflow_status["message"] = "管廊数据管道执行完成（%d 条）" % count
    except Exception as exc:
        workflow_status["current_step"] = "失败"
        workflow_status["message"] = str(exc)
        workflow_status["error"] = str(exc)
    finally:
        workflow_status["running"] = False


@router.get("/workflow/status", summary="管道工作流状态")
def get_workflow_status():
    return workflow_status


@router.post("/workflow/run", summary="执行管廊数据管道")
def run_workflow(count: int = 50000, background_tasks: BackgroundTasks = None):
    """一键执行：生成管廊数据 → 加载Hive → ETL → 发送Kafka（需大数据集群在线）"""
    if workflow_status["running"]:
        raise HTTPException(status_code=400, detail="工作流正在运行中，请等待完成")
    if not 1000 <= count <= 1000000:
        raise HTTPException(status_code=422, detail="count 必须在 1000~1000000")
    workflow_status["running"] = True
    workflow_status["start_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    workflow_status["error"] = None
    if background_tasks:
        background_tasks.add_task(run_tunnel_pipeline, count,
                                  os.path.join("data", "logs"))
        return {"status": "started", "message": "管廊数据管道已启动",
                "count": count, "estimated_time": "约3-5分钟"}
    run_tunnel_pipeline(count, os.path.join("data", "logs"))
    return {"status": "finished", "message": workflow_status["message"]}


# ==============================================================================
# Excel 导入/导出（管廊管控）
# ==============================================================================

@router.get("/pipelines/export", summary="导出管线台账 Excel")
def export_pipelines():
    from common.excel_utils import download_xlsx
    data = tstore.list_pipelines(page=1, page_size=99999)["data"]
    return download_xlsx(data, "tunnel_pipelines.xlsx", "管线台账")

@router.post("/pipelines/import", summary="从 Excel 导入管线台账")
def import_pipelines(file: UploadFile = File(...)):
    content = file.file.read()
    from common.excel_utils import import_from_excel
    parsed = import_from_excel(content)
    created = []
    for row in parsed["rows"]:
        try:
            tstore.create_pipeline(row)
            created.append(row)
        except Exception:
            pass
    # Sync into memory for conflict detection
    sim._reload()
    return {"status": "success", "imported": len(created), "total_rows": len(parsed["rows"])}

@router.get("/alarms/export", summary="导出环境告警 Excel")
def export_alarms():
    from common.excel_utils import download_xlsx
    data = tstore.list_alarms(page=1, page_size=99999)["data"]
    return download_xlsx(data, "tunnel_alarms.xlsx", "环境告警")

@router.get("/security/access/export", summary="导出门禁记录 Excel")
def export_access_records():
    from common.excel_utils import download_xlsx
    data = tstore.list_access_records(page=1, page_size=99999)["data"]
    return download_xlsx(data, "tunnel_access.xlsx", "门禁记录")
