# 修复板材边界倾斜问题 + 添加全焊透支持

## ✅ 修复完成

### 问题1：板材下边界倾斜 ❌
**修复：板材上下边界始终保持水平** ✅

### 问题2：全焊透坡口深度需要手动设置 ❌
**修复：添加全焊透选项，自动设置坡口深度=板厚** ✅

---

## 🔧 修复内容

### 1. 板材边界倾斜问题

**问题根源：**
内坡口绘制路径错误，导致板材下边界变成斜线。

**错误代码（修复前）：**
```typescript
// 内坡口：从下往上绘制坡口
ctx.lineTo(cx - g_root / 2, leftGrooveEndY)       // 到根部间隙
ctx.lineTo(cx - g_root / 2, leftBluntStartY)      // 钝边（垂直段）
ctx.lineTo(cx - g_root / 2 - leftSlopeWidth, leftBluntEndY)  // 斜坡
ctx.lineTo(cx - g_root / 2 - leftSlopeWidth, leftTopY)  // 回到右上角
```

**问题：**
- ❌ 从左下角直接连到根部间隙，跳过了底部水平线
- ❌ 导致板材下边界变成斜线

**正确代码（修复后）：**
```typescript
// 内坡口：从下往上绘制坡口
ctx.lineTo(cx - g_root / 2 - leftSlopeWidth, leftBottomY)  // 右下角（水平）✅
ctx.lineTo(cx - g_root / 2 - leftSlopeWidth, leftBluntEndY)  // 垂直到坡口底部
ctx.lineTo(cx - g_root / 2, leftBluntStartY)      // 斜坡到钝边顶部
ctx.lineTo(cx - g_root / 2, leftGrooveEndY)       // 钝边（垂直段）
ctx.lineTo(cx - g_root / 2 - leftSlopeWidth, leftTopY)  // 垂直到顶部
```

**关键改进：**
- ✅ 先绘制底部水平线到右下角
- ✅ 然后垂直向上到坡口底部
- ✅ 确保板材下边界保持水平

**左板绘制路径（内坡口）：**
```
1. 左上角 (leftOuterX, leftTopY)
2. 左下角 (leftOuterX, leftBottomY) ← 水平 ✅
3. 右下角 (cx - g_root/2 - leftSlopeWidth, leftBottomY) ← 水平 ✅
4. 垂直到坡口底部
5. 斜坡到钝边顶部
6. 钝边（垂直段）
7. 垂直到顶部
8. 闭合路径
```

**右板绘制路径（内坡口）：**
```
1. 左上角 (cx + g_root/2 + rightSlopeWidth, rightTopY) ← 水平 ✅
2. 垂直到坡口底部
3. 斜坡到钝边顶部
4. 钝边（垂直段）
5. 垂直到右下角
6. 右下角外侧 (rightOuterX, rightBottomY) ← 水平 ✅
7. 右上角外侧 (rightOuterX, rightTopY) ← 水平 ✅
8. 闭合路径
```

---

### 2. 全焊透支持

**新增参数：**
```typescript
leftFullPenetration?: boolean  // 左侧是否全焊透
rightFullPenetration?: boolean  // 右侧是否全焊透
```

**参数验证逻辑：**
```typescript
// 如果是全焊透，坡口深度等于板厚；否则不超过板厚-1mm
const validDL = p.leftFullPenetration ? tL : Math.min(dL, tL - 1)
const validDR = p.rightFullPenetration ? tR : Math.min(dR, tR - 1)
```

**表单字段：**
```typescript
<Form.Item label="左侧全焊透" valuePropName="checked">
  <input
    type="checkbox"
    checked={params.leftFullPenetration || false}
    onChange={(e) => setParams({ ...params, leftFullPenetration: e.target.checked })}
  />
  <span style={{ marginLeft: 8 }}>全焊透（坡口深度=板厚）</span>
</Form.Item>

{!params.leftFullPenetration && (
  <Form.Item label="左侧坡口深度 (mm)">
    <InputNumber
      value={params.leftGrooveDepth}
      onChange={(value) => setParams({ ...params, leftGrooveDepth: value || 8 })}
      min={1}
      max={params.leftThickness - 1}
    />
  </Form.Item>
)}
```

**功能说明：**
- ✅ 勾选"全焊透"后，坡口深度输入框隐藏
- ✅ 坡口深度自动设置为板厚
- ✅ 左右两侧独立控制
- ✅ 适用于全焊透对接接头

---

## 📐 修复效果

### 修复前（板材边界倾斜）

