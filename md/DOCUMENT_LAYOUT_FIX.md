# 文档布局修复 - 支持多列布局和完整字段显示

**更新时间**: 2025-10-27  
**状态**: ✅ 已修复

---

## 🐛 问题描述

### 问题1: 模板分列布局未应用
- **现象**: 在模板中设置了2列、3列、4列布局，但生成的文档仍然是单列上下排列
- **原因**: `convertModulesToTipTapHTML` 函数没有使用 `rowIndex` 和 `columnIndex` 信息

### 问题2: 未填写字段被隐藏
- **现象**: 表单中未填写的字段在文档中不显示，导致表格不完整
- **原因**: 只遍历了 `moduleData.data` 中已有的字段，而不是模块定义中的所有字段
- **影响**: 实际的WPS/PQR文档应该是密密麻麻的完整表格，不应该有缺失

---

## ✅ 解决方案

### 1. 支持多列布局

#### 实现逻辑
```typescript
// 按行分组模块
const rowGroups = new Map<number, ModuleInstance[]>()
modules.forEach(instance => {
  const rowIndex = instance.rowIndex ?? 0
  if (!rowGroups.has(rowIndex)) {
    rowGroups.set(rowIndex, [])
  }
  rowGroups.get(rowIndex)!.push(instance)
})

// 按行索引排序
const sortedRows = Array.from(rowGroups.entries()).sort((a, b) => a[0] - b[0])

// 遍历每一行
sortedRows.forEach(([rowIndex, rowModules]) => {
  // 按列索引排序
  const sortedModules = rowModules.sort((a, b) => (a.columnIndex ?? 0) - (b.columnIndex ?? 0))
  
  const columnCount = sortedModules.length
  
  if (columnCount === 1) {
    // 单列：全宽显示
    html += generateModuleHTML(instance, modulesData, moduleType, '100%')
  } else {
    // 多列：使用表格布局
    const columnWidth = `${Math.floor(100 / columnCount)}%`
    
    html += `<table style="width: 100%;">`
    html += `<tbody><tr style="vertical-align: top;">`
    
    sortedModules.forEach((instance, index) => {
      html += `<td style="width: ${columnWidth};">`
      html += generateModuleHTML(instance, modulesData, moduleType, '100%', false)
      html += `</td>`
    })
    
    html += `</tr></tbody></table>`
  }
})
```

#### 支持的布局
- ✅ **1列**: 全宽显示
- ✅ **2列**: 左右分栏（50% / 50%）
- ✅ **3列**: 三等分（33% / 33% / 33%）
- ✅ **4列**: 四等分（25% / 25% / 25% / 25%）
- ✅ **混合**: 不同行可以有不同的列数

### 2. 显示所有字段（包括未填写的）

#### 修改前 ❌
```typescript
// 只遍历已填写的字段
Object.entries(moduleData.data || {}).forEach(([fieldKey, value]) => {
  const fieldDef = module.fields[fieldKey]
  // ...
})
```

#### 修改后 ✅
```typescript
// 遍历模块定义中的所有字段
Object.entries(module.fields).forEach(([fieldKey, fieldDef]) => {
  const label = fieldDef.label || fieldKey
  const value = moduleData?.data?.[fieldKey]  // 可能为空
  const formattedValue = formatFieldValue(value, fieldDef)
  // ...
})
```

#### 效果
- ✅ 所有字段都显示
- ✅ 未填写的字段显示为 "-"
- ✅ 保持表格完整性
- ✅ 符合真实WPS/PQR文档格式

---

## 🎨 新的文档样式

### 布局示例

#### 单列布局
```
┌─────────────────────────────────────────┐
│          基本信息                        │
├──────────────┬──────────────────────────┤
│ 焊接工艺     │ SMAW                     │
│ 标准         │ AWS D1.1                 │
│ 材料         │ Q345B                    │
└──────────────┴──────────────────────────┘
```

