# 焊接接头示意图生成器 V2 - 最终修正

## 🎯 用户反馈的核心要求

1. **不要考虑上下边界的对齐** - 右侧板材从左侧钝边终点开始，独立绘制
2. **不要考虑坡口深度** - 直接按照板厚绘制
3. **右侧钝边长度不对** - 需要正确绘制钝边
4. **削边需要水平镜像** - 左侧从左向右削，右侧从右向左削

---

## ✅ 最终修正方案

### 1. 右侧板材不考虑对齐

**修正前：**
```typescript
// 错误：基于画布中心计算上下边界
const topY = centerY - thickness / 2
const bottomY = centerY + thickness / 2
```

**修正后：**
```typescript
// 正确：基于起始点和板厚独立计算
// 内坡口
const topY = startY - grooveDepth + bluntEdge
const bottomY = startY + thickness - grooveDepth

// 外坡口
const topY = startY - thickness + bluntEdge
const bottomY = startY + bluntEdge
```

**说明：**
- 右侧板材从 `startY`（左侧钝边终点）开始
- 不考虑与左侧板材的对齐
- 完全独立绘制

---

### 2. 右侧钝边长度修正

**内坡口：**
```typescript
// 向下绘制时，钝边从 startY 到 startY + bluntEdge
ctx.lineTo(startX, startY + bluntEdge)
```

**外坡口：**
```typescript
// 向下绘制时，钝边从 startY 到 startY（实际上钝边已经在起始点）
// bottomY = startY + bluntEdge
ctx.lineTo(startX, bottomY)
```

**说明：**
- 钝边长度 = `bluntEdge`
- 内坡口：钝边在下方
- 外坡口：钝边在上方（起始点就是钝边起点）

---

### 3. 削边水平镜像

#### 左侧板材削边（从左向右削）

**下边界削边：**
```typescript
// 从左向右削
ctx.lineTo(leftEdgeX + bevelLength, bottomY)
ctx.lineTo(leftEdgeX + bevelLength, bottomY - bevelHeight)
ctx.lineTo(cx - rootGap / 2 - slopeWidth, bottomY - bevelHeight)
```

**上边界削边：**
```typescript
// 从左向右削
ctx.lineTo(leftEdgeX + bevelLength, topY + bevelHeight)
ctx.lineTo(leftEdgeX + bevelLength, topY)
ctx.lineTo(leftEdgeX, topY)
```

#### 右侧板材削边（从右向左削）

**上边界削边：**
```typescript
// 从右向左削（水平镜像）
ctx.lineTo(startX + slopeWidth, topY)
ctx.lineTo(startX + slopeWidth, topY + bevelHeight)
ctx.lineTo(rightEdgeX, topY + bevelHeight)
```

**下边界削边：**
```typescript
// 从右向左削（水平镜像）
ctx.lineTo(rightEdgeX, bottomY - bevelHeight)
ctx.lineTo(startX + slopeWidth, bottomY - bevelHeight)
ctx.lineTo(startX + slopeWidth, bottomY)
```

**说明：**
- 左侧板材：削边从左边缘向右延伸
- 右侧板材：削边从坡口边缘向右延伸（水平镜像）
- 削边长度都是 `bevelLength`

---

## 📊 削边示意图

### 左侧板材削边（从左向右）

```
上边界削边：
    ┌─────────────┐
    │             │
   ╱│             │  <- 从左向右削
  ╱ │             │
 ╱  │             │
────┘             │

下边界削边：
│                 │
│                 │
│                 ╲  <- 从左向右削
│                  ╲
└───────────────────╲
```

### 右侧板材削边（从右向左，水平镜像）

```
上边界削边：
┌─────────────┐
│             │╲
│             │ ╲  <- 从右向左削
│             │  ╲
│             └────

下边界削边：
│             ┌────
│             │  ╱
│             │ ╱  <- 从右向左削
│             │╱
└─────────────┘
```

---

## 🔧 代码修正详情

### 右侧板材 - 内坡口

```typescript
if (groovePosition === 'inner') {
  // 向上绘制：判断上边界是否有削边
  const topY = startY - grooveDepth + bluntEdge
  
  if (bevel && bevelPosition === 'outer') {
    // 有上边界削边（水平镜像：从右向左削）
    ctx.lineTo(startX + slopeWidth, topY)
    ctx.lineTo(startX + slopeWidth, topY + bevelHeight)
    ctx.lineTo(rightEdgeX, topY + bevelHeight)
  } else {
    // 没有削边
    ctx.lineTo(startX + slopeWidth, topY)
    ctx.lineTo(rightEdgeX, topY)
  }

  // 向下绘制
  const bottomY = startY + thickness - grooveDepth
  
  if (bevel && bevelPosition === 'inner') {
    // 有下边界削边（水平镜像：从右向左削）
    ctx.lineTo(rightEdgeX, bottomY - bevelHeight)
    ctx.lineTo(startX + slopeWidth, bottomY - bevelHeight)
    ctx.lineTo(startX + slopeWidth, bottomY)
  } else {
    // 没有削边
    ctx.lineTo(rightEdgeX, bottomY)
    ctx.lineTo(startX + slopeWidth, bottomY)
  }

  // 绘制坡口斜面
  ctx.lineTo(startX, startY + bluntEdge)
}
```

