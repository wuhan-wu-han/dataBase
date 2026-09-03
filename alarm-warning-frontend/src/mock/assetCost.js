/**
 * 资产成本管理 Mock 数据
 * 覆盖：总览、资产台账、资产明细、折旧计算、成本记录、成本分析、全生命周期成本（LCC）
 */
export default {
  // 1. 总览指标
  overview: {
    total_assets: 3842,
    total_original_value: 285600000,
    total_annual_cost: 12680000,
    overall_depr_pct: 34.6
  },

  // 2. 资产类别（折旧年限 / 残值率）
  categories: {
    pipe: { name: '管道', depr_years: 30, residual_rate: 0.05 },
    valve: { name: '阀门', depr_years: 20, residual_rate: 0.05 },
    pump: { name: '泵机', depr_years: 15, residual_rate: 0.05 },
    meter: { name: '仪表', depr_years: 10, residual_rate: 0.05 },
    electrical: { name: '电气设备', depr_years: 12, residual_rate: 0.05 }
  },

  // 3. 材质字典
  materials: {
    steel: { name: '钢管' },
    pe: { name: 'PE管' },
    ductile: { name: '球墨铸铁' },
    copper: { name: '铜管' },
    pvc: { name: 'PVC管' }
  },

  // 4. 片区
  regions: ['城北片区', '城南片区', '开发区', '高新区', '老城区'],

  // 5. 折旧方法
  deprMethods: {
    straight: '直线法',
    double_declining: '双倍余额递减法',
    sum_years: '年数总和法'
  },

  // 6. 资产台账列表
  assets: {
    items: [
      {
        asset_id: 'AS-2026-0001',
        name: '城北主干供水管道A段',
        category: 'pipe',
        category_name: '管道',
        region: '城北片区',
        material: 'steel',
        material_name: '钢管',
        specs: 'DN800×12mm 螺旋焊接钢管',
        original_value: 5000000,
        install_date: '2016-05-20',
        status: '在用',
        accumulated_depr: 1583330,
        net_value: 3416670,
        depr_pct: 31.7,
        depr_method: 'straight',
        depr_years: 30,
        residual_rate: 0.05,
        annual_depr: 158333,
        years_elapsed: 10
      },
      {
        asset_id: 'AS-2026-0002',
        name: '城南配水管网PE管道',
        category: 'pipe',
        category_name: '管道',
        region: '城南片区',
        material: 'pe',
        material_name: 'PE管',
        specs: 'DN400 PE100级',
        original_value: 1850000,
        install_date: '2019-08-12',
        status: '在用',
        accumulated_depr: 410081,
        net_value: 1439919,
        depr_pct: 22.2,
        depr_method: 'straight',
        depr_years: 30,
        residual_rate: 0.05,
        annual_depr: 58583,
        years_elapsed: 7
      },
      {
        asset_id: 'AS-2026-0003',
        name: '开发区球墨铸铁主管',
        category: 'pipe',
        category_name: '管道',
        region: '开发区',
        material: 'ductile',
        material_name: '球墨铸铁',
        specs: 'DN600 K9级',
        original_value: 3200000,
        install_date: '2021-03-15',
        status: '在用',
        accumulated_depr: 506665,
        net_value: 2693335,
        depr_pct: 15.8,
        depr_method: 'straight',
        depr_years: 30,
        residual_rate: 0.05,
        annual_depr: 101333,
        years_elapsed: 5
      },
      {
        asset_id: 'AS-2026-0004',
        name: '高新区铜质仪表管线',
        category: 'pipe',
        category_name: '管道',
        region: '高新区',
        material: 'copper',
        material_name: '铜管',
        specs: 'DN50 紫铜管',
        original_value: 420000,
        install_date: '2023-06-10',
        status: '在用',
        accumulated_depr: 39900,
        net_value: 380100,
        depr_pct: 9.5,
        depr_method: 'straight',
        depr_years: 30,
        residual_rate: 0.05,
        annual_depr: 13300,
        years_elapsed: 3
      },
      {
        asset_id: 'AS-2026-0005',
        name: '老城区PVC排水管',
        category: 'pipe',
        category_name: '管道',
        region: '老城区',
        material: 'pvc',
        material_name: 'PVC管',
        specs: 'DN300 PVC-U双壁波纹管',
        original_value: 280000,
        install_date: '2015-09-25',
        status: '已审核',
        accumulated_depr: 97537,
        net_value: 182463,
        depr_pct: 34.8,
        depr_method: 'straight',
        depr_years: 30,
        residual_rate: 0.05,
        annual_depr: 8867,
        years_elapsed: 11
      },
      {
        asset_id: 'AS-2026-0006',
        name: '城北片区电动蝶阀',
        category: 'valve',
        category_name: '阀门',
        region: '城北片区',
        material: 'ductile',
        material_name: '球墨铸铁',
        specs: 'DN600 电动法兰蝶阀',
        original_value: 356000,
        install_date: '2020-11-08',
        status: '在用',
        accumulated_depr: 101460,
        net_value: 254540,
        depr_pct: 28.5,
        depr_method: 'straight',
        depr_years: 20,
        residual_rate: 0.05,
        annual_depr: 16910,
        years_elapsed: 6
      },
      {
        asset_id: 'AS-2026-0007',
        name: '高新区智能调节阀',
        category: 'valve',
        category_name: '阀门',
        region: '高新区',
        material: 'copper',
        material_name: '铜管',
        specs: 'DN200 智能电动调节阀',
        original_value: 485000,
        install_date: '2022-07-19',
        status: '在用',
        accumulated_depr: 92152,
        net_value: 392848,
        depr_pct: 19.0,
        depr_method: 'straight',
        depr_years: 20,
        residual_rate: 0.05,
        annual_depr: 23038,
        years_elapsed: 4
      },
      {
        asset_id: 'AS-2026-0008',
        name: '开发区闸阀组',
        category: 'valve',
        category_name: '阀门',
        region: '开发区',
        material: 'steel',
        material_name: '钢管',
        specs: 'DN400 暗杆楔式闸阀×6',
        original_value: 128000,
        install_date: '2018-04-02',
        status: '已提足',
        accumulated_depr: 48640,
        net_value: 79360,
        depr_pct: 38.0,
        depr_method: 'straight',
        depr_years: 20,
        residual_rate: 0.05,
        annual_depr: 6080,
        years_elapsed: 8
      },
      {
        asset_id: 'AS-2026-0009',
        name: '城南加压站主泵机',
        category: 'pump',
        category_name: '泵机',
        region: '城南片区',
        material: 'steel',
        material_name: '钢管',
        specs: '单级双吸离心泵 250kW',
        original_value: 1560000,
        install_date: '2017-10-30',
        status: '在用',
        accumulated_depr: 889200,
        net_value: 670800,
        depr_pct: 57.0,
        depr_method: 'straight',
        depr_years: 15,
        residual_rate: 0.05,
        annual_depr: 98800,
        years_elapsed: 9
      },
      {
        asset_id: 'AS-2026-0010',
        name: '城北二次加压泵组',
        category: 'pump',
        category_name: '泵机',
        region: '城北片区',
        material: 'steel',
        material_name: '钢管',
        specs: '立式多级离心泵 55kW×3',
        original_value: 386000,
        install_date: '2024-05-16',
        status: '在用',
        accumulated_depr: 48894,
        net_value: 337106,
        depr_pct: 12.7,
        depr_method: 'straight',
        depr_years: 15,
        residual_rate: 0.05,
        annual_depr: 24447,
        years_elapsed: 2
      },
      {
        asset_id: 'AS-2026-0011',
        name: '老城区污水提升泵',
        category: 'pump',
        category_name: '泵机',
        region: '老城区',
        material: 'ductile',
        material_name: '球墨铸铁',
        specs: '潜水排污泵 30kW',
        original_value: 96000,
        install_date: '2014-08-21',
        status: '已报废',
        accumulated_depr: 72960,
        net_value: 23040,
        depr_pct: 76.0,
        depr_method: 'straight',
        depr_years: 15,
        residual_rate: 0.05,
        annual_depr: 6080,
        years_elapsed: 12
      },
      {
        asset_id: 'AS-2026-0012',
        name: '高新区电磁流量计',
        category: 'meter',
        category_name: '仪表',
        region: '高新区',
        material: 'copper',
        material_name: '铜管',
        specs: 'DN300 一体式电磁流量计',
        original_value: 215000,
        install_date: '2023-09-05',
        status: '在用',
        accumulated_depr: 61275,
        net_value: 153725,
        depr_pct: 28.5,
        depr_method: 'straight',
        depr_years: 10,
        residual_rate: 0.05,
        annual_depr: 20425,
        years_elapsed: 3
      },
      {
        asset_id: 'AS-2026-0013',
        name: '开发区超声波水表',
        category: 'meter',
        category_name: '仪表',
        region: '开发区',
        material: 'pvc',
        material_name: 'PVC管',
        specs: 'DN150 外夹式超声波水表',
        original_value: 86000,
        install_date: '2026-01-15',
        status: '在用',
        accumulated_depr: 0,
        net_value: 86000,
        depr_pct: 0,
        depr_method: 'straight',
        depr_years: 10,
        residual_rate: 0.05,
        annual_depr: 8170,
        years_elapsed: 0
      },
      {
        asset_id: 'AS-2026-0014',
        name: '城南压力变送器',
        category: 'meter',
        category_name: '仪表',
        region: '城南片区',
        material: 'copper',
        material_name: '铜管',
        specs: '0-1.6MPa 智能压力变送器',
        original_value: 45000,
        install_date: '2021-12-20',
        status: '已审核',
        accumulated_depr: 21375,
        net_value: 23625,
        depr_pct: 47.5,
        depr_method: 'straight',
        depr_years: 10,
        residual_rate: 0.05,
        annual_depr: 4275,
        years_elapsed: 5
      },
      {
        asset_id: 'AS-2026-0015',
        name: '城北10kV配电柜',
        category: 'electrical',
        category_name: '电气设备',
        region: '城北片区',
        material: 'steel',
        material_name: '钢管',
        specs: 'KYN28A-12 铠装移开式开关柜×4',
        original_value: 1280000,
        install_date: '2019-03-28',
        status: '在用',
        accumulated_depr: 709331,
        net_value: 570669,
        depr_pct: 55.4,
        depr_method: 'straight',
        depr_years: 12,
        residual_rate: 0.05,
        annual_depr: 101333,
        years_elapsed: 7
      },
      {
        asset_id: 'AS-2026-0016',
        name: '高新区变频控制柜',
        category: 'electrical',
        category_name: '电气设备',
        region: '高新区',
        material: 'steel',
        material_name: '钢管',
        specs: '200kW 变频调速控制柜',
        original_value: 320000,
        install_date: '2022-10-12',
        status: '在用',
        accumulated_depr: 165678,
        net_value: 154322,
        depr_pct: 51.8,
        depr_method: 'double_declining',
        depr_years: 12,
        residual_rate: 0.05,
        annual_depr: 30864,
        years_elapsed: 4
      },
      {
        asset_id: 'AS-2026-0017',
        name: '开发区箱式变压器',
        category: 'electrical',
        category_name: '电气设备',
        region: '开发区',
        material: 'copper',
        material_name: '铜管',
        specs: 'S13-M-800kVA 油浸式变压器',
        original_value: 680000,
        install_date: '2020-06-18',
        status: '在用',
        accumulated_depr: 472077,
        net_value: 207923,
        depr_pct: 69.4,
        depr_method: 'sum_years',
        depr_years: 12,
        residual_rate: 0.05,
        annual_depr: 49692,
        years_elapsed: 6
      }
    ],
    total: 25
  },

  // 7. 资产明细（含成本履历）
  assetDetail: {
    asset: {
      asset_id: 'AS-2026-0001',
      name: '城北主干供水管道A段',
      category: 'pipe',
      category_name: '管道',
      region: '城北片区',
      material: 'steel',
      material_name: '钢管',
      specs: 'DN800×12mm 螺旋焊接钢管',
      original_value: 5000000,
      install_date: '2016-05-20',
      status: '在用',
      accumulated_depr: 1583330,
      net_value: 3416670,
      depr_pct: 31.7,
      depr_method: 'straight',
      depr_years: 30,
      residual_rate: 0.05,
      annual_depr: 158333,
      years_elapsed: 10
    },
    cost_history: [
      { record_id: 'CH-2026-0101', cost_type: '定期维修', amount: 45000, record_date: '2026-01-08', description: '管道渗漏点补焊维修' },
      { record_id: 'CH-2026-0102', cost_type: '日常运维', amount: 28000, record_date: '2026-01-26', description: '管线阀门井防锈保养' },
      { record_id: 'CH-2026-0103', cost_type: '定期维修', amount: 62000, record_date: '2026-02-14', description: '冬季冻裂管段应急抢修' },
      { record_id: 'CH-2026-0104', cost_type: '应急维修', amount: 15000, record_date: '2026-03-05', description: '管道打压试验及水质检测' },
      { record_id: 'CH-2026-0105', cost_type: '技改更换', amount: 38000, record_date: '2026-03-22', description: '更换伸缩节及法兰垫片' },
      { record_id: 'CH-2026-0106', cost_type: '日常运维', amount: 22500, record_date: '2026-04-11', description: '防腐涂层局部修补保养' },
      { record_id: 'CH-2026-0107', cost_type: '定期维修', amount: 56000, record_date: '2026-04-22', description: '管道防腐层整体翻新' },
      { record_id: 'CH-2026-0108', cost_type: '应急维修', amount: 18500, record_date: '2026-05-15', description: '管道机器人CCTV内窥检测' }
    ],
    total_cost: 285000
  },

  // 8. 折旧计算示例（直线法）
  depreciation: {
    method: 'straight',
    years: 30,
    depreciable: 4750000,
    schedule: [
      { year: 1, beginning_value: 5000000, depr_amount: 158333, accumulated: 158333, ending_value: 4841667 },
      { year: 2, beginning_value: 4841667, depr_amount: 158333, accumulated: 316666, ending_value: 4683334 },
      { year: 3, beginning_value: 4683334, depr_amount: 158333, accumulated: 474999, ending_value: 4525001 },
      { year: 4, beginning_value: 4525001, depr_amount: 158333, accumulated: 633332, ending_value: 4366668 },
      { year: 5, beginning_value: 4366668, depr_amount: 158333, accumulated: 791665, ending_value: 4208335 }
    ]
  },

  // 9. 成本记录列表
  costRecords: {
    items: [
      {
        record_id: 'CR-2026-0001',
        asset_id: 'AS-2026-0001',
        cost_type: '定期维修',
        amount: 45000,
        description: '管道渗漏点补焊维修',
        region: '城北片区',
        record_date: '2026-01-08',
        approved: true,
        created_at: '2026-01-08 10:23:15'
      },
      {
        record_id: 'CR-2026-0002',
        asset_id: 'AS-2026-0009',
        cost_type: '日常运维',
        amount: 28000,
        description: '主泵机年度大修及轴承润滑保养',
        region: '城南片区',
        record_date: '2026-01-15',
        approved: true,
        created_at: '2026-01-15 14:05:42'
      },
      {
        record_id: 'CR-2026-0003',
        asset_id: 'AS-2026-0012',
        cost_type: '应急维修',
        amount: 6500,
        description: '电磁流量计周期计量校准',
        region: '高新区',
        record_date: '2026-02-03',
        approved: true,
        created_at: '2026-02-03 09:18:30'
      },
      {
        record_id: 'CR-2026-0004',
        asset_id: 'AS-2026-0005',
        cost_type: '技改更换',
        amount: 62000,
        description: '更换老化破裂PVC管段及配件',
        region: '老城区',
        record_date: '2026-02-18',
        approved: true,
        created_at: '2026-02-18 16:40:07'
      },
      {
        record_id: 'CR-2026-0005',
        asset_id: 'AS-2026-0015',
        cost_type: '日常运维',
        amount: 35000,
        description: '配电柜绝缘清扫及母排紧固保养',
        region: '城北片区',
        record_date: '2026-03-02',
        approved: true,
        created_at: '2026-03-02 11:12:55'
      },
      {
        record_id: 'CR-2026-0006',
        asset_id: 'AS-2026-0006',
        cost_type: '定期维修',
        amount: 18500,
        description: '电动蝶阀执行机构故障维修',
        region: '城北片区',
        record_date: '2026-03-16',
        approved: true,
        created_at: '2026-03-16 15:33:21'
      },
      {
        record_id: 'CR-2026-0007',
        asset_id: 'AS-2026-0010',
        cost_type: '能耗费用',
        amount: 42000,
        description: '二次加压泵组三月份电费',
        region: '城北片区',
        record_date: '2026-03-31',
        approved: false,
        created_at: '2026-03-31 17:50:08'
      },
      {
        record_id: 'CR-2026-0008',
        asset_id: 'AS-2026-0003',
        cost_type: '应急维修',
        amount: 25800,
        description: '主干管道超声波测厚及探伤检测',
        region: '开发区',
        record_date: '2026-04-10',
        approved: true,
        created_at: '2026-04-10 10:02:44'
      },
      {
        record_id: 'CR-2026-0009',
        asset_id: 'AS-2026-0001',
        cost_type: '定期维修',
        amount: 56000,
        description: '管道防腐涂层整体翻新维修',
        region: '城北片区',
        record_date: '2026-04-22',
        approved: true,
        created_at: '2026-04-22 09:45:19'
      },
      {
        record_id: 'CR-2026-0010',
        asset_id: 'AS-2026-0013',
        cost_type: '日常运维',
        amount: 3200,
        description: '超声波水表标定及日常维护',
        region: '开发区',
        record_date: '2026-05-06',
        approved: true,
        created_at: '2026-05-06 13:27:36'
      },
      {
        record_id: 'CR-2026-0011',
        asset_id: 'AS-2026-0009',
        cost_type: '定期维修',
        amount: 38000,
        description: '泵机机械密封及叶轮更换维修',
        region: '城南片区',
        record_date: '2026-05-19',
        approved: false,
        created_at: '2026-05-19 16:08:52'
      },
      {
        record_id: 'CR-2026-0012',
        asset_id: 'AS-2026-0016',
        cost_type: '能耗费用',
        amount: 21600,
        description: '变频控制柜五月份运行电费',
        region: '高新区',
        record_date: '2026-06-02',
        approved: true,
        created_at: '2026-06-02 08:56:13'
      }
    ],
    total: 20
  },

  // 10. 成本分析
  costAnalysis: {
    total_cost: 12680000,
    by_type: {
      '定期维修': { total: 4200000, count: 156 },
      '日常运维': { total: 3100000, count: 234 },
      '技改更换': { total: 2800000, count: 89 },
      '应急维修': { total: 1580000, count: 67 },
      '能耗费用': { total: 1000000, count: 45 }
    },
    by_region: {
      '城北片区': { total: 3200000, count: 120 },
      '城南片区': { total: 2800000, count: 98 },
      '开发区': { total: 2600000, count: 85 },
      '高新区': { total: 2280000, count: 72 },
      '老城区': { total: 1800000, count: 56 }
    },
    monthly_trend: {
      '2026-01': 980000,
      '2026-02': 850000,
      '2026-03': 1120000,
      '2026-04': 1050000,
      '2026-05': 1180000,
      '2026-06': 1250000
    },
    top_cost_assets: [
      { asset_id: 'AS-2026-0001', total_cost: 285000, record_count: 12 },
      { asset_id: 'AS-2026-0009', total_cost: 236000, record_count: 9 },
      { asset_id: 'AS-2026-0015', total_cost: 198500, record_count: 8 },
      { asset_id: 'AS-2026-0005', total_cost: 164200, record_count: 10 },
      { asset_id: 'AS-2026-0006', total_cost: 142800, record_count: 7 }
    ]
  },

  // 11. 全生命周期成本（LCC）分析列表
  lccList: [
    {
      analysis_id: 'LCC-2026-001',
      project_name: '城北主干供水管道更新工程',
      design_life: 30,
      discount_rate: 0.06,
      recommended: 'steel',
      options: [
        { rank: 1, material: 'steel', material_name: '钢管', initial_cost: 5000000, annual_maintenance: 180000, annual_energy: 420000, replacement_cost: 0, disposal_cost: 250000, total_lcc: 23250000, npv: 13302500 },
        { rank: 2, material: 'pe', material_name: 'PE管', initial_cost: 3900000, annual_maintenance: 210000, annual_energy: 430000, replacement_cost: 1500000, disposal_cost: 120000, total_lcc: 24720000, npv: 13356300 },
        { rank: 3, material: 'ductile', material_name: '球墨铸铁', initial_cost: 5600000, annual_maintenance: 150000, annual_energy: 415000, replacement_cost: 0, disposal_cost: 300000, total_lcc: 22850000, npv: 13429300 }
      ],
      created_at: '2026-01-12 09:30:00'
    },
    {
      analysis_id: 'LCC-2026-002',
      project_name: '城南配水管网改造工程',
      design_life: 30,
      discount_rate: 0.05,
      recommended: 'pe',
      options: [
        { rank: 1, material: 'pe', material_name: 'PE管', initial_cost: 2600000, annual_maintenance: 160000, annual_energy: 280000, replacement_cost: 900000, disposal_cost: 90000, total_lcc: 16790000, npv: 9817600 },
        { rank: 2, material: 'steel', material_name: '钢管', initial_cost: 3100000, annual_maintenance: 190000, annual_energy: 285000, replacement_cost: 0, disposal_cost: 160000, total_lcc: 17510000, npv: 10439000 },
        { rank: 3, material: 'pvc', material_name: 'PVC管', initial_cost: 2200000, annual_maintenance: 230000, annual_energy: 290000, replacement_cost: 1100000, disposal_cost: 70000, total_lcc: 18970000, npv: 10739000 }
      ],
      created_at: '2026-02-20 14:15:30'
    },
    {
      analysis_id: 'LCC-2026-003',
      project_name: '开发区泵站机电设备选型',
      design_life: 15,
      discount_rate: 0.06,
      recommended: 'ductile',
      options: [
        { rank: 1, material: 'ductile', material_name: '球墨铸铁', initial_cost: 1800000, annual_maintenance: 120000, annual_energy: 560000, replacement_cost: 350000, disposal_cost: 60000, total_lcc: 12410000, npv: 8624800 },
        { rank: 2, material: 'copper', material_name: '铜管', initial_cost: 2350000, annual_maintenance: 90000, annual_energy: 545000, replacement_cost: 280000, disposal_cost: 150000, total_lcc: 12305000, npv: 8736200 },
        { rank: 3, material: 'steel', material_name: '钢管', initial_cost: 1650000, annual_maintenance: 150000, annual_energy: 590000, replacement_cost: 420000, disposal_cost: 80000, total_lcc: 13250000, npv: 9104900 }
      ],
      created_at: '2026-03-28 10:42:11'
    },
    {
      analysis_id: 'LCC-2026-004',
      project_name: '老城区排水管道修复工程',
      design_life: 25,
      discount_rate: 0.055,
      recommended: 'pvc',
      options: [
        { rank: 1, material: 'pvc', material_name: 'PVC管', initial_cost: 1200000, annual_maintenance: 85000, annual_energy: 60000, replacement_cost: 400000, disposal_cost: 50000, total_lcc: 5275000, npv: 3369700 },
        { rank: 2, material: 'pe', material_name: 'PE管', initial_cost: 1380000, annual_maintenance: 80000, annual_energy: 62000, replacement_cost: 520000, disposal_cost: 45000, total_lcc: 5495000, npv: 3571200 },
        { rank: 3, material: 'ductile', material_name: '球墨铸铁', initial_cost: 1600000, annual_maintenance: 95000, annual_energy: 62000, replacement_cost: 0, disposal_cost: 90000, total_lcc: 5615000, npv: 3730800 }
      ],
      created_at: '2026-05-09 16:20:45'
    }
  ],

  // 12. LCC 分析详情（完整比选数据）
  lccDetail: {
    analysis_id: 'LCC-2026-001',
    project_name: '城北主干供水管道更新工程',
    design_life: 30,
    discount_rate: 0.06,
    recommended: 'steel',
    options: [
      { rank: 1, material: 'steel', material_name: '钢管', initial_cost: 5000000, annual_maintenance: 180000, annual_energy: 420000, replacement_cost: 0, disposal_cost: 250000, total_lcc: 23250000, npv: 13302500 },
      { rank: 2, material: 'pe', material_name: 'PE管', initial_cost: 3900000, annual_maintenance: 210000, annual_energy: 430000, replacement_cost: 1500000, disposal_cost: 120000, total_lcc: 24720000, npv: 13356300 },
      { rank: 3, material: 'ductile', material_name: '球墨铸铁', initial_cost: 5600000, annual_maintenance: 150000, annual_energy: 415000, replacement_cost: 0, disposal_cost: 300000, total_lcc: 22850000, npv: 13429300 }
    ],
    created_at: '2026-01-12 09:30:00'
  }
}
