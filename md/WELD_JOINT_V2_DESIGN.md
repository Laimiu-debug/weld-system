# 焊接接头示意图生成器 V2 - 设计文档

## 📋 设计目标

创建一个新的焊接接头示意图生成模块，采用更清晰的绘制逻辑：

1. **不考虑上下对齐问题** - 简化绘制流程
2. **左右板材独立绘制** - 每个板材的绘制逻辑独立
3. **统一的起始点计算** - 右侧板材起始点计算方式统一
4. **清晰的绘制顺序** - 内外坡口绘制顺序明确

---

## 🎯 绘制流程

### 一、左侧板材的绘制顺序

**起始点：** 左侧板的左下角

**绘制步骤：**

1. **从左下角起始点开始绘制**
   ```
   起始点坐标：(leftEdgeX, bottomY)
   ```

2. **绘制一段下边界**
   - 从左下角向右绘制

3. **判断左侧板下边界是否有削边**
   - **如果有削边**：绘制削边过渡
     - 外坡口 + 内削边：在下边界削边
     - 内坡口 + 外削边：在下边界削边
   - **如果没有削边**：继续绘制下边界直到根部

4. **到达根部后，判断坡口类型（内坡口/外坡口）**
   - **如果是内坡口**：
     1. 先绘制坡口斜面
     2. 再绘制钝边（垂直段）
   - **如果是外坡口**：
     1. 先绘制钝边（垂直段）
     2. 再绘制坡口斜面

5. **绘制上边界**
   - **判断上边界是否有削边**
     - 如果有削边：绘制上边界的削边过渡
     - 如果没有削边：直接绘制上边界

6. **闭合路径**

---

### 二、右侧板材起始点的确定

**统一计算方式：**

无论左侧板是哪种情况，右侧板材的起始点坐标计算方式统一为：

- **Y坐标**：从左侧板钝边的终点获取Y坐标
- **X坐标**：左侧板钝边终点的X坐标 + 根部间隙

**代码实现：**

```typescript
const calculateRightStartPoint = (cx, cy, params) => {
  const { leftThickness, leftGrooveDepth, bluntEdge, rootGap, groovePosition } = params

  let y: number
  if (groovePosition === 'inner') {
    // 内坡口：钝边终点在上方
    y = cy + leftThickness / 2 - leftGrooveDepth + bluntEdge
  } else {
    // 外坡口：钝边终点在下方
    y = cy + leftThickness / 2 - bluntEdge
  }

  const x = cx - rootGap / 2 + rootGap

  return { x, y }
}
```

---

### 三、右侧板材的绘制顺序

根据坡口类型分为两种情况：

#### 情况A：内坡口

**向上绘制：**
1. 判断上边界是否有削边
   - 如果有削边：绘制削边
   - 如果没有削边：直接绘制上边界

**向下绘制：**
1. 先绘制钝边
2. 再绘制坡口斜面
3. 判断下边界是否有削边
   - 如果有削边：绘制削边
   - 如果没有削边：绘制下边界

#### 情况B：外坡口

**向上绘制：**
1. 先绘制坡口斜面
2. 判断上边界是否有削边
   - 如果有削边：绘制削边
   - 如果没有削边：绘制上边界

**向下绘制：**
1. 先绘制钝边
2. 判断下边界是否有削边
   - 如果有削边：绘制削边
   - 如果没有削边：绘制下边界

**重要说明：**
- 削边处理只与板材的上下边界有关系
- 削边与内外坡口没有直接关系
- 上边界削边：在板材上表面
- 下边界削边：在板材下表面

---

## 📐 坐标系统

### 基准点

- **中心点 (cx, cy)**：画布中心
- **板材厚度方向**：垂直方向（Y轴）
- **板材长度方向**：水平方向（X轴）

### 左侧板材坐标

```
leftEdgeX = cx - rootGap / 2 - slopeWidth - plateWidth
topY = cy - thickness / 2
bottomY = cy + thickness / 2
```

### 右侧板材坐标

```
rightEdgeX = startX + slopeWidth + plateWidth
topY = startY - thickness + grooveDepth - bluntEdge (内坡口)
     = startY - thickness + bluntEdge (外坡口)
bottomY = startY + thickness - grooveDepth (内坡口)
        = startY + thickness - bluntEdge (外坡口)
```

---

## 🔧 削边处理

### 削边位置

- **外削边（outer）**：
  - 外坡口：在上边界
  - 内坡口：在下边界

- **内削边（inner）**：
  - 外坡口：在下边界
  - 内坡口：在上边界

### 削边参数

- **bevelLength**：削边过渡长度（水平方向）
- **bevelHeight**：削边厚度变化量（垂直方向）

---

## 🎨 绘制示例

