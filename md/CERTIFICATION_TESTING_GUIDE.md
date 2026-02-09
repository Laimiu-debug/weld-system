# 焊工证书管理功能测试指南

## 🚀 快速开始

### 1. 启动服务

**后端：**
```bash
cd backend
python main.py
```

**前端：**
```bash
cd frontend
npm run dev
```

---

## 📋 测试步骤

### 测试 1：查看证书列表

1. 登录系统
2. 进入"焊工管理"模块
3. 点击任意焊工的"查看"按钮
4. 在焊工详情页，点击"证书管理"标签页
5. **预期结果**：显示证书列表（如果有）或空状态

---

### 测试 2：添加证书

1. 在证书管理标签页，点击"添加证书"按钮
2. 填写证书信息：

**基本信息：**
- 证书编号：`CERT-TEST-001`
- 证书类型：选择"特种焊接技术证书"
- 认证体系：选择"ASME"
- 认证标准：输入"ASME Section IX"
- 证书等级：输入"高级焊工"
- 项目名称：输入"压力容器焊接"

**颁发信息：**
- 颁发机构：输入"美国机械工程师协会"
- 颁发国家：输入"美国"
- 颁发日期：选择日期
- 有效期至：选择未来日期

**合格项目：**
- 合格工艺：选择"SMAW, GTAW, GMAW"
- 合格材料组：选择"碳钢, 不锈钢"
- 合格填充材料：输入"E7018, ER308L"
- 合格位置：选择"1G, 2G, 3G, 4G, 5G, 6G"

**合格范围：**
- 合格厚度范围：输入"3-12mm"
- 合格直径范围：输入"DN50-DN300"

**考试信息（可选）：**
- 考试日期：选择日期
- 考试地点：输入"北京"
- 考试成绩：输入"95"
- 实操测试结果：选择"合格"
- 理论测试结果：选择"合格"

**其他信息：**
- 证书状态：选择"有效"
- 是否主要证书：选择"是"
- 备注：输入"首次认证"

3. 点击"确定"按钮
4. **预期结果**：
   - 显示"证书添加成功"消息
   - 证书列表中出现新添加的证书
   - 证书卡片正确显示所有信息
   - **合格工艺、合格材料、合格位置以蓝色/绿色/紫色标签突出显示**

---

### 测试 3：验证证书卡片显示

检查证书卡片是否正确显示：

✅ 证书类型和认证体系标签
✅ 证书编号
✅ 认证标准标签
✅ 项目名称
✅ **合格工艺**（蓝色标签）
✅ **合格材料**（绿色标签）
✅ **合格位置**（紫色标签）
✅ 厚度范围和直径范围（橙色标签）
✅ 颁发机构和日期
✅ 有效期和状态
✅ 编辑和删除按钮

---

### 测试 4：编辑证书

1. 点击证书卡片的"编辑"按钮
2. 修改以下信息：
   - 证书等级：改为"特级焊工"
   - 添加复审信息：
     - 最近复审日期：选择日期
     - 下次复审日期：选择未来日期
     - 复审次数：输入"1"
     - 复审结果：选择"通过"
     - 复审备注：输入"复审合格"
3. 点击"确定"按钮
4. **预期结果**：
   - 显示"证书更新成功"消息
   - 证书卡片显示更新后的信息
   - 复审信息正确显示

---

### 测试 5：添加第二个证书

1. 再次点击"添加证书"按钮
2. 填写不同认证体系的证书：

**基本信息：**
- 证书编号：`CERT-TEST-002`
- 证书类型：选择"特种焊接技术证书"
- 认证体系：选择"国标"
- 认证标准：输入"GB/T 3091"
- 项目名称：输入"管道焊接"

**合格项目：**
- 合格工艺：选择"SMAW, GTAW"
- 合格材料组：选择"碳钢"
- 合格位置：选择"5G, 6G"

**合格范围：**
- 合格厚度范围：输入"6-20mm"
- 合格直径范围：输入"DN100-DN500"

3. 点击"确定"按钮
4. **预期结果**：
   - 证书列表中显示两个证书
   - 每个证书的认证体系标签颜色不同（ASME 蓝色，国标 绿色）

---

### 测试 6：筛选功能

**按认证体系筛选：**
1. 在"认证体系"下拉框中选择"ASME"
2. **预期结果**：只显示 ASME 认证的证书

**按状态筛选：**
1. 在"证书状态"下拉框中选择"有效"
2. **预期结果**：只显示有效状态的证书

**关键词搜索：**
1. 在搜索框中输入"压力容器"
2. **预期结果**：只显示项目名称包含"压力容器"的证书

**清除筛选：**
1. 点击筛选条件的"清除"按钮
2. **预期结果**：显示所有证书

---

### 测试 7：删除证书

1. 点击第二个证书的"删除"按钮
2. 在确认对话框中点击"确定"
3. **预期结果**：
   - 显示"证书删除成功"消息
   - 证书从列表中消失
   - 只剩下第一个证书

