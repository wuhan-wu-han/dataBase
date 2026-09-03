/**
 * 风险研判中心 / 数据治理 Mock 数据
 *
 * 对应接口（src/api/riskAnalysis.js）：
 *   GET  /governance/overview            → overview
 *   GET  /governance/master/stats        → masterStats
 *   GET  /governance/master/{dataType}   → masterList
 *   GET  /governance/standards           → standards
 *   GET  /governance/compliance          → compliance
 *   GET  /governance/quality/report      → qualityReport
 *   POST /governance/quality/check       → qualityCheckResult
 *   GET  /governance/api/services        → apiServices
 *   GET  /governance/api/stats           → apiStats
 *
 * 说明：部分对象带有 "视图兼容字段"（如 api_id / endpoint / rule_code 等），
 * 这些是 src/views/riskAnalysis/Index.vue 表格直接读取的别名，便于 Mock 直接替换后端。
 */

const riskAnalysisMock = {
  // ==================== 数据总览 ====================
  overview: {
    total_master_data: 1256,
    api_services_count: 42,
    api_total_calls_24h: 15680,
    pipeline_count: 386,
    sensor_count: 1842,
    alarm_count_30d: 267,
    compliance_rate: 94.2,
    data_quality_score: 88.5,
    api_count: 42,
    api_calls_24h: 15680,

    // 视图兼容字段（Index.vue overviewTiles / StatCard 读取）
    equipment_count: 312,
    personnel_count: 168,
    organization_count: 46,
    geo_space_count: 102,
    data_standards_count: 12,
    quality_rules_count: 15,
    quality_passed: 12,
    avg_quality_score: 88.5,
    api_services_count: 42,
    api_total_calls_24h: 15680,
    api_avg_response_ms: 126
  },

  // ==================== 主数据统计 ====================
  masterStats: {
    master_data: [
      {
        category: '管道',
        count: 456,
        healthy: 420,
        warning: 28,
        error: 8,
        // 视图兼容字段
        type: 'pipeline',
        name: '管道主数据',
        icon: 'Share',
        subtypes: ['燃气干管', '给水管道', '电力电缆', '通信光缆']
      },
      {
        category: '阀门',
        count: 312,
        healthy: 290,
        warning: 15,
        error: 7,
        type: 'valve',
        name: '阀门主数据',
        icon: 'Setting',
        subtypes: ['电动闸阀', '蝶阀', '球阀', '安全阀']
      },
      {
        category: '传感器',
        count: 286,
        healthy: 265,
        warning: 14,
        error: 7,
        type: 'sensor',
        name: '传感器主数据',
        icon: 'Odometer',
        subtypes: ['甲烷浓度', '温湿度', '液位', '位移沉降']
      },
      {
        category: '站点',
        count: 102,
        healthy: 95,
        warning: 5,
        error: 2,
        type: 'station',
        name: '站点主数据',
        icon: 'OfficeBuilding',
        subtypes: ['监控中心', '分区节点', '出入口', '通风口']
      },
      {
        category: '工单',
        count: 100,
        healthy: 88,
        warning: 9,
        error: 3,
        type: 'workorder',
        name: '工单主数据',
        icon: 'Tickets',
        subtypes: ['日常巡检', '计划维修', '应急抢修', '保养维护']
      }
    ]
  },

  // ==================== 主数据清单 ====================
  masterList: {
    data: [
      {
        data_id: 'MD-2026-0001',
        name: '综合管廊A舱燃气干管 DN600',
        category: '管道',
        source_system: 'GIS地理信息系统',
        sync_status: '已同步',
        last_sync_at: '2026-08-31 22:15:08',
        data_quality_score: 96.4,
        record_count: 1286,
        status: 'active'
      },
      {
        data_id: 'MD-2026-0002',
        name: '城东分输站电动闸阀 Z941H',
        category: '阀门',
        source_system: 'EAM资产管理系统',
        sync_status: '已同步',
        last_sync_at: '2026-08-31 21:40:22',
        data_quality_score: 92.1,
        record_count: 642,
        status: 'active'
      },
      {
        data_id: 'MD-2026-0003',
        name: '甲烷浓度监测传感器阵列',
        category: '传感器',
        source_system: 'IoT感知平台',
        sync_status: '同步中',
        last_sync_at: '2026-09-01 08:05:47',
        data_quality_score: 88.7,
        record_count: 1842,
        status: 'active'
      },
      {
        data_id: 'MD-2026-0004',
        name: '综合管廊监控中心站点台账',
        category: '站点',
        source_system: 'BIM运维平台',
        sync_status: '已同步',
        last_sync_at: '2026-08-30 18:22:35',
        data_quality_score: 94.8,
        record_count: 102,
        status: 'active'
      },
      {
        data_id: 'MD-2026-0005',
        name: '巡检维修工单主数据',
        category: '工单',
        source_system: '工单管理系统',
        sync_status: '已同步',
        last_sync_at: '2026-08-31 23:58:11',
        data_quality_score: 90.3,
        record_count: 3268,
        status: 'active'
      },
      {
        data_id: 'MD-2026-0006',
        name: '高压电力电缆舱管线档案',
        category: '管道',
        source_system: 'GIS地理信息系统',
        sync_status: '未同步',
        last_sync_at: '2026-08-28 09:12:40',
        data_quality_score: 76.5,
        record_count: 486,
        status: 'inactive'
      },
      {
        data_id: 'MD-2026-0007',
        name: '给排水主干管阀门组',
        category: '阀门',
        source_system: 'SCADA监控系统',
        sync_status: '同步中',
        last_sync_at: '2026-09-01 07:48:03',
        data_quality_score: 85.2,
        record_count: 318,
        status: 'active'
      },
      {
        data_id: 'MD-2026-0008',
        name: '温湿度与液位复合传感器',
        category: '传感器',
        source_system: 'IoT感知平台',
        sync_status: '已同步',
        last_sync_at: '2026-08-31 20:30:56',
        data_quality_score: 91.6,
        record_count: 964,
        status: 'active'
      },
      {
        data_id: 'MD-2026-0009',
        name: '通风口及出入口站点坐标',
        category: '站点',
        source_system: 'GIS地理信息系统',
        sync_status: '已同步',
        last_sync_at: '2026-08-29 16:05:19',
        data_quality_score: 89.4,
        record_count: 268,
        status: 'active'
      },
      {
        data_id: 'MD-2026-0010',
        name: '应急抢修工单归档数据',
        category: '工单',
        source_system: '应急指挥平台',
        sync_status: '未同步',
        last_sync_at: '2026-08-25 11:37:52',
        data_quality_score: 72.8,
        record_count: 540,
        status: 'inactive'
      },
      {
        data_id: 'MD-2026-0011',
        name: '通信管道与光纤线路台账',
        category: '管道',
        source_system: '通信管线系统',
        sync_status: '已同步',
        last_sync_at: '2026-08-31 19:14:27',
        data_quality_score: 93.5,
        record_count: 724,
        status: 'active'
      },
      {
        data_id: 'MD-2026-0012',
        name: '燃气泄漏报警联动阀门',
        category: '阀门',
        source_system: 'SCADA监控系统',
        sync_status: '已同步',
        last_sync_at: '2026-09-01 06:22:14',
        data_quality_score: 95.1,
        record_count: 156,
        status: 'active'
      }
    ],
    total: 20
  },

  // ==================== 数据标准 ====================
  standards: {
    standards: [
      {
        standard_id: 'STD-PIPE-001',
        name: '管道编码规范',
        category: '编码规范',
        version: 'V2.3',
        status: '已发布',
        field_count: 28,
        created_at: '2026-01-12',
        updated_at: '2026-07-18',
        description: '规定综合管廊内各类管道的唯一编码结构、舱室标识与管径表示方法，统一 GIS 与运维平台的管线命名。',
        // 视图兼容字段
        code: 'STD-PIPE-001',
        encoding_rule: 'GL-{区域码}{舱室码}-{管径}-{四位序号}',
        unit_standard: 'mm / MPa',
        format_spec: 'DN + 三位数字，压力保留两位小数',
        sample_count: 456
      },
      {
        standard_id: 'STD-VALVE-002',
        name: '阀门台账数据规范',
        category: '台账规范',
        version: 'V1.8',
        status: '已发布',
        field_count: 34,
        created_at: '2026-02-03',
        updated_at: '2026-06-25',
        description: '明确阀门台账必填字段、型号命名、驱动方式与联动关系的数据结构，保障 EAM 与 SCADA 数据一致。',
        code: 'STD-VALVE-002',
        encoding_rule: 'FM-{管种码}-{口径}-{两位序号}',
        unit_standard: 'mm / N·m',
        format_spec: '型号采用厂商标准代号，口径 DN 表示',
        sample_count: 312
      },
      {
        standard_id: 'STD-SENSOR-003',
        name: '传感器计量单位规范',
        category: '计量标准',
        version: 'V3.1',
        status: '已发布',
        field_count: 22,
        created_at: '2025-11-20',
        updated_at: '2026-08-06',
        description: '统一各类感知设备的量纲、精度与采样频率表达方式，避免 %LEL、ppm、mg/m³ 混用导致研判偏差。',
        code: 'STD-SENSOR-003',
        encoding_rule: 'SN-{监测类型}-{站点码}-{三位序号}',
        unit_standard: '%LEL / ppm / ℃ / %RH / m',
        format_spec: '数值保留一位小数，单位后缀紧跟量值',
        sample_count: 286
      },
      {
        standard_id: 'STD-SITE-004',
        name: '站点空间坐标规范',
        category: '空间标准',
        version: 'V2.0',
        status: '已发布',
        field_count: 18,
        created_at: '2026-03-08',
        updated_at: '2026-07-30',
        description: '规定站点、出入口、通风口等空间要素的坐标系（CGCS2000）、高程基准与拓扑层级表达方式。',
        code: 'STD-SITE-004',
        encoding_rule: 'ST-{行政区码}-{分区码}-{两位序号}',
        unit_standard: 'CGCS2000 / 1985国家高程基准',
        format_spec: '经纬度保留 8 位小数，高程保留 3 位小数',
        sample_count: 102
      },
      {
        standard_id: 'STD-WO-005',
        name: '工单状态与流程规范',
        category: '流程规范',
        version: 'V1.5',
        status: '已发布',
        field_count: 26,
        created_at: '2026-04-15',
        updated_at: '2026-08-12',
        description: '定义工单从创建、派发、处置到归档的状态枚举与时间字段，统一各业务系统的工单数据口径。',
        code: 'STD-WO-005',
        encoding_rule: 'WO-{年月}-{类型码}-{五位流水号}',
        unit_standard: 'ISO 8601 时间格式',
        format_spec: '状态枚举：待派发/处理中/已完成/已归档',
        sample_count: 100
      },
      {
        standard_id: 'STD-COMMON-006',
        name: '主数据唯一标识规范',
        category: '编码规范',
        version: 'V2.6',
        status: '已发布',
        field_count: 12,
        created_at: '2025-09-02',
        updated_at: '2026-05-19',
        description: '规定全域主数据的唯一标识生成规则、前缀分类与跨系统映射表维护要求，消除一物多码现象。',
        code: 'STD-COMMON-006',
        encoding_rule: 'MD-{年份}-{四位分类码}-{四位序号}',
        unit_standard: '—',
        format_spec: '全大写 ASCII，长度固定 15 位',
        sample_count: 1256
      },
      {
        standard_id: 'STD-QUALITY-007',
        name: '数据质量评估规范',
        category: '质量规范',
        version: 'V1.9',
        status: '已发布',
        field_count: 31,
        created_at: '2026-01-28',
        updated_at: '2026-08-20',
        description: '定义完整性、准确性、一致性、唯一性、时效性、规范性六个维度的评分模型与阈值判定方法。',
        code: 'STD-QUALITY-007',
        encoding_rule: 'QR-{维度码}-{三位序号}',
        unit_standard: '百分制（0-100）',
        format_spec: '得分保留一位小数，阈值精确到整数',
        sample_count: 1256
      },
      {
        standard_id: 'STD-EXCHANGE-008',
        name: '数据交换接口规范',
        category: '接口规范',
        version: 'V2.2',
        status: '已发布',
        field_count: 40,
        created_at: '2026-02-19',
        updated_at: '2026-07-05',
        description: '规范跨系统数据交换的 RESTful 接口命名、请求响应结构、鉴权方式与错误码，支撑统一 API 服务目录。',
        code: 'STD-EXCHANGE-008',
        encoding_rule: 'SVC-{业务域码}-{三位序号}',
        unit_standard: 'HTTP/JSON，UTF-8 编码',
        format_spec: '路径小写中划线分隔，响应含 code/data/message',
        sample_count: 42
      },
      {
        standard_id: 'STD-SEC-009',
        name: '敏感数据分级分类规范',
        category: '安全规范',
        version: 'V0.9',
        status: '草稿',
        field_count: 24,
        created_at: '2026-07-22',
        updated_at: '2026-08-28',
        description: '按公开、内部、敏感、机密四级对管廊运维数据进行分类，明确各级数据的脱敏、加密与访问审计要求。',
        code: 'STD-SEC-009',
        encoding_rule: 'DS-{级别码}-{业务域码}-{序号}',
        unit_standard: '—',
        format_spec: '级别枚举：L1公开/L2内部/L3敏感/L4机密',
        sample_count: 0
      },
      {
        standard_id: 'STD-OLD-010',
        name: '管线巡检记录规范（旧版）',
        category: '流程规范',
        version: 'V1.2',
        status: '已废弃',
        field_count: 15,
        created_at: '2024-06-10',
        updated_at: '2025-12-01',
        description: '早期人工巡检纸质记录电子化标准，已由 STD-WO-005 工单状态与流程规范替代，仅保留历史数据映射用途。',
        code: 'STD-OLD-010',
        encoding_rule: 'INS-{班组码}-{日期}-{序号}',
        unit_standard: '—',
        format_spec: '日期格式 YYYYMMDD',
        sample_count: 0
      }
    ],
    total: 12
  },

  // ==================== 标准符合度 ====================
  compliance: {
    overall_compliance: 94.2,
    checks: [
      {
        check_id: 'CHK-2026-0001',
        name: '管道编码规范符合性核查',
        category: '编码规范',
        compliance_rate: 96.7,
        total_records: 456,
        compliant_records: 441,
        non_compliant_records: 15,
        check_date: '2026-08-31',
        status: '达标',
        // 视图兼容字段
        standard_code: 'STD-PIPE-001',
        standard_name: '管道编码规范',
        passed: true,
        sample_count: 456,
        violations: 15
      },
      {
        check_id: 'CHK-2026-0002',
        name: '阀门台账字段完整性核查',
        category: '完整性',
        compliance_rate: 92.3,
        total_records: 312,
        compliant_records: 288,
        non_compliant_records: 24,
        check_date: '2026-08-31',
        status: '达标',
        standard_code: 'STD-VALVE-002',
        standard_name: '阀门台账数据规范',
        passed: true,
        sample_count: 312,
        violations: 24
      },
      {
        check_id: 'CHK-2026-0003',
        name: '传感器计量单位标准核查',
        category: '计量标准',
        compliance_rate: 95.1,
        total_records: 286,
        compliant_records: 272,
        non_compliant_records: 14,
        check_date: '2026-08-30',
        status: '达标',
        standard_code: 'STD-SENSOR-003',
        standard_name: '传感器计量单位规范',
        passed: true,
        sample_count: 286,
        violations: 14
      },
      {
        check_id: 'CHK-2026-0004',
        name: '站点坐标系一致性核查',
        category: '空间标准',
        compliance_rate: 89.2,
        total_records: 102,
        compliant_records: 91,
        non_compliant_records: 11,
        check_date: '2026-08-30',
        status: '未达标',
        standard_code: 'STD-SITE-004',
        standard_name: '站点空间坐标规范',
        passed: false,
        sample_count: 102,
        violations: 11
      },
      {
        check_id: 'CHK-2026-0005',
        name: '工单状态枚举规范核查',
        category: '流程规范',
        compliance_rate: 97.0,
        total_records: 100,
        compliant_records: 97,
        non_compliant_records: 3,
        check_date: '2026-08-31',
        status: '达标',
        standard_code: 'STD-WO-005',
        standard_name: '工单状态与流程规范',
        passed: true,
        sample_count: 100,
        violations: 3
      },
      {
        check_id: 'CHK-2026-0006',
        name: '主数据更新时效性核查',
        category: '时效性',
        compliance_rate: 93.8,
        total_records: 1256,
        compliant_records: 1178,
        non_compliant_records: 78,
        check_date: '2026-09-01',
        status: '达标',
        standard_code: 'STD-COMMON-006',
        standard_name: '主数据唯一标识规范',
        passed: true,
        sample_count: 1256,
        violations: 78
      },
      {
        check_id: 'CHK-2026-0007',
        name: '质量评估维度覆盖核查',
        category: '质量规范',
        compliance_rate: 98.2,
        total_records: 1256,
        compliant_records: 1233,
        non_compliant_records: 23,
        check_date: '2026-09-01',
        status: '达标',
        standard_code: 'STD-QUALITY-007',
        standard_name: '数据质量评估规范',
        passed: true,
        sample_count: 1256,
        violations: 23
      }
    ]
  },

  // ==================== 数据质量报告 ====================
  qualityReport: {
    overall_score: 88.5,
    overall_level: '良好',
    rules: [
      {
        rule_id: 'QR-COMP-001',
        name: '管线坐标完整性校验',
        category: '完整性',
        severity: 'high',
        violation_count: 12,
        description: '校验管道主数据的起点、终点经纬度与高程字段是否齐全，缺失将导致拓扑分析无法闭环。',
        suggestion: '对缺失坐标的 12 条管线记录，由 GIS 班组在 5 个工作日内补测并回写。',
        // 视图兼容字段
        rule_code: 'QR-COMP-001',
        rule_name: '管线坐标完整性校验',
        score: 97.4,
        threshold: 95,
        passed: true,
        sample_size: 456,
        error_count: 12
      },
      {
        rule_id: 'QR-UNIQ-002',
        name: '阀门编码唯一性校验',
        category: '唯一性',
        severity: 'high',
        violation_count: 3,
        description: '检测阀门台账中编码重复或一物多码情况，重复编码会造成工单派发对象错乱。',
        suggestion: '合并 3 组重复阀门记录，保留资产编号最早的一条并建立映射关系。',
        rule_code: 'QR-UNIQ-002',
        rule_name: '阀门编码唯一性校验',
        score: 99.0,
        threshold: 99,
        passed: true,
        sample_size: 312,
        error_count: 3
      },
      {
        rule_id: 'QR-CONS-003',
        name: '传感器量纲一致性校验',
        category: '一致性',
        severity: 'medium',
        violation_count: 27,
        description: '核查同类型传感器的计量单位是否统一，%LEL 与 ppm 混用会直接影响燃气报警阈值研判。',
        suggestion: '按 STD-SENSOR-003 统一转换为 %LEL，并在接入层增加单位校验拦截。',
        rule_code: 'QR-CONS-003',
        rule_name: '传感器量纲一致性校验',
        score: 90.6,
        threshold: 95,
        passed: false,
        sample_size: 286,
        error_count: 27
      },
      {
        rule_id: 'QR-ACCU-004',
        name: '工单时间逻辑校验',
        category: '准确性',
        severity: 'medium',
        violation_count: 18,
        description: '校验工单的创建、派发、完成、归档时间是否满足先后顺序，异常时间会污染处置时效统计。',
        suggestion: '对 18 条时间倒挂工单回溯原始操作日志，修正后重新计算时效指标。',
        rule_code: 'QR-ACCU-004',
        rule_name: '工单时间逻辑校验',
        score: 82.0,
        threshold: 90,
        passed: false,
        sample_size: 100,
        error_count: 18
      },
      {
        rule_id: 'QR-RELA-005',
        name: '站点归属关系校验',
        category: '关联性',
        severity: 'low',
        violation_count: 6,
        description: '检查站点与所属分区、上级管理机构的关联是否有效，孤立站点会影响空间缓冲分析结果。',
        suggestion: '补全 6 个站点的分区归属，并在主数据平台建立外键约束。',
        rule_code: 'QR-RELA-005',
        rule_name: '站点归属关系校验',
        score: 94.1,
        threshold: 92,
        passed: true,
        sample_size: 102,
        error_count: 6
      },
      {
        rule_id: 'QR-UNIQ-006',
        name: '设备台账重复记录检测',
        category: '唯一性',
        severity: 'high',
        violation_count: 9,
        description: '基于名称、型号、安装位置三要素相似度识别重复台账，重复记录会虚增资产统计口径。',
        suggestion: '人工确认后合并 9 条疑似重复设备记录，并同步更新资产折旧数据。',
        rule_code: 'QR-UNIQ-006',
        rule_name: '设备台账重复记录检测',
        score: 96.9,
        threshold: 98,
        passed: false,
        sample_size: 286,
        error_count: 9
      },
      {
        rule_id: 'QR-TIME-007',
        name: '主数据更新时效性校验',
        category: '时效性',
        severity: 'medium',
        violation_count: 34,
        description: '统计超过 72 小时未完成同步的主数据集，长时间滞后会削弱风险研判的实时性。',
        suggestion: '排查 2 个未同步数据源的接口状态，将同步周期由每日一次调整为每 6 小时一次。',
        rule_code: 'QR-TIME-007',
        rule_name: '主数据更新时效性校验',
        score: 87.3,
        threshold: 90,
        passed: false,
        sample_size: 268,
        error_count: 34
      },
      {
        rule_id: 'QR-NORM-008',
        name: '管径规格枚举值校验',
        category: '规范性',
        severity: 'low',
        violation_count: 15,
        description: '校验管道规格字段是否落在 DN100-DN1200 的标准枚举集合内，非标准写法影响统计分组。',
        suggestion: '批量替换 15 条非标准规格写法，并在录入表单增加下拉约束。',
        rule_code: 'QR-NORM-008',
        rule_name: '管径规格枚举值校验',
        score: 96.7,
        threshold: 95,
        passed: true,
        sample_size: 456,
        error_count: 15
      }
    ],
    trend_7d: [
      { date: '2026-08-26', score: 86.2 },
      { date: '2026-08-27', score: 87.1 },
      { date: '2026-08-28', score: 85.9 },
      { date: '2026-08-29', score: 87.6 },
      { date: '2026-08-30', score: 88.0 },
      { date: '2026-08-31', score: 88.3 },
      { date: '2026-09-01', score: 88.5 }
    ]
  },

  // ==================== 质检执行结果 ====================
  qualityCheckResult: {
    check_id: 'QC-20260901-0915',
    check_time: '2026-09-01 09:15:32',
    total_rules: 15,
    passed: 12,
    failed: 3,
    score: 88.5,
    level: '良好',
    details: [
      { rule_name: '管线坐标完整性校验', passed: true, violations: 12, message: '完整性得分 97.4，高于阈值 95，判定通过。' },
      { rule_name: '阀门编码唯一性校验', passed: true, violations: 3, message: '唯一性得分 99.0，达到阈值 99，判定通过。' },
      { rule_name: '传感器量纲一致性校验', passed: false, violations: 27, message: '存在 27 条 %LEL 与 ppm 混用记录，一致性得分 90.6 低于阈值 95。' },
      { rule_name: '工单时间逻辑校验', passed: false, violations: 18, message: '18 条工单出现完成时间早于派发时间，准确性得分 82.0 低于阈值 90。' },
      { rule_name: '站点归属关系校验', passed: true, violations: 6, message: '关联性得分 94.1，高于阈值 92，判定通过。' },
      { rule_name: '设备台账重复记录检测', passed: true, violations: 9, message: '重复率 3.1%，唯一性得分 96.8，处于可接受区间。' },
      { rule_name: '主数据更新时效性校验', passed: false, violations: 34, message: '34 个数据集超过 72 小时未同步，时效性得分 87.3 低于阈值 90。' },
      { rule_name: '管径规格枚举值校验', passed: true, violations: 15, message: '规范性得分 96.7，高于阈值 95，判定通过。' },
      { rule_name: '管道材质代码校验', passed: true, violations: 4, message: '材质代码匹配率 99.1%，判定通过。' },
      { rule_name: '阀门驱动方式枚举校验', passed: true, violations: 2, message: '枚举值合法率 99.4%，判定通过。' },
      { rule_name: '传感器采样频率校验', passed: true, violations: 7, message: '采样频率落在 1-60s 区间内，判定通过。' },
      { rule_name: '站点高程基准校验', passed: true, violations: 5, message: 'CGCS2000 与 1985 高程基准覆盖率 95.1%，判定通过。' },
      { rule_name: '工单处置人有效性校验', passed: true, violations: 3, message: '处置人员与人员主数据匹配率 97.0%，判定通过。' },
      { rule_name: '权属单位字段校验', passed: true, violations: 8, message: '权属单位标准化率 98.2%，判定通过。' },
      { rule_name: '最近巡检日期有效性校验', passed: true, violations: 6, message: '巡检日期均不晚于当前日期，判定通过。' }
    ]
  },

  // ==================== 统一 API 服务 ====================
  apiServices: {
    services: [
      {
        service_id: 'SVC-WO-001',
        name: '工单列表查询服务',
        domain: 'workorder',
        method: 'GET',
        path: '/governance/api/workorder/list',
        status: 'active',
        avg_response_ms: 96,
        calls_24h: 3660,
        error_rate: 0.32,
        // 视图兼容字段
        api_id: 'SVC-WO-001',
        endpoint: '/governance/api/workorder/list',
        qps_limit: 200,
        auth_required: true,
        call_count_24h: 3660
      },
      {
        service_id: 'SVC-WO-002',
        name: '工单派发服务',
        domain: 'workorder',
        method: 'POST',
        path: '/governance/api/workorder/dispatch',
        status: 'active',
        avg_response_ms: 142,
        calls_24h: 860,
        error_rate: 0.75,
        api_id: 'SVC-WO-002',
        endpoint: '/governance/api/workorder/dispatch',
        qps_limit: 80,
        auth_required: true,
        call_count_24h: 860
      },
      {
        service_id: 'SVC-AS-003',
        name: '资产台账查询服务',
        domain: 'asset',
        method: 'GET',
        path: '/governance/api/asset/ledger',
        status: 'active',
        avg_response_ms: 118,
        calls_24h: 3210,
        error_rate: 0.21,
        api_id: 'SVC-AS-003',
        endpoint: '/governance/api/asset/ledger',
        qps_limit: 150,
        auth_required: true,
        call_count_24h: 3210
      },
      {
        service_id: 'SVC-AS-004',
        name: '资产变更记录服务',
        domain: 'asset',
        method: 'POST',
        path: '/governance/api/asset/change-log',
        status: 'active',
        avg_response_ms: 165,
        calls_24h: 540,
        error_rate: 0.48,
        api_id: 'SVC-AS-004',
        endpoint: '/governance/api/asset/change-log',
        qps_limit: 60,
        auth_required: true,
        call_count_24h: 540
      },
      {
        service_id: 'SVC-AL-005',
        name: '告警实时推送服务',
        domain: 'alarm',
        method: 'GET',
        path: '/governance/api/alarm/realtime',
        status: 'active',
        avg_response_ms: 78,
        calls_24h: 2680,
        error_rate: 0.15,
        api_id: 'SVC-AL-005',
        endpoint: '/governance/api/alarm/realtime',
        qps_limit: 300,
        auth_required: true,
        call_count_24h: 2680
      },
      {
        service_id: 'SVC-AL-006',
        name: '告警规则配置服务',
        domain: 'alarm',
        method: 'PUT',
        path: '/governance/api/alarm/rules',
        status: 'active',
        avg_response_ms: 205,
        calls_24h: 120,
        error_rate: 1.24,
        api_id: 'SVC-AL-006',
        endpoint: '/governance/api/alarm/rules',
        qps_limit: 30,
        auth_required: true,
        call_count_24h: 120
      },
      {
        service_id: 'SVC-TN-007',
        name: '管廊拓扑查询服务',
        domain: 'tunnel',
        method: 'GET',
        path: '/governance/api/tunnel/topology',
        status: 'active',
        avg_response_ms: 186,
        calls_24h: 1420,
        error_rate: 0.62,
        api_id: 'SVC-TN-007',
        endpoint: '/governance/api/tunnel/topology',
        qps_limit: 100,
        auth_required: true,
        call_count_24h: 1420
      },
      {
        service_id: 'SVC-TN-008',
        name: '管廊环境监测服务',
        domain: 'tunnel',
        method: 'GET',
        path: '/governance/api/tunnel/environment',
        status: 'active',
        avg_response_ms: 132,
        calls_24h: 1180,
        error_rate: 0.38,
        api_id: 'SVC-TN-008',
        endpoint: '/governance/api/tunnel/environment',
        qps_limit: 120,
        auth_required: false,
        call_count_24h: 1180
      },
      {
        service_id: 'SVC-SN-009',
        name: '传感器数据接入服务',
        domain: 'sensor',
        method: 'POST',
        path: '/governance/api/sensor/ingest',
        status: 'active',
        avg_response_ms: 88,
        calls_24h: 2010,
        error_rate: 0.27,
        api_id: 'SVC-SN-009',
        endpoint: '/governance/api/sensor/ingest',
        qps_limit: 500,
        auth_required: true,
        call_count_24h: 2010
      },
      {
        service_id: 'SVC-MD-010',
        name: '主数据同步任务服务',
        domain: 'master',
        method: 'POST',
        path: '/governance/api/master/sync',
        status: 'inactive',
        avg_response_ms: 0,
        calls_24h: 0,
        error_rate: 0,
        api_id: 'SVC-MD-010',
        endpoint: '/governance/api/master/sync',
        qps_limit: 50,
        auth_required: true,
        call_count_24h: 0
      }
    ],
    total: 10
  },

  // ==================== API 调用统计 ====================
  apiStats: {
    total_apis: 42,
    total_calls_24h: 15680,
    avg_response_ms: 126,
    domain_stats: [
      { domain: '工单管理', calls: 4520, avg_ms: 98 },
      { domain: '资产管理', calls: 3750, avg_ms: 132 },
      { domain: '告警预警', calls: 2800, avg_ms: 86 },
      { domain: '管廊运维', calls: 2600, avg_ms: 158 },
      { domain: '感知接入', calls: 2010, avg_ms: 92 }
    ],
    top_apis: [
      { name: '工单列表查询服务', path: '/governance/api/workorder/list', calls: 3660, avg_ms: 96 },
      { name: '资产台账查询服务', path: '/governance/api/asset/ledger', calls: 3210, avg_ms: 118 },
      { name: '告警实时推送服务', path: '/governance/api/alarm/realtime', calls: 2680, avg_ms: 78 },
      { name: '传感器数据接入服务', path: '/governance/api/sensor/ingest', calls: 2010, avg_ms: 88 },
      { name: '管廊拓扑查询服务', path: '/governance/api/tunnel/topology', calls: 1420, avg_ms: 186 },
      { name: '管廊环境监测服务', path: '/governance/api/tunnel/environment', calls: 1180, avg_ms: 132 }
    ]
  }
}

export default riskAnalysisMock
