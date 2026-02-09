/**
 * pPQR预设字段模块库
 * 定义所有可用的pPQR字段模块
 * pPQR用于试验性焊接，探索最佳焊接参数
 */
import { FieldModule } from '@/types/wpsModules'

/**
 * pPQR预设模块库
 */
export const PPQR_PRESET_MODULES: FieldModule[] = [
  // ==================== 1. pPQR基本信息 ====================
  {
    id: 'ppqr_basic_info',
    name: 'pPQR基本信息',
    description: 'pPQR的基本识别信息和试验目的',
    icon: 'ExperimentOutlined',
    category: 'basic',
    repeatable: false,
    fields: {
      ppqr_number: {
        label: 'pPQR编号',
        type: 'text',
        required: true,
        placeholder: '如：pPQR-2024-001'
      },
      title: {
        label: 'pPQR标题',
        type: 'text',
        required: true,
        placeholder: '如：Q345R钢板对接焊参数优化试验'
      },
      test_date: {
        label: '试验日期',
        type: 'date',
        required: true
      },
      test_purpose: {
        label: '试验目的',
        type: 'textarea',
        required: true,
        placeholder: '如：探索最佳焊接参数、验证新工艺可行性、优化热输入等'
      },
      reference_standard: {
        label: '参考标准',
        type: 'select',
        options: ['AWS D1.1', 'ASME IX', 'EN ISO 15614-1', 'GB/T 15169', 'GB/T 19869']
      },
      welding_process: {
        label: '焊接方法',
        type: 'select',
        options: ['111-手工电弧焊', '114-药芯焊丝电弧焊', '121-埋弧焊', '131-MIG焊', '135-MAG焊', '141-TIG焊', '15-等离子弧焊'],
        required: true
      },
      welder_name: {
        label: '焊工姓名',
        type: 'text'
      },
      project_name: {
        label: '项目名称',
        type: 'text',
        placeholder: '关联的项目或产品'
      }
    }
  },

  // ==================== 2. 试验方案 ====================
  {
    id: 'ppqr_test_plan',
    name: '试验方案',
    description: 'pPQR的试验方案和参数设计',
    icon: 'ProjectOutlined',
    category: 'basic',
    repeatable: false,
    fields: {
      test_variables: {
        label: '试验变量',
        type: 'textarea',
        required: true,
        placeholder: '如：焊接电流(120-160A)、焊接速度(150-250mm/min)、预热温度(100-150°C)'
      },
      number_of_specimens: {
        label: '试样数量',
        type: 'number',
        min: 1,
        placeholder: '计划制作的试样数量'
      },
      test_matrix: {
        label: '试验矩阵',
        type: 'textarea',
        placeholder: '描述不同参数组合的试验方案'
      },
      expected_outcome: {
        label: '预期结果',
        type: 'textarea',
        placeholder: '描述试验的预期目标和成功标准'
      },
      risk_assessment: {
        label: '风险评估',
        type: 'textarea',
        placeholder: '可能的风险和应对措施'
      }
    }
  },

  // ==================== 3. 材料信息 ====================
  {
    id: 'ppqr_materials',
    name: '材料信息',
    description: 'pPQR试验使用的材料',
    icon: 'BlockOutlined',
    category: 'materials',
    repeatable: false,
    fields: {
      base_material_spec: {
        label: '母材规格',
        type: 'text',
        placeholder: '如：GB/T 713 Q345R'
      },
      base_material_grade: {
        label: '母材牌号',
        type: 'text',
        placeholder: '如：Q345R'
      },
      thickness: {
        label: '板厚',
        type: 'number',
        unit: 'mm',
        min: 0
      },
      filler_metal_spec: {
        label: '焊材规格',
        type: 'text',
        placeholder: '如：AWS A5.1 E7018'
      },
      filler_metal_classification: {
        label: '焊材型号',
        type: 'text',
        placeholder: '如：E7018'
      },
      diameter: {
        label: '焊材直径',
        type: 'number',
        unit: 'mm',
        min: 0
      },
      shielding_gas_type: {
        label: '保护气体类型',
        type: 'select',
        options: ['Ar', 'CO2', 'Ar+CO2', 'Ar+O2', 'He', 'He+Ar', '无']
      },
      gas_composition: {
        label: '气体成分',
        type: 'text',
        placeholder: '如：Ar 80% + CO2 20%'
      }
    }
  },

  // ==================== 4. 参数对比组 ====================
  {
    id: 'ppqr_parameter_group',
    name: '参数对比组',
    description: 'pPQR的参数对比组，可添加多组进行对比',
    icon: 'BarChartOutlined',
    category: 'parameters',
    repeatable: true,  // 可重复，支持多组参数对比
    fields: {
      group_name: {
        label: '组名',
        type: 'text',
        required: true,
        placeholder: '如：组1-低热输入、组2-中热输入、组3-高热输入'
      },
      current: {
        label: '焊接电流',
        type: 'number',
        unit: 'A',
        min: 0,
        required: true
      },
      voltage: {
        label: '焊接电压',
        type: 'number',
        unit: 'V',
        min: 0,
        required: true
      },
      travel_speed: {
        label: '焊接速度',
        type: 'number',
        unit: 'mm/min',
        min: 0
      },
      heat_input: {
        label: '热输入',
        type: 'number',
        unit: 'kJ/mm',
        min: 0,
        readonly: true,
        placeholder: '自动计算'
      },
      preheat_temp: {
        label: '预热温度',
        type: 'number',
        unit: '°C',
        min: 0
      },
      interpass_temp: {
        label: '层间温度',
        type: 'number',
        unit: '°C',
        min: 0
      },
      polarity: {
        label: '极性',
        type: 'select',
        options: ['DCEP(直流正接)', 'DCEN(直流反接)', 'AC(交流)']
      },
      wire_feed_speed: {
        label: '送丝速度',
        type: 'number',
        unit: 'm/min',
        min: 0
      },
      gas_flow_rate: {
        label: '气体流量',
        type: 'number',
        unit: 'L/min',
        min: 0
      },
      notes: {
        label: '备注',
        type: 'textarea',
        placeholder: '记录特殊情况或观察'
      }
    }
  },

  // ==================== 5. 外观检查 ====================
  {
    id: 'ppqr_visual_inspection',
    name: '外观检查',
    description: 'pPQR试样的外观检查结果',
    icon: 'EyeOutlined',
    category: 'tests',
    repeatable: false,
    fields: {
      weld_appearance: {
        label: '焊缝外观',
        type: 'select',
        options: ['优秀', '良好', '一般', '差'],
        required: true
      },
      surface_defects: {
        label: '表面缺陷',
        type: 'textarea',
        placeholder: '描述裂纹、气孔、夹渣、咬边等缺陷'
      },
      weld_profile: {
        label: '焊缝成形',
        type: 'select',
        options: ['均匀', '不均匀', '凹陷', '凸起']
      },
      spatter_level: {
        label: '飞溅程度',
        type: 'select',
        options: ['无', '轻微', '中等', '严重']
      },
      penetration_visual: {
        label: '熔透情况',
        type: 'select',
        options: ['完全熔透', '部分熔透', '未熔透', '未知']
      },
      overall_rating: {
        label: '综合评价',
        type: 'select',
        options: ['优秀', '良好', '合格', '不合格'],
        required: true
      },
      photos: {
        label: '照片',
        type: 'file',
        placeholder: '上传焊缝照片'
      }
    }
  },

  // ==================== 6. 简易力学测试 ====================
  {
    id: 'ppqr_mechanical_test',
    name: '简易力学测试',
    description: 'pPQR的简易力学性能测试',
    icon: 'ExperimentOutlined',
    category: 'tests',
    repeatable: true,
    fields: {
      test_type: {
        label: '测试类型',
        type: 'select',
        options: ['弯曲试验', '拉伸试验', '硬度测试', '冲击试验', '其他'],
        required: true
      },
      specimen_id: {
        label: '试样编号',
        type: 'text'
      },
      test_result: {
        label: '测试结果',
        type: 'textarea',
        required: true,
        placeholder: '描述测试结果和数据'
      },
      pass_fail: {
        label: '是否通过',
        type: 'select',
        options: ['通过', '未通过', '待定'],
        required: true
      }
    }
  },

  // ==================== 7. 参数对比分析 ====================
  {
    id: 'ppqr_comparison_analysis',
    name: '参数对比分析',
    description: 'pPQR各参数组的对比分析',
    icon: 'LineChartOutlined',
    category: 'analysis',
    repeatable: false,
    fields: {
      best_parameter_group: {
        label: '最佳参数组',
        type: 'text',
        required: true,
        placeholder: '如：组2-中热输入'
      },
      comparison_summary: {
        label: '对比总结',
        type: 'textarea',
        required: true,
        placeholder: '总结各组参数的优缺点和对比结果'
      },
      key_findings: {
        label: '关键发现',
        type: 'textarea',
        placeholder: '记录重要的发现和规律'
      },
      parameter_recommendations: {
        label: '参数建议',
        type: 'textarea',
        placeholder: '基于试验结果的参数建议'
      },
      charts_data: {
        label: '图表数据',
        type: 'textarea',
        placeholder: '用于生成对比图表的数据'
      }
    }
  },

  // ==================== 8. 试验评价 ====================
  {
    id: 'ppqr_evaluation',
    name: '试验评价',
    description: 'pPQR的整体评价和结论',
    icon: 'CheckCircleOutlined',
    category: 'evaluation',
    repeatable: false,
    fields: {
      test_conclusion: {
        label: '试验结论',
        type: 'textarea',
        required: true,
        placeholder: '总结试验的主要结论'
      },
      objectives_met: {
        label: '目标达成情况',
        type: 'select',
        options: ['完全达成', '部分达成', '未达成'],
        required: true
      },
      recommended_parameters: {
        label: '推荐参数',
        type: 'textarea',
        required: true,
        placeholder: '基于试验结果推荐的最佳参数'
      },
      next_steps: {
        label: '后续步骤',
        type: 'textarea',
        placeholder: '如：进行正式PQR、调整参数再试验等'
      },
      lessons_learned: {
        label: '经验教训',
        type: 'textarea',
        placeholder: '记录试验过程中的经验和教训'
      },
      evaluator_name: {
        label: '评价人',
        type: 'text'
      },
      evaluation_date: {
        label: '评价日期',
        type: 'date'
      },
      approval_status: {
        label: '批准状态',
        type: 'select',
        options: ['待批准', '已批准', '需修改', '已拒绝']
      }
    }
  }
]

/**
 * 根据ID获取pPQR模块
 */
export const getPPQRModuleById = (moduleId: string): FieldModule | undefined => {
  return PPQR_PRESET_MODULES.find(module => module.id === moduleId)
}

/**
 * 获取所有pPQR模块
 */
export const getAllPPQRModules = (): FieldModule[] => {
  return PPQR_PRESET_MODULES
}

/**
 * 根据分类获取pPQR模块
 */
export const getPPQRModulesByCategory = (category: string): FieldModule[] => {
  return PPQR_PRESET_MODULES.filter(module => module.category === category)
}

