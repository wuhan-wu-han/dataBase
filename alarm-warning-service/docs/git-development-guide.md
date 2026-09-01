# Git 开发协作规范

> 版本：v1.0  
> 更新日期：2026-08-31  
> 适用团队：tunnel-service / gas-risk-service / alarm-warning-service 开发组

---

## 1. 分支管理策略

采用 **Git Flow 简化版**，适合 4 人小团队：

```
main          ← 生产环境，始终保持可部署状态
  └── develop ← 开发主线，集成所有已完成功能
        ├── feature/alarm-warning-engine
        ├── feature/tunnel-sensor-collect
        ├── feature/gas-risk-assessment
        └── fix/kafka-consumer-timeout
```

| 分支 | 作用 | 谁可以操作 |
|---|---|---|
| `main` | 生产分支，每个 release 打 Tag | 任何人不得直接 push，仅通过 PR 合入 |
| `develop` | 开发主线，日常集成 | 仅通过 PR 合入，需至少 1 人审核 |
| `feature/*` | 功能开发分支 | 个人自由创建、开发、删除 |
| `fix/*` | Bug 修复分支 | 个人自由创建、开发、删除 |
| `hotfix/*` | 紧急线上修复 | 从 main 拉出，修复后同时合入 main 和 develop |

---

## 2. 分支命名规范

### 功能分支

```
feature/{模块名}-{功能简述}
```

示例：

| 分支名 | 说明 |
|---|---|
| `feature/alarm-warning-engine` | 预警引擎核心逻辑 |
| `feature/alarm-dedup-aggregation` | 预警降噪聚合 |
| `feature/tunnel-sensor-collect` | 管廊传感器数据采集 |
| `feature/gas-risk-assessment` | 燃气风险评估 |
| `feature/dispatch-sms-channel` | 短信推送渠道 |

### 修复分支

```
fix/{模块名}-{问题简述}
```

示例：

| 分支名 | 说明 |
|---|---|
| `fix/alarm-kafka-consumer-timeout` | Kafka 消费者超时问题 |
| `fix/tunnel-db-connection-pool` | 数据库连接池泄漏 |

### 紧急修复

```
hotfix/{问题简述}
```

示例：`hotfix/production-memory-leak`

---

## 3. 开发流程

### 3.1 完整流程图

```
1. 从 develop 创建功能分支
         │
         ▼
2. 本地开发 + 提交
         │
         ▼
3. push 到 GitHub
         │
         ▼
4. 创建 Pull Request → develop
         │
         ▼
5. 团队成员 Code Review
         │
         ▼
6. 审核通过 → 合并（Squash Merge）
         │
         ▼
7. 删除功能分支
```

### 3.2 详细步骤

**Step 1：创建功能分支**

```bash
git checkout develop
git pull origin develop
git checkout -b feature/alarm-warning-engine
```

**Step 2：开发并提交**

```bash
git add .
git commit -m "feat(alarm): 实现四级预警规则引擎"
```

**Step 3：推送到远程**

```bash
git push -u origin feature/alarm-warning-engine
```

**Step 4：创建 Pull Request**

- 在 GitHub 上点击 "New Pull Request"
- 源分支：`feature/alarm-warning-engine`
- 目标分支：`develop`
- 填写 PR 描述，说明改动内容和影响范围

**Step 5：代码审核**

- 至少 1 名团队成员审核
- 审核人重点关注：
  - 代码逻辑是否正确
  - 是否影响其他模块
  - 是否遵循 Kafka 协议规范
  - 是否有明显 bug

**Step 6：合并**

- 审核通过后，使用 **Squash and Merge** 合入 develop
- 合并后删除远程功能分支

**Step 7：同步最新代码**

```bash
git checkout develop
git pull origin develop
```

---

## 4. Commit 提交规范

### 4.1 格式

```
<type>(<scope>): <subject>
```

- `type`：提交类型（必填）
- `scope`：影响范围/模块（选填）
- `subject`：简短描述（必填，不超过 50 字）

### 4.2 type 类型

| type | 说明 | 示例 |
|---|---|---|
| `feat` | 新功能 | `feat(alarm): 实现四级预警判定逻辑` |
| `fix` | Bug 修复 | `fix(tunnel): 修复传感器数据解析空指针` |
| `docs` | 文档变更 | `docs: 更新 Kafka 协议文档` |
| `refactor` | 代码重构（不改功能） | `refactor(alarm): 提取规则匹配为独立方法` |
| `style` | 格式调整（不影响逻辑） | `style: 统一代码缩进和空行` |
| `test` | 测试相关 | `test(alarm): 添加预警规则引擎单元测试` |
| `chore` | 构建/工具变更 | `chore: 升级 Spring Boot 版本到 3.2.5` |

