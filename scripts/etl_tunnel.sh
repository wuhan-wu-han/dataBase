#!/bin/bash

# ==============================================================================
# 管廊环境数据ETL脚本 - ODS → DWD → DWS → ADS 全链路处理
# 使用纯Hive SQL实现，不依赖Spark
# ==============================================================================

DATE=$1
if [ -z "$DATE" ]; then
    DATE=$(date -d "-1 day" +%Y-%m-%d)
fi

echo "======================================"
echo "  管廊环境数据ETL脚本"
echo "  处理日期: $DATE"
echo "======================================"

# ==============================================================================
# 步骤1：ODS → DWD 清洗转换（展开params为独立指标字段）
# ==============================================================================
echo ""
echo "[1/4] 步骤1: ODS → DWD 数据清洗..."
sudo docker exec hive-server hive -e "
SET hive.exec.dynamic.partition.mode=nonstrict;
SET hive.exec.dynamic.partition=true;

USE dwd;

INSERT OVERWRITE TABLE dwd.tunnel_sensor_detail PARTITION (dt='$DATE')
SELECT
    get_json_object(raw_json, '$.device_id') AS device_id,
    get_json_object(raw_json, '$.device_type') AS device_type,
    get_json_object(raw_json, '$.cabin') AS cabin,
    get_json_object(raw_json, '$.cabin_name') AS cabin_name,
    get_json_object(raw_json, '$.zone') AS zone,
    get_json_object(raw_json, '$.workshop') AS workshop,
    get_json_object(raw_json, '$.event_timestamp') AS event_time,
    hour(from_unixtime(CAST(get_json_object(raw_json, '$.ts') AS BIGINT) div 1000)) AS hour,
    CAST(get_json_object(raw_json, '$.params.temperature') AS DOUBLE) AS temperature,
    CAST(get_json_object(raw_json, '$.params.humidity') AS DOUBLE) AS humidity,
    CAST(get_json_object(raw_json, '$.params.o2') AS DOUBLE) AS o2,
    CAST(get_json_object(raw_json, '$.params.co') AS DOUBLE) AS co,
    CAST(get_json_object(raw_json, '$.params.h2s') AS DOUBLE) AS h2s,
    CAST(get_json_object(raw_json, '$.params.ch4') AS DOUBLE) AS ch4,
    CAST(get_json_object(raw_json, '$.params.water_level') AS DOUBLE) AS water_level,
    CAST(get_json_object(raw_json, '$.params.smoke') AS DOUBLE) AS smoke,
    CAST(get_json_object(raw_json, '$.level') AS INT) AS level,
    CAST(get_json_object(raw_json, '$.alarm_code') AS INT) AS alarm_code,
    get_json_object(raw_json, '$.alarm_desc') AS alarm_desc,
    CAST(get_json_object(raw_json, '$.health_score') AS INT) AS health_score,
    CASE WHEN CAST(get_json_object(raw_json, '$.alarm_code') AS INT) != 0
          OR CAST(get_json_object(raw_json, '$.level') AS INT) > 0
         THEN 1 ELSE 0 END AS is_abnormal
FROM ods.tunnel_sensor_raw
WHERE dt = '$DATE';
"

# ==============================================================================
# 步骤2：DWD → DWS 舱段环境聚合（按舱室+区段）
# ==============================================================================
echo ""
echo "[2/4] 步骤2: DWD → DWS 舱段环境聚合..."
sudo docker exec hive-server hive -e "
SET hive.exec.dynamic.partition.mode=nonstrict;
SET hive.exec.dynamic.partition=true;

USE dws;

INSERT OVERWRITE TABLE dws.tunnel_env_summary PARTITION (dt='$DATE')
SELECT
    cabin,
    MAX(cabin_name) AS cabin_name,
    zone,
    COUNT(*) AS total_records,
    ROUND(AVG(temperature), 2) AS avg_temperature,
    ROUND(MAX(temperature), 2) AS max_temperature,
    ROUND(AVG(humidity), 2) AS avg_humidity,
    ROUND(MAX(humidity), 2) AS max_humidity,
    ROUND(AVG(o2), 2) AS avg_o2,
    ROUND(MIN(o2), 2) AS min_o2,
    ROUND(MAX(co), 2) AS max_co,
    ROUND(MAX(h2s), 2) AS max_h2s,
    ROUND(MAX(ch4), 4) AS max_ch4,
    ROUND(MAX(water_level), 2) AS max_water_level,
    ROUND(MAX(smoke), 2) AS max_smoke,
    SUM(CASE WHEN alarm_code != 0 THEN 1 ELSE 0 END) AS alarm_count,
    ROUND(AVG(health_score), 2) AS avg_health_score
