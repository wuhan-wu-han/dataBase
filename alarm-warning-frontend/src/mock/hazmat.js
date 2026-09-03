/**
 * 危化品监管 / 介质监测 模拟数据
 * 涵盖：介质监测、管道路由、运输溯源、管段腐蚀评估、危化品台账、阀门管理
 */

export default {
  // 1. 总览
  overview: {
    total_media: 156,
    abnormal_count: 3,
    compliance_rate: 97.8,
    media_count: 156,
    media_warning_count: 3,
    route_count: 42,
    trace_count: 1286,
    segment_count: 328,
    valve_count: 89,
    emergency_valve_alerts: 2
  },

  // 2. 介质监测列表
  media: {
    total: 12,
    media: [
      {
        media_id: 'MED-001',
        name: '甲烷传感器M-001',
        type: 'gas',
        location: '一号压缩机房',
        sensor_id: 'SEN-CH4-1001',
        unit: '%LEL',
        real_time_value: 12.5,
        threshold_min: 0,
        threshold_max: 25,
        status: 'normal',
        updated_at: '2026-03-15 09:32:10'
      },
      {
        media_id: 'MED-002',
        name: '硫化氢传感器M-002',
        type: 'gas',
        location: '脱硫装置区',
        sensor_id: 'SEN-H2S-1002',
        unit: 'ppm',
        real_time_value: 8.6,
        threshold_min: 0,
        threshold_max: 10,
        status: 'warning',
        updated_at: '2026-03-15 09:31:45'
      },
      {
        media_id: 'MED-003',
        name: '液氨储罐液位计M-003',
        type: 'liquid',
        location: '液氨储罐区T-201',
        sensor_id: 'SEN-LVL-1003',
        unit: 'm',
        real_time_value: 6.82,
        threshold_min: 1.5,
        threshold_max: 8.0,
        status: 'normal',
        updated_at: '2026-03-15 09:30:20'
      },
      {
        media_id: 'MED-004',
        name: '氯气检测仪M-004',
        type: 'gas',
        location: '液氯充装站',
        sensor_id: 'SEN-CL2-1004',
        unit: 'ppm',
        real_time_value: 2.3,
        threshold_min: 0,
        threshold_max: 1,
        status: 'alarm',
        updated_at: '2026-03-15 09:33:02'
      },
      {
        media_id: 'MED-005',
        name: '甲醇浓度监测M-005',
        type: 'chemical',
        location: '甲醇中间罐区',
        sensor_id: 'SEN-MEOH-1005',
        unit: 'mg/m³',
        real_time_value: 21.4,
        threshold_min: 0,
        threshold_max: 50,
        status: 'normal',
        updated_at: '2026-03-15 09:28:55'
      },
      {
        media_id: 'MED-006',
        name: '苯系物检测仪M-006',
        type: 'chemical',
        location: '芳烃装置二层平台',
        sensor_id: 'SEN-BTX-1006',
        unit: 'mg/m³',
        real_time_value: 5.8,
        threshold_min: 0,
        threshold_max: 6,
        status: 'warning',
        updated_at: '2026-03-15 09:32:40'
      },
      {
        media_id: 'MED-007',
        name: '液化石油气压力M-007',
        type: 'gas',
        location: 'LPG球罐区V-301',
        sensor_id: 'SEN-PRS-1007',
        unit: 'MPa',
        real_time_value: 1.62,
        threshold_min: 0.8,
        threshold_max: 2.2,
        status: 'normal',
        updated_at: '2026-03-15 09:31:10'
      },
      {
        media_id: 'MED-008',
        name: '硫酸储罐温度M-008',
        type: 'liquid',
        location: '酸库98%硫酸罐',
        sensor_id: 'SEN-TMP-1008',
        unit: '℃',
        real_time_value: 38.7,
        threshold_min: 5,
        threshold_max: 45,
        status: 'normal',
        updated_at: '2026-03-15 09:29:33'
      },
      {
        media_id: 'MED-009',
        name: '一氧化碳报警器M-009',
        type: 'gas',
        location: '煤气化车间北侧',
        sensor_id: 'SEN-CO-1009',
        unit: 'ppm',
        real_time_value: 26.1,
        threshold_min: 0,
        threshold_max: 24,
        status: 'alarm',
        updated_at: '2026-03-15 09:33:28'
      },
      {
        media_id: 'MED-010',
        name: '乙烯流量计M-010',
        type: 'gas',
        location: '乙烯输送管线首站',
        sensor_id: 'SEN-FLW-1010',
        unit: 't/h',
        real_time_value: 45.2,
        threshold_min: 10,
        threshold_max: 60,
        status: 'normal',
        updated_at: '2026-03-15 09:30:48'
      },
      {
        media_id: 'MED-011',
        name: '氢氧化钠浓度M-011',
        type: 'chemical',
        location: '碱液配制间',
        sensor_id: 'SEN-CON-1011',
        unit: '%',
        real_time_value: 31.5,
        threshold_min: 28,
        threshold_max: 33,
        status: 'normal',
        updated_at: '2026-03-15 09:27:15'
      },
      {
        media_id: 'MED-012',
        name: '丙烯腈检测仪M-012',
        type: 'chemical',
        location: '丙烯腈装置罐区',
        sensor_id: 'SEN-ACN-1012',
        unit: 'mg/m³',
        real_time_value: 1.2,
        threshold_min: 0,
        threshold_max: 2,
        status: 'normal',
        updated_at: '2026-03-15 09:32:01'
      }
    ]
  },

  // 3. 介质监测详情（含24小时趋势）
  mediaDetail: {
    media_id: 'MED-001',
    name: '甲烷传感器M-001',
    type: 'gas',
    location: '一号压缩机房',
    sensor_id: 'SEN-CH4-1001',
    unit: '%LEL',
    real_time_value: 12.5,
    threshold_min: 0,
    threshold_max: 25,
    status: 'normal',
    updated_at: '2026-03-15 09:32:10',
    calibration_date: '2026-01-20',
    next_calibration_date: '2026-07-20',
    manufacturer: '汉威科技集团',
    trend_24h: [
      { time: '00:00', value: 10.2 },
      { time: '01:00', value: 10.5 },
      { time: '02:00', value: 10.1 },
      { time: '03:00', value: 9.8 },
      { time: '04:00', value: 10.0 },
      { time: '05:00', value: 10.4 },
      { time: '06:00', value: 11.0 },
      { time: '07:00', value: 11.8 },
      { time: '08:00', value: 12.3 },
      { time: '09:00', value: 12.6 },
      { time: '10:00', value: 13.1 },
      { time: '11:00', value: 13.5 },
      { time: '12:00', value: 12.9 },
      { time: '13:00', value: 12.4 },
      { time: '14:00', value: 12.7 },
      { time: '15:00', value: 13.2 },
      { time: '16:00', value: 13.8 },
      { time: '17:00', value: 13.4 },
      { time: '18:00', value: 12.8 },
      { time: '19:00', value: 12.2 },
      { time: '20:00', value: 11.9 },
      { time: '21:00', value: 11.5 },
      { time: '22:00', value: 11.0 },
      { time: '23:00', value: 10.6 }
    ]
  },

  // 4. 管道路由列表
  routes: {
    total: 10,
    routes: [
      {
        route_id: 'RTE-001',
        name: '西气东输支线A段',
        start_point: '首站(库尔勒分输站)',
        end_point: '末站(鄯善计量站)',
        length_km: 186.5,
        medium_type: '天然气',
        pipe_material: 'L450M螺旋缝埋弧焊钢管',
        pressure_level: '10.0MPa',
        status: '合规',
        last_inspect_date: '2026-02-18',
        violation_count: 0
      },
      {
        route_id: 'RTE-002',
        name: '临港LPG输送管线',
        start_point: 'LPG码头接收站',
        end_point: '化工园区储罐区',
        length_km: 23.8,
        medium_type: '液化石油气',
        pipe_material: '20#无缝钢管',
        pressure_level: '4.0MPa',
        status: '合规',
        last_inspect_date: '2026-01-30',
        violation_count: 0
      },
      {
        route_id: 'RTE-003',
        name: '园区甲醇管廊干线',
        start_point: '甲醇装置区界外阀室',
        end_point: '下游MTO项目首站',
        length_km: 12.4,
        medium_type: '工业化学品',
        pipe_material: '304不锈钢管',
        pressure_level: '2.5MPa',
        status: '预警',
        last_inspect_date: '2026-02-05',
        violation_count: 1
      },
      {
        route_id: 'RTE-004',
        name: '氯碱公司液氯管线',
        start_point: '电解车间液氯工段',
        end_point: '环氧丙烷装置',
        length_km: 5.6,
        medium_type: '工业化学品',
        pipe_material: '衬氟无缝钢管',
        pressure_level: '1.6MPa',
        status: '违规',
        last_inspect_date: '2026-01-12',
        violation_count: 3
      },
      {
        route_id: 'RTE-005',
        name: '城燃高压环网北段',
        start_point: '北城门站',
        end_point: '开发区调压站',
        length_km: 38.2,
        medium_type: '天然气',
        pipe_material: 'PE100燃气管',
        pressure_level: '4.0MPa',
        status: '合规',
        last_inspect_date: '2026-03-01',
        violation_count: 0
      },
      {
        route_id: 'RTE-006',
        name: '丙烯输送专线',
        start_point: '催化裂化装置',
        end_point: '聚丙烯原料罐区',
        length_km: 8.9,
        medium_type: '工业化学品',
        pipe_material: 'L245直缝埋弧焊管',
        pressure_level: '6.3MPa',
        status: '合规',
        last_inspect_date: '2026-02-22',
        violation_count: 0
      },
      {
        route_id: 'RTE-007',
        name: '氨氢综合利用管线',
        start_point: '合成氨装置',
        end_point: '氢能充装站',
        length_km: 15.3,
        medium_type: '工业化学品',
        pipe_material: '16MnDR低温钢管',
        pressure_level: '8.0MPa',
        status: '预警',
        last_inspect_date: '2026-01-08',
        violation_count: 1
      },
      {
        route_id: 'RTE-008',
        name: '乙烯长输管线东段',
        start_point: '乙烯首站',
        end_point: '东区分输站',
        length_km: 64.7,
        medium_type: '工业化学品',
        pipe_material: 'L415M无缝钢管',
        pressure_level: '12.5MPa',
        status: '合规',
        last_inspect_date: '2026-03-05',
        violation_count: 0
      }
    ]
  },

  // 5. 管道路由详情（含分段信息）
  routeDetail: {
    route_id: 'RTE-001',
    name: '西气东输支线A段',
    start_point: '首站(库尔勒分输站)',
    end_point: '末站(鄯善计量站)',
    length_km: 186.5,
    medium_type: '天然气',
    pipe_material: 'L450M螺旋缝埋弧焊钢管',
    pressure_level: '10.0MPa',
    status: '合规',
    last_inspect_date: '2026-02-18',
    violation_count: 0,
    design_pressure: '12.0MPa',
    operating_pressure: '9.6MPa',
    buried_depth_m: 1.8,
    segments: [
      {
        segment_id: 'SEG-001-01',
        start_marker: 'K0+000',
        end_marker: 'K25+400',
        length_m: 25400,
        condition: '良好',
        last_check: '2026-02-18'
      },
      {
        segment_id: 'SEG-001-02',
        start_marker: 'K25+400',
        end_marker: 'K52+100',
        length_m: 26700,
        condition: '良好',
        last_check: '2026-02-19'
      },
      {
        segment_id: 'SEG-001-03',
        start_marker: 'K52+100',
        end_marker: 'K80+600',
        length_m: 28500,
        condition: '轻微腐蚀',
        last_check: '2026-02-20'
      },
      {
        segment_id: 'SEG-001-04',
        start_marker: 'K80+600',
        end_marker: 'K110+200',
        length_m: 29600,
        condition: '良好',
        last_check: '2026-02-21'
      },
      {
        segment_id: 'SEG-001-05',
        start_marker: 'K110+200',
        end_marker: 'K186+500',
        length_m: 76300,
        condition: '良好',
        last_check: '2026-02-23'
      }
    ]
  },

  // 6. 路由合规检查
  routeCheck: {
    route_id: 'RTE-001',
    compliant: true,
    violations: [],
    check_time: '2026-02-18 14:30:00',
    inspector: '王建国'
  },

  // 7. 运输溯源列表
  traces: {
    total: 15,
    traces: [
      {
        trace_id: 'TRC-20260301-001',
        manifest_no: 'YH-2026-0312-088',
        chemical_name: '液化石油气',
        quantity_tons: 25.6,
        from_location: '茂名石化炼油厂区',
        to_location: '广州南沙储配站',
        transport_mode: '槽车',
        status: '运输中',
        start_time: '2026-03-14 06:30:00',
        eta: '2026-03-15 12:00:00',
        carrier: '粤西危化物流有限公司'
      },
      {
        trace_id: 'TRC-20260301-002',
        manifest_no: 'YH-2026-0310-076',
        chemical_name: '液氯',
        quantity_tons: 18.2,
        from_location: '宁波镇海氯碱厂',
        to_location: '杭州湾精细化工园',
        transport_mode: '罐箱',
        status: '已签收',
        start_time: '2026-03-10 08:00:00',
        eta: '2026-03-11 09:30:00',
        carrier: '浙江安运危化品运输公司'
      },
      {
        trace_id: 'TRC-20260302-003',
        manifest_no: 'YH-2026-0312-091',
        chemical_name: '甲醇',
        quantity_tons: 32.0,
        from_location: '榆林煤化工厂',
        to_location: '天津港保税区罐区',
        transport_mode: '管道',
        status: '运输中',
        start_time: '2026-03-12 10:15:00',
        eta: '2026-03-16 18:00:00',
        carrier: '长庆管输公司'
      },
      {
        trace_id: 'TRC-20260302-004',
        manifest_no: 'YH-2026-0309-064',
        chemical_name: '硫酸',
        quantity_tons: 28.5,
        from_location: '铜陵有色冶炼厂',
        to_location: '南京化工产业园',
        transport_mode: '槽车',
        status: '异常',
        start_time: '2026-03-09 07:20:00',
        eta: '2026-03-10 15:00:00',
        carrier: '安徽中达危化运输有限公司'
      },
      {
        trace_id: 'TRC-20260303-005',
        manifest_no: 'YH-2026-0313-095',
        chemical_name: '丙烯',
        quantity_tons: 22.4,
        from_location: '齐鲁石化烯烃厂',
        to_location: '青岛董家口化工基地',
        transport_mode: '罐箱',
        status: '已到达',
        start_time: '2026-03-13 05:45:00',
        eta: '2026-03-14 11:00:00',
        carrier: '山东鲁运危化物流有限公司'
      },
      {
        trace_id: 'TRC-20260303-006',
        manifest_no: 'YH-2026-0314-102',
        chemical_name: '液氨',
        quantity_tons: 40.0,
        from_location: '内蒙鄂尔多斯化肥厂',
        to_location: '河北沧州临港化工园',
        transport_mode: '管道',
        status: '运输中',
        start_time: '2026-03-14 22:00:00',
        eta: '2026-03-17 08:00:00',
        carrier: '国家能源管输华北公司'
      },
      {
        trace_id: 'TRC-20260304-007',
        manifest_no: 'YH-2026-0308-059',
        chemical_name: '氢氧化钠溶液',
        quantity_tons: 30.0,
        from_location: '滨化集团氯碱装置',
        to_location: '潍坊滨海开发区水厂',
        transport_mode: '槽车',
        status: '已签收',
        start_time: '2026-03-08 09:00:00',
        eta: '2026-03-08 16:30:00',
        carrier: '山东鲁运危化物流有限公司'
      },
      {
        trace_id: 'TRC-20260304-008',
        manifest_no: 'YH-2026-0314-105',
        chemical_name: '苯',
        quantity_tons: 26.8,
        from_location: '上海石化芳烃装置',
        to_location: '江苏泰兴经济开发区',
        transport_mode: '罐箱',
        status: '运输中',
        start_time: '2026-03-14 13:40:00',
        eta: '2026-03-15 20:00:00',
        carrier: '江苏宁扬危化品运输公司'
      },
      {
        trace_id: 'TRC-20260305-009',
        manifest_no: 'YH-2026-0307-051',
        chemical_name: '天然气凝液',
        quantity_tons: 35.2,
        from_location: '长庆油田第二处理厂',
        to_location: '西安泾渭工业园储库',
        transport_mode: '管道',
        status: '已到达',
        start_time: '2026-03-07 06:00:00',
        eta: '2026-03-09 12:00:00',
        carrier: '长庆管输公司'
      }
    ]
  },

  // 8. 运输溯源详情（含全链路信息）
  traceDetail: {
    trace_id: 'TRC-20260301-001',
    manifest_no: 'YH-2026-0312-088',
    chemical_name: '液化石油气',
    cas_number: '68476-85-7',
    quantity_tons: 25.6,
    from_location: '茂名石化炼油厂区',
    to_location: '广州南沙储配站',
    transport_mode: '槽车',
    vehicle_plate: '粤K·9527挂',
    driver_name: '李志强',
    driver_license_no: '440882198805123316',
    escort_name: '陈国华',
    status: '运输中',
    start_time: '2026-03-14 06:30:00',
    eta: '2026-03-15 12:00:00',
    carrier: '粤西危化物流有限公司',
    carrier_license_no: '440900012345',
    emergency_contact: '0668-2871119',
    current_position: '沈海高速阳江服务区(K3372)',
    distance_remaining_km: 118,
    temperature: 24.8,
    pressure: 1.15,
    insurance_company: '中国人保财险茂名分公司',
    chain: [
      {
        step: 1,
        type: '装车',
        location: '茂名石化装车台3号鹤位',
        operator: '李志强',
        at: '2026-03-14 05:40',
        status: 'completed',
        temperature: 25.1,
        pressure: 1.12
      },
      {
        step: 2,
        type: '出厂检查',
        location: '茂名石化东门安检口',
        operator: '黄伟明',
        at: '2026-03-14 06:25',
        status: 'completed',
        temperature: 25.0,
        pressure: 1.13
      },
      {
        step: 3,
        type: '途中监控',
        location: '沈海高速K3480(电白段)',
        operator: 'GPS平台自动记录',
        at: '2026-03-14 08:15',
        status: 'completed',
        temperature: 24.9,
        pressure: 1.14
      },
      {
        step: 4,
        type: '途中监控',
        location: '沈海高速阳江服务区(K3372)',
        operator: 'GPS平台自动记录',
        at: '2026-03-14 10:30',
        status: 'in_progress',
        temperature: 24.8,
        pressure: 1.15
      },
      {
        step: 5,
        type: '卸车签收',
        location: '广州南沙储配站',
        operator: '待指派',
        at: null,
        status: 'pending',
        temperature: null,
        pressure: null
      }
    ],
    total_steps: 5,
    current_status: '运输中'
  },

  // 9. 运输溯源链路
  traceChain: {
    trace_id: 'TRC-20260302-003',
    manifest_no: 'YH-2026-0312-091',
    chain: [
      {
        step: 1,
        type: '装车',
        location: '化工厂装车台',
        operator: '张三',
        at: '2026-03-12 08:00',
        status: 'completed',
        temperature: 25.3,
        pressure: 1.2
      },
      {
        step: 2,
        type: '出厂检查',
        location: '榆林煤化工厂北门',
        operator: '赵铁柱',
        at: '2026-03-12 09:30',
        status: 'completed',
        temperature: 25.0,
        pressure: 1.21
      },
      {
        step: 3,
        type: '中转',
        location: '太原危化品中转库',
        operator: '刘芳',
        at: '2026-03-13 16:45',
        status: 'completed',
        temperature: 26.2,
        pressure: 1.24
      },
      {
        step: 4,
        type: '在途',
        location: '荣乌高速沧州段',
        operator: 'GPS平台自动记录',
        at: '2026-03-15 07:20',
        status: 'in_progress',
        temperature: 24.6,
        pressure: 1.18
      },
      {
        step: 5,
        type: '签收',
        location: '天津港保税区罐区',
        operator: '待指派',
        at: null,
        status: 'pending',
        temperature: null,
        pressure: null
      }
    ],
    total_steps: 5,
    current_status: '运输中'
  },

  // 10. 管段列表
  segments: {
    total: 20,
    segments: [
      {
        segment_id: 'SEG-001-01',
        pipe_id: 'PIPE-001',
        start_marker: 'K0+000',
        end_marker: 'K25+400',
        length_m: 25400,
        material: 'L450M螺旋缝埋弧焊钢管',
        wall_thickness_mm: 14.2,
        corrosion_rate_mm_y: 0.05,
        last_inspect_date: '2026-02-18',
        condition: '良好',
        risk_level: 'low'
      },
      {
        segment_id: 'SEG-001-03',
        pipe_id: 'PIPE-001',
        start_marker: 'K52+100',
        end_marker: 'K80+600',
        length_m: 28500,
        material: 'L450M螺旋缝埋弧焊钢管',
        wall_thickness_mm: 12.8,
        corrosion_rate_mm_y: 0.12,
        last_inspect_date: '2026-02-20',
        condition: '轻微腐蚀',
        risk_level: 'medium'
      },
      {
        segment_id: 'SEG-002-01',
        pipe_id: 'PIPE-002',
        start_marker: 'K0+000',
        end_marker: 'K8+200',
        length_m: 8200,
        material: '20#无缝钢管',
        wall_thickness_mm: 9.5,
        corrosion_rate_mm_y: 0.03,
        last_inspect_date: '2026-01-30',
        condition: '良好',
        risk_level: 'low'
      },
      {
        segment_id: 'SEG-003-01',
        pipe_id: 'PIPE-003',
        start_marker: 'K0+000',
        end_marker: 'K6+300',
        length_m: 6300,
        material: '304不锈钢管',
        wall_thickness_mm: 6.4,
        corrosion_rate_mm_y: 0.18,
        last_inspect_date: '2026-02-05',
        condition: '需关注',
        risk_level: 'medium'
      },
      {
        segment_id: 'SEG-003-02',
        pipe_id: 'PIPE-003',
        start_marker: 'K6+300',
        end_marker: 'K12+400',
        length_m: 6100,
        material: '304不锈钢管',
        wall_thickness_mm: 5.1,
        corrosion_rate_mm_y: 0.32,
        last_inspect_date: '2026-02-05',
        condition: '需更换',
        risk_level: 'high'
      },
      {
        segment_id: 'SEG-004-01',
        pipe_id: 'PIPE-004',
        start_marker: 'K0+000',
        end_marker: 'K5+600',
        length_m: 5600,
        material: '衬氟无缝钢管',
        wall_thickness_mm: 8.0,
        corrosion_rate_mm_y: 0.41,
        last_inspect_date: '2026-01-12',
        condition: '需更换',
        risk_level: 'high'
      },
      {
        segment_id: 'SEG-005-01',
        pipe_id: 'PIPE-005',
        start_marker: 'K0+000',
        end_marker: 'K18+800',
        length_m: 18800,
        material: 'PE100燃气管',
        wall_thickness_mm: 22.3,
        corrosion_rate_mm_y: 0.01,
        last_inspect_date: '2026-03-01',
        condition: '良好',
        risk_level: 'low'
      },
      {
        segment_id: 'SEG-006-01',
        pipe_id: 'PIPE-006',
        start_marker: 'K0+000',
        end_marker: 'K8+900',
        length_m: 8900,
        material: 'L245直缝埋弧焊管',
        wall_thickness_mm: 11.0,
        corrosion_rate_mm_y: 0.08,
        last_inspect_date: '2026-02-22',
        condition: '良好',
        risk_level: 'low'
      },
      {
        segment_id: 'SEG-007-01',
        pipe_id: 'PIPE-007',
        start_marker: 'K0+000',
        end_marker: 'K15+300',
        length_m: 15300,
        material: '16MnDR低温钢管',
        wall_thickness_mm: 10.2,
        corrosion_rate_mm_y: 0.15,
        last_inspect_date: '2026-01-08',
        condition: '需关注',
        risk_level: 'medium'
      },
      {
        segment_id: 'SEG-008-01',
        pipe_id: 'PIPE-008',
        start_marker: 'K0+000',
        end_marker: 'K32+500',
        length_m: 32500,
        material: 'L415M无缝钢管',
        wall_thickness_mm: 16.0,
        corrosion_rate_mm_y: 0.04,
        last_inspect_date: '2026-03-05',
        condition: '良好',
        risk_level: 'low'
      },
      {
        segment_id: 'SEG-008-02',
        pipe_id: 'PIPE-008',
        start_marker: 'K32+500',
        end_marker: 'K64+700',
        length_m: 32200,
        material: 'L415M无缝钢管',
        wall_thickness_mm: 13.6,
        corrosion_rate_mm_y: 0.11,
        last_inspect_date: '2026-03-06',
        condition: '轻微腐蚀',
        risk_level: 'medium'
      },
      {
        segment_id: 'SEG-002-02',
        pipe_id: 'PIPE-002',
        start_marker: 'K8+200',
        end_marker: 'K23+800',
        length_m: 15600,
        material: '20#无缝钢管',
        wall_thickness_mm: 8.9,
        corrosion_rate_mm_y: 0.09,
        last_inspect_date: '2026-01-31',
        condition: '轻微腐蚀',
        risk_level: 'medium'
      }
    ]
  },

  // 11. 腐蚀评估
  corrosionEval: {
    segment_id: 'SEG-001-03',
    current_thickness: 8.2,
    original_thickness: 10.0,
    corrosion_rate: 0.12,
    estimated_remaining_life_years: 15,
    risk_level: 'medium',
    recommendation: '建议6个月后复检',
    eval_date: '2026-02-20',
    eval_method: '超声波测厚+内检测数据综合分析',
    inspector: '孙立军',
    corrosion_type: '均匀腐蚀',
    min_required_thickness: 5.0
  },

  // 12. 危化品台账
  ledger: {
    total: 15,
    ledger: [
      {
        ledger_id: 'LDG-001',
        chemical_name: '甲醇',
        cas_number: '67-56-1',
        quantity_stored: 450.0,
        storage_location: '甲醇中间罐区A组(V-101~V-104)',
        hazard_class: '易燃',
        max_storage_limit: 800.0,
        last_check_date: '2026-03-10',
        compliance_status: '合规',
        responsible_person: '周敏'
      },
      {
        ledger_id: 'LDG-002',
        chemical_name: '液氯',
        cas_number: '7782-50-5',
        quantity_stored: 68.5,
        storage_location: '液氯储罐区(T-201~T-203)',
        hazard_class: '有毒',
        max_storage_limit: 60.0,
        last_check_date: '2026-03-12',
        compliance_status: '超标',
        responsible_person: '吴海涛'
      },
      {
        ledger_id: 'LDG-003',
        chemical_name: '硫酸',
        cas_number: '7664-93-9',
        quantity_stored: 320.0,
        storage_location: '酸库98%硫酸罐区',
        hazard_class: '腐蚀',
        max_storage_limit: 500.0,
        last_check_date: '2026-03-08',
        compliance_status: '合规',
        responsible_person: '郑春霞'
      },
      {
        ledger_id: 'LDG-004',
        chemical_name: '液氨',
        cas_number: '7664-41-7',
        quantity_stored: 185.0,
        storage_location: '液氨储罐区(V-301~V-302)',
        hazard_class: '有毒',
        max_storage_limit: 300.0,
        last_check_date: '2026-02-28',
        compliance_status: '合规',
        responsible_person: '王建军'
      },
      {
        ledger_id: 'LDG-005',
        chemical_name: '过氧化氢(双氧水)',
        cas_number: '7722-84-1',
        quantity_stored: 42.0,
        storage_location: '氧化剂专用库房2号',
        hazard_class: '易爆',
        max_storage_limit: 50.0,
        last_check_date: '2026-03-11',
        compliance_status: '合规',
        responsible_person: '李晓峰'
      },
      {
        ledger_id: 'LDG-006',
        chemical_name: '苯',
        cas_number: '71-43-2',
        quantity_stored: 210.0,
        storage_location: '芳烃罐区(B-101~B-103)',
        hazard_class: '易燃',
        max_storage_limit: 400.0,
        last_check_date: '2026-03-01',
        compliance_status: '待检',
        responsible_person: '刘志强'
      },
      {
        ledger_id: 'LDG-007',
        chemical_name: '氢氧化钠',
        cas_number: '1310-73-2',
        quantity_stored: 96.0,
        storage_location: '碱液配制间储罐区',
        hazard_class: '腐蚀',
        max_storage_limit: 150.0,
        last_check_date: '2026-03-09',
        compliance_status: '合规',
        responsible_person: '赵秀兰'
      },
      {
        ledger_id: 'LDG-008',
        chemical_name: '丙烯腈',
        cas_number: '107-13-1',
        quantity_stored: 55.0,
        storage_location: '丙烯腈专用罐区(N-401)',
        hazard_class: '易燃',
        max_storage_limit: 50.0,
        last_check_date: '2026-03-13',
        compliance_status: '超标',
        responsible_person: '陈立新'
      },
      {
        ledger_id: 'LDG-009',
        chemical_name: '硝酸铵',
        cas_number: '6484-52-2',
        quantity_stored: 28.0,
        storage_location: '爆炸品专用仓库1号',
        hazard_class: '易爆',
        max_storage_limit: 40.0,
        last_check_date: '2026-03-06',
        compliance_status: '合规',
        responsible_person: '孙国栋'
      },
      {
        ledger_id: 'LDG-010',
        chemical_name: '氰化钠',
        cas_number: '143-33-9',
        quantity_stored: 8.5,
        storage_location: '剧毒品双人双锁专库',
        hazard_class: '有毒',
        max_storage_limit: 15.0,
        last_check_date: '2026-03-14',
        compliance_status: '合规',
        responsible_person: '马振华'
      }
    ]
  },

  // 13. 阀门列表
  valves: {
    total: 12,
    valves: [
      {
        valve_id: 'VLV-001',
        name: '首站出口紧急切断阀',
        location: '库尔勒分输站出口',
        type: '球阀',
        pipe_id: 'PIPE-001',
        status: '正常',
        last_maintenance: '2026-01-15',
        pressure_rating: 'PN100',
        is_emergency: true,
        remote_control: true
      },
      {
        valve_id: 'VLV-002',
        name: '液氯充装站切断阀',
        location: '液氯充装站鹤管根部',
        type: '截止阀',
        pipe_id: 'PIPE-004',
        status: '待维护',
        last_maintenance: '2025-08-20',
        pressure_rating: 'PN25',
        is_emergency: true,
        remote_control: false
      },
      {
        valve_id: 'VLV-003',
        name: '甲醇管廊干线调节阀',
        location: '甲醇管廊3号阀室',
        type: '球阀',
        pipe_id: 'PIPE-003',
        status: '正常',
        last_maintenance: '2026-02-10',
        pressure_rating: 'PN40',
        is_emergency: false,
        remote_control: true
      },
      {
        valve_id: 'VLV-004',
        name: 'LPG球罐安全阀',
        location: 'LPG球罐区V-301顶部',
        type: '安全阀',
        pipe_id: 'PIPE-002',
        status: '正常',
        last_maintenance: '2026-01-28',
        pressure_rating: 'PN63',
        is_emergency: true,
        remote_control: false
      },
      {
        valve_id: 'VLV-005',
        name: '乙烯管线分段闸阀',
        location: '乙烯东段K32+500阀井',
        type: '闸阀',
        pipe_id: 'PIPE-008',
        status: '故障',
        last_maintenance: '2025-11-05',
        pressure_rating: 'PN160',
        is_emergency: false,
        remote_control: true
      },
      {
        valve_id: 'VLV-006',
        name: '合成氨装置出口切断阀',
        location: '合成氨装置界区外',
        type: '球阀',
        pipe_id: 'PIPE-007',
        status: '正常',
        last_maintenance: '2026-02-25',
        pressure_rating: 'PN100',
        is_emergency: true,
        remote_control: true
      },
      {
        valve_id: 'VLV-007',
        name: '城燃调压站安全阀',
        location: '开发区调压站',
        type: '安全阀',
        pipe_id: 'PIPE-005',
        status: '待维护',
        last_maintenance: '2025-09-12',
        pressure_rating: 'PN40',
        is_emergency: false,
        remote_control: false
      },
      {
        valve_id: 'VLV-008',
        name: '丙烯专线紧急切断阀',
        location: '催化裂化装置出口',
        type: '球阀',
        pipe_id: 'PIPE-006',
        status: '正常',
        last_maintenance: '2026-03-02',
        pressure_rating: 'PN63',
        is_emergency: true,
        remote_control: true
      },
      {
        valve_id: 'VLV-009',
        name: '硫酸罐区放料闸阀',
        location: '酸库硫酸罐区泵房',
        type: '闸阀',
        pipe_id: 'PIPE-009',
        status: '正常',
        last_maintenance: '2026-01-20',
        pressure_rating: 'PN16',
        is_emergency: false,
        remote_control: false
      },
      {
        valve_id: 'VLV-010',
        name: '液氨储罐根部截止阀',
        location: '液氨储罐区T-201根部',
        type: '截止阀',
        pipe_id: 'PIPE-010',
        status: '正常',
        last_maintenance: '2026-02-14',
        pressure_rating: 'PN40',
        is_emergency: true,
        remote_control: true
      },
      {
        valve_id: 'VLV-011',
        name: '末站计量区球阀',
        location: '鄯善计量站',
        type: '球阀',
        pipe_id: 'PIPE-001',
        status: '正常',
        last_maintenance: '2026-01-16',
        pressure_rating: 'PN100',
        is_emergency: false,
        remote_control: true
      },
      {
        valve_id: 'VLV-012',
        name: '苯罐区防火堤外切断阀',
        location: '芳烃罐区B-101防火堤外',
        type: '闸阀',
        pipe_id: 'PIPE-011',
        status: '故障',
        last_maintenance: '2025-10-08',
        pressure_rating: 'PN25',
        is_emergency: true,
        remote_control: false
      }
    ]
  }
}
