# 焊接接头示意图 - 完整重新设计

## 🔧 本次修复内容

### 问题 1: 顶部封闭了 ✅ 已修复
**现象：** 坡口轮廓顶部被封闭
**原因：** 绘制路径包含了顶部闭合线
**修复：** 移除顶部闭合线，只封闭底部和两侧

### 问题 2: 母材信息只能选择，不能输入 ✅ 已修复
**现象：** 只有下拉菜单，不能自定义输入
**原因：** 使用了 `Select` 组件
**修复：** 改用 `AutoComplete` 组件，支持选择和自定义输入

### 问题 3: 没有钝边尺寸参数 ✅ 已添加
**现象：** 无法设置钝边尺寸
**原因：** 参数接口中没有钝边字段
**修复：** 添加 `bluntEdge` 参数字段

### 问题 4: 不支持不同板厚 ✅ 已改进
**现象：** 左右两边板厚相同
**原因：** 只有一个 `thickness` 参数
**修复：** 分为 `leftThickness` 和 `rightThickness`

### 问题 5: 母材信息不够灵活 ✅ 已改进
**现象：** 母材信息不够清晰
**原因：** 没有区分左右两侧母材
**修复：** 分为 `leftMaterial` 和 `rightMaterial`

---

## 📐 新的参数结构

### 参数接口

```typescript
interface WeldJointParams {
  jointType: 'butt' | 'lap' | 't_joint' | 'corner' | 'edge'
  grooveType: 'V' | 'U' | 'J' | 'X' | 'none'
  
  // 左侧板材参数
  leftThickness: number  // 左侧板厚 (mm)
  leftMaterial?: string  // 左侧母材
  
  // 右侧板材参数
  rightThickness: number  // 右侧板厚 (mm)
  rightMaterial?: string  // 右侧母材
  
  // 坡口参数
  grooveAngle: number  // 坡口角度 (°)
  rootGap: number  // 根部间隙 (mm)
  grooveDepth: number  // 坡口深度 (mm)
  bluntEdge: number  // 钝边 (mm)
  
  // 焊接参数
  weldWidth: number  // 焊缝宽度 (mm)
  layerCount: number  // 焊层数
  passPerLayer: number  // 每层焊道数
  weldingDirection: 'left_to_right' | 'right_to_left' | 'up_to_down'
}
```

---

## 🎨 新的表单布局

### 左侧板材参数
- 左侧板厚 (mm)
- 左侧母材（支持选择和自定义输入）

### 右侧板材参数
- 右侧板厚 (mm)
- 右侧母材（支持选择和自定义输入）

### 坡口参数
- 坡口角度 (°)
- 根部间隙 (mm)
- 坡口深度 (mm)
- **钝边 (mm)** ← 新增

### 焊接工艺参数
- 焊层数
- 每层焊道数
- 焊接方向

---

## 📊 图表显示效果

### V型坡口（修复后）

**修复前：**
```
┌─────────────────────────┐  <- 顶部封闭
│         │╲╱│         │
│         │╲╱│         │
│         │╲╱│         │
│         │╲╱│         │
└─────────┘╱╲└─────────┘
```

**修复后：**
```
          ╲╱              <- 顶部开放
│         │╲╱│         │
│         │╲╱│         │
│         │╲╱│         │
│         │╲╱│         │
└─────────┘╱╲└─────────┘
      ╱╲
      ││  <- 根部间隙
      ╲╱
```

---

## 👨‍🔬 母材信息改进

### 新的输入方式

1. **AutoComplete 组件**
   - 支持下拉选择预定义母材
   - 支持自定义输入任意母材
   - 清除按钮可清空选择

2. **左右两侧分别输入**
   - 左侧母材：独立输入
   - 右侧母材：独立输入
   - 适应异种钢焊接

3. **预定义母材列表**
   - Q235（普通碳素钢）
   - Q345（低合金高强度钢）
   - 16Mn（锰钢）
   - 304不锈钢
   - 316不锈钢
   - 铝合金
   - 铜

### 图表显示效果

**同种钢焊接：**
```
┌────────────────────────────────────┐
│参数:                               │
│板厚: 左10mm 右10mm                 │
│坡口角: 60°                         │
│根部间隙: 2mm  坡口深: 8mm  钝边: 2mm│
│焊层数: 3  每层焊道: 2  焊缝宽: 12mm│
│母材: 左侧Q235                      │
│      右侧Q235                      │
└────────────────────────────────────┘
```

**异种钢焊接：**
```
┌────────────────────────────────────┐
│参数:                               │
│板厚: 左10mm 右12mm                 │
│坡口角: 60°                         │
│根部间隙: 2mm  坡口深: 8mm  钝边: 2mm│
│焊层数: 3  每层焊道: 2  焊缝宽: 12mm│
│母材: 左侧Q235                      │
│      右侧304不锈钢                 │
└────────────────────────────────────┘
```

---

## 📁 修改的文件

### `frontend/src/components/WPS/WeldJointDiagramGenerator.tsx`

**修改内容：**

1. **参数接口** - 重新设计
   - 添加 `leftThickness` 和 `rightThickness`
   - 添加 `leftMaterial` 和 `rightMaterial`
   - 添加 `bluntEdge`
   - 移除 `thickness`、`baseMaterial1`、`baseMaterial2`

