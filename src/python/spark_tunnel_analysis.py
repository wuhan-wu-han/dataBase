#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Spark管廊环境数据分析脚本

功能：
1. 数据清洗：从ODS层读取原始管廊环境数据，展开params为独立指标字段
2. 舱段聚合：按舱室+区段汇总各环境指标与告警
3. 舱室汇总：点位在线率与环境健康分
4. 大屏应用：管廊环境总览、告警类型统计

与 scripts/etl_tunnel.sh 逻辑一致，二选一执行。

使用示例：
    spark-submit --master spark://spark-master:7077 spark_tunnel_analysis.py 2026-08-28

依赖：
    PySpark 3.0+
"""

import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import *


def create_spark_session(app_name="TunnelEnvironmentAnalysis"):
    """
    创建SparkSession实例

    Args:
        app_name (str): 应用名称

    Returns:
        SparkSession: 配置好的Spark会话
    """
    spark = SparkSession.builder \
        .appName(app_name) \
        .enableHiveSupport() \
        .config("spark.sql.hive.metastorePartitionPruningFallbackOnException", "true") \
        .config("spark.sql.hive.metastorePartitionPruningFastFallback", "true") \
        .config("spark.sql.hive.convertMetastoreParquet", "false") \
        .config("spark.sql.hive.convertMetastoreOrc", "false") \
        .getOrCreate()
    return spark


def clean_and_transform(spark, date):
    """
    数据清洗：从ODS层读取原始JSON数据，展开params为独立指标字段写入DWD层

    Args:
        spark (SparkSession): Spark会话
        date (str): 日期参数

    Returns:
        DataFrame: 清洗后的明细DataFrame
    """
    cleaned_df = spark.sql(f"""
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
                 THEN 1 ELSE 0 END AS is_abnormal,
            dt
        FROM ods.tunnel_sensor_raw
        WHERE dt = '{date}'
    """)

    cleaned_df.write.mode("overwrite").partitionBy("dt").saveAsTable("dwd.tunnel_sensor_detail")
    print(f"DWD层管廊明细数据已保存，日期: {date}")

    return cleaned_df


def build_env_summary(spark, date):
    """
    构建舱段环境聚合表（DWS层，按舱室+区段）

    Args:
        spark (SparkSession): Spark会话
        date (str): 日期参数
    """
    spark.sql(f"""
        INSERT OVERWRITE TABLE dws.tunnel_env_summary PARTITION (dt='{date}')
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
        WHERE dt = '{date}'
        GROUP BY cabin, zone
    """)
    print("舱段环境聚合表构建完成")


def build_cabin_summary(spark, date):
    """
    构建舱室汇总表（DWS层，在线率与环境健康分）

    Args:
        spark (SparkSession): Spark会话
        date (str): 日期参数
    """
    spark.sql(f"""
        INSERT OVERWRITE TABLE dws.tunnel_cabin_summary PARTITION (dt='{date}')
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
        WHERE dt = '{date}'
        GROUP BY cabin
    """)
    print("舱室汇总表构建完成")


def build_tunnel_overview(spark, date):
    """
    构建管廊环境总览表（ADS层）

    Args:
        spark (SparkSession): Spark会话
        date (str): 日期参数
    """
    spark.sql(f"""
        INSERT OVERWRITE TABLE ads.tunnel_overview PARTITION (dt='{date}')
        SELECT
            COUNT(DISTINCT device_id) AS total_points,
            COUNT(*) AS total_records,
            SUM(CASE WHEN alarm_code != 0 THEN 1 ELSE 0 END) AS alarm_count,
            SUM(CASE WHEN level = 1 THEN 1 ELSE 0 END) AS warn_count,
            SUM(CASE WHEN level = 2 THEN 1 ELSE 0 END) AS crit_count,
            ROUND(AVG(health_score), 2) AS avg_health_score,
            ROUND(AVG(health_score), 2) AS env_health_score
        FROM dwd.tunnel_sensor_detail
        WHERE dt = '{date}'
    """)
    print("管廊环境总览表构建完成")


def build_alarm_stats(spark, date):
    """
    构建管廊告警类型统计表（ADS层）

    Args:
        spark (SparkSession): Spark会话
        date (str): 日期参数
    """
    spark.sql(f"""
        INSERT OVERWRITE TABLE ads.tunnel_alarm_stats PARTITION (dt='{date}')
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
        WHERE dt = '{date}' AND alarm_code != 0
        GROUP BY alarm_code
    """)
    print("管廊告警类型统计表构建完成")


def main():
    """
    主函数：执行完整的管廊环境分析流程
    """
    from datetime import datetime, timedelta
    date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    if len(sys.argv) > 1:
        date = sys.argv[1]

    print(f"处理日期: {date}")

    spark = create_spark_session()

    try:
        print("\n[步骤1] 数据清洗与转换 (ODS → DWD)...")
        clean_and_transform(spark, date)

        print("\n[步骤2] 舱段环境聚合 (DWD → DWS)...")
        build_env_summary(spark, date)

        print("\n[步骤3] 舱室汇总 (DWD → DWS)...")
        build_cabin_summary(spark, date)

        print("\n[步骤4] 管廊环境总览 (DWD → ADS)...")
        build_tunnel_overview(spark, date)

        print("\n[步骤5] 告警类型统计 (DWD → ADS)...")
        build_alarm_stats(spark, date)

        print("\n✓ 所有管廊分析任务执行完成")

    finally:
        spark.stop()
        print("Spark会话已停止")


if __name__ == "__main__":
    main()
