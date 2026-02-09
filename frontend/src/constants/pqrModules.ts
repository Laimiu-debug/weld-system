/**
 * PQR预设字段模块库
 * 定义所有可用的PQR字段模块
 */
import { FieldModule } from '@/types/wpsModules'

/**
 * PQR预设模块库
 */
export const PQR_PRESET_MODULES: FieldModule[] = [
  // ==================== 1. PQR基本信息 ====================
  {
    id: 'pqr_basic_info',
    name: 'PQR基本信息',
    description: 'PQR的基本识别信息和评定标准',
    icon: 'FileTextOutlined',
    category: 'basic',
    repeatable: false,
    fields: {
      pqr_number: {
        label: 'PQR编号',
        type: 'text',
        required: true,
        placeholder: '如：PQR-2024-001'
      },
      title: {
        label: 'PQR标题',
        type: 'text',
        required: true,
        placeholder: '如：Q345R钢板对接焊PQR'
      },
      test_date: {
        label: '试验日期',
        type: 'date',
        required: true
      },
      standard: {
        label: '评定标准',
        type: 'select',
        options: ['AWS D1.1', 'ASME IX', 'EN ISO 15614-1', 'GB/T 15169', 'GB/T 19869'],
        required: true
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
      welder_certificate: {
        label: '焊工证书号',
        type: 'text'
      }
    }
  },

  // ==================== 2. 母材信息 ====================
  {
    id: 'pqr_base_material',
    name: '母材信息',
    description: 'PQR试验使用的母材信息',
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
      p_number: {
        label: 'P-Number',
        type: 'text',
        placeholder: 'ASME分组号'
      },
      group_number: {
        label: 'Group Number',
        type: 'text',
        placeholder: 'ASME组号'
      }
    }
  },

  // ==================== 3. 填充金属信息 ====================
  {
    id: 'pqr_filler_material',
    name: '填充金属',
    description: 'PQR试验使用的焊接材料',
    icon: 'GoldOutlined',
    category: 'materials',
    repeatable: false,
    fields: {
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
      f_number: {
        label: 'F-Number',
        type: 'text',
        placeholder: 'ASME焊材分组号'
      },
      a_number: {
        label: 'A-Number',
        type: 'text',
        placeholder: 'ASME焊缝金属分析分组号'
      },
      batch_number: {
        label: '批号',
        type: 'text'
      }
    }
  },

  // ==================== 4. 保护气体 ====================
  {
    id: 'pqr_shielding_gas',
    name: '保护气体',
    description: '气体保护焊使用的保护气体',
    icon: 'CloudOutlined',
    category: 'materials',
    repeatable: false,
    fields: {
      shielding_gas_type: {
        label: '保护气体类型',
        type: 'select',
        options: ['Ar', 'CO2', 'Ar+CO2', 'Ar+O2', 'He', 'He+Ar']
      },
      gas_composition: {
        label: '气体成分',
        type: 'text',
        placeholder: '如：Ar 80% + CO2 20%'
      },
      flow_rate: {
        label: '气体流量',
        type: 'number',
        unit: 'L/min',
        min: 0
      },
      backing_gas: {
        label: '背面保护气体',
        type: 'select',
        options: ['无', 'Ar', 'N2', 'Ar+N2']
      },
      backing_gas_flow_rate: {
        label: '背面气体流量',
        type: 'number',
        unit: 'L/min',
        min: 0
      }
    }
  },

  // ==================== 5. 焊接参数 ====================
  {
    id: 'pqr_welding_parameters',
    name: '焊接参数',
    description: 'PQR试验的实际焊接参数（测量值）',
    icon: 'ThunderboltOutlined',
    category: 'parameters',
    repeatable: true,  // 可重复，支持多道次
    fields: {
      pass_number: {
        label: '焊道序号',
        type: 'text',
        placeholder: '如：1, 2, 3或根部、填充、盖面'
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
        placeholder: '自动计算：(电流×电压×60)/(速度×1000)'
      },
      polarity: {
        label: '极性',
        type: 'select',
        options: ['DCEP(直流正接)', 'DCEN(直流反接)', 'AC(交流)']
      }
    }
  },

  // ==================== 6. 温度控制 ====================
  {
    id: 'pqr_temperature_control',
    name: '温度控制',
    description: '预热温度和层间温度控制',
    icon: 'FireOutlined',
    category: 'parameters',
    repeatable: false,
    fields: {
      preheat_temp_min: {
        label: '最低预热温度',
        type: 'number',
        unit: '°C',
        min: 0
      },
      preheat_temp_actual: {
        label: '实际预热温度',
        type: 'number',
        unit: '°C',
        min: 0
      },
      interpass_temp_max: {
        label: '最高层间温度',
        type: 'number',
        unit: '°C',
        min: 0
      },
      interpass_temp_actual: {
        label: '实际层间温度',
        type: 'number',
        unit: '°C',
        min: 0
      },
      pwht_required: {
        label: '是否需要焊后热处理',
        type: 'select',
        options: ['是', '否']
      },
      pwht_temperature: {
        label: '焊后热处理温度',
        type: 'number',
        unit: '°C',
        min: 0
      },
      pwht_holding_time: {
        label: '焊后热处理保温时间',
        type: 'number',
        unit: 'min',
        min: 0
      }
    }
  },

  // ==================== 7. 拉伸试验 ====================
  {
    id: 'pqr_tensile_test',
    name: '拉伸试验',
    description: '焊接接头拉伸试验结果',
    icon: 'ArrowsAltOutlined',
    category: 'tests',
    repeatable: true,  // 可重复，支持多个试样
    fields: {
      specimen_number: {
        label: '试样编号',
        type: 'text',
        placeholder: '如：T-1, T-2'
      },
      specimen_type: {
        label: '试样类型',
        type: 'select',
        options: ['全截面', '板状', '圆棒状']
      },
      width: {
        label: '试样宽度',
        type: 'number',
        unit: 'mm',
        min: 0
      },
      thickness: {
        label: '试样厚度',
        type: 'number',
        unit: 'mm',
        min: 0
      },
      cross_section_area: {
        label: '横截面积',
        type: 'number',
        unit: 'mm²',
        min: 0
      },
      ultimate_load: {
        label: '最大载荷',
        type: 'number',
        unit: 'kN',
        min: 0
      },
      tensile_strength: {
        label: '抗拉强度',
        type: 'number',
        unit: 'MPa',
        min: 0,
        required: true
      },
      fracture_location: {
        label: '断裂位置',
        type: 'select',
        options: ['母材', '焊缝', '热影响区', '熔合线']
      },
      acceptance_criteria: {
        label: '验收标准',
        type: 'text',
        placeholder: '如：≥400 MPa'
      },
      result: {
        label: '试验结果',
        type: 'select',
        options: ['合格', '不合格'],
        required: true
      }
    }
  },

  // ==================== 8. 弯曲试验 ====================
  {
    id: 'pqr_bend_test',
    name: '弯曲试验',
    description: '焊接接头弯曲试验结果',
    icon: 'BranchesOutlined',
    category: 'tests',
    repeatable: true,
    fields: {
      specimen_number: {
        label: '试样编号',
        type: 'text',
        placeholder: '如：B-1, B-2'
      },
      bend_type: {
        label: '弯曲类型',
        type: 'select',
        options: ['面弯', '背弯', '侧弯', '纵向弯曲'],
        required: true
      },
      bend_angle: {
        label: '弯曲角度',
        type: 'number',
        unit: '°',
        min: 0,
        default: 180
      },
      mandrel_diameter: {
        label: '弯心直径',
        type: 'number',
        unit: 'mm',
        min: 0
      },
      defect_description: {
        label: '缺陷描述',
        type: 'textarea',
        placeholder: '描述裂纹、气孔等缺陷'
      },
      max_defect_size: {
        label: '最大缺陷尺寸',
        type: 'number',
        unit: 'mm',
        min: 0
      },
      acceptance_criteria: {
        label: '验收标准',
        type: 'text',
        placeholder: '如：无大于3mm的裂纹'
      },
      result: {
        label: '试验结果',
        type: 'select',
        options: ['合格', '不合格'],
        required: true
      }
    }
  },

  // ==================== 9. 冲击试验 ====================
  {
    id: 'pqr_impact_test',
    name: '冲击试验',
    description: '焊接接头冲击试验结果',
    icon: 'ThunderboltOutlined',
    category: 'tests',
    repeatable: true,
    fields: {
      specimen_number: {
        label: '试样编号',
        type: 'text',
        placeholder: '如：I-1, I-2'
      },
      test_temperature: {
        label: '试验温度',
        type: 'number',
        unit: '°C',
        required: true
      },
      notch_location: {
        label: '缺口位置',
        type: 'select',
        options: ['焊缝中心', '熔合线', '热影响区', '母材'],
        required: true
      },
      notch_type: {
        label: '缺口类型',
        type: 'select',
        options: ['V型', 'U型']
      },
      impact_energy: {
        label: '冲击吸收能量',
        type: 'number',
        unit: 'J',
        min: 0,
        required: true
      },
      lateral_expansion: {
        label: '侧膨胀',
        type: 'number',
        unit: 'mm',
        min: 0
      },
      shear_area: {
        label: '剪切面积',
        type: 'number',
        unit: '%',
        min: 0,
        max: 100
      },
      acceptance_criteria: {
        label: '验收标准',
        type: 'text',
        placeholder: '如：≥27J'
      },
      result: {
        label: '试验结果',
        type: 'select',
        options: ['合格', '不合格'],
        required: true
      }
    }
  },

  // ==================== 10. 硬度试验 ====================
  {
    id: 'pqr_hardness_test',
    name: '硬度试验',
    description: '焊接接头硬度试验结果',
    icon: 'DashboardOutlined',
    category: 'tests',
    repeatable: false,
    fields: {
      test_method: {
        label: '试验方法',
        type: 'select',
        options: ['维氏(HV)', '布氏(HB)', '洛氏(HRC)'],
        required: true
      },
      test_load: {
        label: '试验载荷',
        type: 'text',
        placeholder: '如：10kg, 100kg'
      },
      weld_metal_hardness: {
        label: '焊缝金属硬度',
        type: 'text',
        placeholder: '如：180-200 HV10'
      },
      haz_hardness: {
        label: '热影响区硬度',
        type: 'text',
        placeholder: '如：190-210 HV10'
      },
      base_metal_hardness: {
        label: '母材硬度',
        type: 'text',
        placeholder: '如：150-170 HV10'
      },
      max_hardness: {
        label: '最大硬度值',
        type: 'number',
        min: 0
      },
      acceptance_criteria: {
        label: '验收标准',
        type: 'text',
        placeholder: '如：≤350 HV10'
      },
      result: {
        label: '试验结果',
        type: 'select',
        options: ['合格', '不合格'],
        required: true
      }
    }
  },

  // ==================== 11. 宏观检验 ====================
  {
    id: 'pqr_macro_examination',
    name: '宏观检验',
    description: '焊接接头宏观金相检验',
    icon: 'EyeOutlined',
    category: 'tests',
    repeatable: false,
    fields: {
      specimen_number: {
        label: '试样编号',
        type: 'text'
      },
      etching_reagent: {
        label: '浸蚀剂',
        type: 'text',
        placeholder: '如：5%硝酸酒精'
      },
      weld_appearance: {
        label: '焊缝外观',
        type: 'textarea',
        placeholder: '描述焊缝成形、表面质量等'
      },
      penetration: {
        label: '熔透情况',
        type: 'select',
        options: ['完全熔透', '部分熔透', '未熔透']
      },
      fusion_quality: {
        label: '熔合质量',
        type: 'select',
        options: ['良好', '一般', '差']
      },
      defects_found: {
        label: '发现的缺陷',
        type: 'textarea',
        placeholder: '描述裂纹、气孔、夹渣等缺陷'
      },
      result: {
        label: '检验结果',
        type: 'select',
        options: ['合格', '不合格'],
        required: true
      }
    }
  },

  // ==================== 12. 射线检测 ====================
  {
    id: 'pqr_radiographic_test',
    name: '射线检测(RT)',
    description: '焊接接头射线检测',
    icon: 'RadarChartOutlined',
    category: 'tests',
    repeatable: false,
    fields: {
      test_standard: {
        label: '检测标准',
        type: 'select',
        options: ['GB/T 3323', 'ASME V', 'ISO 17636', 'EN 1435']
      },
      radiation_source: {
        label: '射线源',
        type: 'select',
        options: ['X射线', 'γ射线(Ir-192)', 'γ射线(Co-60)', 'γ射线(Se-75)']
      },
      film_type: {
        label: '胶片类型',
        type: 'text'
      },
      sensitivity: {
        label: '灵敏度',
        type: 'text',
        placeholder: '如：1-2T'
      },
      defects_found: {
        label: '发现的缺陷',
        type: 'textarea',
        placeholder: '描述缺陷类型、位置、尺寸'
      },
      quality_level: {
        label: '质量等级',
        type: 'select',
        options: ['I级', 'II级', 'III级', 'IV级']
      },
      result: {
        label: '检测结果',
        type: 'select',
        options: ['合格', '不合格'],
        required: true
      }
    }
  },

  // ==================== 13. 超声检测 ====================
  {
    id: 'pqr_ultrasonic_test',
    name: '超声检测(UT)',
    description: '焊接接头超声检测',
    icon: 'SoundOutlined',
    category: 'tests',
    repeatable: false,
    fields: {
      test_standard: {
        label: '检测标准',
        type: 'select',
        options: ['GB/T 11345', 'ASME V', 'ISO 17640', 'EN 1714']
      },
      probe_type: {
        label: '探头类型',
        type: 'text',
        placeholder: '如：2.5MHz 70°'
      },
      coupling_medium: {
        label: '耦合剂',
        type: 'text',
        placeholder: '如：机油、甘油'
      },
      reference_block: {
        label: '对比试块',
        type: 'text'
      },
      defects_found: {
        label: '发现的缺陷',
        type: 'textarea',
        placeholder: '描述缺陷类型、位置、当量'
      },
      quality_level: {
        label: '质量等级',
        type: 'select',
        options: ['I级', 'II级', 'III级', 'IV级']
      },
      result: {
        label: '检测结果',
        type: 'select',
        options: ['合格', '不合格'],
        required: true
      }
    }
  },

  // ==================== 14. 合格判定 ====================
  {
    id: 'pqr_qualification',
    name: '合格判定',
    description: 'PQR的最终合格判定和审批信息',
    icon: 'CheckCircleOutlined',
    category: 'approval',
    repeatable: false,
    fields: {
      qualification_result: {
        label: '评定结果',
        type: 'select',
        options: ['合格', '不合格', '有条件合格'],
        required: true
      },
      qualification_date: {
        label: '评定日期',
        type: 'date'
      },
      qualified_by: {
        label: '评定人',
        type: 'text'
      },
      qualified_by_title: {
        label: '评定人职称',
        type: 'text',
        placeholder: '如：焊接工程师'
      },
      approved_by: {
        label: '批准人',
        type: 'text'
      },
      approved_date: {
        label: '批准日期',
        type: 'date'
      },
      failure_reason: {
        label: '不合格原因',
        type: 'textarea',
        placeholder: '如果不合格，请说明原因'
      },
      corrective_action: {
        label: '纠正措施',
        type: 'textarea',
        placeholder: '针对不合格项的改进措施'
      },
      applicable_wps: {
        label: '适用的WPS编号',
        type: 'text',
        placeholder: '如：WPS-001, WPS-002'
      },
      validity_period: {
        label: '有效期',
        type: 'text',
        placeholder: '如：长期有效、2年'
      },
      remarks: {
        label: '备注',
        type: 'textarea'
      }
    }
  }
]

/**
 * 根据ID获取PQR模块定义
 */
export const getPQRModuleById = (moduleId: string): FieldModule | undefined => {
  return PQR_PRESET_MODULES.find(m => m.id === moduleId)
}

/**
 * 获取所有PQR模块
 */
export const getAllPQRModules = (): FieldModule[] => {
  return PQR_PRESET_MODULES
}

/**
 * 按分类获取PQR模块
 */
export const getPQRModulesByCategory = (category: string): FieldModule[] => {
  return PQR_PRESET_MODULES.filter(m => m.category === category)
}

