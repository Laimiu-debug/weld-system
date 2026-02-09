# 焊接接头示意图生成器 V2 - 使用指南

## 🚀 快速开始

### 1. 文件位置

```
frontend/src/
├── components/WPS/
│   └── WeldJointDiagramGeneratorV2.tsx    # 新的生成器组件
└── pages/
    └── TestWeldJointV2.tsx                # 测试页面
```

### 2. 启动测试页面

#### 方法1：直接访问（需要配置路由）

```bash
# 启动前端开发服务器
cd frontend
npm run dev

# 访问测试页面
http://localhost:3000/test-weld-joint-v2
```

#### 方法2：在现有页面中使用

```typescript
import WeldJointDiagramGeneratorV2 from '@/components/WPS/WeldJointDiagramGeneratorV2'

const MyComponent = () => {
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

  return (
    <WeldJointDiagramGeneratorV2 
      params={params} 
      width={800} 
      height={600} 
    />
  )
}
```

---

## 📋 参数说明

### 必需参数

| 参数名 | 类型 | 说明 | 示例值 |
|--------|------|------|--------|
| `grooveType` | `'V' \| 'U' \| 'K' \| 'J' \| 'X' \| 'I'` | 坡口型式 | `'V'` |
| `groovePosition` | `'outer' \| 'inner'` | 坡口位置（外坡口/内坡口） | `'outer'` |
| `leftThickness` | `number` | 左侧板厚 (mm) | `10` |
| `leftGrooveAngle` | `number` | 左侧坡口角 (°) | `30` |
| `leftGrooveDepth` | `number` | 左侧坡口深度 (mm) | `8` |
| `rightThickness` | `number` | 右侧板厚 (mm) | `10` |
| `rightGrooveAngle` | `number` | 右侧坡口角 (°) | `30` |
| `rightGrooveDepth` | `number` | 右侧坡口深度 (mm) | `8` |
| `bluntEdge` | `number` | 钝边 (mm) | `2` |
| `rootGap` | `number` | 根部间隙 (mm) | `2` |

### 可选参数（削边）

| 参数名 | 类型 | 说明 | 示例值 |
|--------|------|------|--------|
| `leftBevel` | `boolean` | 左侧是否削边 | `true` |
| `leftBevelPosition` | `'outer' \| 'inner'` | 左侧削边位置 | `'outer'` |
| `leftBevelLength` | `number` | 左侧削边长度 (mm) | `5` |
| `leftBevelHeight` | `number` | 左侧削边高度 (mm) | `2` |
| `rightBevel` | `boolean` | 右侧是否削边 | `true` |
| `rightBevelPosition` | `'outer' \| 'inner'` | 右侧削边位置 | `'outer'` |
| `rightBevelLength` | `number` | 右侧削边长度 (mm) | `5` |
| `rightBevelHeight` | `number` | 右侧削边高度 (mm) | `2` |

---

## 🎨 使用示例

