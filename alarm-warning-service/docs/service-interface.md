# 服务接口设计规范

> 版本：v2.0
> 更新日期：2026-08-31
> 适用范围：tunnel-service / gas-risk-service / alarm-warning-service

---

## 1. 服务职责划分

### 1.1 tunnel-service（管廊监测服务）

| 职责 | 说明 |
|---|---|
| 管廊传感器数据采集 | 对接管廊内各类传感器硬件，采集原始监测数据 |
| Kafka 生产 | 通过 Kafka 向下游服务发送传感器数据和告警事件 |

**已实现 Topic：**

| Topic | 用途 |
|---|---|
| `tunnel-sensor-topic` | 管廊全量传感器数据 |
| `tunnel-alarm-topic` | 管廊异常告警数据 |

**不负责：** 预警等级判定、根因分析、降噪聚合

### 1.2 gas-risk-service（燃气风险分析服务）

| 职责 | 说明 |
|---|---|
| 燃气风险分析 | 基于历史数据和实时数据评估燃气管网风险等级 |
| 风险事件产生 | 产出燃气风险事件并通过 Kafka 上报 |

**规划 Topic：**

| Topic | 用途 |
|---|---|
| `gas-risk-event-topic` | 燃气风险事件数据 |

**不负责：** 管廊环境监测、预警等级判定

### 1.3 alarm-warning-service（分级分类预警引擎服务）

| 职责 | 说明 |
|---|---|
| 四级预警判断 | 消费上游数据，按规则判定蓝/黄/橙/红预警等级 |
| 根因分析 | 自动分析预警原因（腐蚀/泄漏/压力异常/施工破坏等） |
| 降噪聚合 | 同区域同时段多传感器告警合并去重 |
| 优先级计算 | 根据区域重要度、人口、时段计算处理优先级 |
| 预警查询 | 提供预警事件的分页查询、详情查看、状态管理 |

**规划 Topic：**

| Topic | 用途 |
|---|---|
| `alert-event-topic` | 预警引擎产出的预警事件 |

**不负责：** 原始数据采集、风险评估模型、设备管理

### 1.4 职责边界原则

- 每个服务只拥有自己的数据，不直接访问其他服务的数据库
- 服务间通过 Kafka 异步通信或通过 REST API 同步查询
- 上游服务不感知下游的处理逻辑

### 1.5 服务隔离约束（强制）

各服务之间**禁止直接依赖代码**，必须保持完全独立：

| 禁止行为 | 说明 |
|---|---|
| 复制对方代码 | 不得将其他服务的源码文件复制到本服务中使用 |
| 共享实体类 | 不得引用或复制其他服务的 Entity / DTO / VO 类 |
| 共享数据库表 | 不得直接读写其他服务的数据库表 |
| 直接依赖代码 | 不得通过 Maven / pip 等方式引入其他服务的模块 |

**服务间唯一允许的通信方式：**

| 通信方式 | 用途 |
|---|---|
| Kafka 消息 | 实时事件流传递（传感器数据、告警、风险事件、预警结果） |
| REST API | 同步查询与管理操作（设备详情、区域信息、状态管理） |

> 各服务独立定义自己的数据模型。即使多个服务存在语义相同的字段（如 `deviceId`、`areaId`），也应在各自服务中独立定义，通过 Kafka 消息协议和 REST API 契约保持字段语义一致。

---

## 2. 服务通信关系

### 2.1 通信关系图

```
tunnel-service
      |
      |  Kafka（tunnel-sensor-topic / tunnel-alarm-topic）
      |
      ▼
alarm-warning-service

gas-risk-service
      |
      |  Kafka（gas-risk-event-topic）
      |
      ▼
alarm-warning-service
```

### 2.2 通信方式说明

| 通信方式 | 用途 | 说明 |
|---|---|---|
| **Kafka** | 实时事件流 | 传感器数据上报、告警事件传递、风险事件传递、预警结果产出 |
| **REST API** | 查询、管理 | 设备详情查询、区域信息查询、预警规则管理、预警状态管理 |

**Kafka 适用场景：**

