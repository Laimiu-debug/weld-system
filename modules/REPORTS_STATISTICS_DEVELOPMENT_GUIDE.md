# 报表统计模块 - 开发指南

## 📋 模块概述

### 功能定位
报表统计模块用于生成各类数据报表和统计分析，为管理决策提供数据支持。

### 适用场景
- 生成各类业务报表
- 数据统计分析
- 趋势分析和预测
- 数据可视化展示
- 报表导出和打印

### 开发优先级
**第三阶段** - 增强功能，后续开发

---

## 🎯 会员权限

### 访问权限
| 会员等级 | 访问权限 | 功能范围 |
|---------|---------|---------|
| 游客模式 | ❌ 不可访问 | - |
| 个人免费版 | ❌ 不可访问 | - |
| 个人专业版 | ❌ 不可访问 | - |
| 个人高级版 | ✅ 可访问 | 基础报表 |
| 个人旗舰版 | ✅ 可访问 | 完整报表 + 自定义报表 |
| 企业版 | ✅ 可访问 | 完整报表 + 企业报表 |
| 企业PRO | ✅ 可访问 | 完整报表 + 企业报表 |
| 企业PRO MAX | ✅ 可访问 | 完整报表 + 企业报表 |

**重要说明**: 报表统计功能仅对**个人高级版及以上**会员开放。

---

## 📊 功能清单

### 1. 基础报表（高级版及以上）
- **WPS 统计报表**: WPS 数量、状态统计
- **PQR 统计报表**: PQR 数量、合格率统计
- **焊工统计报表**: 焊工数量、证书统计
- **焊材统计报表**: 库存、消耗统计
- **设备统计报表**: 设备数量、使用率统计

### 2. 生产报表（高级版及以上）
- **生产任务报表**: 任务完成情况
- **生产进度报表**: 进度统计分析
- **工时统计报表**: 工时消耗统计
- **效率分析报表**: 生产效率分析

### 3. 质量报表（高级版及以上）
- **质量检验报表**: 检验数量、合格率
- **缺陷统计报表**: 缺陷类型、数量统计
- **不合格品报表**: 不合格品处理情况
- **质量趋势报表**: 质量趋势分析

### 4. 成本报表（旗舰版及以上）
- **焊材成本报表**: 焊材采购、消耗成本
- **人工成本报表**: 人工成本统计
- **设备成本报表**: 设备维护成本
- **项目成本报表**: 项目总成本分析

### 5. 自定义报表（旗舰版及以上）
- **报表模板**: 创建自定义报表模板
- **数据筛选**: 自定义数据筛选条件
- **图表类型**: 选择不同图表类型
- **报表保存**: 保存常用报表配置

### 6. 企业报表（企业版）
- **跨工厂报表**: 多工厂数据对比
- **部门报表**: 各部门数据统计
- **员工报表**: 员工工作量统计
- **综合分析报表**: 企业综合数据分析

### 7. 报表导出
- **导出 PDF**: 导出为 PDF 格式
- **导出 Excel**: 导出为 Excel 格式
- **导出图片**: 导出图表为图片
- **打印报表**: 直接打印报表

---

## 🗄️ 数据模型

### 报表配置表
```sql
CREATE TABLE report_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    
    -- 报表信息
    template_name VARCHAR(255) NOT NULL,           -- 报表名称
    template_type VARCHAR(50),                     -- 报表类型
    description TEXT,                              -- 描述
    
    -- 报表配置
    data_source VARCHAR(100),                      -- 数据源
    filters JSONB,                                 -- 筛选条件
    columns JSONB,                                 -- 显示列
    chart_type VARCHAR(50),                        -- 图表类型
    chart_config JSONB,                            -- 图表配置
    
    -- 权限
    is_public BOOLEAN DEFAULT FALSE,               -- 是否公开（企业内）
    shared_with JSONB,                            -- 共享给的用户
    
    -- 统计
    usage_count INTEGER DEFAULT 0,                 -- 使用次数
    
    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    deleted_at TIMESTAMP,
    
    -- 索引
    INDEX idx_user (user_id),
    INDEX idx_company (company_id),
    INDEX idx_template_type (template_type),
    INDEX idx_deleted (deleted_at)
);
```

---

## 🔌 API接口

### 1. WPS 统计报表
```http
GET /api/v1/reports/wps-statistics?start_date=2025-09-01&end_date=2025-10-16
Authorization: Bearer <token>
```

