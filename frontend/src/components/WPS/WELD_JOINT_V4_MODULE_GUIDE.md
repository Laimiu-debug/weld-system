# 焊接接头示意图生成器 V4 模块使用指南

## 概述

焊接接头示意图生成器 V4 是一个集成到 WPS 模块系统中的参数化坡口图形生成器。它允许用户通过配置参数自动生成专业的焊接接头横截面示意图。

## 模块ID

```
weld_joint_diagram_v4
```

## 功能特性

### ✅ 核心功能

1. **内外坡口支持**
   - 外坡口（outer）：从外侧开坡口
   - 内坡口（inner）：从内侧开坡口

2. **左右不同厚度板材**
   - 左右板材可独立配置厚度、坡口角度和坡口深度

3. **削边（钝边）实现**
   - 支持外削边（远离坡口侧）
   - 支持内削边（靠近坡口侧）
   - 可配置削边长度和高度

4. **三种对齐方式**
   - 中心线对齐：板材中心线对齐
   - 外侧对齐：外表面齐平
   - 内侧对齐：内表面齐平

## 使用方法

### 1. 在模块管理中查看

1. 访问 `/wps/modules`
2. 点击 **预设模块** 标签页
3. 找到 **焊接接头示意图生成器 V4** 模块
4. 查看模块详情和字段定义

### 2. 在模板中使用

1. 访问 `/wps/templates`
2. 创建或编辑模板
3. 从模块库中拖拽 **焊接接头示意图生成器 V4** 到模板画布
4. 保存模板

### 3. 在 WPS 创建中使用

1. 访问 `/wps/create`
2. 选择包含 V4 模块的模板
3. 填写坡口参数：
   - 基本参数：坡口类型、坡口位置、对齐方式
   - 左侧板材参数：板厚、坡口角度、坡口深度、削边参数
   - 右侧板材参数：板厚、坡口角度、坡口深度、削边参数
   - 根部参数：钝边、根部间隙
4. 点击 **自动生成** 按钮
5. 在弹出的生成器中预览和调整参数
6. 点击 **生成图表** 按钮
7. 生成的图片会自动填充到表单中

## 参数说明

### 基本参数

| 参数 | 类型 | 选项 | 默认值 | 说明 |
|------|------|------|--------|------|
| groove_type | select | V, X, U, I | V | 坡口类型 |
| groove_position | select | outer, inner | outer | 坡口位置 |
| alignment | select | centerline, outer_flush, inner_flush | centerline | 对齐方式 |

### 左侧板材参数

| 参数 | 类型 | 范围 | 默认值 | 说明 |
|------|------|------|--------|------|
| left_thickness | number | 1-50 | 12 | 板厚 (mm) |
| left_groove_angle | number | 0-60 | 30 | 坡口角度 (°) |
| left_groove_depth | number | 1-50 | 10 | 坡口深度 (mm) |
| left_bevel | checkbox | - | false | 启用削边 |
| left_bevel_position | select | outer, inner | outer | 削边位置 |
| left_bevel_length | number | 1-50 | 15 | 削边长度 (mm) |
| left_bevel_height | number | 1-10 | 2 | 削边高度 (mm) |

### 右侧板材参数

| 参数 | 类型 | 范围 | 默认值 | 说明 |
|------|------|------|--------|------|
| right_thickness | number | 1-50 | 10 | 板厚 (mm) |
| right_groove_angle | number | 0-60 | 30 | 坡口角度 (°) |
| right_groove_depth | number | 1-50 | 8 | 坡口深度 (mm) |
| right_bevel | checkbox | - | false | 启用削边 |
| right_bevel_position | select | outer, inner | outer | 削边位置 |
| right_bevel_length | number | 1-50 | 15 | 削边长度 (mm) |
| right_bevel_height | number | 1-10 | 2 | 削边高度 (mm) |

### 根部参数

| 参数 | 类型 | 范围 | 默认值 | 说明 |
|------|------|------|--------|------|
| blunt_edge | number | 0-10 | 2 | 钝边 (mm) |
| root_gap | number | 0-10 | 2 | 根部间隙 (mm) |

## 典型应用场景

### 场景1：等厚度板材对接

