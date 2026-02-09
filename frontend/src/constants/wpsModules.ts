/**
 * WPS预设字段模块库
 * 定义所有可用的字段模块
 */
import { FieldModule } from '@/types/wpsModules'
import { getPQRModuleById } from './pqrModules'
import { getPPQRModuleById } from './ppqrModules'

/**
 * 预设模块库
 */
export const PRESET_MODULES: FieldModule[] = [
  // ==================== 占位符模块 ====================
  {
    id: 'placeholder',
    name: '占位符',
    description: '临时占位，请拖拽模块替换或删除',
    icon: 'PlusOutlined',
    category: 'basic',
    repeatable: true,
    fields: {
      placeholder: {
        label: '占位符',
        type: 'text',
        placeholder: '请从左侧拖拽模块替换此占位符',
        readonly: true,
      },
    },
  },

  // ==================== 基本信息模块 ====================
  {
    id: 'basic_info',
    name: '基本信息',
    description: '焊接工艺、道次、焊道编号等基本信息',
    icon: 'InfoCircleOutlined',
    category: 'basic',
    repeatable: true,  // 可重复，用于多层多道焊
    fields: {
      welding_process: {
        label: '焊接工艺',
        type: 'select',
        options: ['111', '114', '121', '135', '141', '15', '311'],
        required: true,
      },
      welding_method_type: {
        label: '焊接方法类型',
        type: 'text',
      },
      pass_number: {
        label: '焊接道次',
        type: 'number',
        min: 1,
      },
      layer_id: {
        label: '焊道ID',
        type: 'text',
      },
      groove_thickness: {
        label: '熔覆金属坡口焊缝厚度',
        type: 'number',
        unit: 'mm',
        min: 0,
      },
    },
  },

  // ==================== 填充金属模块 ====================
  {
    id: 'filler_metal',
    name: '填充金属',
    description: '填充金属的型号、直径、制造商等信息',
    icon: 'BuildOutlined',
    category: 'material',
    repeatable: true,
    fields: {
      filler_metal_type: {
        label: '填充金属型号',
        type: 'text',
        placeholder: '例如：ER70S-6',
      },
      filler_metal_diameter: {
        label: '填充金属直径',
        type: 'number',
        unit: 'mm',
        min: 0,
      },
      filler_metal_manufacturer: {
        label: '填充金属制造商',
        type: 'text',
      },
      filler_metal_brand: {
        label: '填充金属商标名',
        type: 'text',
      },
    },
  },

  // ==================== 电极处理模块 ====================
  {
    id: 'electrode_treatment',
    name: '电极处理',
    description: '电极二次烘干温度和时间',
    icon: 'FireOutlined',
    category: 'material',
    repeatable: false,
    fields: {
      electrode_redry_temp: {
        label: '电极二次烘干温度',
        type: 'number',
        unit: '°C',
        min: 0,
      },
      electrode_redry_time: {
        label: '电极二次烘干时间',
        type: 'number',
        unit: 'h',
        min: 0,
      },
    },
  },

  // ==================== 保护气体模块 ====================
  {
    id: 'shielding_gas',
    name: '保护气体',
    description: '保护气体的名称、流量、时间等参数',
    icon: 'CloudOutlined',
    category: 'gas',
    repeatable: false,
    fields: {
      shielding_gas_name: {
        label: '保护气体名称',
        type: 'select',
        options: ['Ar', 'CO2', 'Ar+CO2', 'He', 'N2'],
      },
      shielding_gas_flow: {
        label: '保护气体流量',
        type: 'number',
        unit: 'L/min',
        min: 0,
      },
      shielding_gas_pretime: {
        label: '保护气体预送气时间',
        type: 'number',
        unit: 's',
        min: 0,
      },
      shielding_gas_posttime: {
        label: '保护气体延迟送气时间',
        type: 'number',
        unit: 's',
        min: 0,
      },
      shielding_gas_brand: {
        label: '保护气体商标名',
        type: 'text',
      },
      shielding_gas_manufacturer: {
        label: '保护气体制造商',
        type: 'text',
      },
    },
  },

  // ==================== 背部保护气模块 ====================
  {
    id: 'backing_gas',
    name: '背部保护气',
    description: '背部保护气体的参数',
    icon: 'CloudServerOutlined',
    category: 'gas',
    repeatable: false,
    fields: {
      backing_gas_name: {
        label: '背部保护气名称',
        type: 'select',
        options: ['Ar', 'CO2', 'Ar+CO2', 'He', 'N2'],
      },
      backing_gas_flow: {
        label: '背部保护气流量',
        type: 'number',
        unit: 'L/min',
        min: 0,
      },
      backing_gas_pretime: {
        label: '背部保护气预送气时间',
        type: 'number',
        unit: 's',
        min: 0,
      },
      backing_gas_posttime: {
        label: '背部保护气延迟送气时间',
        type: 'number',
        unit: 's',
        min: 0,
      },
      backing_gas_brand: {
        label: '背部保护气商标名',
        type: 'text',
      },
      backing_gas_manufacturer: {
        label: '背部保护气制造商',
        type: 'text',
      },
    },
  },

  // ==================== 等离子气模块 ====================
  {
    id: 'plasma_gas',
    name: '等离子气',
    description: '等离子气体的参数（用于等离子焊）',
    icon: 'ThunderboltOutlined',
    category: 'gas',
    repeatable: false,
    fields: {
      plasma_gas_name: {
        label: '等离子气名称',
        type: 'select',
        options: ['Ar', 'He', 'Ar+H2'],
      },
      plasma_gas_flow: {
        label: '等离子气流量',
        type: 'number',
        unit: 'L/min',
        min: 0,
      },
      plasma_gas_brand: {
        label: '等离子气商标名',
        type: 'text',
      },
      plasma_gas_manufacturer: {
        label: '等离子气制造商',
        type: 'text',
      },
    },
  },

  // ==================== 电流电压模块 ====================
  {
    id: 'current_voltage',
    name: '电流电压',
    description: '电流种类、电流、电压等电气参数',
    icon: 'BoltOutlined',
    category: 'electrical',
    repeatable: true,
    fields: {
      current_type: {
        label: '电流种类与极性',
        type: 'select',
        options: ['AC', 'DCEP', 'DCEN'],
      },
      current: {
        label: '电流',
        type: 'text',
        placeholder: '例如：100-150A',
      },
      voltage: {
        label: '焊接电压',
        type: 'text',
        placeholder: '例如：20-25V',
      },
    },
  },

  // ==================== 电流脉冲模块 ====================
  {
    id: 'current_pulse',
    name: '电流脉冲',
    description: '脉冲电流参数（用于TIG焊等）',
    icon: 'LineChartOutlined',
    category: 'electrical',
    repeatable: false,
    fields: {
      current_pulse: {
        label: '电流脉冲',
        type: 'select',
        options: ['none', 'pulsed'],
      },
      start_current: {
        label: '启动电流',
        type: 'number',
        unit: 'A',
        min: 0,
      },
      current_ramp_up: {
        label: '焊接电流增加',
        type: 'number',
        unit: 'A/s',
        min: 0,
      },
      base_current: {
        label: '基值电流',
        type: 'number',
        unit: 'A',
        min: 0,
      },
      current_ramp_down: {
        label: '焊接电流衰减',
        type: 'number',
        unit: 'A/s',
        min: 0,
      },
      final_current: {
        label: '末级电流',
        type: 'number',
        unit: 'A',
        min: 0,
      },
    },
  },

  // ==================== 焊接速度模块 ====================
  {
    id: 'welding_speed',
    name: '焊接速度',
    description: '焊接速度、倾斜角度等运动参数',
    icon: 'DashboardOutlined',
    category: 'motion',
    repeatable: true,
    fields: {
      travel_speed: {
        label: '焊接速度',
        type: 'text',
        placeholder: '例如：10-15 cm/min',
      },
      angle: {
        label: '倾斜角度',
        type: 'number',
        unit: '°',
        min: 0,
        max: 90,
      },
    },
  },

  // ==================== 送丝速度模块 ====================
  {
    id: 'wire_feed',
    name: '送丝速度',
    description: '送丝速度、材料过渡等参数（用于TIG焊等）',
    icon: 'ArrowRightOutlined',
    category: 'motion',
    repeatable: false,
    fields: {
      wire_feed_speed: {
        label: '送丝速度',
        type: 'text',
        placeholder: '例如：5-8 m/min',
      },
      transfer_mode: {
        label: '材料过渡',
        type: 'select',
        options: ['Short arc', 'Spray arc', 'Pulsed arc'],
      },
      contact_tip_distance: {
        label: '焊嘴间距',
        type: 'number',
        unit: 'mm',
        min: 0,
      },
    },
  },

  // ==================== 抖动参数模块 ====================
  {
    id: 'oscillation',
    name: '抖动参数',
    description: '抖动宽度、频率、停留时间',
    icon: 'SwapOutlined',
    category: 'motion',
    repeatable: false,
    fields: {
      oscillation_width: {
        label: '抖动宽度',
        type: 'number',
        unit: 'mm',
        min: 0,
      },
      oscillation_frequency: {
        label: '抖动频率',
        type: 'number',
        unit: 'Hz',
        min: 0,
      },
      oscillation_dwell: {
        label: '抖动停留时间',
        type: 'number',
        unit: 's',
        min: 0,
      },
    },
  },

  // ==================== 钨电极模块 ====================
  {
    id: 'tungsten_electrode',
    name: '钨电极',
    description: '钨电极型号、直径等参数（用于TIG焊）',
    icon: 'ToolOutlined',
    category: 'material',
    repeatable: false,
    fields: {
      tungsten_electrode_type: {
        label: '钨电极型号',
        type: 'select',
        options: ['WT20', 'WC20', 'WL15', 'WL20', 'WP'],
      },
      tungsten_electrode_diameter: {
        label: '钨电极直径',
        type: 'number',
        unit: 'mm',
        min: 0,
      },
      tungsten_electrode_manufacturer: {
        label: '钨电极制造商',
        type: 'text',
      },
      tungsten_electrode_brand: {
        label: '钨电极商标名',
        type: 'text',
      },
    },
  },

  // ==================== 喷嘴参数模块 ====================
  {
    id: 'nozzle',
    name: '喷嘴参数',
    description: '喷嘴尺寸等参数',
    icon: 'AimOutlined',
    category: 'equipment',
    repeatable: false,
    fields: {
      nozzle_size: {
        label: '喷嘴尺寸',
        type: 'number',
        unit: 'mm',
        min: 0,
      },
    },
  },

  // ==================== 焊接设备模块 ====================
  {
    id: 'welding_equipment',
    name: '焊接设备',
    description: '焊接设备制造商和名称',
    icon: 'SettingOutlined',
    category: 'equipment',
    repeatable: false,
    fields: {
      equipment_manufacturer: {
        label: '焊接设备制造商',
        type: 'text',
      },
      equipment_name: {
        label: '焊接设备名称',
        type: 'text',
      },
    },
  },

  // ==================== 预热参数模块 ====================
  {
    id: 'preheat_parameters',
    name: '预热参数',
    description: '预热温度、层间温度等参数',
    icon: 'FireOutlined',
    category: 'basic',
    repeatable: false,
    fields: {
      preheat_temp: {
        label: '预热温度',
        type: 'number',
        unit: '°C',
        min: 0,
      },
      interpass_temp: {
        label: '层间温度',
        type: 'number',
        unit: '°C',
        min: 0,
      },
      max_interpass_temp: {
        label: '最大层间温度',
        type: 'number',
        unit: '°C',
        min: 0,
      },
    },
  },

  // ==================== 热输入模块 ====================
  {
    id: 'heat_input',
    name: '热输入',
    description: '热输入计算值和用户输入值',
    icon: 'FireOutlined',
    category: 'calculation',
    repeatable: false,
    fields: {
      heat_input_calculated: {
        label: '热输入（系统计算）',
        type: 'number',
        unit: 'kJ/mm',
        readonly: true,
      },
      heat_input_manual: {
        label: '热输入（用户输入）',
        type: 'number',
        unit: 'kJ/mm',
        min: 0,
      },
    },
  },

  // ==================== 表头数据模块 ====================
  {
    id: 'header_data',
    name: '表头数据',
    description: 'WPS文档的表头信息，包括编号、版本、审批信息等',
    icon: 'FileTextOutlined',
    category: 'basic',
    repeatable: false,
    fields: {
      wps_number: {
        label: 'WPS编号',
        type: 'text',
        required: true,
        placeholder: '例如：WPS-001',
      },
      revision: {
        label: '版本',
        type: 'text',
        required: true,
        default: 'A',
      },
      title: {
        label: 'WPS标题',
        type: 'text',
        required: true,
      },
      manufacturer: {
        label: '制造商',
        type: 'text',
      },
      product_name: {
        label: '产品名称',
        type: 'text',
      },
      customer: {
        label: '用户',
        type: 'text',
      },
      location: {
        label: '地点',
        type: 'text',
      },
      order_number: {
        label: '订单编号',
        type: 'text',
      },
      part_number: {
        label: '部件编号',
        type: 'text',
      },
      drawing_number: {
        label: '图纸编号',
        type: 'text',
      },
      wpqr_number: {
        label: 'WPQR编号',
        type: 'text',
      },
      welder_qualification: {
        label: '焊工资质',
        type: 'text',
      },
      drafted_by: {
        label: '起草人',
        type: 'text',
      },
      drafted_date: {
        label: '起草日期',
        type: 'date',
      },
      reviewed_by: {
        label: '校验人',
        type: 'text',
      },
      reviewed_date: {
        label: '校验日期',
        type: 'date',
      },
      approved_by: {
        label: '批准人',
        type: 'text',
      },
      approved_date: {
        label: '批准日期',
        type: 'date',
      },
      notes: {
        label: '备注',
        type: 'textarea',
      },
      pdf_link: {
        label: 'PDF文件',
        type: 'file',
      },
    },
  },

  // ==================== 概要模块 ====================
  {
    id: 'summary_info',
    name: '概要信息',
    description: '焊接工艺的概要信息，包括母材、厚度、焊接位置等',
    icon: 'ProfileOutlined',
    category: 'basic',
    repeatable: false,
    fields: {
      backing_strip: {
        label: '背部衬垫',
        type: 'text',
      },
      base_material_1: {
        label: '母材1',
        type: 'text',
        required: true,
      },
      base_material_2: {
        label: '母材2',
        type: 'text',
      },
      thickness: {
        label: '厚度',
        type: 'number',
        unit: 'mm',
        min: 0,
      },
      outer_diameter: {
        label: '外径',
        type: 'number',
        unit: 'mm',
        min: 0,
      },
      weld_geometry: {
        label: '焊缝几何形状',
        type: 'select',
        options: ['对接焊', '角焊', '转角焊'],
      },
      weld_preparation: {
        label: '焊前准备',
        type: 'select',
        options: ['氧乙炔切割', '等离子切割', '机械加工'],
      },
      root_treatment: {
        label: '根焊道处理',
        type: 'select',
        options: ['无', '磨削', '挖槽'],
      },
      cleaning_method: {
        label: '清根方法',
        type: 'text',
      },
      preheat_temp: {
        label: '预热温度',
        type: 'text',
      },
      interpass_temp: {
        label: '层间温度',
        type: 'number',
        unit: '°C',
      },
      welding_position: {
        label: '焊接位置',
        type: 'select',
        options: ['PA', 'PB', 'PC', 'PD', 'PE', 'PF', 'PG'],
      },
      bead_shape: {
        label: '焊道形状',
        type: 'select',
        options: ['直焊道', '摆焊道'],
      },
      heat_treatment: {
        label: '热处理',
        type: 'select',
        options: ['无需', 'PWHT', '正火', '退火'],
      },
      hydrogen_removal: {
        label: '消氢退火',
        type: 'select',
        options: ['无', '需要'],
      },
    },
  },

  // ==================== 示意图模块 ====================
  {
    id: 'diagram_info',
    name: '示意图',
    description: '焊接接头的示意图和焊接顺序说明，支持上传或自动生成',
    icon: 'PictureOutlined',
    category: 'basic',
    repeatable: false,
    fields: {
      joint_diagram: {
        label: '接头示意图',
        type: 'image',  // 改为 image 类型以支持自动生成
        description: '支持上传图片或自动生成焊接接头示意图',
      },
      welding_sequence: {
        label: '焊接顺序',
        type: 'textarea',
      },
      dimensions: {
        label: '尺寸标注',
        type: 'textarea',
      },
    },
  },

  // ==================== 焊接接头示意图生成器 V4 ====================
  {
    id: 'weld_joint_diagram_v4',
    name: '焊接接头示意图生成器 V4',
    description: '参数化焊接坡口图形生成器，支持内外坡口、不同厚度板材、削边和三种对齐方式',
    icon: 'PictureOutlined',
    category: 'basic',
    repeatable: false,
    fields: {
      // 基本参数
      groove_type: {
        label: '坡口类型',
        type: 'select',
        options: [
          { label: 'V型坡口', value: 'V' },
          { label: 'X型坡口', value: 'X' },
          { label: 'U型坡口', value: 'U' },
          { label: 'I型坡口（方槽）', value: 'I' },
        ],
        defaultValue: 'V',
      },
      groove_position: {
        label: '坡口位置',
        type: 'select',
        options: [
          { label: '外坡口（从外侧开坡口）', value: 'outer' },
          { label: '内坡口（从内侧开坡口）', value: 'inner' },
        ],
        defaultValue: 'outer',
      },
      alignment: {
        label: '对齐方式',
        type: 'select',
        options: [
          { label: '中心线对齐', value: 'centerline' },
          { label: '外侧对齐（外表面齐平）', value: 'outer_flush' },
          { label: '内侧对齐（内表面齐平）', value: 'inner_flush' },
        ],
        defaultValue: 'centerline',
      },

      // 左侧板材参数
      left_thickness: {
        label: '左侧板厚 (mm)',
        type: 'number',
        defaultValue: 12,
        min: 1,
        max: 50,
      },
      left_groove_angle: {
        label: '左侧坡口角度 (°)',
        type: 'number',
        defaultValue: 30,
        min: 0,
        max: 60,
      },
      left_groove_depth: {
        label: '左侧坡口深度 (mm)',
        type: 'number',
        defaultValue: 10,
        min: 1,
        max: 50,
      },
      left_bevel: {
        label: '左侧启用削边',
        type: 'checkbox',
        defaultValue: false,
      },
      left_bevel_position: {
        label: '左侧削边位置',
        type: 'select',
        options: [
          { label: '外削边（板材外侧边界）', value: 'outer' },
          { label: '内削边（板材内侧边界）', value: 'inner' },
        ],
        defaultValue: 'outer',
        condition: { field: 'left_bevel', value: true },
        description: '削边位置在坡口起点处，外削边在板材外侧边界，内削边在板材内侧边界',
      },
      left_bevel_length: {
        label: '左侧削边长度 (mm)',
        type: 'number',
        defaultValue: 15,
        min: 1,
        max: 50,
        condition: { field: 'left_bevel', value: true },
      },
      left_bevel_height: {
        label: '左侧削边高度 (mm)',
        type: 'number',
        defaultValue: 2,
        min: 1,
        max: 10,
        condition: { field: 'left_bevel', value: true },
      },

      // 右侧板材参数
      right_thickness: {
        label: '右侧板厚 (mm)',
        type: 'number',
        defaultValue: 10,
        min: 1,
        max: 50,
      },
      right_groove_angle: {
        label: '右侧坡口角度 (°)',
        type: 'number',
        defaultValue: 30,
        min: 0,
        max: 60,
      },
      right_groove_depth: {
        label: '右侧坡口深度 (mm)',
        type: 'number',
        defaultValue: 8,
        min: 1,
        max: 50,
      },
      right_bevel: {
        label: '右侧启用削边',
        type: 'checkbox',
        defaultValue: false,
      },
      right_bevel_position: {
        label: '右侧削边位置',
        type: 'select',
        options: [
          { label: '外削边（板材外侧边界）', value: 'outer' },
          { label: '内削边（板材内侧边界）', value: 'inner' },
        ],
        defaultValue: 'outer',
        condition: { field: 'right_bevel', value: true },
        description: '削边位置在坡口起点处，外削边在板材外侧边界，内削边在板材内侧边界',
      },
      right_bevel_length: {
        label: '右侧削边长度 (mm)',
        type: 'number',
        defaultValue: 15,
        min: 1,
        max: 50,
        condition: { field: 'right_bevel', value: true },
      },
      right_bevel_height: {
        label: '右侧削边高度 (mm)',
        type: 'number',
        defaultValue: 2,
        min: 1,
        max: 10,
        condition: { field: 'right_bevel', value: true },
      },

      // 根部参数
      blunt_edge: {
        label: '钝边 (mm)',
        type: 'number',
        defaultValue: 2,
        min: 0,
        max: 10,
        step: 0.5,
      },
      root_gap: {
        label: '根部间隙 (mm)',
        type: 'number',
        defaultValue: 2,
        min: 0,
        max: 10,
        step: 0.5,
      },

      // 生成的图片
      generated_diagram: {
        label: '生成的示意图',
        type: 'image',
        description: '根据上述参数自动生成的焊接接头横截面示意图',
      },
    },
  },

  // ==================== 焊层模块 ====================
  {
    id: 'weld_layer',
    name: '焊层信息',
    description: '单层焊接的详细参数信息',
    icon: 'OrderedListOutlined',
    category: 'basic',
    repeatable: true,
    fields: {
      layer_id: {
        label: '焊层ID',
        type: 'text',
      },
      pass_number: {
        label: '焊接道次',
        type: 'number',
        min: 1,
      },
      welding_process: {
        label: '焊接工艺',
        type: 'select',
        options: ['111', '114', '121', '135', '141', '15', '311'],
        required: true,
      },
      filler_metal_type: {
        label: '填充金属型号',
        type: 'text',
      },
      filler_metal_diameter: {
        label: '填充金属直径',
        type: 'number',
        unit: 'mm',
      },
      shielding_gas: {
        label: '保护气体',
        type: 'text',
      },
      current_type: {
        label: '电流类型',
        type: 'select',
        options: ['DC+', 'DC-', 'AC'],
      },
      current_values: {
        label: '电流值',
        type: 'number',
        unit: 'A',
      },
      voltage: {
        label: '电压',
        type: 'number',
        unit: 'V',
      },
      transfer_mode: {
        label: '传输模式',
        type: 'text',
      },
      wire_feed_speed: {
        label: '送丝速度',
        type: 'number',
        unit: 'm/min',
      },
      travel_speed: {
        label: '焊接速度',
        type: 'number',
        unit: 'cm/min',
      },
      oscillation: {
        label: '抖动参数',
        type: 'text',
      },
      contact_tip_distance: {
        label: '接触尖端距离',
        type: 'number',
        unit: 'mm',
      },
      angle: {
        label: '焊枪角度',
        type: 'number',
        unit: '°',
      },
      equipment: {
        label: '设备',
        type: 'text',
      },
      heat_input: {
        label: '热输入',
        type: 'number',
        unit: 'kJ/mm',
      },
    },
  },

  // ==================== 技术图表模块 ====================
  {
    id: 'technical_diagrams',
    name: '技术图表',
    description: '坡口图、焊层焊道图等技术图表',
    icon: 'PictureOutlined',
    category: 'basic',
    repeatable: false,
    fields: {
      groove_diagram: {
        label: '坡口图',
        type: 'image',
        accept: 'image/*',
        placeholder: '上传坡口示意图',
      },
      weld_layer_diagram: {
        label: '焊层焊道图',
        type: 'image',
        accept: 'image/*',
        placeholder: '上传焊层焊道示意图',
      },
      other_diagrams: {
        label: '其他技术图表',
        type: 'file',
        accept: '.pdf,.png,.jpg,.jpeg,.svg',
        placeholder: '上传其他相关技术文档',
      },
    },
  },

  // ==================== 附加信息模块 ====================
  {
    id: 'additional_info',
    name: '附加信息',
    description: '其他补充信息和文件附件',
    icon: 'FileOutlined',
    category: 'basic',
    repeatable: false,
    fields: {
      additional_notes: {
        label: '附加备注',
        type: 'textarea',
      },
      supporting_documents: {
        label: '支持文件',
        type: 'text',
      },
      attachments: {
        label: '附件',
        type: 'file',
      },
    },
  },
]