| 场景 | 原因 |
|---|---|
| 传感器数据实时上报 | 高频、高吞吐、允许少量延迟 |
| 告警/风险事件传递 | 异步处理、不阻塞生产者 |
| 预警结果广播 | 多个下游系统同时消费 |

**REST API 适用场景：**

| 场景 | 原因 |
|---|---|
| 查询设备/区域详情 | 需要即时响应、数据量小 |
| 配置管理（规则 CRUD） | 需要明确的成功/失败反馈 |
| 预警查询与状态管理 | 管理后台操作，需要即时反馈 |
| 服务健康检查 | 同步探活 |

### 2.3 调用原则

- 实时数据流一律走 Kafka，不走 HTTP
- 查询、管理操作走 REST API
- 生产者不关心消费者处理结果
- 上游服务不感知下游的处理逻辑

---

## 3. 端口规划

| 服务 | 端口 | 说明 |
|---|---|---|
| API Gateway | 8080 | 统一入口，路由转发 |
| tunnel-service | 8081 | 管廊监测服务 |
| gas-risk-service | 8082 | 燃气风险分析服务 |
| alarm-warning-service | 8085 | 预警引擎服务 |

### 3.1 端口分配原则

- 业务服务端口范围：`8080 - 8099`
- 基础设施端口使用官方默认端口（MySQL 3306、Kafka 9092、Redis 6379）
- 新增服务前在本文档中登记端口，避免冲突
- 开发环境各服务端口与生产保持一致

### 3.2 Gateway 路由规则（预留）

| 路径前缀 | 转发目标 |
|---|---|
| `/api/tunnel/**` | tunnel-service:8081 |
| `/api/gas/**` | gas-risk-service:8082 |
| `/api/alerts/**` | alarm-warning-service:8085 |
| `/api/alert-rules/**` | alarm-warning-service:8085 |

---

## 4. REST API 设计规范

### 4.1 URL 命名规范

```
/api/{资源名}              # 集合
/api/{资源名}/{id}         # 单个资源
/api/{资源名}/{id}/{子资源} # 子资源
```

规则：
- 资源名使用**小写复数**：`/api/alerts`、`/api/devices`
- 使用**连字符**分隔多词：`/api/alert-rules`
- 不使用动词：用 `POST /api/alerts` 而不是 `/api/createAlert`
- 嵌套不超过两层

### 4.2 请求方式

| 方法 | 用途 | 示例 |
|---|---|---|
| `GET` | 查询 | `GET /api/alerts?page=1&size=20` |
| `POST` | 创建 | `POST /api/alert-rules` |
| `PUT` | 全量更新 | `PUT /api/alert-rules/{id}` |
| `PATCH` | 部分更新 | `PATCH /api/alerts/{id}/status` |
| `DELETE` | 删除 | `DELETE /api/alert-rules/{id}` |

### 4.3 统一返回格式

**成功响应：**

```json
{
  "code": 200,
  "message": "success",
  "data": { }
}
```

**分页响应：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "records": [],
    "total": 100,
    "page": 1,
    "size": 20,
    "pages": 5
  }
}
```

**错误响应：**

```json
{
  "code": 40001,
  "message": "预警规则不存在",
  "data": null,
  "timestamp": 1725100800000,
  "path": "/api/alert-rules/999"
}
```

### 4.4 各服务 API 规划

#### tunnel-service（端口 8081）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/devices/{id}` | 查询设备详情 |
| GET | `/api/devices` | 设备列表 |
| GET | `/api/areas/{id}` | 查询区域信息 |
| GET | `/api/areas` | 区域列表 |

#### gas-risk-service（端口 8082）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/pipe-segments/{id}` | 查询管段详情 |
| GET | `/api/pipe-segments` | 管段列表 |
| GET | `/api/risk-assessment/{areaId}` | 查询区域风险评估 |

