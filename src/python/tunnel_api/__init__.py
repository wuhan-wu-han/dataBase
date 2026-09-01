# -*- coding: utf-8 -*-
"""
地下综合管廊管控子模块

包含数据模型（models）、实时模拟引擎（simulator）、
空间冲突检测（conflict）与 API 路由（routes）。

注意：模拟引擎依赖进程内全局状态，部署必须保持单 worker
（uvicorn main:app，不加 --workers），否则多进程间数据不一致。
"""

from .routes import router
from .simulator import start_simulator

# 启动后台模拟线程（异常兜底，失败不阻断主服务）
try:
    start_simulator()
except Exception as exc:
    print("⚠ 管廊模拟引擎启动异常: %s" % exc)

__all__ = ["router"]
