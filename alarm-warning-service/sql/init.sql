-- ============================================================
-- alarm-warning-service 数据库初始化脚本
-- 数据库：alert_db
-- MySQL 8.0+
-- ============================================================

SET NAMES utf8mb4;

CREATE DATABASE IF NOT EXISTS `alert_db`
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_general_ci;

USE `alert_db`;

-- ============================================================
-- 1. alert_rule 预警规则表
-- ============================================================
DROP TABLE IF EXISTS `alert_rule`;
CREATE TABLE `alert_rule` (
    `id`               BIGINT        NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `rule_code`        VARCHAR(64)   NOT NULL COMMENT '规则编码，唯一标识',
    `rule_name`        VARCHAR(128)  NOT NULL COMMENT '规则名称',
    `device_type`      VARCHAR(32)   NOT NULL COMMENT '设备类型：PRESSURE / TEMPERATURE / CH4 / H2S 等',
    `metric_key`       VARCHAR(64)   NOT NULL COMMENT '指标编码：pressure / temperature / ch4_concentration 等',
    `area_id`          VARCHAR(64)   DEFAULT NULL COMMENT '区域ID，NULL 表示全局规则',
    `blue_threshold`   DECIMAL(12,4) DEFAULT NULL COMMENT '蓝色预警阈值',
    `yellow_threshold` DECIMAL(12,4) DEFAULT NULL COMMENT '黄色预警阈值',
    `orange_threshold` DECIMAL(12,4) DEFAULT NULL COMMENT '橙色预警阈值',
    `red_threshold`    DECIMAL(12,4) DEFAULT NULL COMMENT '红色预警阈值',
    `compare_type`     VARCHAR(16)   NOT NULL DEFAULT 'GT' COMMENT '比较方式：GT / GTE / LT / LTE / EQ',
    `enabled`          TINYINT(1)    NOT NULL DEFAULT 1 COMMENT '是否启用：0-停用 1-启用',
    `description`      VARCHAR(512)  DEFAULT NULL COMMENT '规则描述',
    `created_at`       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_rule_code` (`rule_code`),
    KEY `idx_device_type` (`device_type`),
    KEY `idx_metric_key` (`metric_key`),
    KEY `idx_area_id` (`area_id`),
    KEY `idx_enabled` (`enabled`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='预警规则表';

-- ============================================================
-- 2. alert_event 预警事件表
-- ============================================================
DROP TABLE IF EXISTS `alert_event`;
CREATE TABLE `alert_event` (
    `id`               BIGINT        NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `alert_event_code` VARCHAR(64)   NOT NULL COMMENT '预警事件编码，唯一标识',
    `source_event_id`  VARCHAR(128)  NOT NULL COMMENT '来源事件ID，对应 Kafka 消息 eventId',
    `source`           VARCHAR(64)   NOT NULL COMMENT '来源服务：tunnel-service / gas-risk-service',
    `device_id`        VARCHAR(64)   NOT NULL COMMENT '设备/传感器唯一标识',
    `device_type`      VARCHAR(32)   NOT NULL COMMENT '设备类型：PRESSURE / TEMPERATURE / CH4 / H2S 等',
    `zone`             VARCHAR(64)   DEFAULT NULL COMMENT '区域分区，管廊区段编号',
    `area_id`          VARCHAR(64)   NOT NULL COMMENT '统一区域标识',
    `alert_level`      VARCHAR(16)   NOT NULL COMMENT '预警等级：BLUE / YELLOW / ORANGE / RED',
    `alert_status`     VARCHAR(16)   NOT NULL DEFAULT 'OPEN' COMMENT '预警状态：OPEN / ACKNOWLEDGED / RESOLVED / CLOSED',
    `metric_key`       VARCHAR(64)   NOT NULL COMMENT '触发指标编码',
    `metric_value`     DECIMAL(12,4) NOT NULL COMMENT '触发时指标值',
    `threshold_value`  DECIMAL(12,4) NOT NULL COMMENT '触发时阈值',
    `root_cause`       VARCHAR(64)   DEFAULT NULL COMMENT '根因分类：PRESSURE_ABNORMAL / GAS_LEAK 等',
    `root_cause_desc`  VARCHAR(512)  DEFAULT NULL COMMENT '根因分析描述',
    `priority_score`   INT           DEFAULT 0 COMMENT '动态优先级分数 1-100',
    `alert_group_id`   BIGINT        DEFAULT NULL COMMENT '所属聚合组ID',
    `merged_count`     INT           NOT NULL DEFAULT 1 COMMENT '合并事件数量',
    `event_timestamp`  BIGINT        NOT NULL COMMENT '事件产生时间，Unix 毫秒时间戳',
    `created_at`       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_alert_event_code` (`alert_event_code`),
    KEY `idx_source_event_id` (`source_event_id`),
    KEY `idx_area_id` (`area_id`),
    KEY `idx_alert_level` (`alert_level`),
    KEY `idx_alert_status` (`alert_status`),
    KEY `idx_device_id` (`device_id`),
    KEY `idx_alert_group_id` (`alert_group_id`),
    KEY `idx_event_timestamp` (`event_timestamp`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='预警事件表';

-- ============================================================
-- 3. alert_group 预警聚合组表
-- ============================================================
DROP TABLE IF EXISTS `alert_group`;
CREATE TABLE `alert_group` (
    `id`             BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `group_code`     VARCHAR(64)  NOT NULL COMMENT '聚合组编码，唯一标识',
    `area_id`        VARCHAR(64)  NOT NULL COMMENT '统一区域标识',
    `zone`           VARCHAR(64)  DEFAULT NULL COMMENT '区域分区',
    `highest_level`  VARCHAR(16)  NOT NULL COMMENT '最高预警等级：BLUE / YELLOW / ORANGE / RED',
    `total_count`    INT          NOT NULL DEFAULT 0 COMMENT '组内预警总数',
    `group_status`   VARCHAR(16)  NOT NULL DEFAULT 'OPEN' COMMENT '组状态：OPEN / ACKNOWLEDGED / RESOLVED / CLOSED',
    `window_start`   DATETIME     NOT NULL COMMENT '滑动窗口开始时间',
    `window_end`     DATETIME     NOT NULL COMMENT '滑动窗口结束时间',
    `created_at`     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_group_code` (`group_code`),
    KEY `idx_area_id` (`area_id`),
    KEY `idx_highest_level` (`highest_level`),
    KEY `idx_group_status` (`group_status`),
    KEY `idx_window_start` (`window_start`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='预警聚合组表';

-- ============================================================
-- 4. area_priority 区域优先级配置表
-- ============================================================
DROP TABLE IF EXISTS `area_priority`;
CREATE TABLE `area_priority` (
    `id`                BIGINT        NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `area_id`           VARCHAR(64)   NOT NULL COMMENT '统一区域标识',
    `area_name`         VARCHAR(128)  NOT NULL COMMENT '区域名称',
    `importance`        INT           NOT NULL DEFAULT 50 COMMENT '区域重要度 1-100',
    `population_weight` DECIMAL(6,4)  NOT NULL DEFAULT 0.5000 COMMENT '人口权重 0.0000-1.0000',
    `description`       VARCHAR(512)  DEFAULT NULL COMMENT '区域描述',
    `created_at`        DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`        DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_area_id` (`area_id`),
    KEY `idx_importance` (`importance`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='区域优先级配置表';

-- ============================================================
-- 测试数据
-- ============================================================

-- 区域优先级
INSERT INTO `area_priority` (`area_id`, `area_name`, `importance`, `population_weight`, `description`) VALUES
('AREA-A01', '管廊A区01段', 80, 0.6000, '主管廊入口段，人流量较大'),
('AREA-A02', '管廊A区02段', 60, 0.3000, '管廊中段，常规监测区域'),
('AREA-A03', '管廊A区03段', 90, 0.8000, '靠近居民区，高优先级'),
('AREA-B02', '燃气管网B区02段', 85, 0.7000, '燃气管网关键节点');

-- 预警规则
INSERT INTO `alert_rule` (`rule_code`, `rule_name`, `device_type`, `metric_key`, `area_id`, `blue_threshold`, `yellow_threshold`, `orange_threshold`, `red_threshold`, `compare_type`, `description`) VALUES
('RULE-PRESSURE-001', '管道压力超限规则', 'PRESSURE', 'pressure', NULL, 3.5000, 4.0000, 4.5000, 5.0000, 'GT', '管道压力超过阈值时触发预警，全局规则'),
('RULE-TEMP-001', '温度超限规则', 'TEMPERATURE', 'temperature', NULL, 40.0000, 50.0000, 60.0000, 70.0000, 'GT', '温度超过阈值时触发预警，全局规则'),
('RULE-CH4-001', '甲烷浓度超标规则', 'CH4', 'ch4_concentration', NULL, 1.0000, 2.0000, 3.0000, 5.0000, 'GT', '甲烷浓度超过阈值时触发预警'),
('RULE-H2S-001', '硫化氢浓度超标规则', 'H2S', 'h2s_concentration', NULL, 5.0000, 10.0000, 15.0000, 20.0000, 'GT', '硫化氢浓度超过阈值时触发预警');

-- 预警事件（测试）
INSERT INTO `alert_event` (`alert_event_code`, `source_event_id`, `source`, `device_id`, `device_type`, `zone`, `area_id`, `alert_level`, `alert_status`, `metric_key`, `metric_value`, `threshold_value`, `root_cause`, `root_cause_desc`, `priority_score`, `event_timestamp`) VALUES
('ALT-20260831-0001', 'tunnel-service-a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'tunnel-service', 'SENSOR-P-001', 'PRESSURE', 'ZONE-A01', 'AREA-A01', 'ORANGE', 'OPEN', 'pressure', 4.2000, 4.0000, 'PRESSURE_ABNORMAL', '管道压力骤升至4.2MPa，超过黄色阈值', 72, 1725100800000),
('ALT-20260831-0002', 'tunnel-service-f7e8d9c0-b1a2-3456-7890-abcdef123456', 'tunnel-service', 'SENSOR-T-015', 'TEMPERATURE', 'ZONE-A03', 'AREA-A03', 'YELLOW', 'OPEN', 'temperature', 55.0000, 50.0000, 'TEMPERATURE_ABNORMAL', '温度升至55℃，超过黄色阈值', 65, 1725100860000);

-- 预警聚合组（测试）
INSERT INTO `alert_group` (`group_code`, `area_id`, `zone`, `highest_level`, `total_count`, `group_status`, `window_start`, `window_end`) VALUES
('GRP-20260831-A01-001', 'AREA-A01', 'ZONE-A01', 'ORANGE', 1, 'OPEN', '2026-08-31 10:00:00', '2026-08-31 10:10:00');

-- ============================================================
-- 5. failure_prediction 故障预报与寿命预测表
-- ============================================================
DROP TABLE IF EXISTS `failure_prediction`;
CREATE TABLE `failure_prediction` (
    `id`                    BIGINT        NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `device_id`             VARCHAR(64)   NOT NULL COMMENT '设备唯一标识',
    `device_type`           VARCHAR(64)   NOT NULL COMMENT '设备类型：PRESSURE / TEMPERATURE / CH4 / H2S 等',
    `area_id`               VARCHAR(64)   NOT NULL COMMENT '所属区域标识',
    `health_score`          DECIMAL(5,2)  NOT NULL COMMENT '健康度评分 0.00-100.00',
    `risk_score`            DECIMAL(5,2)  NOT NULL COMMENT '风险评分 0.00-100.00',
    `failure_probability`   DECIMAL(5,2)  NOT NULL COMMENT '故障概率 0.00-100.00',
    `remaining_life_month`  INT           NOT NULL COMMENT '剩余寿命（月）',
    `prediction_level`      VARCHAR(20)   NOT NULL COMMENT '预测等级：LOW / MEDIUM / HIGH / CRITICAL',
    `prediction_time`       DATETIME      NOT NULL COMMENT '预测生成时间',
    `created_at`            DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_device_id` (`device_id`),
    KEY `idx_device_type` (`device_type`),
    KEY `idx_area_id` (`area_id`),
    KEY `idx_prediction_level` (`prediction_level`),
    KEY `idx_prediction_time` (`prediction_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='故障预报与寿命预测表';

-- 故障预测（测试数据）
INSERT INTO `failure_prediction` (`device_id`, `device_type`, `area_id`, `health_score`, `risk_score`, `failure_probability`, `remaining_life_month`, `prediction_level`, `prediction_time`) VALUES
('SENSOR-P-001', 'PRESSURE',    'AREA-A01', 72.50,  35.20,  18.50,  24, 'LOW',      '2026-09-01 08:00:00'),
('SENSOR-T-015', 'TEMPERATURE', 'AREA-A03', 45.80,  68.40,  52.30,   8, 'HIGH',     '2026-09-01 08:00:00'),
('SENSOR-CH4-07','CH4',         'AREA-B02', 30.20,  82.10,  78.60,   3, 'CRITICAL', '2026-09-01 08:00:00'),
('SENSOR-H2S-03','H2S',         'AREA-A02', 88.00,  12.50,   5.20,  36, 'LOW',      '2026-09-01 08:00:00'),
('SENSOR-P-009', 'PRESSURE',    'AREA-A03', 58.30,  55.00,  38.70,  14, 'MEDIUM',   '2026-09-01 08:00:00'),
('SENSOR-T-022', 'TEMPERATURE', 'AREA-B02', 62.10,  48.30,  28.40,  18, 'MEDIUM',   '2026-09-01 08:00:00'),
('SENSOR-CH4-12','CH4',         'AREA-A01', 38.50,  75.60,  65.20,   5, 'HIGH',     '2026-09-01 08:00:00'),
('SENSOR-H2S-08','H2S',         'AREA-A03', 91.20,   8.30,   3.10,  42, 'LOW',      '2026-09-01 08:00:00');
