# 焊接接头示意图生成器 V4

## 概述

WeldJointDiagramGeneratorV4 是一个参数化的焊接坡口图形生成器，用于生成焊接工艺规程（WPS）中的接头横截面示意图。

## 核心功能

### ✅ 1. 内外坡口支持
- **外坡口（outer）**：从板材外侧（远离焊接区域）开坡口，常用于单面焊接
- **内坡口（inner）**：从板材内侧（靠近焊接区域）开坡口，常用于管道内部焊接

### ✅ 2. 左右不同厚度板材
- 左右板材可以设置不同的厚度
- 左右板材可以设置不同的坡口角度
- 左右板材可以设置不同的坡口深度

### ✅ 3. 削边（钝边）实现
- 支持左右板材独立配置削边参数
- **削边位置**：
  - 外削边：在远离坡口的一侧削边
  - 内削边：在靠近坡口的一侧削边
- **削边参数**：
  - 削边长度：水平过渡长度
  - 削边高度：厚度变化量

### ✅ 4. 三种对齐方式
- **中心线对齐（centerline）**：左右板材中心线对齐，适用于等厚度或对称焊接
- **外侧对齐（outer_flush）**：外表面齐平
  - 外坡口时：上表面齐平
  - 内坡口时：下表面齐平
- **内侧对齐（inner_flush）**：内表面齐平
  - 外坡口时：下表面齐平
  - 内坡口时：上表面齐平

## 技术实现

### 绘制逻辑

采用**8点逆时针绘制模式**（借鉴V3版本）：

#### 左侧板材8个关键点（逆时针）：
1. P0：左下角
2. P1：削边过渡点（如果有内削边）
3. P2：右下角（坡口起点下方）
4. P3：坡口底部（钝边起点）
5. P4-P5：钝边（水平线）
6. P6：坡口斜面
7. P7：削边过渡点（如果有外削边）
8. P8：左上角

#### 右侧板材8个关键点（逆时针）：
类似左侧板材，但从根部间隙右侧开始

### 坐标系统

- **原点**：画布中心
- **X轴**：向右为正
- **Y轴**：向下为正
- **缩放比例**：6（1mm = 6px）

### 对齐方式实现

通过计算Y轴偏移量（yOffset）来实现不同的对齐方式：

```typescript
const calculateYOffsets = (p: WeldJointParamsV4): { left: number; right: number } => {
  const leftThickness = p.leftThickness * SCALE
  const rightThickness = p.rightThickness * SCALE
  
  if (p.alignment === 'centerline') {
    // 中心线对齐
    return {
      left: -leftThickness / 2,
      right: -rightThickness / 2
    }
  } else if (p.alignment === 'outer_flush') {
    // 外侧对齐
    if (p.groovePosition === 'outer') {
      return { left: 0, right: 0 }  // 上表面齐平
    } else {
      return { left: -leftThickness, right: -rightThickness }  // 下表面齐平
    }
  } else {
    // 内侧对齐
    if (p.groovePosition === 'outer') {
      return { left: -leftThickness, right: -rightThickness }  // 下表面齐平
    } else {
      return { left: 0, right: 0 }  // 上表面齐平
    }
  }
}
```

## 参数接口

```typescript
interface WeldJointParamsV4 {
  // 坡口类型与方向
  grooveType: 'V' | 'U' | 'X' | 'I'
  groovePosition: 'outer' | 'inner'

  // 左侧板材参数
  leftThickness: number
  leftGrooveAngle: number
  leftGrooveDepth: number
  leftBevel?: boolean
  leftBevelPosition?: 'outer' | 'inner'
  leftBevelLength?: number
  leftBevelHeight?: number

  // 右侧板材参数
  rightThickness: number
  rightGrooveAngle: number
  rightGrooveDepth: number
  rightBevel?: boolean
  rightBevelPosition?: 'outer' | 'inner'
  rightBevelLength?: number
  rightBevelHeight?: number

  // 根部参数
  bluntEdge: number
  rootGap: number

  // 对齐方式
  alignment: 'inner_flush' | 'outer_flush' | 'centerline'
}
```

## 使用示例

```tsx
import WeldJointDiagramGeneratorV4 from './components/WPS/WeldJointDiagramGeneratorV4'

function App() {
  return (
    <WeldJointDiagramGeneratorV4 
      onGenerate={(canvas) => {
        console.log('图表已生成', canvas)
      }}
    />
  )
}
```

## 典型应用场景