#### alarm-warning-service（端口 8085）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/alerts` | 预警事件列表（分页） |
| GET | `/api/alerts/{id}` | 预警事件详情 |
| PATCH | `/api/alerts/{id}/status` | 更新预警状态 |
| GET | `/api/alert-groups` | 预警聚合组列表 |
| GET | `/api/alert-groups/{id}` | 聚合组详情 |
| GET | `/api/alert-rules` | 预警规则列表 |
| POST | `/api/alert-rules` | 创建预警规则 |
| PUT | `/api/alert-rules/{id}` | 更新预警规则 |
| DELETE | `/api/alert-rules/{id}` | 删除预警规则 |
| GET | `/api/area-priority` | 区域优先级配置 |

---

## 5. 数据格式统一规则

### 5.1 字段命名

- 全部使用 **camelCase**（JSON 字段）
- 数据库字段使用 **snake_case**，ORM 层自动转换
- ID 字段统一命名为 `id`，类型为 `Long`
- 外键字段命名为 `{关联资源}Id`，如 `areaId`、`deviceId`

### 5.2 时间格式

| 场景 | 格式 | 示例 |
|---|---|---|
| Kafka 消息中的时间戳 | Unix 毫秒时间戳（Long） | `1725100800000` |
| REST API 请求/响应 | ISO 8601 字符串 | `"2026-08-31T15:30:00+08:00"` |
| 数据库存储 | `DATETIME`，UTC 存储 | `2026-08-31 07:30:00` |
| 日志输出 | ISO 8601 + 时区 | `2026-08-31T15:30:00.123+08:00` |

### 5.3 统一错误码

| 错误码范围 | 服务 | 说明 |
|---|---|---|
| `200` | 通用 | 成功 |
| `40001 - 40099` | tunnel-service | 业务错误 |
| `40101 - 40199` | gas-risk-service | 业务错误 |
| `40201 - 40299` | alarm-warning-service | 业务错误 |
| `50001 - 50099` | tunnel-service | 系统错误 |
| `50101 - 50199` | gas-risk-service | 系统错误 |
| `50201 - 50299` | alarm-warning-service | 系统错误 |

**通用错误码：**

| 错误码 | 含义 |
|---|---|
| `400` | 请求参数错误 |
| `401` | 未认证 |
| `403` | 无权限 |
| `404` | 资源不存在 |
| `500` | 服务内部错误 |

**业务错误码示例（alarm-warning-service）：**

| 错误码 | 含义 |
|---|---|
| `40201` | 预警规则不存在 |
| `40202` | 预警规则已停用 |
| `40203` | 阈值配置不合法 |
| `40204` | 预警事件不存在 |
| `40205` | 预警状态流转不合法 |

### 5.4 枚举值统一

| 枚举 | 值 | 说明 |
|---|---|---|
| 预警等级 | `BLUE` / `YELLOW` / `ORANGE` / `RED` | 大写字符串 |
| 预警状态 | `OPEN` / `ACKNOWLEDGED` / `RESOLVED` / `CLOSED` | 大写字符串 |
| 设备状态 | `ONLINE` / `OFFLINE` / `FAULT` | 大写字符串 |
| 根因分类 | `PRESSURE_ABNORMAL` / `GAS_LEAK` / `PIPELINE_CORROSION` / ... | 大写字符串 + 下划线 |

---

## 6. 健康检查与降级

### 6.1 健康检查端点

每个服务必须提供：

```
GET /actuator/health
```

返回：

```json
{
  "status": "UP",
  "components": {
    "db": { "status": "UP" },
    "kafka": { "status": "UP" },
    "redis": { "status": "UP" }
  }
}
```

### 6.2 服务依赖关系

```
alarm-warning-service
  ├── 依赖 Kafka（消费 tunnel-sensor-topic / tunnel-alarm-topic / gas-risk-event-topic）
  ├── 依赖 MySQL（存储预警数据）
  ├── 依赖 Redis（降噪缓存）
  ├── 可选依赖 tunnel-service（查询设备详情）
  └── 可选依赖 gas-risk-service（查询管段信息）
```

### 6.3 降级策略

- tunnel-service 或 gas-risk-service 不可用时，alarm-warning-service 应继续消费 Kafka 并正常处理
- REST 调用失败时使用缓存数据或返回默认值，不阻塞核心流程
- Kafka 消费失败时记录错误日志，不丢消息，支持重试
