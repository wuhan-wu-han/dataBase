#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数字化预案管理子模块（5.1）

导出 router 并在导入时启动后台引擎（引擎启动失败不阻断路由注册）。
部署约束：依赖单 worker 部署（进程内全局状态）。
"""

from .routes import router

try:
    from . import simulator as _simulator
    _simulator.start_engine()
except Exception as _exc:  # pragma: no cover - 兜底不阻断主服务
    import sys
    print("[plan_api] 后台引擎启动失败，实时联动不可用：%s" % _exc, file=sys.stderr)
