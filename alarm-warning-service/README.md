# alarm-warning-service

城市综合管廊分级分类预警引擎服务。消费上游管廊监测数据和燃气风险事件，执行规则匹配、四级预警判定、根因分析、降噪聚合、动态优先级计算，并提供预警事件 REST API 查询与管理。

## 技术栈

| 组件 | 版本 |
|---|---|
| Java | 17 |
| Spring Boot | 3.2.5 |
| MyBatis-Plus | 3.5.5 |
| MySQL | 8.0+ |
| Kafka | 3.x |
| Redis | 7.x |

## 系统架构

```
tunnel-service ──┬── tunnel-sensor-topic ──┐
                 └── tunnel-alarm-topic ────┤
                                            ├──► alarm-warning-service ──► alert-event-topic
gas-risk-service ──── gas-risk-event-topic ─┘
```

### 核心处理流程

```
Kafka 消息
  → 消息解析（KafkaMessage）
  → 规则匹配（RuleMatchService）
  → 根因分析（RootCauseService）
  → 降噪去重（AlertDedupService，Redis 滑动窗口）
  → 优先级计算（PriorityCalcService）
  → 预警事件入库（AlertEvent）
  → 聚合组管理（AlertGroup）
  → 产出消息（AlertEventProducer → alert-event-topic）
```

### 四级预警

| 等级 | 说明 |
|---|---|
| BLUE | 最低级别预警 |
| YELLOW | 一般预警 |
| ORANGE | 严重预警 |
| RED | 特别严重预警 |

## 快速启动

### 前置条件

- JDK 17+
- Maven 3.8+
- MySQL 8.0+
- Kafka 3.x
- Redis 7.x

### 1. 初始化数据库

```bash
mysql -uroot -p --default-character-set=utf8mb4 < sql/init.sql
```

### 2. 创建 Kafka Topic

```bash
kafka-topics.sh --create --topic tunnel-sensor-topic --partitions 3 --replication-factor 1 --bootstrap-server localhost:9092
kafka-topics.sh --create --topic tunnel-alarm-topic --partitions 3 --replication-factor 1 --bootstrap-server localhost:9092
kafka-topics.sh --create --topic gas-risk-event-topic --partitions 3 --replication-factor 1 --bootstrap-server localhost:9092
kafka-topics.sh --create --topic alert-event-topic --partitions 3 --replication-factor 1 --bootstrap-server localhost:9092
```

### 3. 配置环境变量

| 变量 | 默认值 | 说明 |
|---|---|---|
| `MYSQL_HOST` | localhost | MySQL 地址 |
| `MYSQL_PORT` | 3306 | MySQL 端口 |
| `MYSQL_USER` | root | 数据库用户 |
| `MYSQL_PASSWORD` | 123456 | 数据库密码 |
| `KAFKA_BOOTSTRAP_SERVERS` | localhost:9092 | Kafka 地址 |
| `REDIS_HOST` | localhost | Redis 地址 |
| `REDIS_PORT` | 6379 | Redis 端口 |
| `REDIS_PASSWORD` | (空) | Redis 密码 |

### 4. 启动服务

```bash
mvn spring-boot:run -Dspring-boot.run.profiles=dev
```

服务启动后监听 `http://localhost:8085`。

## REST API

### 预警事件

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/alerts?page=1&size=10&alertLevel=&status=&areaId=` | 预警事件列表（分页） |
| GET | `/api/alerts/{id}` | 预警事件详情 |
| PATCH | `/api/alerts/{id}/status` | 更新预警状态 |

状态流转：`OPEN → ACKNOWLEDGED → RESOLVED → CLOSED`

### 预警聚合组

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/alert-groups?page=1&size=10&areaId=` | 聚合组列表（分页） |
| GET | `/api/alert-groups/{id}` | 聚合组详情 |

### 预警规则

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/alert-rules?page=1&size=10&deviceType=&alertLevel=&enabled=` | 规则列表（分页） |
| POST | `/api/alert-rules` | 创建规则 |
| PUT | `/api/alert-rules/{id}` | 更新规则 |
| DELETE | `/api/alert-rules/{id}` | 删除规则 |

### 区域优先级

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/area-priority` | 区域优先级列表 |

### 统一响应格式

```json
{
  "code": 200,
  "message": "success",
  "data": {},
  "timestamp": 1725100800000
}
```

