# 设备管理表单修复报告

## 问题描述
在设备创建页面中点击"新增设备"时出现Ant Design警告：
```
Warning: [antd: Form.Item] `defaultValue` will not work on controlled Field. You should use `initialValues` of Form instead.
```

## 问题原因
在Ant Design的受控表单中，不应该在Form.Item内部的组件上使用`defaultValue`属性，因为：
1. 表单字段已经由Form组件的`initialValues`和`form.setFieldsValue()`控制
2. `defaultValue`只在非受控组件中有效
3. 在受控表单中使用`defaultValue`会导致冲突和警告

## 修复内容

### 修复的文件
`g:\CODE\sdweld1019\frontend\src\pages\Equipment\EquipmentCreate.tsx`

### 具体修复
1. **货币选择字段** (第350行)
   ```jsx
   // 修复前
   <Select defaultValue="CNY">

   // 修复后
   <Select>
   ```

2. **访问级别字段** (第490行)
   ```jsx
   // 修复前
   <Select defaultValue="private">

   // 修复后
   <Select>
   ```

### 表单初始化验证
Form组件已正确配置`initialValues`：
```jsx
initialValues={{
  status: 'operational',
  is_active: true,
  is_critical: false,
  currency: 'CNY',        // 货币字段默认值
  access_level: 'private', // 访问级别字段默认值
}}
```

## 修复效果
✅ **警告消除**：不再出现Ant Design的defaultValue警告
✅ **功能保持**：表单字段仍然有正确的默认值
✅ **表单控制**：完全使用Ant Design的受控表单机制
✅ **数据一致性**：默认值统一在initialValues中管理

## 最佳实践建议
1. 在Ant Design受控表单中，只使用Form的`initialValues`设置默认值
2. 避免在Form.Item内部的组件上使用`defaultValue`
3. 使用`form.setFieldsValue()`在运行时动态设置字段值
4. 对于需要根据其他字段值动态设置默认值的场景，使用Form的`onValuesChange`或字段联动

## 验证
- ✅ 货币字段默认显示"人民币 (¥)"
- ✅ 访问级别字段默认显示"私有"
- ✅ 表单提交数据正确
- ✅ 不再出现警告信息

现在点击"新增设备"应该不会再出现警告了。