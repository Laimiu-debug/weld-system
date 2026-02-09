# Blob URL 失效问题修复总结

## 问题描述

在 WPS 编辑页面加载时，出现以下错误：

```
[WPSEdit] 图片 0 包含失效的 blob URL，已跳过: weld_joint_v4_1761810209324.png blob:http://localhost:3000/2d90df25-4e1e-4e64-889b
[WPSEdit] 字段 32fea8e5-87da-4ab5-829c-11d5c237208f_generated_diagram 的所有图片数据已损坏，请重新生成或上传图片
```

### 根本原因

1. **Blob URL 的生命周期限制**：Blob URL（`blob:http://...`）只在创建它的浏览器会话中有效
2. **页面刷新导致失效**：当用户刷新页面或重新加载数据时，之前生成的 blob URL 会失效
3. **数据持久化问题**：焊接接头示意图生成器在生成图片时，使用了 blob URL 而不是 base64 格式保存

## 修复方案

### 1. 修改所有图片生成组件

已修复的文件：
- `frontend/src/components/WPS/WeldJointDiagramV4Field.tsx`
- `frontend/src/components/WPS/DiagramField.tsx`
- `frontend/src/components/WPS/WeldJointDiagramField.tsx`

**问题代码**：
- 将 canvas 转换为 base64 后，再转换为 blob，然后使用 blob URL
- 这导致 blob URL 在页面刷新后失效

**修复方案**：
- 直接使用 canvas 的 base64 URL（`canvas.toDataURL('image/png')`）
- 移除不必要的 blob 转换步骤
- 不保存 `originFileObj`，避免序列化问题

**修复后的代码**：
```typescript
const handleGenerate = (canvas: HTMLCanvasElement) => {
  // 将 canvas 直接转换为 base64 URL（不使用 blob URL）
  const base64Url = canvas.toDataURL('image/png')

  if (!base64Url) {
    message.error('生成图表失败')
    return
  }

  // 创建 UploadFile 对象，直接使用 base64 URL
  const uploadFile: UploadFile = {
    uid: `-${Date.now()}`,
    name: `weld_joint_v4_${Date.now()}.png`,
    status: 'done',
    url: base64Url,  // 使用 base64 URL，这样在页面刷新后仍然有效
    thumbUrl: base64Url
    // 不包含 originFileObj，避免序列化问题
  }

  onChange?.([uploadFile])
  setModalVisible(false)
  message.success('焊接接头示意图生成成功！')
}
```

### 2. 增强 `WPSEdit.tsx` 中的图片验证

**文件**: `frontend/src/pages/WPS/WPSEdit.tsx`

**改进**：
- 添加注释说明 blob URL 在页面刷新后会失效
- 保持现有的 blob URL 过滤逻辑（作为防御性编程）
- 确保只有 base64 格式的图片被保存和恢复

## 关键要点

### ✅ 正确的做法

1. **使用 Base64 格式**：
   - 直接使用 `canvas.toDataURL()` 生成的 base64 URL
   - Base64 URL 可以被序列化、存储和跨会话使用

2. **图片字段处理**：
   - 在 `WeldJointDiagramV4Field.tsx` 中生成 base64 URL
   - 在 `WPSEdit.tsx` 中验证和恢复 base64 URL
   - 在 `moduleToTipTapHTML.ts` 中正确渲染 base64 图片

3. **导出功能**：
   - Word/PDF 导出时使用 `URL.createObjectURL()` 是正确的（用于临时下载）
   - 这些 blob URL 不需要持久化

### ❌ 错误的做法

1. **使用 Blob URL 存储**：
   - 不要将 blob URL 保存到数据库
   - Blob URL 只在当前会话有效

2. **不必要的 Blob 转换**：
   - 不需要将 base64 转换为 blob 再转换回 URL
   - 直接使用 base64 URL 更简单高效

## 测试步骤

1. 打开 WPS 编辑页面
2. 使用焊接接头示意图生成器生成图片
3. 保存 WPS 文档
4. 刷新页面
5. 重新打开 WPS 编辑页面
6. 验证图片能正确加载（不应该看到 blob URL 失效的警告）

## 修复的文件列表

### 前端组件（已修复）
1. `frontend/src/components/WPS/WeldJointDiagramV4Field.tsx` - 焊接接头示意图 V4 字段组件
2. `frontend/src/components/WPS/DiagramField.tsx` - 通用图表字段组件
3. `frontend/src/components/WPS/WeldJointDiagramField.tsx` - 焊接接头示意图字段组件
4. `frontend/src/pages/WPS/WPSEdit.tsx` - WPS 编辑页面（增强了 blob URL 检测）

### 相关文件（无需修改）
- `frontend/src/utils/moduleToTipTapHTML.ts` - 模块转 HTML 工具函数（已正确处理 base64 图片）
- `frontend/src/components/DocumentEditor/WPSDocumentEditor.tsx` - 文档编辑器（已正确处理 base64 图片）
- `backend/app/services/document_export_service.py` - 文档导出服务（已正确处理 base64 图片）

## 性能影响

- **正面**：减少了不必要的 blob 转换，性能略有提升
- **中立**：Base64 URL 长度较长，但在现代浏览器中不是问题
- **中立**：图片数据仍然完整保存，没有数据丢失

