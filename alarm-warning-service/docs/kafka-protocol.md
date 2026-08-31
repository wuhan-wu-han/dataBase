# Kafka 通信协议规范

> 版本：v2.0
> 更新日期：2026-08-31
> 适用范围：tunnel-service / gas-risk-service / alarm-warning-service

---

## 1. Kafka Topic 设计

### 1.1 已实现 Topic

以下 Topic 已由 tunnel-service 实现并投入使用：

| Topic 名称 | 生产者 | 消费者 | 数据用途 |
|---|---|---|---|
| `tunnel-sensor-topic` | tunnel-service | alarm-warning-service | 管廊全量传感器数据 |
| `tunnel-alarm-topic` | tunnel-service | alarm-warning-service | 管廊异常告警数据 |

### 1.2 规划 Topic

以下 Topic 为后续规划，尚未实现：

| Topic 名称 | 生产者 | 消费者 | 数据用途 |
|---|---|---|---|
| `gas-risk-event-topic` | gas-risk-service | alarm-warning-service | 燃气风险事件数据 |
| `alert-event-topic` | alarm-warning-service | 大屏 / APP / 推送服务 | 预警引擎产出的预警事件 |

### 1.3 Topic 规划原则

- 每个业务域独立 Topic，生产者拥有 Topic 的所有权
- Topic 命名格式：`{服务域}-{数据类型}-topic`
- 消费者组命名格式：`{消费服务名}`，每个消费服务使用独立 consumer group
- 所有 Topic 默认保留 7 天，分区数根据吞吐量评估

---

## 2. 统一消息格式

### 2.1 消息结构

所有 Kafka 消息统一使用以下格式：

```json
{
  "eventId": "",
  "source": "",
  "deviceId": "",
  "deviceType": "",
  "location": {
    "zone": "",
    "areaId": ""
  },
  "timestamp": "",
  "eventType": "",
  "alarmCode": "",
  "alarmLevel": "",
  "metrics": {},
  "healthScore": ""
}
```

### 2.2 字段说明表

| 字段名称 | 类型 | 是否必填 | 说明 |
|---|---|---|---|
| `eventId` | String | 是 | 全局唯一事件ID，格式：`{source}-{UUID}` |
| `source` | String | 是 | 来源服务标识，如 `tunnel-service`、`gas-risk-service` |
| `deviceId` | String | 是 | 设备/传感器唯一标识 |
| `deviceType` | String | 是 | 设备类型，如 `PRESSURE`、`TEMPERATURE`、`CH4`、`H2S` |
| `location` | Object | 是 | 位置信息 |
| `location.zone` | String | 是 | 区域分区，如管廊区段编号 |
| `location.areaId` | String | 是 | 统一区域标识，映射各服务的 cabin/zone/workshop |
| `timestamp` | Long | 是 | 事件产生时间，Unix 毫秒时间戳 |
| `eventType` | String | 是 | 事件类型，见 2.3 节 |
| `alarmCode` | String | 条件必填 | 告警编码，告警类事件必填 |
| `alarmLevel` | String | 条件必填 | 告警等级，告警类事件必填（BLUE / YELLOW / ORANGE / RED） |
| `metrics` | Object | 是 | 指标数据，键值对形式，key 为指标编码，value 为指标值 |
| `healthScore` | Double | 否 | 设备健康评分 0-100 |

### 2.3 eventType 枚举

| eventType | 说明 | 所属 Topic |
|---|---|---|
| `SENSOR_DATA` | 传感器原始监测数据 | tunnel-sensor-topic |
| `ALARM_EVENT` | 管廊告警事件 | tunnel-alarm-topic |
| `GAS_RISK_EVENT` | 燃气风险事件 | gas-risk-event-topic（规划） |
| `ALERT_CREATED` | 预警事件生成 | alert-event-topic（规划） |

### 2.4 metrics 指标编码

`metrics` 为键值对结构，key 为指标编码，value 为指标值：

```json
{
  "metrics": {
    "pressure": 3.8,
    "temperature": 65.2,
    "ch4_concentration": 2.1
  }
}
```

指标编码由各服务自行定义，但同一物理量必须使用相同编码。常用编码：

| 指标编码 | 含义 | 单位 |
|---|---|---|
| `pressure` | 管道压力 | MPa |
| `temperature` | 温度 | ℃ |
| `humidity` | 湿度 | %RH |
| `ch4_concentration` | 甲烷浓度 | %LEL |
| `h2s_concentration` | 硫化氢浓度 | ppm |
| `co_concentration` | 一氧化碳浓度 | ppm |
| `o2_concentration` | 氧气浓度 | %VOL |
| `wall_thickness` | 管壁厚度 | mm |
| `vibration_amplitude` | 振动幅值 | mm/s |
| `flow_rate` | 流量 | m³/h |

