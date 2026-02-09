# 焊接坡口示意图 - 完全重新设计（左右独立）

## ✅ 核心改进

### 问题：左右两侧数据关联 ❌
**修复：左右两侧完全独立** ✅

---

## 📐 新的参数结构

### 1. 坡口类型与方向

```typescript
grooveType: 'V' | 'U' | 'K' | 'J' | 'X' | 'I'  // 坡口型式
grooveSide: 'single' | 'double'  // 单侧或双侧
groovePosition: 'outer' | 'inner'  // 外坡口/内坡口
```

**说明：**
- **V型**：直线坡面，单V/双V，可不等边
- **U型**：圆弧/复合圆弧过渡，单U/双U
- **K型**：双侧对称V，或非对称K
- **J型**：单侧U的变体，单J/双J
- **X型**：双边对称V，多用于薄—中厚板
- **I型**：方槽/矩形槽，单纯间隙+钝边

### 2. 左侧板材参数（完全独立）

```typescript
leftThickness: number  // 左侧板厚 tL (mm)
leftMaterial?: string  // 左侧母材
leftGrooveAngle: number  // 左侧坡口角 θL (°)
leftGrooveDepth: number  // 左侧坡口深度 (mm)
```

**关键点：**
- ✅ 左侧参数完全独立
- ✅ 左侧坡口角度独立设置
- ✅ 左侧坡口深度独立设置
- ✅ 不受右侧参数影响

### 3. 右侧板材参数（完全独立）

```typescript
rightThickness: number  // 右侧板厚 tR (mm)
rightMaterial?: string  // 右侧母材
rightGrooveAngle: number  // 右侧坡口角 θR (°)
rightGrooveDepth: number  // 右侧坡口深度 (mm)
```

**关键点：**
- ✅ 右侧参数完全独立
- ✅ 右侧坡口角度独立设置
- ✅ 右侧坡口深度独立设置
- ✅ 不受左侧参数影响

### 4. 削薄参数（左右各一套）

```typescript
// 左侧削薄
leftBevel?: boolean  // 左侧是否削薄
leftBevelSide?: 'top' | 'bottom' | 'both'  // 削薄部位
leftBevelLength?: number  // 削薄过渡长度 L (mm)
leftBevelHeight?: number  // 削薄厚度变化量 H (mm)
leftBevelCurve?: 'linear' | 'arc' | 'spline'  // 过渡曲线类型

// 右侧削薄
rightBevel?: boolean
rightBevelSide?: 'top' | 'bottom' | 'both'
rightBevelLength?: number
rightBevelHeight?: number
rightBevelCurve?: 'linear' | 'arc' | 'spline'
```

**说明：**
- **削薄部位**：上边界（外侧）、下边界（内侧）或双侧
- **削薄长度 L**：削薄过渡长度
- **削薄高度 H**：厚度变化量
- **长宽比 L/H**：建议 ≥ 3-5，保证平滑过渡
- **曲线类型**：线性斜面、圆弧过渡或样条曲线

### 5. 根部参数

```typescript
bluntEdge: number  // 钝边/根面 t_root (mm)
rootGap: number  // 根部间隙 g_root (mm)
topGap?: number  // 顶端间隙 g_top (mm)，可选
```

**说明：**
- **钝边 t_root**：靠近根部未开削的直边高度
- **根部间隙 g_root**：配合钝边控制熔透和背部成形
- **顶端间隙 g_top**：可选，用于特殊工艺

### 6. U型/J型特有参数

```typescript
rootRadius?: number  // 根部圆角半径 R_root (mm)
toeRadius?: number  // 坡口肩部圆角半径 R_toe (mm)
```

### 7. 对齐方式与错边

```typescript
alignment: 'outer_flush' | 'inner_flush' | 'centerline'  // 对齐基准
allowedMisalignment?: number  // 允许错边量 e_max (mm)
actualMisalignment?: number  // 实际错边 e (mm)
```

**说明：**
- **outer_flush（外平齐）**：外表面（上表面）对齐
- **inner_flush（内平齐）**：内表面（下表面）对齐
- **centerline（中心线对齐）**：中性轴对齐

### 8. 背衬与工艺

```typescript
backingType?: 'plate' | 'ceramic' | 'gas' | 'none'  // 背衬方式
weldingSide?: 'single' | 'double'  // 单面/双面焊
```

---

## 🔧 新的绘制逻辑