#### 双列布局
```
┌────────────────────┬────────────────────┐
│   母材信息         │   焊材信息         │
├─────────┬──────────┼─────────┬──────────┤
│ 材料牌号│ Q345B    │ 焊条型号│ E7018    │
│ 厚度(mm)│ 10       │ 直径(mm)│ 3.2      │
│ 标准    │ GB/T    │ 标准    │ AWS      │
└─────────┴──────────┴─────────┴──────────┘
```

#### 三列布局
```
┌──────────┬──────────┬──────────┐
│  第1层   │  第2层   │  第3层   │
├────┬─────┼────┬─────┼────┬─────┤
│电流│ 120A│电流│ 140A│电流│ 160A│
│电压│ 24V │电压│ 26V │电压│ 28V │
└────┴─────┴────┴─────┴────┴─────┘
```

### 样式改进

#### 标题样式
```css
/* H1 - 文档标题 */
font-size: 24pt;
text-align: center;
font-weight: bold;

/* H2 - 大模块标题 */
font-size: 16pt;
background-color: #f0f0f0;
border-left: 4px solid #1890ff;
padding: 6px 10px;

/* H3 - 小模块标题 */
font-size: 12pt;
background-color: #f5f5f5;
border-left: 3px solid #1890ff;
padding: 4px 8px;
```

#### 表格样式
```css
/* 紧凑的表格 */
font-size: 10.5pt;
border: 1px solid #333;
padding: 4px 6px;
line-height: 1.4;

/* 字段标签列 */
width: 35%;
font-weight: 500;
background-color: #fafafa;

/* 字段值列 */
width: 65%;
```

---

## 📊 数据流程

### 模板创建时
```
用户拖拽模块到画布
    ↓
设置 rowIndex 和 columnIndex
    ↓
保存到 template.module_instances
    ↓
[
  { instanceId: "1", moduleId: "header", rowIndex: 0, columnIndex: 0 },
  { instanceId: "2", moduleId: "base_metal", rowIndex: 1, columnIndex: 0 },
  { instanceId: "3", moduleId: "filler_metal", rowIndex: 1, columnIndex: 1 },
  { instanceId: "4", moduleId: "layer1", rowIndex: 2, columnIndex: 0 },
  { instanceId: "5", moduleId: "layer2", rowIndex: 2, columnIndex: 1 },
  { instanceId: "6", moduleId: "layer3", rowIndex: 2, columnIndex: 2 }
]
```

### 文档生成时
```
读取 template.module_instances
    ↓
按 rowIndex 分组
    ↓
Row 0: [header]                    → 1列布局
Row 1: [base_metal, filler_metal]  → 2列布局
Row 2: [layer1, layer2, layer3]    → 3列布局
    ↓
每行内按 columnIndex 排序
    ↓
生成对应的HTML布局
    ↓
遍历模块定义的所有字段
    ↓
显示完整的表格（包括空字段）
```

---

## 🔧 修改的文件

### 1. `frontend/src/utils/moduleToTipTapHTML.ts`

#### 主要修改
- ✅ 重写 `convertModulesToTipTapHTML` 函数
- ✅ 添加 `generateModuleHTML` 辅助函数
- ✅ 支持按行列布局生成HTML
- ✅ 遍历所有字段而不是只遍历已填写的

#### 关键代码
```typescript
// 按行分组
const rowGroups = new Map<number, ModuleInstance[]>()

// 按列排序
const sortedModules = rowModules.sort((a, b) => 
  (a.columnIndex ?? 0) - (b.columnIndex ?? 0)
)

// 遍历所有字段
Object.entries(module.fields).forEach(([fieldKey, fieldDef]) => {
  const value = moduleData?.data?.[fieldKey]  // 可能为undefined
  const formattedValue = formatFieldValue(value, fieldDef)
  // ...
})
```

### 2. `frontend/src/components/DocumentEditor/DocumentEditor.css`

#### 样式优化
- ✅ 更紧凑的表格样式（10.5pt字体）
- ✅ 更小的内边距（4px 6px）
- ✅ 更专业的标题样式
- ✅ 更好的打印效果

---

## 📖 使用示例

### 创建多列模板