/**
 * 预设模板定义
 * 基于模块组合的标准模板
 */
export interface PresetTemplate {
  id: string
  name: string
  description: string
  welding_process: string
  welding_process_name: string
  standard: string
  module_instances: Array<{
    instanceId: string
    moduleId: string
    order: number
    customName?: string
  }>
}

export const PRESET_TEMPLATES: PresetTemplate[] = [
  // ==================== SMAW 手工电弧焊标准模板 ====================
  {
    id: 'preset_smaw_standard',
    name: 'SMAW 手工电弧焊标准模板',
    description: '手工电弧焊（SMAW）的标准WPS模板，包含所有必要的信息模块',
    welding_process: '111',
    welding_process_name: '手工电弧焊',
    standard: 'EN ISO 15609-1',
    module_instances: [
      {
        instanceId: 'header_data_1',
        moduleId: 'header_data',
        order: 1,
        customName: '表头数据',
      },
      {
        instanceId: 'summary_info_1',
        moduleId: 'summary_info',
        order: 2,
        customName: '概要信息',
      },
      {
        instanceId: 'diagram_info_1',
        moduleId: 'diagram_info',
        order: 3,
        customName: '示意图',
      },
      {
        instanceId: 'weld_layer_1',
        moduleId: 'weld_layer',
        order: 4,
        customName: '焊层信息',
      },
      {
        instanceId: 'additional_info_1',
        moduleId: 'additional_info',
        order: 5,
        customName: '附加信息',
      },
    ],
  },

  // ==================== GMAW MAG焊标准模板 ====================
  {
    id: 'preset_gmaw_standard',
    name: 'GMAW MAG焊标准模板',
    description: 'MAG焊（熔化极活性气体保护焊）的标准WPS模板',
    welding_process: '135',
    welding_process_name: 'MAG焊（熔化极活性气体保护焊）',
    standard: 'EN ISO 15609-1',
    module_instances: [
      {
        instanceId: 'header_data_2',
        moduleId: 'header_data',
        order: 1,
        customName: '表头数据',
      },
      {
        instanceId: 'summary_info_2',
        moduleId: 'summary_info',
        order: 2,
        customName: '概要信息',
      },
      {
        instanceId: 'diagram_info_2',
        moduleId: 'diagram_info',
        order: 3,
        customName: '示意图',
      },
      {
        instanceId: 'weld_layer_2',
        moduleId: 'weld_layer',
        order: 4,
        customName: '焊层信息',
      },
      {
        instanceId: 'additional_info_2',
        moduleId: 'additional_info',
        order: 5,
        customName: '附加信息',
      },
    ],
  },

  // ==================== GTAW TIG焊标准模板 ====================
  {
    id: 'preset_gtaw_standard',
    name: 'GTAW TIG焊标准模板',
    description: 'TIG焊（钨极惰性气体保护焊）的标准WPS模板',
    welding_process: '141',
    welding_process_name: 'TIG焊（钨极惰性气体保护焊）',
    standard: 'EN ISO 15609-1',
    module_instances: [
      {
        instanceId: 'header_data_3',
        moduleId: 'header_data',
        order: 1,
        customName: '表头数据',
      },
      {
        instanceId: 'summary_info_3',
        moduleId: 'summary_info',
        order: 2,
        customName: '概要信息',
      },
      {
        instanceId: 'diagram_info_3',
        moduleId: 'diagram_info',
        order: 3,
        customName: '示意图',
      },
      {
        instanceId: 'weld_layer_3',
        moduleId: 'weld_layer',
        order: 4,
        customName: '焊层信息',
      },
      {
        instanceId: 'additional_info_3',
        moduleId: 'additional_info',
        order: 5,
        customName: '附加信息',
      },
    ],
  },
]

