# 供水管网精细化管控子模块（后端 water_supply_control）

城市生命线管网 AI 智慧平台 — 供水管道运行监控、漏损治理、水质溯源、压力调度、爆管风险评估。

## 技术栈
- FastAPI + SQLite（Python 3.13 验证通过）
- 端口：8004

## 目录结构
```
water_supply_control/
├── routers/          # 7 组业务路由
│   ├── monitor.py    # 功能1 实时运行监测
│   ├── dma.py        # 功能2 DMA分区漏损管理
│   ├── quality.py    # 功能3 水质全流程溯源
│   ├── pressure.py   # 功能4 智能压力调度
│   ├── secondary.py  # 功能5 二次供水管控
│   ├── hydrant.py    # 功能6 消防栓专项管理
│   └── burst.py      # 功能7 爆管影响分析
├── database.py       # 建表与连接
├── models.py         # Pydantic 请求模型
├── main.py           # 应用入口 + /api/summary
├── seed.py           # 模拟数据播种（≥30条/表）
├── requirements.txt
└── water_supply.db   # 运行 seed.py 后生成
```

## 启动步骤
```bash
# 1. 安装依赖（或使用已含 fastapi/uvicorn 的虚拟环境）
pip install -r requirements.txt

# 2. 播种模拟数据（生成 water_supply.db）
python seed.py

# 3. 启动服务（端口 8004）
python main.py
# 或：uvicorn main:app --host 0.0.0.0 --port 8004
```

接口文档：http://localhost:8004/docs

## 主要接口
| 模块 | 接口 | 说明 |
|---|---|---|
| 汇总 | GET /api/summary | 顶部统计卡片 |
| 监测 | POST /api/monitor/data | 采集并自动研判告警 |
| 监测 | GET /api/monitor/latest /history /alarms /alarm-trend /stats | 实时/历史/告警 |
| DMA | GET /api/dma/zones /records /stats；POST /api/dma/records；POST /api/dma/zones/{id}/locate | 分区漏损 |
| 水质 | GET /api/quality/chain /records /stats；POST /api/quality/data | 全链路溯源 |
| 压力 | GET /api/pressure/stations /plans /stats；POST /api/pressure/plan；POST /api/pressure/plans/{id}/apply | 智能调度 |
| 二供 | GET /api/secondary/units /stats；POST /api/secondary/data | 二次供水 |
| 消防栓 | GET /api/hydrant/list /options /{id}/events /stats/summary；POST /api/hydrant；PUT /api/hydrant/{id}；POST /api/hydrant/{id}/test | 台账+监测 |
| 爆管 | GET /api/burst/cases /{id}/valves /stats/summary；POST /api/burst/predict；POST /api/burst/{id}/handle | 风险+关阀方案 |