### 示例1：基本V型外坡口

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
```

**效果：**
```
┌─────────┐  ┌─────────┐  <- 上边界
│         │  │         │
│         │══│         │  <- 钝边
│         │╲╱│         │  <- 坡口
│         │  │         │
└─────────┘  └─────────┘  <- 下边界
```

### 示例2：V型内坡口

```typescript
const params = {
  grooveType: 'V',
  groovePosition: 'inner',  // 改为内坡口
  leftThickness: 10,
  leftGrooveAngle: 30,
  leftGrooveDepth: 8,
  rightThickness: 10,
  rightGrooveAngle: 30,
  rightGrooveDepth: 8,
  bluntEdge: 2,
  rootGap: 2
}
```

**效果：**
```
┌─────────┐  ┌─────────┐  <- 上边界
│         │  │         │
│         │╲╱│         │  <- 坡口
│         │══│         │  <- 钝边
│         │  │         │
└─────────┘  └─────────┘  <- 下边界
```

### 示例3：不同板厚

```typescript
const params = {
  grooveType: 'V',
  groovePosition: 'outer',
  leftThickness: 12,   // 左侧12mm
  leftGrooveAngle: 30,
  leftGrooveDepth: 10,
  rightThickness: 8,   // 右侧8mm
  rightGrooveAngle: 30,
  rightGrooveDepth: 6,
  bluntEdge: 2,
  rootGap: 2
}
```

### 示例4：带削边的外坡口

```typescript
const params = {
  grooveType: 'V',
  groovePosition: 'outer',
  leftThickness: 10,
  leftGrooveAngle: 30,
  leftGrooveDepth: 8,
  leftBevel: true,              // 启用削边
  leftBevelPosition: 'outer',   // 外削边
  leftBevelLength: 5,           // 削边长度5mm
  leftBevelHeight: 2,           // 削边高度2mm
  rightThickness: 10,
  rightGrooveAngle: 30,
  rightGrooveDepth: 8,
  rightBevel: true,
  rightBevelPosition: 'outer',
  rightBevelLength: 5,
  rightBevelHeight: 2,
  bluntEdge: 2,
  rootGap: 2
}
```

**效果：**
```
┌─────────╲  ╱─────────┐  <- 上边界（削边）
│          ╲╱          │
│          ══          │  <- 钝边
│          ╲╱          │  <- 坡口
│          │  │          │
└──────────┘  └──────────┘  <- 下边界
```

---

## 🧪 测试步骤

### 1. 基本功能测试

1. 启动开发服务器
2. 访问测试页面
3. 调整参数，观察效果

### 2. 测试项目

- [ ] 外坡口绘制
- [ ] 内坡口绘制
- [ ] 不同板厚
- [ ] 不同坡口角度
- [ ] 不同坡口深度
- [ ] 外削边
- [ ] 内削边
- [ ] 钝边标注（红色虚线）
- [ ] 根部间隙标注（蓝色虚线）

### 3. 预期效果

- ✅ 左侧板材正确绘制
- ✅ 右侧板材正确绘制
- ✅ 钝边位置正确
- ✅ 坡口斜面正确
- ✅ 削边过渡平滑
- ✅ 标注线位置正确

---

## 🔧 常见问题

### Q1: 如何配置路由？

在 `frontend/src/App.tsx` 或路由配置文件中添加：

```typescript
import TestWeldJointV2 from './pages/TestWeldJointV2'

// 在路由配置中添加
{
  path: '/test-weld-joint-v2',
  element: <TestWeldJointV2 />
}
```

### Q2: 为什么看不到图形？

检查以下几点：
1. Canvas是否正确渲染
2. 参数是否有效（板厚、坡口深度等）
3. 浏览器控制台是否有错误

### Q3: 削边效果不明显？

尝试增大削边参数：
- `bevelLength`: 5-10mm
- `bevelHeight`: 2-5mm

### Q4: 如何调整画布大小？

```typescript
<WeldJointDiagramGeneratorV2 
  params={params} 
  width={1000}   // 调整宽度
  height={800}   // 调整高度
/>
```

---

## 📊 与旧版本的区别

| 特性 | 旧版本 | V2版本 |
|------|--------|--------|
| **对齐方式** | 需要设置alignment参数 | 不需要 ✅ |
| **绘制逻辑** | 复杂的条件判断 | 简单清晰 ✅ |
| **代码行数** | ~600行 | ~500行 ✅ |
| **可维护性** | 较低 | 高 ✅ |
| **扩展性** | 较差 | 好 ✅ |

---

## 📝 后续计划

### 短期（1-2周）

- [ ] 添加U型坡口支持
- [ ] 添加K型坡口支持
- [ ] 添加J型坡口支持
- [ ] 添加X型坡口支持
- [ ] 添加I型坡口支持

### 中期（1个月）

- [ ] 优化标注功能
- [ ] 添加尺寸标注
- [ ] 添加导出功能（PNG/SVG/PDF）
- [ ] 添加交互功能

### 长期（3个月）

- [ ] 集成到WPS管理模块
- [ ] 替换旧版本
- [ ] 添加更多坡口类型
- [ ] 添加3D视图

---

## 🤝 贡献

如果你发现问题或有改进建议，请：

1. 在测试页面中测试
2. 记录问题或建议
3. 提交反馈

---

## 📚 相关文档

- [设计文档](./WELD_JOINT_V2_DESIGN.md)
- [确认文档](./WELD_JOINT_V2_CONFIRMATION.md)
- [旧版本文档](./WELD_JOINT_REDESIGN_SUMMARY.md)

---

## ✅ 总结

新版本的焊接接头示意图生成器采用了更清晰的绘制逻辑：

1. **不需要对齐** - 简化了参数和计算
2. **统一起点** - 右侧板材起始点计算统一
3. **清晰顺序** - 绘制顺序明确
4. **易于维护** - 代码简洁，逻辑清晰

开始测试吧！🎉