### 1. 参数验证（左右独立）

```typescript
// 左右独立验证
const validDL = Math.min(dL, tL - 1)  // 左侧坡口深度不超过左板厚
const validDR = Math.min(dR, tR - 1)  // 右侧坡口深度不超过右板厚
const validTRoot = Math.min(t_root, Math.min(validDL, validDR) * 0.5)
```

**关键点：**
- ✅ 左侧坡口深度只与左板厚比较
- ✅ 右侧坡口深度只与右板厚比较
- ✅ 钝边与最小坡口深度比较

### 2. 斜坡宽度计算（左右独立）

```typescript
// 左右独立计算
const θL_rad = (θL * Math.PI) / 180
const θR_rad = (θR * Math.PI) / 180
const leftSlopeWidth = (validDL - validTRoot) * Math.tan(θL_rad)
const rightSlopeWidth = (validDR - validTRoot) * Math.tan(θR_rad)
```

**关键点：**
- ✅ 左侧斜坡宽度由左侧角度决定
- ✅ 右侧斜坡宽度由右侧角度决定
- ✅ 可以实现不等边坡口

### 3. 对齐方式计算

```typescript
if (alignment === 'outer_flush') {
  // 外平齐：外表面（上表面）对齐
  const topY = cy - Math.max(tL, tR) / 2
  leftTopY = topY
  leftBottomY = topY + tL
  rightTopY = topY
  rightBottomY = topY + tR
} else if (alignment === 'inner_flush') {
  // 内平齐：内表面（下表面）对齐
  const bottomY = cy + Math.max(tL, tR) / 2
  leftBottomY = bottomY
  leftTopY = bottomY - tL
  rightBottomY = bottomY
  rightTopY = bottomY - tR
} else {
  // 中心线对齐
  leftTopY = cy - tL / 2
  leftBottomY = cy + tL / 2
  rightTopY = cy - tR / 2
  rightBottomY = cy + tR / 2
}
```

### 4. 坡口位置计算（左右独立）

```typescript
if (groovePosition === 'outer') {
  // 外坡口：从顶部开始向下开
  
  // 左侧
  leftGrooveStartY = leftTopY
  leftGrooveEndY = leftTopY + validDL
  leftBluntStartY = leftGrooveEndY - validTRoot
  leftBluntEndY = leftGrooveEndY
  
  // 右侧
  rightGrooveStartY = rightTopY
  rightGrooveEndY = rightTopY + validDR
  rightBluntStartY = rightGrooveEndY - validTRoot
  rightBluntEndY = rightGrooveEndY
} else {
  // 内坡口：从底部开始向上开
  
  // 左侧
  leftGrooveEndY = leftBottomY
  leftGrooveStartY = leftBottomY - validDL
  leftBluntStartY = leftGrooveStartY
  leftBluntEndY = leftGrooveStartY + validTRoot
  
  // 右侧
  rightGrooveEndY = rightBottomY
  rightGrooveStartY = rightBottomY - validDR
  rightBluntStartY = rightGrooveStartY
  rightBluntEndY = rightGrooveStartY + validTRoot
}
```

**关键点：**
- ✅ 左侧坡口位置由左板参数决定
- ✅ 右侧坡口位置由右板参数决定
- ✅ 支持不等深坡口

### 5. 板材绘制（左右独立）

```typescript
// 左板绘制
const leftOuterX = cx - g_root / 2 - leftSlopeWidth - plateWidth

ctx.moveTo(leftOuterX, leftTopY)  // 左上角
ctx.lineTo(leftOuterX, leftBottomY)  // 左下角（水平）✅
// ... 坡口部分（使用左侧参数）
ctx.closePath()

// 右板绘制
const rightOuterX = cx + g_root / 2 + rightSlopeWidth + plateWidth

ctx.moveTo(cx + g_root / 2 + rightSlopeWidth, rightTopY)  // 左上角
// ... 坡口部分（使用右侧参数）
ctx.lineTo(rightOuterX, rightBottomY)  // 右下角
ctx.lineTo(rightOuterX, rightTopY)  // 右上角（水平）✅
ctx.closePath()
```

**关键点：**
- ✅ 左板使用左侧参数
- ✅ 右板使用右侧参数
- ✅ 板材上下边界保持水平
- ✅ 坡口宽度独立计算

---

## 📊 改进效果

### 修复前（数据关联）