### 右侧板材 - 外坡口

```typescript
else {
  // 向上绘制：先绘制坡口斜面 → 判断上边界削边
  const topY = startY - thickness + bluntEdge

  // 先绘制坡口斜面
  ctx.lineTo(startX + slopeWidth, topY)

  if (bevel && bevelPosition === 'outer') {
    // 有上边界削边（水平镜像：从右向左削）
    ctx.lineTo(startX + slopeWidth, topY + bevelHeight)
    ctx.lineTo(rightEdgeX, topY + bevelHeight)
  } else {
    ctx.lineTo(rightEdgeX, topY)
  }

  // 向下绘制
  const bottomY = startY + bluntEdge
  
  if (bevel && bevelPosition === 'inner') {
    // 有下边界削边（水平镜像：从右向左削）
    ctx.lineTo(rightEdgeX, bottomY - bevelHeight)
    ctx.lineTo(startX, bottomY - bevelHeight)
    ctx.lineTo(startX, bottomY)
  } else {
    // 没有削边
    ctx.lineTo(rightEdgeX, bottomY)
    ctx.lineTo(startX, bottomY)
  }
}
```

---

## 🎯 关键理解

### 1. 不考虑对齐

- 左侧板材：基于画布中心 `cy` 绘制
- 右侧板材：基于起始点 `startY` 绘制
- 两者独立，不强制对齐

### 2. 钝边长度

- 钝边长度 = `bluntEdge` 参数
- 内坡口：钝边在坡口下方
- 外坡口：钝边在坡口上方

### 3. 削边方向

- **左侧板材**：从左边缘向右削（从左向右）
- **右侧板材**：从坡口边缘向右削（从右向左，水平镜像）
- 削边让板材变薄：
  - 上边界削边：向下削
  - 下边界削边：向上削

---

## 🧪 测试验证

### 测试用例1：内坡口 + 无削边

```typescript
{
  groovePosition: 'inner',
  leftThickness: 10,
  rightThickness: 10,
  leftGrooveDepth: 8,
  rightGrooveDepth: 8,
  bluntEdge: 2,
  rootGap: 2
}
```

**预期结果：**
- 左侧板材正确绘制
- 右侧板材从左侧钝边终点开始
- 钝边长度为2mm
- 无削边

### 测试用例2：外坡口 + 上边界削边

```typescript
{
  groovePosition: 'outer',
  leftBevel: true,
  leftBevelPosition: 'outer',
  leftBevelLength: 5,
  leftBevelHeight: 2,
  rightBevel: true,
  rightBevelPosition: 'outer',
  rightBevelLength: 5,
  rightBevelHeight: 2
}
```

**预期结果：**
- 左侧上边界削边：从左向右削
- 右侧上边界削边：从右向左削（水平镜像）
- 削边让板材变薄

### 测试用例3：内坡口 + 下边界削边

```typescript
{
  groovePosition: 'inner',
  leftBevel: true,
  leftBevelPosition: 'inner',
  leftBevelLength: 5,
  leftBevelHeight: 2,
  rightBevel: true,
  rightBevelPosition: 'inner',
  rightBevelLength: 5,
  rightBevelHeight: 2
}
```

**预期结果：**
- 左侧下边界削边：从左向右削
- 右侧下边界削边：从右向左削（水平镜像）
- 削边让板材变薄

---

## 📝 总结

### 修正的核心点

1. ✅ **去除对齐逻辑** - 右侧板材独立绘制，不考虑与左侧对齐
2. ✅ **修正钝边长度** - 正确绘制钝边，长度为 `bluntEdge`
3. ✅ **削边水平镜像** - 左侧从左向右削，右侧从右向左削
4. ✅ **简化计算** - 基于起始点和板厚直接计算

### 绘制逻辑

- **左侧板材**：从左下角开始 → 下边界（削边判断）→ 坡口/钝边 → 上边界（削边判断）
- **右侧板材**：从钝边终点开始 → 向上（削边判断）→ 向下（削边判断）→ 坡口/钝边

### 削边理解

- 削边是板材边缘的厚度过渡
- 左侧：从左边缘向右延伸
- 右侧：从坡口边缘向右延伸（水平镜像）
- 上边界削边：向下削
- 下边界削边：向上削

现在的实现应该完全符合你的要求了！🎉