### 4.3 示例

```
feat(alarm): 新增预警降噪聚合功能

- 实现 10 分钟滑动窗口聚合
- 同区域多传感器告警合并为一条
- 合并后取最高预警等级

feat(tunnel): 增加温湿度传感器数据采集
fix(gas): 修复燃气管段风险评估空指针异常
docs: 更新 kafka-protocol.md 字段映射表
refactor(alarm): 将优先级计算逻辑抽取为独立 Service
```

### 4.4 禁止的提交信息

```
❌ "修改了一些东西"
❌ "update"
❌ "fix bug"
❌ "111"
```

---

## 5. 冲突解决规则

### 5.1 模块职责划分

| 成员 | 主要负责模块 |
|---|---|
| 成员 A | tunnel-service |
| 成员 B | gas-risk-service |
| 成员 C | alarm-warning-service |
| 成员 D | 公共模块 / 基础设施 |

### 5.2 冲突预防

1. **不修改别人的模块**
   - 每人只修改自己负责的模块代码
   - 如需修改其他模块，必须先与负责人沟通

2. **公共文件修改需沟通**
   - `pom.xml` 公共依赖变更 → 群内通知全员
   - `application.yml` 公共配置变更 → 群内通知全员
   - `kafka-protocol.md` 协议变更 → 提交 PR，全员审核
   - 数据库公共表结构变更 → 群内讨论后由负责人统一修改

3. **频繁同步，减少冲突窗口**
   - 每天至少 pull 一次 develop 最新代码
   - 功能开发周期超过 3 天的，中间至少 rebase 一次 develop

### 5.3 冲突解决流程

```bash
# 1. 切换到自己的功能分支
git checkout feature/my-feature

# 2. 拉取最新 develop
git fetch origin
git rebase origin/develop

# 3. 解决冲突（如有）
#    手动编辑冲突文件，保留双方合理改动

# 4. 标记冲突已解决
git add .
git rebase --continue

# 5. 推送（需要 force push，因为 rebase 改写了历史）
git push --force-with-lease origin feature/my-feature
```

### 5.4 合并前必须测试

- 功能分支合入 develop 前，必须在本地完成基本功能验证
- 涉及 Kafka 消息变更的，需要端到端验证消息收发
- 涉及数据库变更的，需要确认 SQL 脚本可正确执行

---

## 6. 禁止事项

| 禁止行为 | 原因 |
|---|---|
| **禁止直接 push main** | main 是生产分支，只能通过 PR 合入 |
| **禁止直接 push develop** | develop 只能通过 PR 合入，保证审核流程 |
| **禁止 force push main / develop** | 会破坏团队共享历史 |
| **禁止删除别人的分支** | 分支属于个人工作空间 |
| **禁止在功能分支上合并其他功能分支** | 保持分支职责单一，避免交叉污染 |
| **禁止提交敏感信息** | .env、密钥、密码等不得入库 |
| **禁止提交大文件** | 二进制文件、数据集等不得入库，使用 .gitignore 排除 |
| **禁止无意义的提交** | 避免 "fix typo"、"update" 等无信息量提交，善用 `git commit --amend` |

---

## 7. 日常协作 Checklist

每天开发前检查：

- [ ] 拉取 develop 最新代码
- [ ] 确认功能分支是从最新 develop 创建的
- [ ] 检查是否有公共文件变更需要同步

提交代码前检查：

- [ ] commit message 符合规范
- [ ] 代码能在本地正常运行
- [ ] 没有提交敏感信息或大文件
- [ ] 没有修改其他成员负责的模块

PR 提交前检查：

- [ ] PR 描述清楚改动内容和影响范围
- [ ] 目标分支是 develop（不是 main）
- [ ] 已通过本地基本测试
- [ ] 涉及协议变更的已更新 docs 文档

---

## 8. 快速参考

```bash
# 开始新功能
git checkout develop && git pull
git checkout -b feature/模块名-功能名

# 日常开发
git add .
git commit -m "feat(模块): 功能描述"
git push -u origin feature/模块名-功能名

# 同步最新代码
git fetch origin
git rebase origin/develop

# 提交 PR 后
# → GitHub 上创建 PR → 审核 → Squash Merge → 删除分支
```
