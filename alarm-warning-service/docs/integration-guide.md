# 联调指南

> 版本：v1.0  
> 更新日期：2026-08-31  
> 适用范围：tunnel-service / gas-risk-service / alarm-warning-service

---

## 1. 联调环境要求

| 组件 | 版本 | 用途 |
|---|---|---|
| JDK | 17+ | Java 服务运行 |
| Maven | 3.8+ | 项目构建 |
| MySQL | 8.0+ | 数据存储 |
| Kafka | 3.x | 消息队列 |
| Zookeeper | 3.8+ | Kafka 协调 |
| Redis | 7.x | 缓存 / 降噪 |
| Docker | 24+ | 基础设施容器化 |

---

## 2. 基础设施启动

### 2.1 使用 Docker 启动依赖组件

```bash
# 启动 MySQL、Kafka、Zookeeper、Redis
docker-compose up -d mysql zookeeper kafka redis
```

### 2.2 确认组件就绪

```bash
# MySQL
docker exec -it mysql mysql -uroot -proot -e "SELECT 1"

# Kafka
kafka-broker-api-versions.sh --bootstrap-server localhost:9092

# Redis
docker exec -it redis redis-cli ping
```

---

## 3. 数据库初始化

### 3.1 alarm-warning-service

```bash
mysql -uroot -proot < alarm-warning-service/sql/init.sql
```

### 3.2 创建 Kafka Topic

```bash
kafka-topics.sh --create --topic tunnel-sensor-topic --partitions 3 --replication-factor 1 --bootstrap-server localhost:9092
kafka-topics.sh --create --topic tunnel-alarm-topic --partitions 3 --replication-factor 1 --bootstrap-server localhost:9092
kafka-topics.sh --create --topic gas-risk-event-topic --partitions 3 --replication-factor 1 --bootstrap-server localhost:9092
kafka-topics.sh --create --topic alert-event-topic --partitions 3 --replication-factor 1 --bootstrap-server localhost:9092
```

---

## 4. 服务启动顺序

```
1. tunnel-service      (端口 8081)  ← 先启动，作为数据生产者
2. gas-risk-service    (端口 8082)  ← 先启动，作为数据生产者
3. alarm-warning-service (端口 8085) ← 后启动，作为消费者
```

**原因：** alarm-warning-service 启动后立即开始消费 Kafka，如果生产者未就绪可能导致消费空消息。

### 4.1 启动命令

```bash
# tunnel-service
cd tunnel-service
mvn spring-boot:run -Dspring-boot.run.profiles=dev

# gas-risk-service
cd gas-risk-service
mvn spring-boot:run -Dspring-boot.run.profiles=dev

# alarm-warning-service
cd alarm-warning-service
mvn spring-boot:run -Dspring-boot.run.profiles=dev
```

---

## 5. 联调验证步骤

### 5.1 Step 1：验证基础设施

```bash
# 确认 Kafka Topic 已创建
kafka-topics.sh --list --bootstrap-server localhost:9092

# 预期输出包含：
# tunnel-sensor-topic
# tunnel-alarm-topic
# gas-risk-event-topic
# alert-event-topic
```

### 5.2 Step 2：验证 tunnel-service 数据发送

```bash
# 监听 Topic，确认 tunnel-service 发送了传感器数据
kafka-console-consumer.sh --topic tunnel-sensor-topic --from-beginning --bootstrap-server localhost:9092
```

预期看到符合 `kafka-protocol.md` 规范的 JSON 消息。

### 5.3 Step 3：验证 gas-risk-service 数据发送

```bash
kafka-console-consumer.sh --topic gas-risk-event-topic --from-beginning --bootstrap-server localhost:9092
```

### 5.4 Step 4：验证 alarm-warning-service 消费

观察 alarm-warning-service 日志：

```bash
# 查看日志输出
tail -f alarm-warning-service/logs/alarm-warning.log
```

预期看到：

```
Received sensor data: sensor=SENSOR-P-001, area=AREA-A01, value=3.8
Rule [RULE-PRESSURE-001] triggered: sensor=SENSOR-P-001, value=3.8, level=ORANGE
Alert created: code=ALT-xxx, level=ORANGE, priority=85
```