FROM dwd.tunnel_sensor_detail
WHERE dt = '$DATE'
GROUP BY cabin, zone;
"

# ==============================================================================
# 步骤3：DWD → DWS 舱室汇总（在线率与环境健康分）
# ==============================================================================
echo ""
echo "[3/4] 步骤3: DWD → DWS 舱室汇总..."
sudo docker exec hive-server hive -e "
SET hive.exec.dynamic.partition.mode=nonstrict;
SET hive.exec.dynamic.partition=true;

USE dws;

INSERT OVERWRITE TABLE dws.tunnel_cabin_summary PARTITION (dt='$DATE')
SELECT
    cabin,
    MAX(cabin_name) AS cabin_name,
    COUNT(DISTINCT device_id) AS total_points,
    CASE cabin WHEN 'EL' THEN 30 WHEN 'GS' THEN 36 WHEN 'WS' THEN 24 ELSE 0 END AS expected_points,
    CASE WHEN (CASE cabin WHEN 'EL' THEN 30 WHEN 'GS' THEN 36 WHEN 'WS' THEN 24 ELSE 0 END) > 0
         THEN COUNT(DISTINCT device_id) / (CASE cabin WHEN 'EL' THEN 30 WHEN 'GS' THEN 36 WHEN 'WS' THEN 24 ELSE 0 END)
         ELSE 0 END AS online_rate,
    COUNT(*) AS total_records,
    SUM(CASE WHEN alarm_code != 0 THEN 1 ELSE 0 END) AS alarm_count,
    ROUND(AVG(health_score), 2) AS avg_health_score,
    ROUND(AVG(health_score), 2) AS env_health_score
FROM dwd.tunnel_sensor_detail
WHERE dt = '$DATE'
GROUP BY cabin;
"

# ==============================================================================
# 步骤4：DWD → ADS 大屏应用数据（总览 + 告警统计）
# ==============================================================================
echo ""
echo "[4/4] 步骤4: DWD → ADS 大屏应用数据..."
sudo docker exec hive-server hive -e "
SET hive.exec.dynamic.partition.mode=nonstrict;
SET hive.exec.dynamic.partition=true;

USE ads;

-- 管廊环境总览
INSERT OVERWRITE TABLE ads.tunnel_overview PARTITION (dt='$DATE')
SELECT
    COUNT(DISTINCT device_id) AS total_points,
    COUNT(*) AS total_records,
    SUM(CASE WHEN alarm_code != 0 THEN 1 ELSE 0 END) AS alarm_count,
    SUM(CASE WHEN level = 1 THEN 1 ELSE 0 END) AS warn_count,
    SUM(CASE WHEN level = 2 THEN 1 ELSE 0 END) AS crit_count,
    ROUND(AVG(health_score), 2) AS avg_health_score,
    ROUND(AVG(health_score), 2) AS env_health_score
FROM dwd.tunnel_sensor_detail
WHERE dt = '$DATE';

-- 管廊告警类型统计
INSERT OVERWRITE TABLE ads.tunnel_alarm_stats PARTITION (dt='$DATE')
SELECT
    alarm_code,
    MAX(alarm_desc) AS alarm_desc,
    COUNT(*) AS alarm_count,
    MAX(cabin) AS cabin,
    CASE
        WHEN alarm_code IN (51002, 51012, 51022, 51032, 51042, 51052, 51062, 51072) THEN '高'
        ELSE '中'
    END AS severity
FROM dwd.tunnel_sensor_detail
WHERE dt = '$DATE' AND alarm_code != 0
GROUP BY alarm_code;
"

echo ""
echo "======================================"
echo "  ✅ ETL处理完成！"
echo "  处理日期: $DATE"
echo "======================================"
echo ""
echo "数据验证查询:"
sudo docker exec hive-server hive -e "
USE ads;
SELECT '管廊总览' AS module, total_points, total_records, alarm_count, warn_count, crit_count, env_health_score FROM tunnel_overview WHERE dt='$DATE';
SELECT '告警类型' AS module, alarm_desc, alarm_count, severity FROM tunnel_alarm_stats WHERE dt='$DATE' ORDER BY alarm_count DESC LIMIT 5;
USE dws;
SELECT '舱室汇总' AS module, cabin_name, total_points, online_rate, alarm_count, env_health_score FROM tunnel_cabin_summary WHERE dt='$DATE';
"