---

## 3. tunnel-service 发送规范（已实现）

### 3.1 原始监测数据

- **Topic：** `tunnel-sensor-topic`
- **eventType：** `SENSOR_DATA`
- **发送频率：** 按采集周期发送（建议 10s ~ 60s）

消息示例：

```json
{
  "eventId": "tunnel-service-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "source": "tunnel-service",
  "deviceId": "SENSOR-P-001",
  "deviceType": "PRESSURE",
  "location": {
    "zone": "ZONE-A01",
    "areaId": "AREA-A01"
  },
  "timestamp": 1725100800000,
  "eventType": "SENSOR_DATA",
  "metrics": {
    "pressure": 3.8,
    "temperature": 45.2
  },
  "healthScore": 85.5
}
```

### 3.2 告警事件数据

- **Topic：** `tunnel-alarm-topic`
- **eventType：** `ALARM_EVENT`
- **触发条件：** 管廊内部告警规则触发后发送

消息示例：

```json
{
  "eventId": "tunnel-service-f7e8d9c0-b1a2-3456-7890-abcdef123456",
  "source": "tunnel-service",
  "deviceId": "SENSOR-P-001",
  "deviceType": "PRESSURE",
  "location": {
    "zone": "ZONE-A01",
    "areaId": "AREA-A01"
  },
  "timestamp": 1725100800000,
  "eventType": "ALARM_EVENT",
  "alarmCode": "ALM-OVERPRESSURE",
  "alarmLevel": "ORANGE",
  "metrics": {
    "pressure": 4.2
  },
  "healthScore": 60.0
}
```

### 3.3 tunnel-service 旧字段兼容说明

tunnel-service 已有 Producer 使用以下旧字段，通过转换层映射到统一消息格式：

| 旧字段 | 新字段 | 映射方式 | 说明 |
|---|---|---|---|
| `device_id` | `deviceId` | 直接映射 | 下划线转驼峰 |
| `zone` | `location.zone` | 结构映射 | 移入 location 对象 |
| `alarm_code` | `alarmCode` | 直接映射 | 下划线转驼峰 |
| `device_type` | `deviceType` | 直接映射 | 下划线转驼峰 |
| `cabin` + `workshop` | `location.areaId` | 组合映射 | 多字段合并为统一 areaId |
| `event_timestamp` | `timestamp` | 提升映射 | 移至顶层 |
| `alarm_desc` | 不映射 | 可选扩展 | 后续按需新增 |
| `level` | `alarmLevel` | 直接映射 | 重命名 |
| `health_score` | `healthScore` | 直接映射 | 下划线转驼峰 |

> **转换层实现建议：** 在 tunnel-service 的 Kafka Producer 发送前增加一层消息转换器（MessageConverter），将内部数据模型自动转换为统一消息格式，确保向后兼容。

---

## 4. gas-risk-service 发送规范（规划）

### 4.1 燃气风险事件

- **Topic：** `gas-risk-event-topic`（规划中）
- **eventType：** `GAS_RISK_EVENT`
- **触发条件：** 燃气管网风险评估后产出风险事件时发送

消息示例：

```json
{
  "eventId": "gas-risk-service-12345678-abcd-ef01-2345-6789abcdef01",
  "source": "gas-risk-service",
  "deviceId": "GAS-PIPE-SEC-012",
  "deviceType": "CH4",
  "location": {
    "zone": "ZONE-B02",
    "areaId": "AREA-B02"
  },
  "timestamp": 1725100800000,
  "eventType": "GAS_RISK_EVENT",
  "alarmCode": "GAS-LEAK-HIGH",
  "alarmLevel": "RED",
  "metrics": {
    "ch4_concentration": 3.5,
    "pressure": 2.8,
    "flow_rate": 150.0
  },
  "healthScore": 30.0
}
```

---

## 5. alarm-warning-service 消费规范

### 5.1 消费 Topic

| Topic | 状态 | 消费组 | 处理逻辑 |
|---|---|---|---|
| `tunnel-sensor-topic` | 已实现 | alarm-warning-service | 实时规则匹配，判断四级预警 |
| `tunnel-alarm-topic` | 已实现 | alarm-warning-service | 接收已有告警，补充预警分析 |
| `gas-risk-event-topic` | 规划中 | alarm-warning-service | 接收燃气风险事件，纳入预警体系 |