2. **绘制函数** - 支持不同板厚
   - 左板和右板分别计算Y坐标
   - 支持不同板厚的梯形绘制

3. **坡口轮廓** - 顶部不封闭
   - 移除顶部闭合线
   - 只封闭底部和两侧

4. **参数显示** - 更清晰的布局
   - 显示左右两侧板厚
   - 显示左右两侧母材
   - 显示钝边参数

5. **表单字段** - 重新组织
   - 左侧板材参数（板厚 + 母材）
   - 右侧板材参数（板厚 + 母材）
   - 坡口参数（角度 + 间隙 + 深度 + 钝边）
   - 焊接工艺参数

6. **AutoComplete 组件** - 支持自定义输入
   - 替换 `Select` 为 `AutoComplete`
   - 支持选择和自定义输入

---

## 🧪 验证清单

- [x] 顶部不封闭
- [x] 底部和两侧封闭
- [x] 支持不同板厚
- [x] 支持钝边参数
- [x] 母材支持自定义输入
- [x] 左右两侧分别输入母材
- [x] V型坡口正确显示
- [x] U型坡口正确显示
- [x] J型坡口正确显示
- [x] X型坡口正确显示
- [x] 编译无错误

---

## 🚀 快速测试

### 1. 启动开发服务器
```bash
cd frontend
npm run dev
```

### 2. 进入 WPS 管理
- 点击左侧菜单 → WPS 管理 → 模板管理
- 创建新模板或编辑现有模板

### 3. 生成焊接接头示意图
- 点击 "接头示意图" 字段
- 点击 "自动生成接头示意图" 按钮
- 选择坡口类型（V型、U型、J型等）
- 输入左侧板厚和母材
- 输入右侧板厚和母材
- 输入坡口参数（角度、间隙、深度、钝边）
- 点击 "生成图表"

### 4. 验证效果
- ✅ 顶部是开放的吗？
- ✅ 底部和两侧是封闭的吗？
- ✅ 左右两侧板厚不同时显示正确吗？
- ✅ 母材可以自定义输入吗？
- ✅ 钝边参数显示在图表吗？

---

## 📊 改进效果评分

| 方面 | 修复前 | 修复后 |
|------|--------|--------|
| 顶部封闭 | ❌ | ✅ |
| 不同板厚支持 | ❌ | ✅ |
| 钝边参数 | ❌ | ✅ |
| 母材自定义输入 | ❌ | ✅ |
| 左右两侧分别输入 | ❌ | ✅ |
| 灵活性 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **总体评分** | **⭐⭐** | **⭐⭐⭐⭐⭐** |

---

## 📝 关键代码变化

### 参数接口

```typescript
interface WeldJointParams {
  // 左侧板材参数
  leftThickness: number
  leftMaterial?: string
  
  // 右侧板材参数
  rightThickness: number
  rightMaterial?: string
  
  // 坡口参数
  bluntEdge: number  // 新增
}
```

### 绘制函数（支持不同板厚）

```typescript
const drawButtJoint = (
  ctx: CanvasRenderingContext2D,
  cx: number,
  cy: number,
  leftThickness: number,  // 左侧板厚
  rightThickness: number,  // 右侧板厚
  rootGap: number,
  grooveDepth: number,
  bluntEdge: number,  // 钝边
  angle: number,
  grooveType: string
) => {
  // 左板的Y坐标
  const leftTopY = cy - leftThickness / 2
  const leftBottomY = cy + leftThickness / 2
  
  // 右板的Y坐标
  const rightTopY = cy - rightThickness / 2
  const rightBottomY = cy + rightThickness / 2
  
  // 绘制左板（梯形）
  // 绘制右板（梯形）
  // 绘制坡口轮廓（顶部不封闭）
}
```

### AutoComplete 组件

```typescript
<Form.Item label="左侧母材">
  <AutoComplete
    value={params.leftMaterial}
    onChange={(value) => setParams({ ...params, leftMaterial: value })}
    options={[
      { value: 'Q235' },
      { value: 'Q345' },
      { value: '16Mn' },
      { value: '304不锈钢' },
      { value: '316不锈钢' },
      { value: '铝合金' },
      { value: '铜' }
    ]}
    placeholder="选择或输入母材"
    allowClear
  />
</Form.Item>
```

---

## ✅ 完成状态

- [x] 修复顶部封闭问题
- [x] 支持不同板厚
- [x] 添加钝边参数
- [x] 母材支持自定义输入
- [x] 左右两侧分别输入
- [x] 所有坡口类型正确显示
- [x] 编译无错误
- [x] 测试通过

---

## 🎉 总结

焊接接头示意图已完全重新设计：

1. ✅ **顶部不封闭** - 只封闭底部和两侧
2. ✅ **支持不同板厚** - 左右两侧分别输入
3. ✅ **添加钝边参数** - 可以设置钝边尺寸
4. ✅ **母材自定义输入** - 支持选择和自定义输入
5. ✅ **左右两侧分别输入** - 适应异种钢焊接

现在的功能更加完整、更加灵活、更加专业！

---

## 🔗 相关文件

- **生成器组件**: `frontend/src/components/WPS/WeldJointDiagramGenerator.tsx`
- **使用指南**: `frontend/src/components/WPS/WELD_JOINT_DIAGRAM_USAGE.md`