### 场景1：等厚度板材对接（中心线对齐）
```typescript
{
  grooveType: 'V',
  groovePosition: 'outer',
  alignment: 'centerline',
  leftThickness: 12,
  rightThickness: 12,
  leftGrooveAngle: 30,
  rightGrooveAngle: 30,
  leftGrooveDepth: 10,
  rightGrooveDepth: 10,
  bluntEdge: 2,
  rootGap: 2
}
```

### 场景2：不等厚度板材对接（外侧对齐）
```typescript
{
  grooveType: 'V',
  groovePosition: 'outer',
  alignment: 'outer_flush',
  leftThickness: 12,
  rightThickness: 10,
  leftGrooveAngle: 30,
  rightGrooveAngle: 35,
  leftGrooveDepth: 10,
  rightGrooveDepth: 8,
  bluntEdge: 2,
  rootGap: 2
}
```

### 场景3：带削边的板材对接
```typescript
{
  grooveType: 'V',
  groovePosition: 'outer',
  alignment: 'centerline',
  leftThickness: 12,
  rightThickness: 12,
  leftGrooveAngle: 30,
  rightGrooveAngle: 30,
  leftGrooveDepth: 10,
  rightGrooveDepth: 10,
  leftBevel: true,
  leftBevelPosition: 'outer',
  leftBevelLength: 15,
  leftBevelHeight: 2,
  rightBevel: true,
  rightBevelPosition: 'inner',
  rightBevelLength: 15,
  rightBevelHeight: 2,
  bluntEdge: 2,
  rootGap: 2
}
```

### 场景4：内坡口焊接（管道内部）
```typescript
{
  grooveType: 'V',
  groovePosition: 'inner',
  alignment: 'outer_flush',
  leftThickness: 10,
  rightThickness: 10,
  leftGrooveAngle: 30,
  rightGrooveAngle: 30,
  leftGrooveDepth: 8,
  rightGrooveDepth: 8,
  bluntEdge: 2,
  rootGap: 2
}
```

## 版本对比

| 特性 | V1 | V2 | V3 | V4 |
|------|----|----|----|----|
| 内外坡口支持 | ✅ | ✅ | ✅ | ✅ |
| 左右不同厚度 | ✅ | ✅ | ✅ | ✅ |
| 削边实现 | ⚠️ 复杂 | ⚠️ 简单 | ❌ 不完整 | ✅ 完整 |
| 对齐方式 | ✅ | ❌ | ❌ | ✅ |
| 坡口深度配置 | ✅ | ✅ | ❌ 仅全焊透 | ✅ |
| UI表单 | ✅ | ❌ | ❌ | ✅ |
| 代码清晰度 | ⚠️ 一般 | ✅ | ✅ | ✅ |
| 8点绘制模式 | ❌ | ❌ | ✅ | ✅ |

## 改进点

相比前三个版本，V4版本的主要改进：

1. **综合了V3的8点绘制模式**：逻辑清晰，易于理解和维护
2. **恢复了V1的完整参数系统**：支持所有必要的参数配置
3. **改进了削边实现**：支持内外削边，逻辑清晰
4. **完整的对齐方式支持**：三种对齐方式，适应不同应用场景
5. **完整的UI表单**：用户友好的参数输入界面
6. **代码结构优化**：函数职责清晰，易于扩展

## 未来扩展

可能的扩展方向：

1. 支持U型和J型坡口的圆弧绘制
2. 支持双面坡口（X型坡口）
3. 支持更多坡口类型（K型、复合型等）
4. 添加尺寸标注线
5. 支持导出为SVG格式
6. 支持焊缝填充显示
7. 支持多层多道焊接路径显示

## 维护说明

### 关键函数

- `calculateLeftPlatePoints()`: 计算左侧板材的8个关键点
- `calculateRightPlatePoints()`: 计算右侧板材的8个关键点
- `calculateYOffsets()`: 根据对齐方式计算Y轴偏移
- `drawPlate()`: 绘制板材轮廓
- `drawAnnotations()`: 绘制标注信息
- `drawWeldJoint()`: 主绘制函数

### 修改建议

1. 修改坡口形状：在 `calculateLeftPlatePoints()` 和 `calculateRightPlatePoints()` 中调整点的计算逻辑
2. 添加新的对齐方式：在 `calculateYOffsets()` 中添加新的分支
3. 修改标注样式：在 `drawAnnotations()` 中调整绘制代码
4. 添加新参数：在 `WeldJointParamsV4` 接口中添加，并在相应函数中使用

## 作者

开发日期：2025-10-24
版本：V4

