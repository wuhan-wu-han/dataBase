#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""故障预报与寿命预测 —— API 路由

前缀 /api/failure-predictions，对齐前端 api/request.js 的统一响应契约
{code:200, data:..., message:...}（拦截器只认 code==200 并返回 data）。

路由顺序：/statistics、/generate 必须先于 /{prediction_id} 注册，
否则会被动态段捕获。
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query

from . import store

router = APIRouter(prefix="/api/failure-predictions", tags=["故障预报与寿命预测"])


def _ok(data: Any, message: str = "success") -> Dict[str, Any]:
    return {"code": 200, "data": data, "message": message}


@router.get("", summary="预测记录列表（分页 + 等级过滤）")
def list_predictions(page: int = Query(1, ge=1),
                     size: int = Query(10, ge=1, le=200),
                     predictionLevel: Optional[str] = None):
    store.seed_if_empty()
    return _ok(store.query_list(page=page, size=size, prediction_level=predictionLevel))


@router.get("/statistics", summary="预测统计（设备总数/风险分布/均值）")
def prediction_statistics():
    store.seed_if_empty()
    return _ok(store.statistics())


@router.post("/generate", summary="生成预测（刷新预测时间并返回最高风险设备）")
def generate_prediction():
    store.seed_if_empty()
    result = store.generate()
    if result is None:
        return _ok(None, "无预警事件数据，无法生成预测")
    return _ok(result, "预测生成成功")


@router.get("/{prediction_id}", summary="预测详情")
def prediction_detail(prediction_id: int):
    store.seed_if_empty()
    record = store.get_detail(prediction_id)
    if record is None:
        raise HTTPException(status_code=404, detail="预测记录不存在：%s" % prediction_id)
    return _ok(record)
