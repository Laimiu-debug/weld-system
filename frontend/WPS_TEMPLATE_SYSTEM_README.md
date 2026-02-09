# WPS模板系统使用指南

## 📋 概述

WPS模板系统是一个灵活的动态表单解决方案，允许用户根据不同的焊接工艺和标准创建和使用WPS模板。系统支持系统内置模板和用户自定义模板。

## 🎯 核心功能

### 1. 模板驱动的动态表单
- 根据选择的焊接工艺和标准，自动加载对应的模板
- 模板定义了需要填写的字段、字段类型、验证规则等
- 前端根据模板schema动态渲染表单

### 2. 三种模板类型
- **系统模板**：内置的常用焊接工艺模板（所有用户可用）
- **用户模板**：用户自己创建的模板（仅自己可用）
- **企业模板**：企业内共享的模板（企业成员可用）

### 3. 会员等级配额
- **Free**: 0个自定义模板
- **Pro**: 3个自定义模板
- **Advanced**: 10个自定义模板
- **Flagship**: 无限制

## 📁 文件结构

```
frontend/src/
├── services/
│   └── wpsTemplates.ts              # WPS模板API服务
├── components/WPS/
│   ├── TemplateSelector.tsx         # 模板选择组件
│   └── DynamicFormRenderer.tsx      # 动态表单渲染组件
└── pages/WPS/
    ├── WPSCreate.tsx                # WPS创建页面（已改为模板驱动）
    └── TemplateManagement.tsx       # 模板管理页面

backend/
├── app/
│   ├── models/
│   │   └── wps_template.py          # 模板数据模型
│   ├── schemas/
│   │   └── wps_template.py          # 模板Pydantic schemas
│   ├── services/
│   │   └── wps_template_service.py  # 模板业务逻辑
│   └── api/v1/endpoints/
│       └── wps_templates.py         # 模板API端点
└── migrations/
    ├── create_wps_templates_user_custom.sql  # 创建模板表
    ├── insert_system_templates.sql           # 插入系统模板（111, 114）
    └── insert_remaining_templates.sql        # 插入其余系统模板
```

## 🚀 使用流程

### 创建WPS的流程

1. **选择模板**
   - 用户访问 `/wps/create` 页面
   - 选择焊接工艺（如：111-手工电弧焊）
   - 可选：选择标准（如：EN ISO 15609-1）
   - 从可用模板列表中选择一个模板

2. **填写数据**
   - 系统根据模板动态渲染表单
   - 表单包含：
     - 顶部信息（WPS编号、版本、产品名称等）
     - 多个标签页（表头数据、概要、示意图、焊层、附加信息）
   - 用户填写各个字段

3. **提交保存**
   - 系统验证必填字段
   - 将数据保存到WPS表的JSONB字段中
   - 关联使用的模板ID

### 管理模板的流程

1. **查看模板列表**
   - 访问模板管理页面
   - 查看系统模板、我的模板、企业模板

2. **创建自定义模板**（开发中）
   - 点击"创建模板"按钮
   - 选择焊接工艺和标准
   - 定义字段schema
   - 保存模板

3. **编辑/删除模板**
   - 只能编辑/删除自己创建的模板
   - 系统模板不可编辑/删除

## 🔧 技术实现

### 模板Schema结构

```typescript
interface WPSTemplate {
  id: string
  name: string
  welding_process: string
  standard?: string
  field_schema: {
    top_info?: {
      fields: string[]
      layout: 'horizontal' | 'vertical'
    }
    tabs: [
      {
        key: string
        label: string
        type: 'normal' | 'array'
        fields: {
          [fieldKey: string]: {
            label: string
            type: 'text' | 'number' | 'select' | 'date' | 'textarea' | 'file' | 'checkbox'
            required?: boolean
            options?: string[]
            unit?: string
            min?: number
            max?: number
            // ... 更多配置
          }
        }
      }
    ]
  }
  ui_layout: {
    layout: 'tabs' | 'steps' | 'accordion'
    responsive?: boolean
  }
}
```

### 数据存储结构

WPS表中的JSONB字段：
- `template_id`: 使用的模板ID
- `header_info`: 表头数据（JSON）
- `summary_info`: 概要信息（JSON）
- `diagram_info`: 示意图信息（JSON）
- `weld_layers`: 焊层数组（JSON）
- `additional_info`: 附加信息（JSON）

### API端点

```
GET    /api/v1/wps-templates/                    # 获取模板列表
GET    /api/v1/wps-templates/{id}                # 获取模板详情
POST   /api/v1/wps-templates/                    # 创建模板
PUT    /api/v1/wps-templates/{id}                # 更新模板
DELETE /api/v1/wps-templates/{id}                # 删除模板
GET    /api/v1/wps-templates/welding-processes/list  # 获取焊接工艺列表
GET    /api/v1/wps-templates/standards/list      # 获取标准列表
```

## 📊 已实现的系统模板

目前系统内置了7个焊接工艺的模板：

1. **111** - 手工电弧焊（SMAW）- 完整字段定义
2. **114** - 无保护气的药芯焊（FCAW）- 完整字段定义
3. **121** - 埋弧焊（SAW）- 简化版
4. **135** - MAG焊 - 简化版
5. **141** - 钨极惰性气体保护焊（TIG/GTAW）- 简化版
6. **15** - 等离子焊 - 简化版
7. **311** - 氧乙炔焊 - 简化版

## 🔄 下一步开发计划

### 短期计划
1. ✅ 完成后端模板API
2. ✅ 完成前端模板选择组件
3. ✅ 完成动态表单渲染组件
4. ✅ 集成到WPS创建流程
5. ⏳ 完善系统模板的字段定义（121, 135, 141, 15, 311）
6. ⏳ 实现WPS创建API的调用

### 中期计划
1. ⏳ 实现模板创建功能（可视化表单设计器）
2. ⏳ 实现模板编辑功能
3. ⏳ 实现企业模板共享功能
4. ⏳ 添加模板导入/导出功能

### 长期计划
1. ⏳ 实现拖拽式模板设计器
2. ⏳ 支持模板版本管理
3. ⏳ 模板市场（用户可以分享模板）
4. ⏳ AI辅助模板创建

## 🐛 已知问题

1. 模板创建功能尚未实现（显示"开发中"提示）
2. 模板编辑功能尚未实现
3. WPS创建时的API调用尚未连接（使用TODO标记）
4. 部分系统模板的字段定义较简化，需要补充完整

## 💡 使用建议

1. **对于常见焊接工艺**：直接使用系统内置模板
2. **对于特殊需求**：等待自定义模板功能上线后创建自己的模板
3. **企业用户**：可以创建企业模板供团队成员共享使用

## 📞 技术支持

如有问题，请联系开发团队或查看相关文档。

