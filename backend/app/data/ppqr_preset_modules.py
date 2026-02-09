"""
pPQR预设模块定义
用于pPQR（预焊接工艺评定记录）的系统预设模块
pPQR用于试验性焊接，探索最佳焊接参数
"""

# pPQR预设模块列表
PPQR_PRESET_MODULES = [
    # ========================================================================
    # 1. pPQR基本信息
    # ========================================================================
    {
        'id': 'ppqr_basic_info',
        'name': 'pPQR基本信息',
        'description': 'pPQR的基本识别信息和试验目的',
        'icon': 'ExperimentOutlined',
        'module_type': 'ppqr',
        'category': 'basic',
        'repeatable': False,
        'workspace_type': 'system',
        'is_shared': True,
        'access_level': 'public',
        'fields': {
            'ppqr_number': {
                'label': 'pPQR编号',
                'type': 'text',
                'required': True,
                'placeholder': '如：pPQR-2024-001'
            },
            'title': {
                'label': 'pPQR标题',
                'type': 'text',
                'required': True,
                'placeholder': '如：Q345R钢板对接焊参数优化试验'
            },
            'test_date': {
                'label': '试验日期',
                'type': 'date',
                'required': True
            },
            'test_purpose': {
                'label': '试验目的',
                'type': 'textarea',
                'required': True,
                'placeholder': '如：探索最佳焊接参数、验证新工艺可行性、优化热输入等'
            },
            'reference_standard': {
                'label': '参考标准',
                'type': 'select',
                'options': ['AWS D1.1', 'ASME IX', 'EN ISO 15614-1', 'GB/T 15169', 'GB/T 19869']
            },
            'welding_process': {
                'label': '焊接方法',
                'type': 'select',
                'options': ['111-手工电弧焊', '114-药芯焊丝电弧焊', '121-埋弧焊', '131-MIG焊', '135-MAG焊', '141-TIG焊', '15-等离子弧焊'],
                'required': True
            },
            'welder_name': {
                'label': '焊工姓名',
                'type': 'text'
            },
            'project_name': {
                'label': '项目名称',
                'type': 'text',
                'placeholder': '关联的项目或产品'
            }
        }
    },
    
    # ========================================================================
    # 2. 试验方案
    # ========================================================================
    {
        'id': 'ppqr_test_plan',
        'name': '试验方案',
        'description': 'pPQR的试验方案和参数设计',
        'icon': 'ProjectOutlined',
        'module_type': 'ppqr',
        'category': 'basic',
        'repeatable': False,
        'workspace_type': 'system',
        'is_shared': True,
        'access_level': 'public',
        'fields': {
            'test_variables': {
                'label': '试验变量',
                'type': 'textarea',
                'required': True,
                'placeholder': '如：焊接电流(120-160A)、焊接速度(150-250mm/min)、预热温度(100-150°C)'
            },
            'number_of_specimens': {
                'label': '试样数量',
                'type': 'number',
                'min': 1,
                'placeholder': '计划制作的试样数量'
            },
            'test_matrix': {
                'label': '试验矩阵',
                'type': 'textarea',
                'placeholder': '描述不同参数组合的试验方案'
            },
            'expected_outcome': {
                'label': '预期结果',
                'type': 'textarea',
                'placeholder': '描述试验的预期目标和成功标准'
            },
            'risk_assessment': {
                'label': '风险评估',
                'type': 'textarea',
                'placeholder': '可能的风险和应对措施'
            }
        }
    },
    
    # ========================================================================
    # 3. 材料信息
    # ========================================================================
    {
        'id': 'ppqr_materials',
        'name': '材料信息',
        'description': 'pPQR试验使用的材料',
        'icon': 'BlockOutlined',
        'module_type': 'ppqr',
        'category': 'materials',
        'repeatable': False,
        'workspace_type': 'system',
        'is_shared': True,
        'access_level': 'public',
        'fields': {
            'base_material_spec': {
                'label': '母材规格',
                'type': 'text',
                'placeholder': '如：GB/T 713 Q345R'
            },
            'base_material_grade': {
                'label': '母材牌号',
                'type': 'text',
                'placeholder': '如：Q345R'
            },
            'thickness': {
                'label': '板厚',
                'type': 'number',
                'unit': 'mm',
                'min': 0
            },
            'filler_metal_spec': {
                'label': '焊材规格',
                'type': 'text',
                'placeholder': '如：AWS A5.1 E7018'
            },
            'filler_metal_classification': {
                'label': '焊材型号',
                'type': 'text',
                'placeholder': '如：E7018'
            },
            'diameter': {
                'label': '焊材直径',
                'type': 'number',
                'unit': 'mm',
                'min': 0
            },
            'shielding_gas': {
                'label': '保护气体',
                'type': 'text',
                'placeholder': '如：Ar 80% + CO2 20%'
            },
            'batch_number': {
                'label': '批号',
                'type': 'text'
            }
        }
    },
    
    # ========================================================================
    # 4. 参数对比组（可重复）
    # ========================================================================
    {
        'id': 'ppqr_parameter_group',
        'name': '参数对比组',
        'description': '不同参数组合的试验记录',
        'icon': 'BarChartOutlined',
        'module_type': 'ppqr',
        'category': 'parameters',
        'repeatable': True,  # 可重复，支持多组参数对比
        'workspace_type': 'system',
        'is_shared': True,
        'access_level': 'public',
        'fields': {
            'group_number': {
                'label': '组号',
                'type': 'text',
                'required': True,
                'placeholder': '如：A组、B组、C组或1#、2#、3#'
            },
            'group_description': {
                'label': '组别说明',
                'type': 'text',
                'placeholder': '如：低热输入组、中热输入组、高热输入组'
            },
            'current': {
                'label': '焊接电流',
                'type': 'number',
                'unit': 'A',
                'min': 0,
                'required': True
            },
            'voltage': {
                'label': '焊接电压',
                'type': 'number',
                'unit': 'V',
                'min': 0,
                'required': True
            },
            'travel_speed': {
                'label': '焊接速度',
                'type': 'number',
                'unit': 'mm/min',
                'min': 0
            },
            'heat_input': {
                'label': '热输入',
                'type': 'number',
                'unit': 'kJ/mm',
                'min': 0,
                'readonly': True,
                'placeholder': '自动计算'
            },
            'preheat_temp': {
                'label': '预热温度',
                'type': 'number',
                'unit': '°C',
                'min': 0
            },
            'interpass_temp': {
                'label': '层间温度',
                'type': 'number',
                'unit': '°C',
                'min': 0
            },
            'wire_feed_speed': {
                'label': '送丝速度',
                'type': 'number',
                'unit': 'm/min',
                'min': 0
            },
            'gas_flow_rate': {
                'label': '气体流量',
                'type': 'number',
                'unit': 'L/min',
                'min': 0
            },
            'remarks': {
                'label': '备注',
                'type': 'textarea'
            }
        }
    },
    
    # ========================================================================
    # 5. 外观检查
    # ========================================================================
    {
        'id': 'ppqr_visual_inspection',
        'name': '外观检查',
        'description': '焊缝外观质量检查',
        'icon': 'EyeOutlined',
        'module_type': 'ppqr',
        'category': 'tests',
        'repeatable': True,  # 可重复，对应不同参数组
        'workspace_type': 'system',
        'is_shared': True,
        'access_level': 'public',
        'fields': {
            'group_number': {
                'label': '对应组号',
                'type': 'text',
                'required': True,
                'placeholder': '如：A组、B组'
            },
            'weld_appearance': {
                'label': '焊缝外观',
                'type': 'select',
                'options': ['优秀', '良好', '一般', '不良'],
                'required': True
            },
            'surface_quality': {
                'label': '表面质量',
                'type': 'select',
                'options': ['光滑', '较光滑', '粗糙', '有飞溅']
            },
            'weld_profile': {
                'label': '焊缝成形',
                'type': 'select',
                'options': ['均匀饱满', '基本均匀', '不均匀', '有凹陷']
            },
            'undercut': {
                'label': '咬边',
                'type': 'select',
                'options': ['无', '轻微', '明显']
            },
            'undercut_depth': {
                'label': '咬边深度',
                'type': 'number',
                'unit': 'mm',
                'min': 0
            },
            'overlap': {
                'label': '焊瘤',
                'type': 'select',
                'options': ['无', '有']
            },
            'porosity': {
                'label': '表面气孔',
                'type': 'select',
                'options': ['无', '少量', '较多']
            },
            'cracks': {
                'label': '裂纹',
                'type': 'select',
                'options': ['无', '有'],
                'required': True
            },
            'defect_description': {
                'label': '缺陷描述',
                'type': 'textarea',
                'placeholder': '详细描述发现的缺陷'
            },
            'overall_rating': {
                'label': '综合评价',
                'type': 'select',
                'options': ['优秀', '良好', '合格', '不合格'],
                'required': True
            },
            'remarks': {
                'label': '备注',
                'type': 'textarea'
            }
        }
    },
    
    # ========================================================================
    # 6. 简易力学性能测试
    # ========================================================================
    {
        'id': 'ppqr_mechanical_test',
        'name': '简易力学测试',
        'description': 'pPQR的简化力学性能测试',
        'icon': 'ExperimentOutlined',
        'module_type': 'ppqr',
        'category': 'tests',
        'repeatable': True,
        'workspace_type': 'system',
        'is_shared': True,
        'access_level': 'public',
        'fields': {
            'group_number': {
                'label': '对应组号',
                'type': 'text',
                'required': True
            },
            'test_type': {
                'label': '测试类型',
                'type': 'select',
                'options': ['面弯', '背弯', '侧弯', '拉伸', '硬度', '宏观'],
                'required': True
            },
            'test_result': {
                'label': '测试结果',
                'type': 'textarea',
                'placeholder': '简要描述测试结果'
            },
            'pass_fail': {
                'label': '是否通过',
                'type': 'select',
                'options': ['通过', '未通过', '待定'],
                'required': True
            },
            'remarks': {
                'label': '备注',
                'type': 'textarea'
            }
        }
    },
    
    # ========================================================================
    # 7. 参数对比分析
    # ========================================================================
    {
        'id': 'ppqr_comparison_analysis',
        'name': '参数对比分析',
        'description': '不同参数组的对比分析和优选',
        'icon': 'LineChartOutlined',
        'module_type': 'ppqr',
        'category': 'results',
        'repeatable': False,
        'workspace_type': 'system',
        'is_shared': True,
        'access_level': 'public',
        'fields': {
            'best_group': {
                'label': '最优组别',
                'type': 'text',
                'placeholder': '如：B组'
            },
            'best_group_reason': {
                'label': '选择理由',
                'type': 'textarea',
                'required': True,
                'placeholder': '说明为什么选择该组参数'
            },
            'heat_input_analysis': {
                'label': '热输入分析',
                'type': 'textarea',
                'placeholder': '分析不同热输入对焊接质量的影响'
            },
            'quality_comparison': {
                'label': '质量对比',
                'type': 'textarea',
                'placeholder': '对比各组的外观、力学性能等'
            },
            'efficiency_analysis': {
                'label': '效率分析',
                'type': 'textarea',
                'placeholder': '分析焊接效率和成本'
            },
            'recommended_parameters': {
                'label': '推荐参数',
                'type': 'textarea',
                'required': True,
                'placeholder': '总结推荐用于正式PQR的参数范围'
            }
        }
    },
    
    # ========================================================================
    # 8. 试验评价与结论
    # ========================================================================
    {
        'id': 'ppqr_evaluation',
        'name': '试验评价',
        'description': 'pPQR的最终评价和结论',
        'icon': 'CheckCircleOutlined',
        'module_type': 'ppqr',
        'category': 'results',
        'repeatable': False,
        'workspace_type': 'system',
        'is_shared': True,
        'access_level': 'public',
        'fields': {
            'test_conclusion': {
                'label': '试验结论',
                'type': 'select',
                'options': ['成功-可转PQR', '部分成功-需调整', '失败-需重新设计'],
                'required': True
            },
            'objectives_achieved': {
                'label': '目标达成情况',
                'type': 'textarea',
                'required': True,
                'placeholder': '评估试验目的是否达成'
            },
            'lessons_learned': {
                'label': '经验总结',
                'type': 'textarea',
                'placeholder': '总结试验过程中的经验教训'
            },
            'next_steps': {
                'label': '后续步骤',
                'type': 'textarea',
                'required': True,
                'placeholder': '如：进行正式PQR、调整参数重新试验等'
            },
            'convert_to_pqr': {
                'label': '是否转为PQR',
                'type': 'select',
                'options': ['是', '否', '待定']
            },
            'target_pqr_number': {
                'label': '目标PQR编号',
                'type': 'text',
                'placeholder': '如果转为PQR，填写PQR编号'
            },
            'evaluated_by': {
                'label': '评价人',
                'type': 'text',
                'required': True
            },
            'evaluation_date': {
                'label': '评价日期',
                'type': 'date',
                'required': True
            },
            'remarks': {
                'label': '备注',
                'type': 'textarea'
            }
        }
    }
]

