-- ==============================================================================
-- 地下综合管廊管控数仓建表语句
-- 分层：ODS（原始数据） → DWD（明细数据） → DWS（聚合数据） → ADS（应用数据）
-- 复用设备域已有的 ods/dwd/dws/ads 四库，表名以 tunnel_ 前缀隔离
-- ==============================================================================

CREATE DATABASE IF NOT EXISTS ods;
CREATE DATABASE IF NOT EXISTS dwd;
CREATE DATABASE IF NOT EXISTS dws;
CREATE DATABASE IF NOT EXISTS ads;

-- ==============================================================================
-- ODS层：原始管廊环境传感数据
-- ==============================================================================
USE ods;

-- 管廊环境传感器原始数据表（存储从Kafka采集的完整JSON记录）
-- 使用单列raw_json存储完整JSON字符串，避免依赖第三方JsonSerDe
-- 查询时使用 get_json_object(raw_json, '$.field') 提取字段
CREATE EXTERNAL TABLE IF NOT EXISTS ods.tunnel_sensor_raw (
    raw_json STRING COMMENT '原始JSON记录字符串'
)
PARTITIONED BY (dt STRING COMMENT '日期分区 yyyy-MM-dd')
STORED AS TEXTFILE
LOCATION '/user/hive/warehouse/ods.db/tunnel_sensor_raw';

-- 管廊环境告警原始数据表（同样使用单列raw_json存储）
CREATE EXTERNAL TABLE IF NOT EXISTS ods.tunnel_alarm_raw (
    raw_json STRING COMMENT '原始告警JSON记录字符串'
)
PARTITIONED BY (dt STRING COMMENT '日期分区')
STORED AS TEXTFILE
LOCATION '/user/hive/warehouse/ods.db/tunnel_alarm_raw';

-- ==============================================================================
-- DWD层：清洗后的管廊环境明细数据
-- ==============================================================================
USE dwd;

-- 管廊环境明细宽表（展开params为独立指标字段，便于SQL查询）
CREATE TABLE IF NOT EXISTS dwd.tunnel_sensor_detail (
    device_id STRING COMMENT '传感器点位编码',
    device_type STRING COMMENT '传感器类型名称',
    cabin STRING COMMENT '舱室编码(EL/GS/WS)',
    cabin_name STRING COMMENT '舱室名称',
    zone STRING COMMENT '区段编码(Z01~Z06)',
    workshop STRING COMMENT '定位串(舱室-区段)',
    event_time STRING COMMENT '事件时间',
    hour INT COMMENT '小时(0-23)',
    temperature DOUBLE COMMENT '温度(℃)',
    humidity DOUBLE COMMENT '湿度(%RH)',
    o2 DOUBLE COMMENT '氧气浓度(%VOL)',
    co DOUBLE COMMENT '一氧化碳(ppm)',
    h2s DOUBLE COMMENT '硫化氢(ppm)',
    ch4 DOUBLE COMMENT '甲烷浓度(%VOL)',
    water_level DOUBLE COMMENT '积水液位(mm)',
    smoke DOUBLE COMMENT '烟雾指数',
    level INT COMMENT '判定级别(0正常/1预警/2严重)',
    alarm_code INT COMMENT '告警代码(51xxx)',
    alarm_desc STRING COMMENT '告警描述',
    health_score INT COMMENT '环境健康度评分',
    is_abnormal INT COMMENT '是否越限(0正常/1越限)'
)
PARTITIONED BY (dt STRING COMMENT '日期分区')
STORED AS ORC
TBLPROPERTIES ('orc.compress' = 'SNAPPY');

-- ==============================================================================
-- DWS层：管廊环境聚合数据
-- ==============================================================================
USE dws;

-- 舱段环境聚合表（按舱室+区段汇总各指标与告警）
CREATE TABLE IF NOT EXISTS dws.tunnel_env_summary (
    cabin STRING COMMENT '舱室编码',
    cabin_name STRING COMMENT '舱室名称',
    zone STRING COMMENT '区段编码',
    total_records BIGINT COMMENT '总记录数',
    avg_temperature DECIMAL(10,2) COMMENT '平均温度(℃)',
    max_temperature DECIMAL(10,2) COMMENT '最高温度(℃)',
    avg_humidity DECIMAL(10,2) COMMENT '平均湿度(%RH)',
    max_humidity DECIMAL(10,2) COMMENT '最高湿度(%RH)',
    avg_o2 DECIMAL(10,2) COMMENT '平均氧气浓度(%VOL)',
    min_o2 DECIMAL(10,2) COMMENT '最低氧气浓度(%VOL)',
    max_co DECIMAL(10,2) COMMENT '最高一氧化碳(ppm)',
    max_h2s DECIMAL(10,2) COMMENT '最高硫化氢(ppm)',
    max_ch4 DECIMAL(10,4) COMMENT '最高甲烷浓度(%VOL)',
    max_water_level DECIMAL(10,2) COMMENT '最高积水液位(mm)',
    max_smoke DECIMAL(10,2) COMMENT '最高烟雾指数',
    alarm_count BIGINT COMMENT '告警次数',
    avg_health_score DECIMAL(10,2) COMMENT '平均环境健康度'
)
PARTITIONED BY (dt STRING COMMENT '日期分区')
STORED AS ORC
TBLPROPERTIES ('orc.compress' = 'SNAPPY');

-- 舱室汇总表（在线率与环境健康分）
CREATE TABLE IF NOT EXISTS dws.tunnel_cabin_summary (
    cabin STRING COMMENT '舱室编码',
    cabin_name STRING COMMENT '舱室名称',
    total_points INT COMMENT '上报点位数',
    expected_points INT COMMENT '理论点位数',
    online_rate DECIMAL(10,4) COMMENT '点位在线率',
    total_records BIGINT COMMENT '总记录数',
    alarm_count BIGINT COMMENT '告警次数',
    avg_health_score DECIMAL(10,2) COMMENT '平均环境健康度',
    env_health_score DECIMAL(10,2) COMMENT '环境健康分'
)
PARTITIONED BY (dt STRING COMMENT '日期分区')
STORED AS ORC
TBLPROPERTIES ('orc.compress' = 'SNAPPY');

-- ==============================================================================
-- ADS层：管廊大屏应用层数据
-- ==============================================================================
USE ads;

-- 管廊环境总览表（大屏顶部展示）
CREATE TABLE IF NOT EXISTS ads.tunnel_overview (
    total_points INT COMMENT '上报点位总数',
    total_records BIGINT COMMENT '总记录数',
    alarm_count BIGINT COMMENT '告警总数',
    warn_count BIGINT COMMENT '预警次数',
    crit_count BIGINT COMMENT '严重告警次数',
    avg_health_score DECIMAL(10,2) COMMENT '平均环境健康度',
    env_health_score DECIMAL(10,2) COMMENT '环境健康分'
)
PARTITIONED BY (dt STRING COMMENT '日期分区')
STORED AS ORC
TBLPROPERTIES ('orc.compress' = 'SNAPPY');

-- 管廊告警类型统计表（大屏告警分析展示）
CREATE TABLE IF NOT EXISTS ads.tunnel_alarm_stats (
    alarm_code INT COMMENT '告警代码(51xxx)',
    alarm_desc STRING COMMENT '告警描述',
    alarm_count BIGINT COMMENT '告警次数',
    cabin STRING COMMENT '主要发生舱室',
    severity STRING COMMENT '告警等级(高/中)'
)
PARTITIONED BY (dt STRING COMMENT '日期分区')
STORED AS ORC
TBLPROPERTIES ('orc.compress' = 'SNAPPY');