**响应**:
```json
{
  "success": true,
  "data": {
    "total": 30,
    "by_status": {
      "draft": 5,
      "review": 3,
      "approved": 22
    },
    "by_standard": {
      "AWS D1.1": 15,
      "ISO 15614": 10,
      "GB 50661": 5
    },
    "trend": [
      {"month": "2025-09", "count": 12},
      {"month": "2025-10", "count": 18}
    ]
  }
}
```

### 2. 生产统计报表
```http
GET /api/v1/reports/production-statistics?start_date=2025-09-01&end_date=2025-10-16
Authorization: Bearer <token>
```

### 3. 质量统计报表
```http
GET /api/v1/reports/quality-statistics?start_date=2025-09-01&end_date=2025-10-16
Authorization: Bearer <token>
```

### 4. 自定义报表
```http
POST /api/v1/reports/custom
Authorization: Bearer <token>
Content-Type: application/json

{
  "data_source": "wps_records",
  "filters": {
    "status": "approved",
    "created_at_gte": "2025-09-01"
  },
  "columns": ["wps_number", "title", "status", "created_at"],
  "chart_type": "bar",
  "group_by": "standard"
}
```

### 5. 导出报表
```http
GET /api/v1/reports/{report_id}/export?format=pdf
Authorization: Bearer <token>
```

### 6. 保存报表模板
```http
POST /api/v1/reports/templates
Authorization: Bearer <token>
Content-Type: application/json

{
  "template_name": "月度 WPS 统计",
  "template_type": "wps_statistics",
  "filters": {
    "date_range": "last_month"
  },
  "chart_type": "line"
}
```

---

## 💼 业务逻辑

### 1. WPS 统计
```python
class ReportService:
    def get_wps_statistics(
        self,
        user_id: UUID,
        start_date: date,
        end_date: date,
        db: Session
    ) -> Dict[str, Any]:
        """获取 WPS 统计数据"""
        
        # 总数统计
        total = db.query(WPSRecord).filter(
            WPSRecord.user_id == user_id,
            WPSRecord.created_at >= start_date,
            WPSRecord.created_at <= end_date,
            WPSRecord.deleted_at.is_(None)
        ).count()
        
        # 按状态统计
        by_status = db.query(
            WPSRecord.status,
            func.count(WPSRecord.id)
        ).filter(
            WPSRecord.user_id == user_id,
            WPSRecord.created_at >= start_date,
            WPSRecord.created_at <= end_date,
            WPSRecord.deleted_at.is_(None)
        ).group_by(WPSRecord.status).all()
        
        # 按标准统计
        by_standard = db.query(
            WPSRecord.standard,
            func.count(WPSRecord.id)
        ).filter(
            WPSRecord.user_id == user_id,
            WPSRecord.created_at >= start_date,
            WPSRecord.created_at <= end_date,
            WPSRecord.deleted_at.is_(None)
        ).group_by(WPSRecord.standard).all()
        
        # 趋势分析
        trend = self._calculate_trend(user_id, start_date, end_date, db)
        
        return {
            "total": total,
            "by_status": dict(by_status),
            "by_standard": dict(by_standard),
            "trend": trend
        }
```

### 2. 质量统计
```python
def get_quality_statistics(
    self,
    user_id: UUID,
    start_date: date,
    end_date: date,
    db: Session
) -> Dict[str, Any]:
    """获取质量统计数据"""
    
    inspections = db.query(QualityInspection).filter(
        QualityInspection.user_id == user_id,
        QualityInspection.inspection_date >= start_date,
        QualityInspection.inspection_date <= end_date,
        QualityInspection.deleted_at.is_(None)
    ).all()
    
    total = len(inspections)
    passed = len([i for i in inspections if i.result == "pass"])
    
    # 缺陷统计
    defect_stats = {}
    for inspection in inspections:
        if inspection.defects_found:
            for defect in inspection.defects_found:
                defect_type = defect.get("type", "未知")
                defect_stats[defect_type] = defect_stats.get(defect_type, 0) + 1
    
    # 趋势分析
    trend = self._calculate_quality_trend(inspections)
    
    return {
        "total_inspections": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": round(passed / total * 100, 2) if total > 0 else 0,
        "defect_statistics": defect_stats,
        "trend": trend
    }
```