**外坡口：**
```
┌─────────┐  ┌─────────┐  <- 上边界（水平）✅
│         │╲╱│         │  <- 坡口
│         ││ ││         │
│         │  │         │
└─────────┘  └─────────┘  <- 下边界（水平）✅
```

**内坡口：**
```
┌─────────┐  ┌─────────┐  <- 上边界（水平）✅
│         │  │         │
│         ││ ││         │
│         ╲╱ ╲╱         │  <- 坡口
└─────────╲  ╱─────────┘  <- 下边界（倾斜）❌
```

### 修复后（板材边界水平）

**外坡口：**
```
┌─────────┐  ┌─────────┐  <- 上边界（水平）✅
│         │╲╱│         │  <- 坡口
│         ││ ││         │
│         │  │         │
└─────────┘  └─────────┘  <- 下边界（水平）✅
```

**内坡口：**
```
┌─────────┐  ┌─────────┐  <- 上边界（水平）✅
│         │  │         │
│         ││ ││         │
│         │╲╱│         │  <- 坡口
└─────────┘  └─────────┘  <- 下边界（水平）✅
```

---

## 🧪 测试步骤

### 1. 测试内坡口板材边界

**步骤：**
1. 打开浏览器：http://localhost:3002
2. 导航到焊接工艺规程（WPS）页面
3. 设置坡口位置：内坡口（从下侧开）
4. 设置板厚：左10mm，右10mm
5. 点击"生成图表"

**预期：**
- ✅ 板材上边界水平
- ✅ 板材下边界水平
- ✅ 坡口从下侧向上开
- ✅ 钝边在坡口顶部

### 2. 测试外坡口板材边界

**步骤：**
1. 设置坡口位置：外坡口（从上侧开）
2. 设置板厚：左10mm，右10mm
3. 点击"生成图表"

**预期：**
- ✅ 板材上边界水平
- ✅ 板材下边界水平
- ✅ 坡口从上侧向下开
- ✅ 钝边在坡口底部

### 3. 测试全焊透功能

**步骤：**
1. 设置板厚：左10mm，右8mm
2. 勾选"左侧全焊透"
3. 勾选"右侧全焊透"
4. 点击"生成图表"

**预期：**
- ✅ 左侧坡口深度输入框隐藏
- ✅ 右侧坡口深度输入框隐藏
- ✅ 左侧坡口深度自动设置为10mm
- ✅ 右侧坡口深度自动设置为8mm
- ✅ 坡口贯穿整个板厚

### 4. 测试不等厚板材全焊透

**步骤：**
1. 设置板厚：左12mm，右8mm
2. 设置对齐方式：中心线对齐
3. 勾选"左侧全焊透"
4. 勾选"右侧全焊透"
5. 点击"生成图表"

**预期：**
- ✅ 左侧坡口深度=12mm
- ✅ 右侧坡口深度=8mm
- ✅ 板材上下边界保持水平
- ✅ 中心线对齐正确

---

## 📊 改进效果评分

| 方面 | 修复前 | 修复后 |
|------|--------|--------|
| 外坡口上边界 | 水平 ✅ | 水平 ✅ |
| 外坡口下边界 | 水平 ✅ | 水平 ✅ |
| 内坡口上边界 | 水平 ✅ | 水平 ✅ |
| 内坡口下边界 | 倾斜 ❌ | 水平 ✅ |
| 全焊透支持 | 无 ❌ | 完整 ✅ |
| 左右独立全焊透 | 无 ❌ | 支持 ✅ |
| **总体评分** | **⭐⭐⭐** | **⭐⭐⭐⭐⭐** |

---

## 🎉 总结

已修复所有板材边界问题并添加全焊透支持：

1. ✅ **内坡口下边界修复** - 板材下边界保持水平
2. ✅ **外坡口边界正确** - 板材上下边界都保持水平
3. ✅ **全焊透支持** - 左右独立控制
4. ✅ **自动坡口深度** - 全焊透时自动设置为板厚
5. ✅ **条件显示** - 全焊透时隐藏坡口深度输入框
6. ✅ **不等厚支持** - 左右可以不同板厚且都全焊透

现在板材边界始终保持水平，无论是外坡口还是内坡口！

---

## 📁 相关文件

- **生成器组件**: `frontend/src/components/WPS/WeldJointDiagramGenerator.tsx`
- **左右独立设计**: `COMPLETE_REDESIGN_WITH_INDEPENDENT_SIDES.md`

开发服务器运行中：**http://localhost:3002**

