"""
通用预设模块定义
用于WPS、PQR、pPQR共享的通用模块
"""

# 通用预设模块列表
COMMON_PRESET_MODULES = [
    # ========================================================================
    # 1. 附件管理
    # ========================================================================
    {
        'id': 'common_attachments',
        'name': '附件管理',
        'description': '管理相关的文件附件（图片、PDF、文档等）',
        'icon': 'PaperClipOutlined',
        'module_type': 'common',
        'category': 'attachments',
        'repeatable': True,  # 可重复，支持多个附件
        'workspace_type': 'system',
        'is_shared': True,
        'access_level': 'public',
        'fields': {
            'attachment_name': {
                'label': '附件名称',
                'type': 'text',
                'required': True,
                'placeholder': '如：焊接接头照片、试验报告、检测记录'
            },
            'attachment_type': {
                'label': '附件类型',
                'type': 'select',
                'options': [
                    '照片/图片',
                    'PDF文档',
                    'Word文档',
                    'Excel表格',
                    '检测报告',
                    '试验记录',
                    '证书',
                    '其他'
                ],
                'required': True
            },
            'attachment_category': {
                'label': '附件分类',
                'type': 'select',
                'options': [
                    '焊接过程照片',
                    '焊缝外观照片',
                    '试样照片',
                    '宏观照片',
                    '金相照片',
                    '射线底片',
                    '超声检测报告',
                    '力学试验报告',
                    '材质证明',
                    '设备校准证书',
                    '其他'
                ]
            },
            'file_url': {
                'label': '文件URL',
                'type': 'text',
                'placeholder': '文件存储路径或URL'
            },
            'file_size': {
                'label': '文件大小',
                'type': 'text',
                'placeholder': '如：2.5MB'
            },
            'upload_date': {
                'label': '上传日期',
                'type': 'date'
            },
            'uploaded_by': {
                'label': '上传人',
                'type': 'text'
            },
            'description': {
                'label': '附件说明',
                'type': 'textarea',
                'placeholder': '描述附件的内容和用途'
            },
            'remarks': {
                'label': '备注',
                'type': 'textarea'
            }
        }
    },
    
    # ========================================================================
    # 2. 备注信息
    # ========================================================================
    {
        'id': 'common_notes',
        'name': '备注信息',
        'description': '记录重要的备注、说明和补充信息',
        'icon': 'FormOutlined',
        'module_type': 'common',
        'category': 'notes',
        'repeatable': True,  # 可重复，支持多条备注
        'workspace_type': 'system',
        'is_shared': True,
        'access_level': 'public',
        'fields': {
            'note_title': {
                'label': '备注标题',
                'type': 'text',
                'required': True,
                'placeholder': '如：特殊要求、注意事项、问题记录'
            },
            'note_type': {
                'label': '备注类型',
                'type': 'select',
                'options': [
                    '一般说明',
                    '重要提示',
                    '特殊要求',
                    '问题记录',
                    '改进建议',
                    '技术要点',
                    '安全提示',
                    '质量要求',
                    '其他'
                ],
                'required': True
            },
            'priority': {
                'label': '优先级',
                'type': 'select',
                'options': ['高', '中', '低'],
                'default': '中'
            },
            'note_content': {
                'label': '备注内容',
                'type': 'textarea',
                'required': True,
                'placeholder': '详细描述备注内容'
            },
            'related_section': {
                'label': '相关章节',
                'type': 'text',
                'placeholder': '如：焊接参数、试验结果、质量检验'
            },
            'action_required': {
                'label': '是否需要行动',
                'type': 'select',
                'options': ['是', '否']
            },
            'action_description': {
                'label': '行动说明',
                'type': 'textarea',
                'placeholder': '如果需要行动，描述具体的行动内容'
            },
            'created_by': {
                'label': '创建人',
                'type': 'text'
            },
            'created_date': {
                'label': '创建日期',
                'type': 'date'
            },
            'status': {
                'label': '状态',
                'type': 'select',
                'options': ['待处理', '处理中', '已完成', '已关闭'],
                'default': '待处理'
            }
        }
    },
    
    # ========================================================================
    # 3. 审核记录
    # ========================================================================
    {
        'id': 'common_review_record',
        'name': '审核记录',
        'description': '记录文档的审核、批准过程',
        'icon': 'AuditOutlined',
        'module_type': 'common',
        'category': 'notes',
        'repeatable': True,  # 可重复，支持多级审核
        'workspace_type': 'system',
        'is_shared': True,
        'access_level': 'public',
        'fields': {
            'review_stage': {
                'label': '审核阶段',
                'type': 'select',
                'options': [
                    '技术审核',
                    '质量审核',
                    '安全审核',
                    '最终批准',
                    '客户审核',
                    '第三方审核'
                ],
                'required': True
            },
            'reviewer_name': {
                'label': '审核人',
                'type': 'text',
                'required': True
            },
            'reviewer_title': {
                'label': '审核人职称',
                'type': 'text',
                'placeholder': '如：焊接工程师、质量经理、技术总监'
            },
            'review_date': {
                'label': '审核日期',
                'type': 'date',
                'required': True
            },
            'review_result': {
                'label': '审核结果',
                'type': 'select',
                'options': ['通过', '有条件通过', '不通过', '需修改'],
                'required': True
            },
            'review_comments': {
                'label': '审核意见',
                'type': 'textarea',
                'placeholder': '详细的审核意见和建议'
            },
            'issues_found': {
                'label': '发现的问题',
                'type': 'textarea',
                'placeholder': '列出发现的问题和不符合项'
            },
            'corrective_actions': {
                'label': '纠正措施',
                'type': 'textarea',
                'placeholder': '针对问题的纠正措施'
            },
            'signature': {
                'label': '签名',
                'type': 'text',
                'placeholder': '审核人签名或电子签名'
            }
        }
    }
]