1. **打开模板编辑器**
2. **拖拽第一个模块** → 自动创建第一行
3. **拖拽第二个模块到第一个模块右侧** → 创建2列布局
4. **继续拖拽** → 最多支持4列
5. **拖拽到空白区域** → 创建新行

### 生成的文档效果

#### 模板布局
```
Row 0: [表头信息]                           (1列)
Row 1: [母材信息] [焊材信息]                (2列)
Row 2: [第1层] [第2层] [第3层]              (3列)
Row 3: [检验信息] [备注信息] [审批信息] [附件] (4列)
```

#### 生成的HTML
```html
<!-- Row 0: 单列 -->
<h3>表头信息</h3>
<table>...</table>

<!-- Row 1: 双列 -->
<table>
  <tr>
    <td width="50%">
      <h3>母材信息</h3>
      <table>...</table>
    </td>
    <td width="50%">
      <h3>焊材信息</h3>
      <table>...</table>
    </td>
  </tr>
</table>

<!-- Row 2: 三列 -->
<table>
  <tr>
    <td width="33%"><h3>第1层</h3><table>...</table></td>
    <td width="33%"><h3>第2层</h3><table>...</table></td>
    <td width="33%"><h3>第3层</h3><table>...</table></td>
  </tr>
</table>
```

---

## ✅ 验证测试

### 测试场景1: 单列布局
- ✅ 模块全宽显示
- ✅ 所有字段显示
- ✅ 未填写字段显示"-"

### 测试场景2: 双列布局
- ✅ 两个模块并排显示
- ✅ 各占50%宽度
- ✅ 垂直对齐顶部

### 测试场景3: 三列布局
- ✅ 三个模块并排显示
- ✅ 各占33%宽度
- ✅ 内容紧凑

### 测试场景4: 混合布局
- ✅ 不同行有不同列数
- ✅ 布局正确
- ✅ 样式一致

### 测试场景5: 空字段显示
- ✅ 所有字段都显示
- ✅ 空值显示为"-"
- ✅ 表格完整

---

## 🎯 效果对比

### 修复前 ❌
```
基本信息
┌──────────┬──────┐
│ 焊接工艺 │ SMAW │  ← 只显示已填写的字段
└──────────┴──────┘

母材信息                ← 单列排列
┌──────────┬──────┐
│ 材料牌号 │ Q345B│
└──────────┴──────┘

焊材信息                ← 单列排列
┌──────────┬──────┐
│ 焊条型号 │ E7018│
└──────────┴──────┘
```

### 修复后 ✅
```
基本信息
┌──────────┬──────┐
│ 焊接工艺 │ SMAW │
│ 标准     │ -    │  ← 显示所有字段
│ 材料     │ -    │
└──────────┴──────┘

┌────────────────┬────────────────┐  ← 双列布局
│  母材信息      │  焊材信息      │
├────────┬───────┼────────┬───────┤
│材料牌号│ Q345B │焊条型号│ E7018 │
│厚度(mm)│ -     │直径(mm)│ -     │
│标准    │ -     │标准    │ -     │
└────────┴───────┴────────┴───────┘
```

---

## 📚 相关文档

- **DOCUMENT_MODE_AUTO_SYNC.md** - 文档模式自动同步
- **TIPTAP_IMPORT_FIX.md** - TipTap导入修复
- **README_DOCUMENT_EDITOR.md** - 文档编辑器使用说明

---

## 🎊 总结

### 解决的问题
✅ 支持多列布局（1-4列）  
✅ 完全按照模板布局生成文档  
✅ 显示所有字段（包括未填写的）  
✅ 更专业的文档样式  
✅ 符合真实WPS/PQR文档格式  

### 用户价值
✅ 模板布局得到正确应用  
✅ 文档更加完整和专业  
✅ 密密麻麻的表格符合行业标准  
✅ 打印效果更好  

---

**修复状态**: ✅ 已完成  
**最后更新**: 2025-10-27

现在生成的文档会完全按照模板的布局，并显示所有字段！🎉