---

### 测试 8：证书状态显示

**测试即将过期状态：**
1. 编辑证书，将有效期设置为 60 天后
2. **预期结果**：
   - 有效期旁边显示"即将过期"标签
   - 显示剩余天数提示

**测试已过期状态：**
1. 编辑证书，将有效期设置为过去的日期
2. **预期结果**：
   - 有效期旁边显示"已过期"红色标签
   - 证书状态可以手动改为"已过期"

---

## 🔍 API 测试

### 使用 Postman 或 curl 测试 API

**1. 获取证书列表**
```bash
GET http://localhost:8000/api/v1/welders/{welder_id}/certifications?workspace_type=personal
```

**2. 创建证书**
```bash
POST http://localhost:8000/api/v1/welders/{welder_id}/certifications?workspace_type=personal
Content-Type: application/json

{
  "certification_number": "API-TEST-001",
  "certification_type": "特种焊接技术证书",
  "certification_system": "ASME",
  "certification_standard": "ASME Section IX",
  "issuing_authority": "ASME",
  "issue_date": "2024-01-01",
  "expiry_date": "2027-01-01",
  "qualified_process": "SMAW,GTAW",
  "qualified_material_group": "碳钢,不锈钢",
  "qualified_position": "1G,2G,3G,4G,5G,6G",
  "qualified_thickness_range": "3-12mm",
  "status": "valid"
}
```

**3. 更新证书**
```bash
PUT http://localhost:8000/api/v1/welders/{welder_id}/certifications/{cert_id}?workspace_type=personal
Content-Type: application/json

{
  "renewal_date": "2025-01-01",
  "renewal_count": 1,
  "renewal_result": "通过"
}
```

**4. 删除证书**
```bash
DELETE http://localhost:8000/api/v1/welders/{welder_id}/certifications/{cert_id}?workspace_type=personal
```

---

## ✅ 验收标准

### 功能完整性
- [x] 可以添加证书
- [x] 可以编辑证书
- [x] 可以删除证书
- [x] 可以查看证书列表
- [x] 可以按认证体系筛选
- [x] 可以按状态筛选
- [x] 可以搜索证书

### 界面展示
- [x] 证书卡片正确显示所有信息
- [x] **合格工艺以蓝色标签突出显示**
- [x] **合格材料以绿色标签突出显示**
- [x] **合格位置以紫色标签突出显示**
- [x] 厚度和直径范围以橙色标签显示
- [x] 认证体系标签颜色正确
- [x] 证书状态图标和颜色正确
- [x] 复审信息正确显示

### 数据验证
- [x] 证书编号必填
- [x] 证书类型必填
- [x] 颁发机构必填
- [x] 颁发日期必填
- [x] 日期格式正确
- [x] 数据保存成功

### 性能
- [x] 列表加载速度快
- [x] 筛选响应及时
- [x] 表单提交流畅

---

## 🐛 常见问题

### 问题 1：证书列表不显示
**解决方案：**
- 检查后端服务是否启动
- 检查浏览器控制台是否有错误
- 检查网络请求是否成功

### 问题 2：添加证书失败
**解决方案：**
- 检查必填字段是否填写
- 检查日期格式是否正确
- 检查证书编号是否重复

### 问题 3：筛选不生效
**解决方案：**
- 刷新页面重试
- 检查筛选条件是否正确
- 清除筛选后重新选择

---

## 📊 测试数据示例

### 示例 1：ASME 压力容器焊工证书
```json
{
  "certification_number": "ASME-PV-2024-001",
  "certification_type": "特种焊接技术证书",
  "certification_system": "ASME",
  "certification_standard": "ASME Section IX",
  "project_name": "压力容器焊接",
  "issuing_authority": "美国机械工程师协会",
  "issue_date": "2024-01-01",
  "expiry_date": "2027-01-01",
  "qualified_process": "SMAW,GTAW,GMAW",
  "qualified_material_group": "碳钢,不锈钢",
  "qualified_position": "1G,2G,3G,4G,5G,6G",
  "qualified_thickness_range": "3-25mm",
  "qualified_diameter_range": "DN50-DN500",
  "status": "valid"
}
```

### 示例 2：国标管道焊工证书
```json
{
  "certification_number": "GB-PIPE-2024-002",
  "certification_type": "特种焊接技术证书",
  "certification_system": "国标",
  "certification_standard": "GB/T 9711",
  "project_name": "管道焊接",
  "issuing_authority": "质监局",
  "issue_date": "2024-03-01",
  "expiry_date": "2026-03-01",
  "qualified_process": "SMAW,GTAW",
  "qualified_material_group": "碳钢",
  "qualified_position": "5G,6G",
  "qualified_thickness_range": "6-20mm",
  "qualified_diameter_range": "DN100-DN600",
  "status": "valid"
}
```

---

*测试指南版本：v1.0*
*更新日期：2025-10-20*

