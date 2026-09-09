#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""故障预报与寿命预测子模块

前缀 /api/failure-predictions，替代从不启动的 Java alarm-warning-service，
为前端「故障预报与寿命预测」页面提供设备健康度、故障概率、剩余寿命数据。
"""

from .routes import router  # noqa: F401