### 错误码

| 错误码 | 含义 |
|---|---|
| 400 | 请求参数错误 |
| 40201 | 预警规则不存在 |
| 40202 | 预警规则已停用 |
| 40203 | 阈值配置不合法 |
| 40204 | 预警事件不存在 |
| 40205 | 预警状态流转不合法 |

## Kafka 消息协议

消费上游消息格式遵循 `docs/kafka-protocol.md` 规范：

```json
{
  "eventId": "tunnel-service-uuid",
  "source": "tunnel-service",
  "deviceId": "SENSOR-P-001",
  "deviceType": "PRESSURE",
  "location": { "zone": "ZONE-A01", "areaId": "AREA-A01" },
  "timestamp": 1725100800000,
  "eventType": "SENSOR_DATA",
  "metrics": { "pressure": 3.8 },
  "healthScore": 85.5
}
```

消费 Topic：

| Topic | eventType | 处理逻辑 |
|---|---|---|
| `tunnel-sensor-topic` | `SENSOR_DATA` | 实时规则匹配，判定四级预警 |
| `tunnel-alarm-topic` | `ALARM_EVENT` | 接收已有告警，补充预警分析 |
| `gas-risk-event-topic` | `GAS_RISK_EVENT` | 接收燃气风险事件，纳入预警体系 |

产出 Topic：

| Topic | eventType | 说明 |
|---|---|---|
| `alert-event-topic` | `ALERT_CREATED` | 预警事件生成后广播 |

## 降噪聚合

同一 `areaId` 在 10 分钟滑动窗口内的多条预警合并为一个 `alert_group`，取最高预警等级作为组等级。窗口时间可通过 `alert.dedup.window-minutes` 配置。

## 动态优先级

```
优先级 = 预警等级权重 × 20 + 区域重要度 × 15 + 人口权重 × 10 + 时段权重 × 5
```

分数限制在 1-100 之间。

## 测试

```bash
mvn test
```

当前共 89 个单元测试，覆盖：

| 模块 | 测试数 |
|---|---|
| Kafka Consumer | 5 |
| RuleMatchService | 8 |
| AlertEngineService | 18 |
| RootCauseService | 10 |
| AlertDedupService | 8 |
| PriorityCalcService | 8 |
| AlertService | 8 |
| AlertGroupService | 3 |
| AlertRuleService | 8 |
| AlertController | 4 |
| AlertGroupController | 2 |
| AlertRuleController | 5 |
| AreaPriorityController | 2 |

## 项目结构

```
src/main/java/com/utc/alert/
├── AlertApplication.java              # 启动类
├── common/
│   ├── ErrorCode.java                 # 统一错误码
│   ├── config/
│   │   ├── JacksonConfig.java         # JSON 配置
│   │   ├── KafkaConfig.java           # Kafka 消费者配置
│   │   └── MybatisPlusConfig.java     # 分页插件配置
│   ├── enums/                         # 枚举（AlertLevel, AlertStatus, EventType, RootCauseType）
│   ├── exception/                     # 异常处理（BusinessException, GlobalExceptionHandler）
│   └── result/Result.java            # 统一响应封装
├── controller/                        # REST 控制器（Alert, AlertGroup, AlertRule, AreaPriority）
├── dto/
│   ├── kafka/                         # Kafka 消息 DTO（KafkaMessage, LocationInfo）
│   ├── request/                       # 请求 DTO
│   ├── response/                      # 响应 DTO（含 PageResponse）
│   └── MatchResult, RootCauseResult   # 内部 DTO
├── entity/                            # 数据库实体（AlertEvent, AlertGroup, AlertRule, AreaPriority）
├── kafka/
│   ├── consumer/                      # Kafka 消费者（TunnelSensor, TunnelAlarm, GasRiskEvent）
│   └── producer/                      # Kafka 生产者（AlertEventProducer）
├── mapper/                            # MyBatis-Plus Mapper
└── service/
    ├── impl/                          # 服务实现
    └── *.java                         # 服务接口
```

## 规范文档

| 文档 | 说明 |
|---|---|
| `docs/kafka-protocol.md` | Kafka 通信协议规范 |
| `docs/service-interface.md` | 服务接口设计规范 |
| `docs/integration-guide.md` | 联调指南 |
| `docs/coding-standard.md` | 编码规范 |
