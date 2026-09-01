# 微服务开发规范

> 版本：v1.0
> 更新日期：2026-08-31
> 适用范围：
> - tunnel-service（Python）
> - gas-risk-service（Python）
> - alarm-warning-service（Java Spring Boot）

---

## 1. 通用开发原则

本项目为多语言微服务架构，不同服务可以使用不同技术栈开发，但必须保证服务架构统一、通信协议统一、数据格式统一、协作流程统一。

### 1.1 核心约束

- 服务之间**禁止直接依赖代码**
- 服务之间只允许通过 **Kafka** 和 **REST API** 通信
- 每个服务独立开发、独立部署、独立维护
- 所有对外输出（Kafka 消息、REST API 响应）必须可被其他语言的服务正确解析

### 1.2 统一规范

| 项目 | 规范 | 参考文档 |
|---|---|---|
| Kafka 消息格式 | 遵循统一消息结构 | `kafka-protocol.md` |
| JSON 字段命名 | 跨服务通信统一使用 camelCase | 本文档 |
| 时间格式 | Kafka 消息中使用 Unix 毫秒时间戳 | `kafka-protocol.md` |
| 服务通信方式 | Kafka（实时事件流）+ REST API（查询与管理） | `service-interface.md` |
| 错误处理 | 统一错误码体系，友好错误提示 | `service-interface.md` |

---

## 2. Python 服务开发规范

适用服务：tunnel-service、gas-risk-service

### 2.1 推荐目录结构

```
{service-name}/
├── app/
│   ├── api/              # REST 接口层
│   ├── service/          # 业务逻辑层
│   ├── model/            # 数据模型（entity、dto）
│   ├── repository/       # 数据访问层
│   ├── kafka/            # Kafka 生产者与消费者
│   └── common/           # 通用工具、日志、异常定义
├── tests/                # 测试
├── config.yaml           # 应用配置
├── .env                  # 环境变量（敏感信息，不提交）
├── .env.example          # 环境变量示例（提交）
└── requirements.txt      # 依赖清单
```

> 以上为推荐结构，不要求已有项目修改。新建服务建议按此结构组织。

### 2.2 命名规范