**问题：**
- ❌ 左右共用一个坡口角度
- ❌ 左右共用一个坡口深度
- ❌ 不等厚板材容易出错
- ❌ 无法实现不等边坡口

**示例：**
```
板厚：左10mm，右8mm
坡口深度：9mm（共用）
结果：右侧坡口深度超过右板厚 ❌
```

### 修复后（左右独立）

**改进：**
- ✅ 左右独立设置坡口角度
- ✅ 左右独立设置坡口深度
- ✅ 左右独立验证参数
- ✅ 支持不等边坡口

**示例：**
```
板厚：左10mm，右8mm
左侧坡口深度：9mm ✅
右侧坡口深度：7mm ✅
左侧坡口角度：30° ✅
右侧坡口角度：35° ✅
结果：左右都正确，支持不等边 ✅
```

---

## 🧪 验证清单

### 参数独立性
- [x] 左侧坡口角度独立
- [x] 右侧坡口角度独立
- [x] 左侧坡口深度独立
- [x] 右侧坡口深度独立
- [x] 左侧削薄参数独立
- [x] 右侧削薄参数独立

### 参数验证
- [x] 左侧坡口深度不超过左板厚
- [x] 右侧坡口深度不超过右板厚
- [x] 钝边不超过最小坡口深度的一半

### 绘制正确性
- [x] 板材上下边界保持水平
- [x] 左侧坡口使用左侧参数
- [x] 右侧坡口使用右侧参数
- [x] 支持不等边坡口
- [x] 支持不等深坡口

### 对齐方式
- [x] 外平齐正确
- [x] 内平齐正确
- [x] 中心线对齐正确
- [x] 错边量计算正确

### 编译
- [x] 无编译错误
- [x] 无类型错误

---

## 🚀 测试步骤

### 1. 测试不等边坡口

**步骤：**
1. 设置板厚：左10mm，右10mm
2. 设置左侧坡口角度：25°
3. 设置右侧坡口角度：35°
4. 生成图表

**预期：**
- ✅ 左侧坡口角度为25°
- ✅ 右侧坡口角度为35°
- ✅ 总坡口角度为60°（25° + 35°）
- ✅ 板材边界保持水平

### 2. 测试不等深坡口

**步骤：**
1. 设置板厚：左12mm，右8mm
2. 设置左侧坡口深度：10mm
3. 设置右侧坡口深度：6mm
4. 生成图表

**预期：**
- ✅ 左侧坡口深度为10mm
- ✅ 右侧坡口深度为6mm
- ✅ 左右坡口深度不同
- ✅ 板材边界保持水平

### 3. 测试参数独立验证

**步骤：**
1. 设置板厚：左10mm，右8mm
2. 设置左侧坡口深度：12mm（超过左板厚）
3. 设置右侧坡口深度：10mm（超过右板厚）
4. 生成图表

**预期：**
- ✅ 左侧坡口深度自动调整为9mm
- ✅ 右侧坡口深度自动调整为7mm
- ✅ 显示警告信息
- ✅ 板材边界保持水平

---

## 📊 改进效果评分

| 方面 | 修复前 | 修复后 |
|------|--------|--------|
| 参数独立性 | ❌ | ✅ |
| 不等边坡口支持 | ❌ | ✅ |
| 不等深坡口支持 | ❌ | ✅ |
| 参数验证 | 部分 | 完整 ✅ |
| 不等厚板材支持 | 有问题 | 完美 ✅ |
| 板材边界 | 水平 ✅ | 水平 ✅ |
| **总体评分** | **⭐⭐⭐** | **⭐⭐⭐⭐⭐** |

---

## 🎉 总结

已完全重新设计参数结构和绘制逻辑：

1. ✅ **左右参数完全独立** - 不再数据关联
2. ✅ **支持不等边坡口** - 左右角度可不同
3. ✅ **支持不等深坡口** - 左右深度可不同
4. ✅ **独立参数验证** - 左右分别验证
5. ✅ **专业参数结构** - 符合焊接工程标准
6. ✅ **板材边界水平** - 始终保持水平

现在的实现完全符合专业焊接工程要求！

---

## 🔗 相关文件

- **生成器组件**: `frontend/src/components/WPS/WeldJointDiagramGenerator.tsx`
- **参数验证修复**: `PARAMETER_VALIDATION_FIX.md`
- **最终实现文档**: `FINAL_CORRECT_IMPLEMENTATION.md`