### 5.2 四级预警判定

消费到数据后，按以下流程处理：

1. 根据 `deviceType` 和 `location.areaId` 匹配 `alert_rule` 中的规则
2. 将 `metrics` 中的指标值与阈值对比
3. 判定预警等级：BLUE / YELLOW / ORANGE / RED
4. 未触发任何阈值的数据直接丢弃，不产生预警事件

### 5.3 根因分析

根据 `deviceType` 和指标异常模式推断根因：

| deviceType | 异常模式 | 根因分类 |
|---|---|---|
| `PRESSURE` | 压力骤升 | `PRESSURE_ABNORMAL` |
| `TEMPERATURE` | 温度超限 | `TEMPERATURE_ABNORMAL` |
| `CH4` / `H2S` | 浓度超标 | `GAS_LEAK` |
| `CORROSION` / `WALL_THICKNESS` | 管壁减薄 | `PIPELINE_CORROSION` |
| `VIBRATION` | 振动异常 | `THIRD_PARTY_DAMAGE` |
| 多传感器同时异常 | 区域级联异常 | `MULTI_SENSOR_CASCADE` |

### 5.4 降噪聚合

- 同一 `location.areaId` 在 **10 分钟滑动窗口** 内的多条预警合并为一个 `alert_group`
- 合并后取最高预警等级作为组等级
- 合并记录写入 `merged_from` 字段

### 5.5 动态优先级计算

优先级分数 = 预警等级权重 × 20 + 区域重要度 × 15 + 人口权重 × 10 + 时段权重 × 5

| 时段 | 权重 |
|---|---|
| 22:00 - 06:00 | 1.0 |
| 06:00 - 09:00 | 0.8 |
| 17:00 - 22:00 | 0.7 |
| 09:00 - 17:00 | 0.5 |

最终分数限制在 1-100 之间。

### 5.6 产出消息（规划）

处理完成后，向 `alert-event-topic` 发送预警事件：

```json
{
  "eventId": "alarm-warning-service-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "source": "alarm-warning-service",
  "deviceId": "SENSOR-P-001",
  "deviceType": "PRESSURE",
  "location": {
    "zone": "ZONE-A01",
    "areaId": "AREA-A01"
  },
  "timestamp": 1725100800000,
  "eventType": "ALERT_CREATED",
  "alarmCode": "ALT-OVERPRESSURE",
  "alarmLevel": "ORANGE",
  "metrics": {
    "pressure": 4.2
  },
  "healthScore": 60.0
}
```

> 预警事件额外字段（`alertEventCode`、`rootCause`、`priorityScore`、`sourceEvents`、`mergedCount` 等）作为扩展字段追加，不影响统一结构。

---

## 6. 字段兼容与扩展规则

### 6.1 兼容规则

1. **只增不删**：新增字段不能删除旧字段，只能追加
2. **忽略未知**：消费者必须忽略未知字段，不能因新字段导致反序列化失败
3. **命名统一**：所有字段命名统一使用 camelCase，不使用下划线（`_`）或短横线（`-`）

### 6.2 tunnel-service 旧字段兼容

tunnel-service 已有 Producer 使用旧字段命名（如 `device_id`、`zone`、`alarm_code`），通过转换层映射到新规范：

| 旧字段 | 新字段 | 映射方式 |
|---|---|---|
| `device_id` | `deviceId` | 下划线转驼峰 |
| `zone` | `location.zone` | 移入 location 对象 |
| `alarm_code` | `alarmCode` | 下划线转驼峰 |

> 转换层在 tunnel-service Producer 端实现，对外发送的消息统一使用新字段格式。下游消费者无需关心旧字段。

### 6.3 新增字段流程

1. 在本文档中提交 PR，说明新增字段的名称、类型、含义、是否必填
2. 相关服务 Owner 审核确认
3. 合并后，生产方按新规范发送，消费方按「容忍缺失」原则处理

### 6.4 废弃字段处理

- 废弃字段标记为 `@Deprecated`，保留至少 2 个迭代周期
- 废弃期间生产方继续发送，消费方不再依赖该字段
- 废弃期满后方可移除

---

## 7. 示例消息

### 7.1 正常监测数据（tunnel-sensor-topic）