| 类型 | 命名规则 | 示例 |
|---|---|---|
| 文件名 | snake_case | `alert_service.py`、`sensor_data.py` |
| 类名 | PascalCase | `AlertService`、`SensorDataMessage` |
| 函数 / 方法 | snake_case | `process_sensor_data()` |
| 变量 | snake_case | `device_id`、`alert_level` |
| 常量 | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT` |

**代码内部与跨服务通信的命名区别：**

Python 代码内部使用 `snake_case`，但跨服务通信的 JSON 字段**必须使用 camelCase**：

| 场景 | 命名规则 | 示例 |
|---|---|---|
| 代码内部变量 | snake_case | `device_id`、`area_id` |
| Kafka 消息 JSON | camelCase | `deviceId`、`areaId` |
| REST API 请求/响应 JSON | camelCase | `deviceId`、`areaId` |
| 数据库字段 | snake_case | `device_id`、`area_id` |

### 2.3 Python Kafka 规范

**Producer：**

- 消息发送前必须校验必填字段（eventId、source、deviceId、timestamp、eventType）
- 消息格式必须符合 `kafka-protocol.md` 定义的统一消息格式
- JSON 字段使用 camelCase
- 发送失败记录日志，支持异常重试
- Topic 名称通过配置文件注入，不硬编码

**Consumer：**

- 消费失败必须记录日志（含原始消息内容和异常信息）
- 单条消息解析错误不能导致服务停止
- 消息解析时必须忽略未知字段，支持字段扩展
- 消费逻辑必须包含异常捕获，保证消费者线程不退出

---

## 3. Java Spring Boot 服务开发规范

适用服务：alarm-warning-service

### 3.1 分层规范

| 层级 | 职责 | 禁止事项 |
|---|---|---|
| **Controller** | 接口层：接收请求、参数校验、调用 Service | 禁止写复杂业务逻辑，禁止直接操作数据库 |
| **Service** | 业务逻辑层：核心业务处理、事务管理 | 禁止在 Service 中处理 HTTP 请求/响应对象 |
| **DTO** | 数据传输对象：接口入参和出参 | 禁止直接暴露 Entity 到接口外层 |
| **Entity** | 数据库实体：对应数据库表结构 | 禁止在 Entity 中写业务方法，禁止注入 Spring Bean |
| **Mapper** | 数据访问层：MyBatis-Plus 数据操作 | 禁止在 Mapper 中写业务逻辑 |
| **Kafka Consumer** | 消息消费：异常捕获、委托 Service | 禁止在 Consumer 中写复杂业务逻辑 |

### 3.2 Controller 规范

- 一个 Controller 对应一个资源
- 使用 `@RestController` + `@RequestMapping`
- 统一返回 `Result<T>`
- 只做参数校验和调用 Service，**禁止写复杂业务逻辑**

### 3.3 Service 规范

- 业务逻辑全部放在 Service 层
- 涉及多表写操作的方法加 `@Transactional`
- 纯查询不加事务

### 3.4 Entity 规范

- 使用 MyBatis-Plus 注解 + Lombok `@Data`
- 字段与数据库列一一对应
- 必须包含 `createdAt`、`updatedAt` 字段

### 3.5 DTO 规范

- 接口入参使用 `XxxRequest`，出参使用 `XxxResponse`
- 使用 `@Valid` + JSR 303 注解做参数校验
- Kafka 消息体使用独立 DTO 类，不复用 Entity

### 3.6 Mapper 规范

- 继承 `BaseMapper<T>`
- 简单查询使用 MyBatis-Plus 内置方法
- 复杂查询使用 `@Select` 注解或 XML 映射

### 3.7 Kafka Consumer 规范

- 消息体使用 String 接收，手动反序列化
- 必须 try-catch，消费失败不能导致消费者线程挂掉
- 异常必须记日志（含消息原文和异常栈）
- 解析时忽略未知字段，兼容字段扩展
- 委托 Service 处理业务逻辑，Consumer 层不写复杂逻辑

### 3.8 代码格式约束

| 约束 | 规则 |
|---|---|
| 缩进 | 4 空格，禁止 Tab |
| 方法长度 | ≤ 50 行，超过则拆分 |
| 嵌套层数 | ≤ 3 层，超过则提前 return 或抽取方法 |
| 大括号 | 不换行（K&R 风格） |
| 行宽 | ≤ 120 字符 |

### 3.9 配置管理

- 使用 `application.yml` 管理配置
- 敏感信息使用 `${VAR:默认值}` 引用环境变量
- 不在 `application.yml` 中直接写明文密码

---

## 4. Kafka 开发规范

所有 Producer 和 Consumer 必须遵守 `kafka-protocol.md` 定义的协议规范。

### 4.1 Producer 规范

| 规则 | 说明 |
|---|---|
| Topic 名称 | 使用配置文件注入，不硬编码，遵循 `kafka-protocol.md` 命名 |
| 消息格式 | 必须符合统一消息格式（eventId、source、deviceId、location、timestamp、eventType、metrics 等） |
| JSON 字段 | 使用 camelCase |
| 发送前校验 | 必填字段不能为空 |
| 发送失败处理 | 记录日志，支持重试，不阻塞主流程 |

### 4.2 Consumer 规范

| 规则 | 说明 |
|---|---|
| 消息解析异常 | 捕获异常，记录日志（含原始消息内容），跳过该消息继续消费 |
| 重复消息处理 | 消费逻辑保证幂等，同一消息多次消费结果一致 |
| 字段扩展兼容 | 解析时忽略未知字段，不因新字段导致反序列化失败 |
| 异常不中断 | Consumer 内部必须 try-catch，异常不能导致消费者线程退出 |
| 日志记录 | 消费失败必须记录 topic、消息原文、异常信息 |

### 4.3 字段兼容规则

| 规则 | 说明 |
|---|---|
| 不删除已有字段 | 新增字段只能追加，不能删除或重命名已有字段 |
| 忽略未知字段 | 消费者必须忽略未知字段，不能因新字段导致解析失败 |
| 保持向后兼容 | 新增字段默认为非必填，消费方必须容忍字段缺失 |
| 命名统一 | 所有 JSON 字段统一使用 camelCase |

---

## 5. 配置管理规范

### 5.1 Python 服务

| 文件 | 用途 | 是否提交 Git |
|---|---|---|
| `config.yaml` | 应用配置（服务名、端口、Topic 名称等非敏感信息） | 是 |
| `.env` | 环境变量（Kafka 地址、数据库密码等敏感信息） | **否** |
| `.env.example` | 环境变量示例（占位符，无真实密码） | 是 |

### 5.2 Java 服务

| 文件 | 用途 | 是否提交 Git |
|---|---|---|
| `application.yml` | 应用配置（使用 `${VAR:默认值}` 引用环境变量） | 是 |
| `.env` 或环境变量 | 敏感信息（数据库密码、Redis 密码等） | **否** |

### 5.3 禁止事项

| 禁止行为 | 说明 |
|---|---|
| 硬编码 Kafka 地址 | 必须通过配置文件 / 环境变量注入 |
| 硬编码数据库密码 | 必须使用环境变量 |
| 硬编码 Redis 密码 | 必须使用环境变量 |
| 硬编码 API Key / Token | 必须使用环境变量 |
| 将 `.env` 提交到 Git | `.env` 包含敏感信息，只提交 `.env.example` |

---

## 6. 日志规范

### 6.1 日志必须包含的信息

| 信息 | 说明 |
|---|---|
| 服务名称 | 标识日志来源服务 |
| 时间 | 日志产生时间 |
| 日志级别 | ERROR / WARNING / INFO / DEBUG |
| 请求 ID | 用于链路追踪（如有） |
| 错误原因 | 异常信息、异常栈 |

### 6.2 Python 日志

使用标准 `logging` 模块：

- 格式：`%(asctime)s [%(levelname)s] [%(name)s] - %(message)s`
- 使用占位符（`%s`），不用字符串拼接

### 6.3 Java 日志

使用 SLF4J（Lombok `@Slf4j`）：

- 使用占位符（`{}`），不用字符串拼接

### 6.4 日志级别使用规范

| 级别 | 使用场景 |
|---|---|
| ERROR | 系统异常、影响功能（Kafka 消费失败、数据库连接异常） |
| WARNING | 业务异常、可恢复的问题（规则未匹配、参数不合法） |
| INFO | 关键业务节点（消息发送成功、预警创建） |
| DEBUG | 开发调试信息（方法入参、中间结果），生产环境禁止开启 |

### 6.5 禁止事项

- 禁止使用 `print()` / `System.out.println()` 输出日志
- 禁止使用字符串拼接构造日志（应使用占位符）
- 禁止在日志中打印敏感信息（密码、Token、密钥）
- 禁止在循环中打大量日志
- 禁止生产环境开启 DEBUG 级别

---

## 7. Git 提交规范

所有语言的服务统一使用以下提交规范。

### 7.1 Commit Message 格式

```
<type>: <subject>
```

### 7.2 type 类型

| type | 说明 | 示例 |
|---|---|---|
| `feat` | 新增功能 | `feat: 添加传感器数据采集接口` |
| `fix` | 修复问题 | `fix: 修复压力阈值判断逻辑` |
| `docs` | 文档修改 | `docs: 更新 Kafka 协议文档` |
| `refactor` | 代码重构（不改变功能） | `refactor: 重构消息转换层` |
| `style` | 代码格式调整 | `style: 统一缩进格式` |
| `test` | 测试相关 | `test: 添加预警规则引擎单元测试` |
| `chore` | 构建 / 工具变更 | `chore: 更新依赖版本` |

### 7.3 规则

- subject 使用中文，简明扼要（≤ 50 字）
- 一次提交只做一件事
- 禁止无意义的提交信息（如 `update`、`fix bug`、`修改`）

---

## 8. 服务独立原则

### 8.1 独立开发

- 每个服务拥有独立的代码目录
- 每个服务独立管理自己的依赖
- 各服务可独立启动、独立调试

### 8.2 独立部署

- 每个服务独立打包、独立运行
- 服务端口不冲突（参见 `service-interface.md` 端口规划）
- 每个服务拥有独立的数据库和配置

### 8.3 独立维护

- 每个服务由对应的负责人维护
- 服务版本独立管理
- 服务故障不互相影响

### 8.4 通信约束

| 允许 | 禁止 |
|---|---|
| Kafka 消息通信 | 复制对方代码 |
| REST API 调用 | 共享实体类 |
| 通过协议契约保持字段语义一致 | 共享数据库表 |
| | 通过 Maven / pip 引入对方模块 |

---

## 9. 禁止事项

### 9.1 协作禁止

| 禁止行为 | 说明 |
|---|---|
| 修改别人负责的模块 | 如需修改，先与负责人沟通 |
| 修改 Kafka 协议不通知团队 | 协议变更必须团队评审，更新 `kafka-protocol.md` |
| 直接 push main 分支 | 必须通过 feature 分支 + PR 合并 |
| 提交密码等敏感信息 | `.env`、密钥文件等必须加入 `.gitignore` |

### 9.2 代码禁止

| 禁止行为 | 说明 |
|---|---|
| 复制其他服务的代码 | 各服务独立实现 |
| 共享实体类 / DTO | 各服务独立定义数据模型 |
| 直接读写其他服务的数据库表 | 每个服务只拥有自己的数据 |
| 在代码中硬编码配置值 | Kafka 地址、数据库密码等必须通过配置注入 |

### 9.3 通信禁止

| 禁止行为 | 说明 |
|---|---|
| 服务间直接依赖代码 | 只能通过 Kafka 和 REST API 通信 |
| 绕过 Kafka 直接写其他服务的数据库 | 数据通过 Kafka 消息传递 |
| 同步调用传递实时传感器数据 | 高频数据流必须走 Kafka |
