# -*- coding: utf-8 -*-
"""
models.py — Pydantic 请求模型
=============================
字段注释会直接展示在 /docs 接口文档中。
"""
from typing import Optional

from pydantic import BaseModel, Field

STAGES = ("采购", "施工", "运维", "改造", "报废")


# --------------------------- 2. 全生命周期档案 ---------------------------
class LifecycleCreateReq(BaseModel):
    asset_id: int = Field(..., description="资产 ID")
    stage: str = Field(..., description="阶段：采购/施工/运维/改造/报废")
    occurred_at: str = Field(..., description="发生日期 YYYY-MM-DD")
    responsible: str = Field("", description="责任单位/人")
    description: str = Field("", description="事件描述")
    attachment: str = Field("", description="附件名称（合同/验收单/维修记录等）")
    cost: float = Field(0, ge=0, description="费用（元）")


class LifecycleUpdateReq(BaseModel):
    stage: Optional[str] = None
    occurred_at: Optional[str] = None
    responsible: Optional[str] = None
    description: Optional[str] = None
    attachment: Optional[str] = None
    cost: Optional[float] = None


# --------------------------- 3. 资产盘点 ---------------------------
class InventoryTaskCreateReq(BaseModel):
    method: str = Field(..., description="盘点方式：扫码盘点 / 巡检盘点")
    scope: str = Field("全城管段", description="盘点范围（区域或说明）")
    scope_region: Optional[str] = Field(None, description="按区域圈定盘点资产，缺省为全部资产")
    operator: str = Field(..., description="盘点人")


class ScanCheckReq(BaseModel):
    asset_code: str = Field(..., description="扫码得到的资产编号")


class ItemHandleReq(BaseModel):
    handle_status: str = Field(..., description="差异处理方式：补录 / 修正 / 报废")
    remark: str = Field("", description="处理说明")


# --------------------------- 4. 资产权属管理 ---------------------------
class OwnershipUpdateReq(BaseModel):
    property_unit: Optional[str] = Field(None, description="产权单位")
    property_nature: Optional[str] = Field(None, description="产权性质：国有/集体/企业")
    property_cert_no: Optional[str] = Field(None, description="产权证书编号")
    operation_unit: Optional[str] = Field(None, description="运维单位")
    operation_contract_no: Optional[str] = Field(None, description="运维合同编号")
    supervision_unit: Optional[str] = Field(None, description="监管单位")
    responsibility_boundary: Optional[str] = Field(None, description="责任边界说明")
    handover_at: Optional[str] = Field(None, description="交接时间 YYYY-MM")
