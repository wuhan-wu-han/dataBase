/**
 * 综合管廊监控系统 Mock 数据
 * 包含总览、舱室、环境实时监测、告警、管线、安防出入与入侵等模块
 */
export default {
  // 系统总览
  overview: {
    total_cabins: 12,
    total_sensors: 486,
    alarm_count: 5,
    today_alarm_count: 2,
    pipeline_count: 38,
    access_today: 47,
    intrusion_count: 0,
    env_score: 92.5,
    online_rate: 98.6,
    alarms_today: 2,
    in_tunnel_count: 14
  },

  // 舱室列表
  cabins: [
    {
      cabin_id: 'CAB-Z01-001',
      name: '电力舱A段',
      type: 'EL',
      zone: 'Z01',
      length_m: 320,
      sensor_count: 64,
      status: '正常',
      temperature: 28.6,
      humidity: 58.2,
      latest_alarm_at: null
    },
    {
      cabin_id: 'CAB-Z01-002',
      name: '电力舱B段',
      type: 'EL',
      zone: 'Z01',
      length_m: 305,
      sensor_count: 60,
      status: '预警',
      temperature: 36.8,
      humidity: 61.5,
      latest_alarm_at: '2026-09-01 10:22:35'
    },
    {
      cabin_id: 'CAB-Z02-001',
      name: '燃气舱A段',
      type: 'GS',
      zone: 'Z02',
      length_m: 280,
      sensor_count: 58,
      status: '告警',
      temperature: 24.3,
      humidity: 45.7,
      latest_alarm_at: '2026-09-01 14:05:12'
    },
    {
      cabin_id: 'CAB-Z02-002',
      name: '燃气舱B段',
      type: 'GS',
      zone: 'Z02',
      length_m: 295,
      sensor_count: 56,
      status: '正常',
      temperature: 23.8,
      humidity: 44.2,
      latest_alarm_at: null
    },
    {
      cabin_id: 'CAB-Z03-001',
      name: '水信舱A段',
      type: 'WS',
      zone: 'Z03',
      length_m: 340,
      sensor_count: 68,
      status: '正常',
      temperature: 21.5,
      humidity: 72.3,
      latest_alarm_at: null
    },
    {
      cabin_id: 'CAB-Z03-002',
      name: '水信舱B段',
      type: 'WS',
      zone: 'Z03',
      length_m: 335,
      sensor_count: 66,
      status: '预警',
      temperature: 22.1,
      humidity: 78.9,
      latest_alarm_at: '2026-08-31 22:47:08'
    },
    {
      cabin_id: 'CAB-Z04-001',
      name: '电力舱C段',
      type: 'EL',
      zone: 'Z04',
      length_m: 310,
      sensor_count: 58,
      status: '正常',
      temperature: 27.9,
      humidity: 55.6,
      latest_alarm_at: null
    },
    {
      cabin_id: 'CAB-Z04-002',
      name: '水信舱C段',
      type: 'WS',
      zone: 'Z04',
      length_m: 325,
      sensor_count: 56,
      status: '正常',
      temperature: 21.8,
      humidity: 70.4,
      latest_alarm_at: null
    }
  ],

  // 环境实时监测
  envRealtime: {
    total: 486,
    sensors: [
      {
        sensor_id: 'SEN-T-1001',
        cabin_id: 'CAB-Z01-001',
        cabin_name: '电力舱A段',
        type: 'temperature',
        metric_name: '温度',
        value: 28.6,
        unit: '°C',
        status: 'normal',
        updated_at: '2026-09-01 14:28:00'
      },
      {
        sensor_id: 'SEN-H-1002',
        cabin_id: 'CAB-Z01-001',
        cabin_name: '电力舱A段',
        type: 'humidity',
        metric_name: '湿度',
        value: 58.2,
        unit: '%RH',
        status: 'normal',
        updated_at: '2026-09-01 14:28:00'
      },
      {
        sensor_id: 'SEN-T-1003',
        cabin_id: 'CAB-Z01-002',
        cabin_name: '电力舱B段',
        type: 'temperature',
        metric_name: '温度',
        value: 36.8,
        unit: '°C',
        status: 'warning',
        updated_at: '2026-09-01 14:28:05'
      },
      {
        sensor_id: 'SEN-H-1004',
        cabin_id: 'CAB-Z01-002',
        cabin_name: '电力舱B段',
        type: 'humidity',
        metric_name: '湿度',
        value: 61.5,
        unit: '%RH',
        status: 'normal',
        updated_at: '2026-09-01 14:28:05'
      },
      {
        sensor_id: 'SEN-G-2001',
        cabin_id: 'CAB-Z02-001',
        cabin_name: '燃气舱A段',
        type: 'gas',
        metric_name: '甲烷浓度',
        value: 1.85,
        unit: '%LEL',
        status: 'alarm',
        updated_at: '2026-09-01 14:05:12'
      },
      {
        sensor_id: 'SEN-G-2002',
        cabin_id: 'CAB-Z02-001',
        cabin_name: '燃气舱A段',
        type: 'oxygen',
        metric_name: '氧气浓度',
        value: 20.6,
        unit: '%VOL',
        status: 'normal',
        updated_at: '2026-09-01 14:27:50'
      },
      {
        sensor_id: 'SEN-G-2003',
        cabin_id: 'CAB-Z02-002',
        cabin_name: '燃气舱B段',
        type: 'gas',
        metric_name: '甲烷浓度',
        value: 0.12,
        unit: '%LEL',
        status: 'normal',
        updated_at: '2026-09-01 14:27:55'
      },
      {
        sensor_id: 'SEN-W-3001',
        cabin_id: 'CAB-Z03-001',
        cabin_name: '水信舱A段',
        type: 'water_level',
        metric_name: '集水坑水位',
        value: 0.32,
        unit: 'm',
        status: 'normal',
        updated_at: '2026-09-01 14:26:30'
      },
      {
        sensor_id: 'SEN-W-3002',
        cabin_id: 'CAB-Z03-002',
        cabin_name: '水信舱B段',
        type: 'water_level',
        metric_name: '集水坑水位',
        value: 0.78,
        unit: 'm',
        status: 'warning',
        updated_at: '2026-09-01 14:26:35'
      },
      {
        sensor_id: 'SEN-H-3003',
        cabin_id: 'CAB-Z03-002',
        cabin_name: '水信舱B段',
        type: 'humidity',
        metric_name: '湿度',
        value: 78.9,
        unit: '%RH',
        status: 'normal',
        updated_at: '2026-09-01 14:26:35'
      },
      {
        sensor_id: 'SEN-S-1005',
        cabin_id: 'CAB-Z01-001',
        cabin_name: '电力舱A段',
        type: 'smoke',
        metric_name: '烟雾浓度',
        value: 0.02,
        unit: 'dB/m',
        status: 'normal',
        updated_at: '2026-09-01 14:28:10'
      },
      {
        sensor_id: 'SEN-S-1006',
        cabin_id: 'CAB-Z01-002',
        cabin_name: '电力舱B段',
        type: 'smoke',
        metric_name: '烟雾浓度',
        value: 0.05,
        unit: 'dB/m',
        status: 'normal',
        updated_at: '2026-09-01 14:28:15'
      },
      {
        sensor_id: 'SEN-O-4001',
        cabin_id: 'CAB-Z04-001',
        cabin_name: '电力舱C段',
        type: 'oxygen',
        metric_name: '氧气浓度',
        value: 20.9,
        unit: '%VOL',
        status: 'normal',
        updated_at: '2026-09-01 14:25:40'
      },
      {
        sensor_id: 'SEN-T-4002',
        cabin_id: 'CAB-Z04-001',
        cabin_name: '电力舱C段',
        type: 'temperature',
        metric_name: '温度',
        value: 27.9,
        unit: '°C',
        status: 'normal',
        updated_at: '2026-09-01 14:25:40'
      },
      {
        sensor_id: 'SEN-T-4003',
        cabin_id: 'CAB-Z04-002',
        cabin_name: '水信舱C段',
        type: 'temperature',
        metric_name: '温度',
        value: 21.8,
        unit: '°C',
        status: 'normal',
        updated_at: '2026-09-01 14:25:50'
      },
      {
        sensor_id: 'SEN-W-4004',
        cabin_id: 'CAB-Z04-002',
        cabin_name: '水信舱C段',
        type: 'water_level',
        metric_name: '集水坑水位',
        value: 0.45,
        unit: 'm',
        status: 'normal',
        updated_at: '2026-09-01 14:25:50'
      },
      {
        sensor_id: 'SEN-S-2004',
        cabin_id: 'CAB-Z02-001',
        cabin_name: '燃气舱A段',
        type: 'smoke',
        metric_name: '烟雾浓度',
        value: 0.03,
        unit: 'dB/m',
        status: 'normal',
        updated_at: '2026-09-01 14:27:50'
      }
    ]
  },

  // 告警列表
  alarms: {
    total: 28,
    alarms: [
      {
        alarm_id: 'ALM-20260901-001',
        cabin_id: 'CAB-Z02-001',
        cabin_name: '燃气舱A段',
        sensor_id: 'SEN-G-2001',
        type: 'gas',
        level: 'critical',
        message: '甲烷浓度超限报警：当前 1.85 %LEL，超过报警阈值 1.00 %LEL，疑似燃气泄漏，请立即处置！',
        value: 1.85,
        threshold: 1.0,
        status: 'active',
        created_at: '2026-09-01 14:05:12',
        acked_at: null,
        acked_by: null
      },
      {
        alarm_id: 'ALM-20260901-002',
        cabin_id: 'CAB-Z01-002',
        cabin_name: '电力舱B段',
        sensor_id: 'SEN-T-1003',
        type: 'temperature',
        level: 'warning',
        message: '舱内温度偏高：当前 36.8°C，超过预警阈值 35°C，建议检查通风系统运行状态',
        value: 36.8,
        threshold: 35,
        status: 'acked',
        created_at: '2026-09-01 10:22:35',
        acked_at: '2026-09-01 10:35:20',
        acked_by: '值班员王强'
      },
      {
        alarm_id: 'ALM-20260831-003',
        cabin_id: 'CAB-Z03-002',
        cabin_name: '水信舱B段',
        sensor_id: 'SEN-W-3002',
        type: 'water_level',
        level: 'warning',
        message: '集水坑水位偏高：当前 0.78m，超过预警阈值 0.70m，排水泵已自动启动',
        value: 0.78,
        threshold: 0.7,
        status: 'resolved',
        created_at: '2026-08-31 22:47:08',
        acked_at: '2026-08-31 23:02:41',
        acked_by: '值班员李梅'
      },
      {
        alarm_id: 'ALM-20260831-004',
        cabin_id: 'CAB-Z01-002',
        cabin_name: '电力舱B段',
        sensor_id: 'SEN-S-1006',
        type: 'smoke',
        level: 'info',
        message: '烟雾浓度轻微波动：当前 0.05 dB/m，接近预警值 0.08 dB/m，建议关注',
        value: 0.05,
        threshold: 0.08,
        status: 'resolved',
        created_at: '2026-08-31 16:12:50',
        acked_at: '2026-08-31 16:30:15',
        acked_by: '值班员赵刚'
      },
      {
        alarm_id: 'ALM-20260830-005',
        cabin_id: 'CAB-Z02-002',
        cabin_name: '燃气舱B段',
        sensor_id: 'SEN-O-2005',
        type: 'oxygen',
        level: 'warning',
        message: '氧气浓度偏低：当前 19.2 %VOL，低于预警阈值 19.5 %VOL，通风系统已加强运行',
        value: 19.2,
        threshold: 19.5,
        status: 'resolved',
        created_at: '2026-08-30 09:18:22',
        acked_at: '2026-08-30 09:25:03',
        acked_by: '值班员王强'
      },
      {
        alarm_id: 'ALM-20260829-006',
        cabin_id: 'CAB-Z04-001',
        cabin_name: '电力舱C段',
        sensor_id: 'SEN-T-4002',
        type: 'temperature',
        level: 'warning',
        message: '电缆接头表面温度异常：当前 72.5°C，超过预警阈值 70°C，已安排红外测温复核',
        value: 72.5,
        threshold: 70,
        status: 'resolved',
        created_at: '2026-08-29 15:42:10',
        acked_at: '2026-08-29 15:55:33',
        acked_by: '值班员陈晨'
      },
      {
        alarm_id: 'ALM-20260829-007',
        cabin_id: 'CAB-Z03-001',
        cabin_name: '水信舱A段',
        sensor_id: 'SEN-H-3001',
        type: 'humidity',
        level: 'info',
        message: '舱内湿度持续偏高：当前 82.4 %RH，超过预警值 80 %RH，除湿设备运行中',
        value: 82.4,
        threshold: 80,
        status: 'resolved',
        created_at: '2026-08-29 08:05:47',
        acked_at: '2026-08-29 08:20:11',
        acked_by: '值班员李梅'
      },
      {
        alarm_id: 'ALM-20260828-008',
        cabin_id: 'CAB-Z01-001',
        cabin_name: '电力舱A段',
        sensor_id: 'SEN-S-1005',
        type: 'smoke',
        level: 'critical',
        message: '感烟探测器报警：烟雾浓度 0.15 dB/m，超过报警阈值 0.10 dB/m，现场确认为转载车辆尾气倒灌，误报',
        value: 0.15,
        threshold: 0.1,
        status: 'resolved',
        created_at: '2026-08-28 19:33:05',
        acked_at: '2026-08-28 19:36:48',
        acked_by: '值班员赵刚'
      },
      {
        alarm_id: 'ALM-20260828-009',
        cabin_id: 'CAB-Z02-001',
        cabin_name: '燃气舱A段',
        sensor_id: 'SEN-G-2001',
        type: 'gas',
        level: 'warning',
        message: '甲烷浓度轻微波动：当前 0.45 %LEL，超过预警值 0.25 %LEL，已加密监测频率',
        value: 0.45,
        threshold: 0.25,
        status: 'resolved',
        created_at: '2026-08-28 11:20:36',
        acked_at: '2026-08-28 11:28:02',
        acked_by: '值班员王强'
      },
      {
        alarm_id: 'ALM-20260827-010',
        cabin_id: 'CAB-Z04-002',
        cabin_name: '水信舱C段',
        sensor_id: 'SEN-W-4004',
        type: 'water_level',
        level: 'warning',
        message: '给水管线压力异常波动：疑似爆管前兆，当前水位 0.68m，超过预警阈值 0.60m',
        value: 0.68,
        threshold: 0.6,
        status: 'resolved',
        created_at: '2026-08-27 03:15:29',
        acked_at: '2026-08-27 07:40:55',
        acked_by: '值班员陈晨'
      },
      {
        alarm_id: 'ALM-20260826-011',
        cabin_id: 'CAB-Z01-002',
        cabin_name: '电力舱B段',
        sensor_id: 'SEN-T-1003',
        type: 'temperature',
        level: 'info',
        message: '夏季午后舱内温度自然升高至 33.2°C，未超阈值，系统提示关注趋势',
        value: 33.2,
        threshold: 35,
        status: 'resolved',
        created_at: '2026-08-26 14:50:18',
        acked_at: '2026-08-26 15:10:42',
        acked_by: '值班员李梅'
      },
      {
        alarm_id: 'ALM-20260825-012',
        cabin_id: 'CAB-Z02-002',
        cabin_name: '燃气舱B段',
        sensor_id: 'SEN-G-2003',
        type: 'gas',
        level: 'critical',
        message: '燃气浓度快速上升报警：15分钟内由 0.10 %LEL 升至 1.20 %LEL，紧急切断阀已联动关闭',
        value: 1.2,
        threshold: 1.0,
        status: 'resolved',
        created_at: '2026-08-25 21:08:56',
        acked_at: '2026-08-25 21:10:30',
        acked_by: '值班员赵刚'
      }
    ]
  },

  // 告警确认响应
  ackAlarm: {
    alarm_id: 'ALM-20260901-001',
    acked: true,
    acked_at: '2026-09-01 14:30:00',
    acked_by: '值班员王强'
  },

  // 管线台账
  pipelines: {
    total: 38,
    pipelines: [
      {
        pipeline_id: 'PL-EL-001',
        name: '110kV高压电缆一号线',
        cabin_id: 'CAB-Z01-001',
        type: '电力电缆',
        specs: 'YJLW03-64/110kV-1×630mm²',
        owner_unit: '市供电局输电运检中心',
        install_date: '2023-05-18',
        status: '在运',
        length_m: 320,
        last_inspect_date: '2026-08-15'
      },
      {
        pipeline_id: 'PL-EL-002',
        name: '110kV高压电缆二号线',
        cabin_id: 'CAB-Z01-001',
        type: '电力电缆',
        specs: 'YJLW03-64/110kV-1×630mm²',
        owner_unit: '市供电局输电运检中心',
        install_date: '2023-05-18',
        status: '在运',
        length_m: 320,
        last_inspect_date: '2026-08-15'
      },
      {
        pipeline_id: 'PL-EL-003',
        name: '10kV中压配电电缆干线',
        cabin_id: 'CAB-Z01-002',
        type: '电力电缆',
        specs: 'YJV22-8.7/15kV-3×400mm²',
        owner_unit: '市供电局配电运维班',
        install_date: '2023-08-02',
        status: '在运',
        length_m: 305,
        last_inspect_date: '2026-08-20'
      },
      {
        pipeline_id: 'PL-EL-004',
        name: '10kV中压配电电缆备用线',
        cabin_id: 'CAB-Z04-001',
        type: '电力电缆',
        specs: 'YJV22-8.7/15kV-3×300mm²',
        owner_unit: '市供电局配电运维班',
        install_date: '2024-03-11',
        status: '检修',
        length_m: 310,
        last_inspect_date: '2026-08-28'
      },
      {
        pipeline_id: 'PL-CM-001',
        name: '骨干通信光缆A线',
        cabin_id: 'CAB-Z03-001',
        type: '通信光缆',
        specs: 'GYTA-144B1 单模144芯',
        owner_unit: '市电信分公司网络运维部',
        install_date: '2023-06-25',
        status: '在运',
        length_m: 340,
        last_inspect_date: '2026-08-10'
      },
      {
        pipeline_id: 'PL-CM-002',
        name: '骨干通信光缆B线',
        cabin_id: 'CAB-Z03-002',
        type: '通信光缆',
        specs: 'GYTA-96B1 单模96芯',
        owner_unit: '市移动分公司传输中心',
        install_date: '2023-09-14',
        status: '在运',
        length_m: 335,
        last_inspect_date: '2026-08-12'
      },
      {
        pipeline_id: 'PL-CM-003',
        name: '政务专网光缆',
        cabin_id: 'CAB-Z04-002',
        type: '通信光缆',
        specs: 'GYTA-48B1 单模48芯',
        owner_unit: '市大数据管理局',
        install_date: '2024-01-20',
        status: '在运',
        length_m: 325,
        last_inspect_date: '2026-07-30'
      },
      {
        pipeline_id: 'PL-WS-001',
        name: 'DN800市政给水主管',
        cabin_id: 'CAB-Z03-001',
        type: '给水管道',
        specs: 'DN800 球墨铸铁管 K9级',
        owner_unit: '市水务集团供水公司',
        install_date: '2023-04-08',
        status: '在运',
        length_m: 340,
        last_inspect_date: '2026-08-18'
      },
      {
        pipeline_id: 'PL-WS-002',
        name: 'DN500配水支管',
        cabin_id: 'CAB-Z03-002',
        type: '给水管道',
        specs: 'DN500 球墨铸铁管 K9级',
        owner_unit: '市水务集团供水公司',
        install_date: '2023-07-16',
        status: '在运',
        length_m: 335,
        last_inspect_date: '2026-08-18'
      },
      {
        pipeline_id: 'PL-WS-003',
        name: 'DN400再生水管',
        cabin_id: 'CAB-Z04-002',
        type: '给水管道',
        specs: 'DN400 PE100 聚乙烯管',
        owner_unit: '市水务集团排水公司',
        install_date: '2024-05-09',
        status: '停运',
        length_m: 325,
        last_inspect_date: '2026-06-22'
      },
      {
        pipeline_id: 'PL-GS-001',
        name: '次高压燃气管线A线',
        cabin_id: 'CAB-Z02-001',
        type: '燃气管道',
        specs: 'DN500 1.6MPa 无缝钢管 3PE防腐',
        owner_unit: '市燃气集团管网运行部',
        install_date: '2023-10-12',
        status: '在运',
        length_m: 280,
        last_inspect_date: '2026-09-01'
      },
      {
        pipeline_id: 'PL-GS-002',
        name: '中压燃气管线B线',
        cabin_id: 'CAB-Z02-002',
        type: '燃气管道',
        specs: 'DN400 0.4MPa 无缝钢管 3PE防腐',
        owner_unit: '市燃气集团管网运行部',
        install_date: '2023-11-03',
        status: '检修',
        length_m: 295,
        last_inspect_date: '2026-08-30'
      },
      {
        pipeline_id: 'PL-HT-001',
        name: '集中供热供水管',
        cabin_id: 'CAB-Z04-001',
        type: '热力管道',
        specs: 'DN600 预制直埋保温管 1.6MPa',
        owner_unit: '市热力总公司输配中心',
        install_date: '2024-04-17',
        status: '在运',
        length_m: 310,
        last_inspect_date: '2026-08-05'
      },
      {
        pipeline_id: 'PL-HT-002',
        name: '集中供热回水管',
        cabin_id: 'CAB-Z04-001',
        type: '热力管道',
        specs: 'DN600 预制直埋保温管 1.6MPa',
        owner_unit: '市热力总公司输配中心',
        install_date: '2024-04-17',
        status: '在运',
        length_m: 310,
        last_inspect_date: '2026-08-05'
      }
    ]
  },

  // 安防总览
  securityOverview: {
    total_access_today: 47,
    authorized: 44,
    unauthorized: 0,
    intrusion_count: 0,
    camera_online: 24,
    camera_total: 26
  },

  // 出入记录
  accessRecords: {
    total: 156,
    records: [
      {
        record_id: 'ACC-20260901-001',
        person_name: '王建国',
        company: '市供电局输电运检中心',
        cabin_id: 'CAB-Z01-001',
        purpose: '巡检',
        enter_time: '2026-09-01 08:30:15',
        exit_time: '2026-09-01 09:45:30',
        status: '已出',
        authorized: true,
        photo_url: '/mock/photos/access/acc-001.jpg'
      },
      {
        record_id: 'ACC-20260901-002',
        person_name: '刘志远',
        company: '市燃气集团管网运行部',
        cabin_id: 'CAB-Z02-001',
        purpose: '维修',
        enter_time: '2026-09-01 14:12:05',
        exit_time: null,
        status: '在内部',
        authorized: true,
        photo_url: '/mock/photos/access/acc-002.jpg'
      },
      {
        record_id: 'ACC-20260901-003',
        person_name: '张海峰',
        company: '市燃气集团管网运行部',
        cabin_id: 'CAB-Z02-001',
        purpose: '维修',
        enter_time: '2026-09-01 14:12:38',
        exit_time: null,
        status: '在内部',
        authorized: true,
        photo_url: '/mock/photos/access/acc-003.jpg'
      },
      {
        record_id: 'ACC-20260901-004',
        person_name: '李梅',
        company: '管廊运营公司监控中心',
        cabin_id: 'CAB-Z03-002',
        purpose: '巡检',
        enter_time: '2026-09-01 10:05:22',
        exit_time: '2026-09-01 10:52:41',
        status: '已出',
        authorized: true,
        photo_url: '/mock/photos/access/acc-004.jpg'
      },
      {
        record_id: 'ACC-20260901-005',
        person_name: '陈立',
        company: '中铁十四局管廊项目部',
        cabin_id: 'CAB-Z04-001',
        purpose: '施工',
        enter_time: '2026-09-01 07:55:10',
        exit_time: '2026-09-01 11:30:08',
        status: '已出',
        authorized: true,
        photo_url: '/mock/photos/access/acc-005.jpg'
      },
      {
        record_id: 'ACC-20260901-006',
        person_name: '赵国庆',
        company: '市住房和城乡建设局',
        cabin_id: 'CAB-Z01-002',
        purpose: '参观',
        enter_time: '2026-09-01 09:20:45',
        exit_time: '2026-09-01 10:10:33',
        status: '已出',
        authorized: true,
        photo_url: '/mock/photos/access/acc-006.jpg'
      },
      {
        record_id: 'ACC-20260901-007',
        person_name: '孙晓明',
        company: '市电信分公司网络运维部',
        cabin_id: 'CAB-Z03-001',
        purpose: '维修',
        enter_time: '2026-09-01 13:40:18',
        exit_time: null,
        status: '已入',
        authorized: true,
        photo_url: '/mock/photos/access/acc-007.jpg'
      },
      {
        record_id: 'ACC-20260831-008',
        person_name: '周文博',
        company: '管廊运营公司维保班组',
        cabin_id: 'CAB-Z01-002',
        purpose: '维修',
        enter_time: '2026-08-31 15:22:36',
        exit_time: '2026-08-31 17:05:12',
        status: '已出',
        authorized: true,
        photo_url: '/mock/photos/access/acc-008.jpg'
      },
      {
        record_id: 'ACC-20260831-009',
        person_name: '吴桂芳',
        company: '市水务集团供水公司',
        cabin_id: 'CAB-Z03-001',
        purpose: '巡检',
        enter_time: '2026-08-31 09:12:47',
        exit_time: '2026-08-31 09:58:20',
        status: '已出',
        authorized: true,
        photo_url: '/mock/photos/access/acc-009.jpg'
      },
      {
        record_id: 'ACC-20260831-010',
        person_name: '郑凯',
        company: '第三方安全评估机构（安泰检测）',
        cabin_id: 'CAB-Z02-002',
        purpose: '巡检',
        enter_time: '2026-08-31 14:05:55',
        exit_time: '2026-08-31 16:22:30',
        status: '已出',
        authorized: true,
        photo_url: '/mock/photos/access/acc-010.jpg'
      },
      {
        record_id: 'ACC-20260830-011',
        person_name: '冯建军',
        company: '市热力总公司输配中心',
        cabin_id: 'CAB-Z04-001',
        purpose: '施工',
        enter_time: '2026-08-30 08:02:14',
        exit_time: '2026-08-30 12:40:56',
        status: '已出',
        authorized: true,
        photo_url: '/mock/photos/access/acc-011.jpg'
      },
      {
        record_id: 'ACC-20260830-012',
        person_name: '未知人员',
        company: '未登记',
        cabin_id: 'CAB-Z04-002',
        purpose: '巡检',
        enter_time: '2026-08-30 23:47:09',
        exit_time: '2026-08-30 23:52:41',
        status: '已出',
        authorized: false,
        photo_url: '/mock/photos/access/acc-012.jpg'
      }
    ]
  },

  // 入侵事件
  intrusions: {
    total: 3,
    intrusions: [
      {
        intrusion_id: 'INT-20260830-001',
        cabin_id: 'CAB-Z04-002',
        zone: 'Z04',
        detection_type: '红外',
        detected_at: '2026-08-30 23:46:52',
        level: 'critical',
        snapshot_url: '/mock/photos/intrusion/int-001-snapshot.jpg',
        status: '已处理',
        handler: '值班员赵刚'
      },
      {
        intrusion_id: 'INT-20260812-002',
        cabin_id: 'CAB-Z01-001',
        zone: 'Z01',
        detection_type: '视频分析',
        detected_at: '2026-08-12 02:18:37',
        level: 'warning',
        snapshot_url: '/mock/photos/intrusion/int-002-snapshot.jpg',
        status: '误报',
        handler: '值班员王强'
      },
      {
        intrusion_id: 'INT-20260703-003',
        cabin_id: 'CAB-Z02-002',
        zone: 'Z02',
        detection_type: '门磁',
        detected_at: '2026-07-03 21:05:14',
        level: 'warning',
        snapshot_url: '/mock/photos/intrusion/int-003-snapshot.jpg',
        status: '待确认',
        handler: null
      }
    ]
  }
}