### 外坡口 - 无削边

```
┌─────────┐  ┌─────────┐  <- 上边界
│         │  │         │
│         │══│         │  <- 钝边
│         │╲╱│         │  <- 坡口
│         │  │         │
└─────────┘  └─────────┘  <- 下边界
```

### 内坡口 - 无削边

```
┌─────────┐  ┌─────────┐  <- 上边界
│         │  │         │
│         │╲╱│         │  <- 坡口
│         │══│         │  <- 钝边
│         │  │         │
└─────────┘  └─────────┘  <- 下边界
```

### 外坡口 - 外削边

```
┌─────────╲  ╱─────────┐  <- 上边界（削边）
│          ╲╱          │
│          ══          │  <- 钝边
│          ╲╱          │  <- 坡口
│          │  │          │
└──────────┘  └──────────┘  <- 下边界
```

### 内坡口 - 内削边

```
┌──────────┐  ┌──────────┐  <- 上边界
│          │  │          │
│          ╲╱          │  <- 坡口
│          ══          │  <- 钝边
│          ╱╲          │
└─────────╱  ╲─────────┘  <- 下边界（削边）
```

---

## 📊 参数接口

```typescript
interface WeldJointParamsV2 {
  // 坡口类型与方向
  grooveType: 'V' | 'U' | 'K' | 'J' | 'X' | 'I'
  groovePosition: 'outer' | 'inner'

  // 左侧板材参数
  leftThickness: number
  leftGrooveAngle: number
  leftGrooveDepth: number
  
  // 左侧削边参数
  leftBevel?: boolean
  leftBevelPosition?: 'outer' | 'inner'
  leftBevelLength?: number
  leftBevelHeight?: number

  // 右侧板材参数
  rightThickness: number
  rightGrooveAngle: number
  rightGrooveDepth: number
  
  // 右侧削边参数
  rightBevel?: boolean
  rightBevelPosition?: 'outer' | 'inner'
  rightBevelLength?: number
  rightBevelHeight?: number

  // 根部参数
  bluntEdge: number
  rootGap: number
}
```

---

## ✅ 优势

1. **逻辑清晰**：绘制顺序明确，易于理解和维护
2. **不需要对齐**：简化了计算，避免了复杂的对齐逻辑
3. **统一的起始点**：右侧板材起始点计算方式统一
4. **支持削边**：完整支持外削边和内削边
5. **易于扩展**：可以轻松添加新的坡口类型

---

## 🧪 测试建议

1. **基本功能测试**
   - 测试不同的坡口类型（V、U、K、J、X、I）
   - 测试内坡口和外坡口
   - 测试不同的板厚组合

2. **削边功能测试**
   - 测试外削边
   - 测试内削边
   - 测试不同的削边长度和高度

3. **边界条件测试**
   - 极小的板厚
   - 极大的板厚
   - 极小的坡口角度
   - 极大的坡口角度

4. **视觉验证**
   - 观察钝边标注线（红色虚线）是否正确
   - 观察根部间隙标注线（蓝色虚线）是否正确
   - 观察削边过渡是否平滑

---

## 📁 文件结构

```
frontend/src/
├── components/WPS/
│   ├── WeldJointDiagramGenerator.tsx      # 旧版本（保留）
│   └── WeldJointDiagramGeneratorV2.tsx    # 新版本
└── pages/
    └── TestWeldJointV2.tsx                # 测试页面
```

---

## 🚀 使用方法

### 1. 导入组件

```typescript
import WeldJointDiagramGeneratorV2 from '@/components/WPS/WeldJointDiagramGeneratorV2'
```

### 2. 使用组件

```typescript
const params = {
  grooveType: 'V',
  groovePosition: 'outer',
  leftThickness: 10,
  leftGrooveAngle: 30,
  leftGrooveDepth: 8,
  rightThickness: 10,
  rightGrooveAngle: 30,
  rightGrooveDepth: 8,
  bluntEdge: 2,
  rootGap: 2
}

<WeldJointDiagramGeneratorV2 params={params} width={800} height={600} />
```

### 3. 访问测试页面

```
http://localhost:3000/test-weld-joint-v2
```

---

## 📝 后续改进

1. **支持更多坡口类型**
   - U型坡口（圆弧过渡）
   - K型坡口（双侧坡口）
   - J型坡口（单侧圆弧）
   - X型坡口（双面坡口）

2. **添加更多标注**
   - 坡口角度标注
   - 坡口深度标注
   - 板厚标注
   - 削边尺寸标注

3. **导出功能**
   - 导出为PNG图片
   - 导出为SVG矢量图
   - 导出为PDF文档

4. **交互功能**
   - 鼠标悬停显示尺寸
   - 点击编辑参数
   - 拖拽调整尺寸