```json
{
  "eventId": "tunnel-service-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "source": "tunnel-service",
  "deviceId": "SENSOR-T-015",
  "deviceType": "TEMPERATURE",
  "location": {
    "zone": "ZONE-A03",
    "areaId": "AREA-A03"
  },
  "timestamp": 1725100800000,
  "eventType": "SENSOR_DATA",
  "metrics": {
    "temperature": 42.5,
    "humidity": 55.0
  },
  "healthScore": 92.0
}
```

### 7.2 风险告警数据（gas-risk-event-topic，规划）

```json
{
  "eventId": "gas-risk-service-abcdef01-2345-6789-abcd-ef0123456789",
  "source": "gas-risk-service",
  "deviceId": "GAS-PIPE-SEC-008",
  "deviceType": "CH4",
  "location": {
    "zone": "ZONE-A02",
    "areaId": "AREA-A02"
  },
  "timestamp": 1725101400000,
  "eventType": "GAS_RISK_EVENT",
  "alarmCode": "GAS-LEAK-MEDIUM",
  "alarmLevel": "ORANGE",
  "metrics": {
    "ch4_concentration": 2.8,
    "pressure": 3.1
  },
  "healthScore": 55.0
}
```

### 7.3 红色预警事件（alert-event-topic，规划）

```json
{
  "eventId": "alarm-warning-service-98765432-abcd-ef01-2345-6789abcdef01",
  "source": "alarm-warning-service",
  "deviceId": "SENSOR-CH4-003",
  "deviceType": "CH4",
  "location": {
    "zone": "ZONE-A02",
    "areaId": "AREA-A02"
  },
  "timestamp": 1725102000000,
  "eventType": "ALERT_CREATED",
  "alarmCode": "ALT-GAS-LEAK",
  "alarmLevel": "RED",
  "metrics": {
    "ch4_concentration": 5.2,
    "pressure": 1.8
  },
  "healthScore": 15.0
}
```

---

## 8. 联调流程

### 8.1 架构拓扑

```
tunnel-service ──┬── tunnel-sensor-topic ──┐
                 └── tunnel-alarm-topic ────┤
                                            ├──► alarm-warning-service ──► alert-event-topic
gas-risk-service ──── gas-risk-event-topic ─┘
```

### 8.2 环境准备

1. 启动 Kafka（Docker）：
   ```bash
   docker-compose up -d kafka zookeeper
   ```

2. 创建 Topic：
   ```bash
   # 已实现
   kafka-topics.sh --create --topic tunnel-sensor-topic --partitions 3 --replication-factor 1
   kafka-topics.sh --create --topic tunnel-alarm-topic --partitions 3 --replication-factor 1

   # 规划
   kafka-topics.sh --create --topic gas-risk-event-topic --partitions 3 --replication-factor 1
   kafka-topics.sh --create --topic alert-event-topic --partitions 3 --replication-factor 1
   ```

3. 启动各服务：
   ```bash
   # 按顺序启动
   # 1. tunnel-service（生产者，已实现）
   # 2. gas-risk-service（生产者，规划中）
   # 3. alarm-warning-service（消费者）
   ```

### 8.3 联调步骤

**Step 1：验证 tunnel-service → Kafka**

```bash
kafka-console-consumer.sh --topic tunnel-sensor-topic --from-beginning
kafka-console-consumer.sh --topic tunnel-alarm-topic --from-beginning
```

确认 tunnel-service 发出的消息格式符合统一消息规范。

**Step 2：验证 gas-risk-service → Kafka（规划）**

```bash
kafka-console-consumer.sh --topic gas-risk-event-topic --from-beginning
```

**Step 3：验证 alarm-warning-service 消费**

- 观察 alarm-warning-service 日志，确认消息被正确消费
- 查询数据库 `alert_event` 表，确认预警记录生成
- 查询 REST API 验证数据可查：
  ```bash
  curl http://localhost:8085/api/alerts?page=1&size=20
  ```

**Step 4：端到端验证**

1. tunnel-service 发送一条超阈值传感器数据
2. 确认 alarm-warning-service 在 10 秒内产出预警事件
3. 确认 `alert-event-topic` 收到预警消息
4. 确认预警等级、根因、优先级符合预期

### 8.4 常见问题排查

| 现象 | 排查方向 |
|---|---|
| 消费者收不到消息 | 检查 consumer group 是否重复、Topic 名称是否一致 |
| 消息解析失败 | 检查 JSON 格式是否符合统一消息规范 |
| 预警未触发 | 检查 alert_rule 表中规则是否启用、阈值是否正确 |
| 预警等级不对 | 检查 metrics 中的指标编码是否与规则匹配 |
| 重复预警过多 | 检查降噪窗口配置、location.areaId 映射是否正确 |
