# 燃气管网安全风控系统（后端）

基于 **Python FastAPI + SQLite** 的燃气管网安全风控子模块，覆盖 8 项核心功能，
内置毫秒级数据模拟引擎，开箱即用、可直接运行。

## 快速开始

```bash
cd gas_risk_control

# 1. 创建虚拟环境并安装依赖
python -m venv .venv
# Windows:
.venv\Scripts\pip install -r requirements.txt
# Linux/macOS:
# .venv/bin/pip install -r requirements.txt

# 2. 启动服务
.venv\Scripts\python main.py        # Windows
# .venv/bin/python main.py          # Linux/macOS
```

- 接口文档（Swagger）：http://localhost:8000/docs
- 前端页面：用浏览器直接打开 `../gas_risk_frontend/index.html`
  （或用 `python -m http.server 3000` 托管前端目录）

首次启动会自动创建 `gas_risk.db`、初始化表结构与演示数据，
后台线程每秒写入一帧各监测站的毫秒级监测数据。

## 8 项功能与接口

| # | 功能 | 路由前缀 | 主要接口 |
|---|------|----------|----------|
| 1 | 实时安全监测 | `/api/monitoring` | `GET /realtime` 实时六参数据（浓度/压力/流量/振动/腐蚀/位移）、`GET /history` 历史曲线、`GET /alarms` 报警、`POST /data` 外部上报、`POST /simulate-leak` 注入泄漏演示 |
| 2 | 微泄漏精准定位 | `/api/leak` | `POST /locate-by-concentration` 高斯扩散模型反演、`POST /locate-by-pressure-wave` 负压波时差法、`POST /demo` 双方法对比演示、`GET /records` 定位历史 |
| 3 | 泄漏扩散仿真 | `/api/diffusion` | `POST /simulate` 高斯烟羽浓度场（风速/气压/稳定度）、`POST /explosion-range` 爆炸危险范围（LEL/UEL 分区 + 疏散半径） |
| 4 | 第三方破坏预警 | `/api/third-party` | `POST /event` 施工扰动上报与分级、`POST /simulate` 模拟事件、`GET /warnings` 告警列表、`GET /realtime` 分段扰动态势 |
| 5 | 用户端用气安全 | `/api/user-safety` | `POST /scan` 全网扫描（熄火/微泄漏/过流/CO）、`GET /users` 风险清单、`GET /history` 表具曲线、`POST /simulate-anomaly` 注入异常 |
| 6 | 占压隐患管理 | `/api/occupation` | `GET/POST /records` 台账、`PUT /records/{id}`、`POST /records/{id}/rectify` 整改跟踪、`GET /records/{id}/timeline` 闭环时间线、`GET /stats` 统计 |
| 7 | 阴极保护监测 | `/api/cathodic` | `GET /realtime` 电位/电流 + 评价、`GET /evaluate` 防护效果评估（-0.85V~-1.2V 准则）、`POST /data` 上报、`GET /history` 趋势、`POST /simulate-data` 生成数据 |
| 8 | 应急联动关阀 | `/api/emergency` | `POST /trigger` 生成级联关阀方案、`POST /events/{id}/execute` 执行关阀、`POST /events/{id}/restore` 恢复供气、`GET /valves` 阀门状态、`GET /events` 事件记录 |

完整字段说明见 `/docs`。

## 演示流程建议

1. 打开前端「实时安全监测」页 → 点击 **模拟泄漏**，观察浓度骤升、报警弹出；
2. 打开「微泄漏精准定位」→ 点击演示，浓度扩散模型与压力波法给出定位结果；
3. 「泄漏扩散仿真」→ 调整风速/气压/稳定度，观察爆炸危险区范围变化；
4. 「应急联动关阀」→ 输入泄漏桩号触发预案，执行级联关阀，隔离泄漏段。

## 技术说明

- **数据存储**：SQLite（标准库 sqlite3，WAL 模式），首次启动自动建表并注入种子数据。
- **数据模拟**：`simulator.py` 后台线程每秒为 7 个监测站生成一帧带毫秒时间戳的数据
  （均值回归随机游走 + 故障注入），并按阈值规则评估报警。
- **定位算法**：浓度法对 `c(x)=A·exp(-(x-μ)²/2σ²)+b` 做最小二乘网格搜索反演 μ；
  压力波法 `x=(L+v·Δt)/2`。
- **扩散仿真**：Briggs 乡村扩散系数的高斯烟羽模型，体积浓度按环境气压/温度换算，
  按甲烷爆炸极限 5%~15%VOL 划分爆炸区/过富集区/警戒区。
- **无重型依赖**：仅 fastapi + uvicorn，算法全部用纯 Python 实现。

## 目录结构

```
gas_risk_control/
├── main.py              # 服务入口（生命周期、CORS、路由注册）
├── database.py          # SQLite 建表、种子数据
├── simulator.py         # 毫秒级数据模拟 + 报警评估
├── models.py            # Pydantic 请求模型
├── requirements.txt
└── routers/
    ├── monitoring.py    # 1 实时安全监测
    ├── leak.py          # 2 微泄漏精准定位
    ├── diffusion.py     # 3 泄漏扩散仿真
    ├── third_party.py   # 4 第三方破坏预警
    ├── user_safety.py   # 5 用户端用气安全
    ├── occupation.py    # 6 占压隐患管理
    ├── cathodic.py      # 7 阴极保护监测
    └── emergency.py     # 8 应急联动关阀
```