```
坡口类型: V型
坡口位置: 外坡口
对齐方式: 中心线对齐
左侧板厚: 12mm
右侧板厚: 12mm
坡口角度: 30° (左右相同)
钝边: 2mm
根部间隙: 2mm
```

### 场景2：不等厚度板材对接

```
坡口类型: V型
坡口位置: 外坡口
对齐方式: 外侧对齐
左侧板厚: 12mm
右侧板厚: 10mm
左侧坡口角度: 30°
右侧坡口角度: 35°
钝边: 2mm
根部间隙: 2mm
```

### 场景3：带削边的板材对接

```
坡口类型: V型
坡口位置: 外坡口
对齐方式: 中心线对齐
左侧板厚: 12mm
右侧板厚: 12mm
左侧启用外削边: 是
  - 削边长度: 15mm
  - 削边高度: 2mm
右侧启用内削边: 是
  - 削边长度: 15mm
  - 削边高度: 2mm
```

### 场景4：管道内部焊接

```
坡口类型: V型
坡口位置: 内坡口
对齐方式: 外侧对齐
左侧板厚: 10mm
右侧板厚: 10mm
坡口角度: 30° (左右相同)
钝边: 2mm
根部间隙: 2mm
```

## 技术实现

### 组件结构

```
WeldJointDiagramGeneratorV4.tsx
├── 参数配置表单
├── Canvas 绘制逻辑
└── 图表生成和下载功能

WeldJointDiagramV4Field.tsx
├── 图片预览
├── 自动生成按钮
├── 上传图片按钮
└── 生成器模态框

ModuleFormRenderer.tsx
├── 特殊处理 V4 模块
├── 参数字段渲染
└── 生成图片字段渲染
```

### 数据流

```
1. 用户填写参数 → Form 表单
2. 点击"自动生成" → 打开生成器模态框
3. 生成器读取表单参数 → 初始化生成器
4. 用户调整参数 → 实时预览
5. 点击"生成图表" → Canvas 绘制
6. Canvas 转 Blob → 创建 File 对象
7. File 对象 → UploadFile 对象
8. 更新表单字段 → 显示图片预览
```

## 文件清单

### 核心组件

- `frontend/src/components/WPS/WeldJointDiagramGeneratorV4.tsx` - V4 生成器主组件
- `frontend/src/components/WPS/WeldJointDiagramV4Field.tsx` - V4 字段组件
- `frontend/src/components/WPS/ModuleFormRenderer.tsx` - 模块表单渲染器（已更新）

### 配置文件

- `frontend/src/constants/wpsModules.ts` - 模块定义（已添加 V4 模块）
- `frontend/src/types/wpsModules.ts` - 类型定义（已扩展）

### 文档

- `frontend/src/components/WPS/WeldJointDiagramGeneratorV4_README.md` - V4 技术文档
- `frontend/src/components/WPS/WELD_JOINT_V4_MODULE_GUIDE.md` - 本文档

## 常见问题

### Q1: 如何在现有模板中添加 V4 模块？

A: 
1. 进入模板编辑页面
2. 从左侧模块库中找到 "焊接接头示意图生成器 V4"
3. 拖拽到模板画布中
4. 保存模板

### Q2: 生成的图片可以编辑吗？

A: 生成的图片是静态的 PNG 文件，不能直接编辑。但您可以：
- 调整参数后重新生成
- 或者上传自己编辑好的图片

### Q3: 参数填写后，图片会自动生成吗？

A: 不会自动生成。您需要点击"自动生成"按钮，在弹出的生成器中预览并确认后，才会生成图片。

### Q4: 可以同时使用多个 V4 模块吗？

A: 可以。每个模块实例都是独立的，可以配置不同的参数。

### Q5: 生成的图片保存在哪里？

A: 生成的图片会作为表单数据的一部分保存在 WPS 记录中。您也可以在生成器中点击"下载图表"按钮单独保存。

## 更新日志

### v4.0.0 (2025-10-24)

- ✨ 首次发布
- ✅ 支持内外坡口
- ✅ 支持左右不同厚度
- ✅ 支持削边功能
- ✅ 支持三种对齐方式
- ✅ 集成到 WPS 模块系统

## 反馈与支持

如有问题或建议，请联系开发团队。