### 3. 自定义报表生成
```python
def generate_custom_report(
    self,
    user_id: UUID,
    report_config: CustomReportConfig,
    db: Session
) -> Dict[str, Any]:
    """生成自定义报表"""
    
    # 根据配置构建查询
    query = self._build_query(
        report_config.data_source,
        report_config.filters,
        user_id,
        db
    )
    
    # 执行查询
    data = query.all()
    
    # 数据处理
    processed_data = self._process_data(
        data,
        report_config.columns,
        report_config.group_by
    )
    
    # 生成图表数据
    chart_data = self._generate_chart_data(
        processed_data,
        report_config.chart_type,
        report_config.chart_config
    )
    
    return {
        "data": processed_data,
        "chart": chart_data
    }
```

---

## 🔐 权限控制

```python
@router.get("/reports/wps-statistics")
@require_feature("advanced_reports")  # 需要高级版及以上
async def get_wps_statistics(
    start_date: date,
    end_date: date,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取 WPS 统计报表"""
    service = ReportService(db)
    return service.get_wps_statistics(
        current_user.id,
        start_date,
        end_date,
        db
    )

@router.post("/reports/custom")
@require_feature("custom_reports")  # 需要旗舰版及以上
async def generate_custom_report(
    report_config: CustomReportConfig,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """生成自定义报表"""
    service = ReportService(db)
    return service.generate_custom_report(
        current_user.id,
        report_config,
        db
    )
```

---

## 🎨 前端界面

### 报表中心页面
```typescript
// src/pages/Reports/ReportCenter.tsx

const ReportCenter: React.FC = () => {
  const [reportType, setReportType] = useState('wps');
  const [dateRange, setDateRange] = useState([]);
  const { data, loading, refetch } = useReport(reportType, dateRange);
  
  return (
    <div className="report-center">
      <Row gutter={16}>
        <Col span={6}>
          <Menu
            selectedKeys={[reportType]}
            onClick={({ key }) => setReportType(key)}
          >
            <Menu.Item key="wps">WPS 统计</Menu.Item>
            <Menu.Item key="pqr">PQR 统计</Menu.Item>
            <Menu.Item key="production">生产统计</Menu.Item>
            <Menu.Item key="quality">质量统计</Menu.Item>
            <Menu.Item key="custom">自定义报表</Menu.Item>
          </Menu>
        </Col>
        
        <Col span={18}>
          <Card>
            <RangePicker onChange={setDateRange} />
            <Button onClick={refetch}>生成报表</Button>
            <Button onClick={handleExport}>导出</Button>
          </Card>
          
          <Card title="统计数据">
            <Statistic title="总数" value={data.total} />
            <Chart data={data.chart} type={data.chartType} />
          </Card>
          
          <Card title="详细数据">
            <Table dataSource={data.details} />
          </Card>
        </Col>
      </Row>
    </div>
  );
};
```

### 自定义报表构建器
```typescript
// src/pages/Reports/CustomReportBuilder.tsx

const CustomReportBuilder: React.FC = () => {
  const [config, setConfig] = useState<ReportConfig>({});
  
  return (
    <div className="custom-report-builder">
      <Steps current={currentStep}>
        <Step title="选择数据源" />
        <Step title="设置筛选条件" />
        <Step title="选择显示列" />
        <Step title="选择图表类型" />
        <Step title="预览和保存" />
      </Steps>
      
      {currentStep === 0 && <DataSourceSelector onChange={handleDataSourceChange} />}
      {currentStep === 1 && <FilterBuilder onChange={handleFilterChange} />}
      {currentStep === 2 && <ColumnSelector onChange={handleColumnChange} />}
      {currentStep === 3 && <ChartTypeSelector onChange={handleChartChange} />}
      {currentStep === 4 && <ReportPreview config={config} />}
    </div>
  );
};
```

---

## 📝 预定义报表列表

### 1. WPS 相关报表
- WPS 数量统计报表
- WPS 状态分布报表
- WPS 标准分布报表
- WPS 创建趋势报表

### 2. PQR 相关报表
- PQR 数量统计报表
- PQR 合格率报表
- PQR 测试类型分布报表
- PQR 趋势分析报表

### 3. 生产相关报表
- 生产任务统计报表
- 生产进度报表
- 工时统计报表
- 生产效率报表

### 4. 质量相关报表
- 质量检验统计报表
- 合格率趋势报表
- 缺陷类型分布报表
- 不合格品处理报表

### 5. 资源相关报表
- 焊工统计报表
- 焊材库存报表
- 设备使用率报表
- 资源利用率报表

---

**文档版本**: 1.0  
**最后更新**: 2025-10-16  
**开发状态**: 已实现（需测试）