/**
 * 自定义模块缓存
 * 用于在模板画布中显示自定义模块的名称
 */
let customModulesCache: FieldModule[] = []

/**
 * 设置自定义模块缓存
 */
export const setCustomModulesCache = (modules: FieldModule[]) => {
  customModulesCache = modules
}

/**
 * 获取自定义模块缓存
 */
export const getCustomModulesCache = (): FieldModule[] => {
  return customModulesCache
}

/**
 * 根据ID获取模块定义
 * 支持预设模块和自定义模块
 */
export const getModuleById = (moduleId: string): FieldModule | undefined => {
  // 先从预设模块中查找
  const presetModule = PRESET_MODULES.find(m => m.id === moduleId)
  if (presetModule) {
    return presetModule
  }

  // 再从自定义模块缓存中查找
  return customModulesCache.find(m => m.id === moduleId)
}

/**
 * 根据ID和模块类型获取模块定义
 * 支持 WPS、PQR、pPQR 预设模块和自定义模块
 */
export const getModuleByIdAndType = (moduleId: string, moduleType: 'wps' | 'pqr' | 'ppqr' = 'wps'): FieldModule | undefined => {
  // 先从自定义模块缓存中查找（自定义模块优先级最高）
  const customModule = customModulesCache.find(m => m.id === moduleId)
  if (customModule) {
    return customModule
  }

  // 再从对应类型的预设模块中查找
  // 注意：这里不能使用 require，需要在文件顶部静态导入
  let presetModule: FieldModule | undefined

  if (moduleType === 'wps') {
    presetModule = PRESET_MODULES.find(m => m.id === moduleId)
  } else if (moduleType === 'pqr') {
    // PQR 模块需要在顶部导入
    presetModule = getPQRModuleById(moduleId)
  } else if (moduleType === 'ppqr') {
    // pPQR 模块需要在顶部导入
    presetModule = getPPQRModuleById(moduleId)
  }

  return presetModule
}

/**
 * 根据分类获取模块列表
 */
export const getModulesByCategory = (category: string): FieldModule[] => {
  return PRESET_MODULES.filter(m => m.category === category)
}

/**
 * 获取所有模块分类
 */
export const getAllCategories = (): string[] => {
  return Array.from(new Set(PRESET_MODULES.map(m => m.category)))
}

/**
 * 根据ID获取预设模板
 */
export const getPresetTemplateById = (templateId: string): PresetTemplate | undefined => {
  return PRESET_TEMPLATES.find(t => t.id === templateId)
}

/**
 * 获取所有预设模板
 */
export const getAllPresetTemplates = (): PresetTemplate[] => {
  return PRESET_TEMPLATES
}

/**
 * 根据焊接工艺获取预设模板
 */
export const getPresetTemplatesByProcess = (process: string): PresetTemplate[] => {
  return PRESET_TEMPLATES.filter(t => t.welding_process === process)
}