### 5.5 Step 5：验证 REST API

```bash
# 查询预警列表
curl http://localhost:8085/api/alerts?page=1&size=20

# 查询预警详情
curl http://localhost:8085/api/alerts/1

# 查询预警规则
curl http://localhost:8085/api/alert-rules
```

### 5.6 Step 6：端到端验证

1. 通过 tunnel-service 接口或脚本发送一条超阈值传感器数据
2. 等待 10 秒
3. 查询 alarm-warning-service API，确认预警记录已生成
4. 确认预警等级、根因、优先级符合预期

---

## 6. 手动发送测试消息

如果不想启动 tunnel-service，可直接向 Kafka 发送测试消息：

### 6.1 传感器数据（触发蓝色预警）

```bash
kafka-console-producer.sh --topic tunnel-sensor-topic --bootstrap-server localhost:9092
```

粘贴：

```json
{"eventId":"test-001","source":"tunnel-service","timestamp":1725100800000,"eventType":"SENSOR_DATA","payload":{"deviceId":"SENSOR-P-001","deviceType":"PRESSURE","areaId":"AREA-A01","areaName":"核心管廊区","metrics":{"pressure":2.5},"healthScore":85.0}}
```

### 6.2 传感器数据（触发红色预警）

```json
{"eventId":"test-002","source":"tunnel-service","timestamp":1725100800000,"eventType":"SENSOR_DATA","payload":{"deviceId":"SENSOR-P-001","deviceType":"PRESSURE","areaId":"AREA-A02","areaName":"居民区管段","metrics":{"pressure":4.5},"healthScore":30.0}}
```

### 6.3 燃气风险事件

```bash
kafka-console-producer.sh --topic gas-risk-event-topic --bootstrap-server localhost:9092
```

粘贴：

```json
{"eventId":"test-003","source":"gas-risk-service","timestamp":1725100800000,"eventType":"GAS_RISK_EVENT","payload":{"deviceId":"GAS-PIPE-008","deviceType":"CH4","areaId":"AREA-A02","areaName":"居民区管段","metrics":{"ch4_concentration":3.5},"alarmCode":"GAS-LEAK-HIGH","alarmLevel":"RED","alarmDesc":"燃气管段泄漏风险极高","healthScore":25.0}}
```

---

## 7. 常见问题排查

| 现象 | 排查方向 | 解决方案 |
|---|---|---|
| 消费者收不到消息 | consumer group 重复 / Topic 名称不一致 | 检查 `application.yml` 中 topic 和 group-id 配置 |
| JSON 解析失败 | 消息格式不符合协议规范 | 对照 `kafka-protocol.md` 检查字段 |
| 预警未触发 | 规则未匹配 | 检查 `alert_rule` 表中 sensor_type 和 area_id 是否匹配 |
| 数据库连接失败 | MySQL 未启动 / 密码错误 | 检查 `application-dev.yml` 数据源配置 |
| 端口冲突 | 其他服务占用端口 | `netstat -ano \| findstr :8085` 查看占用 |
| 重复预警过多 | 降噪窗口配置问题 | 检查 `AlertDedupService` 中窗口时间设置 |
| Kafka 连接超时 | Kafka 未启动 / 地址错误 | 确认 `docker ps` 中 Kafka 容器运行正常 |

---

## 8. 联调 Checklist

### 环境准备

- [ ] Docker 已启动
- [ ] MySQL 已初始化（执行 init.sql）
- [ ] Kafka Topic 已创建（4 个 Topic）
- [ ] Redis 已启动

### 服务启动

- [ ] tunnel-service 启动成功（端口 8081）
- [ ] gas-risk-service 启动成功（端口 8082）
- [ ] alarm-warning-service 启动成功（端口 8085）
- [ ] 三个服务健康检查通过（`/actuator/health`）

### 功能验证

- [ ] tunnel-service 向 Kafka 发送数据正常
- [ ] gas-risk-service 向 Kafka 发送数据正常
- [ ] alarm-warning-service 消费消息正常
- [ ] 预警事件正确生成并入库
- [ ] REST API 查询返回正确
- [ ] 四级预警等级判定正确
- [ ] 降噪聚合功能正常
- [ ] 优先级计算符合预期
