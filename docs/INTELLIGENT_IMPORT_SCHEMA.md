# 智能导入字段与动态 Schema 说明

## 目标

智能导入不绑定某一家大模型，也不改变现有手工录入流程。模块库仍是字段结构的唯一来源；AI 只依据当前模块或模板生成带证据的待确认草稿。

## 三层标识

1. 模块字段键：现有 `fields` JSON 对象的键，用于表单读写。
2. `field_id`：字段不可变 UUID，用于字段改名、审核记录和证据关联。旧字段会按模块 ID 和字段键生成稳定 UUID。
3. `canonical_field_key`：可选的平台语义键，例如 `base_material.specification`。它让不同企业、不同中文标签的字段共享提取和规则语义；企业特有字段可以不映射。

## AI 字段配置

- `auto`：进入动态提取 Schema。
- `manual`：仅手工填写，不发送给模型。
- `derived`：由确定性计算或规则产生，不发送给模型。
- `disabled`：不参与智能导入。
- `confidence_threshold`：低于阈值的结果必须人工确认。
- `use_in_rules`：是否允许作为确定性规则的输入，默认关闭。

文件、图片字段不会作为结构化值直接提取。每个可提取字段的输出都包含 `value`、`confidence` 和 `evidence`；证据包含页码、原文片段和可选区域坐标。

## 接口

- `GET /api/v1/custom-modules/semantic-fields/registry`：语义字段字典，可按 `module_type` 筛选。
- `GET /api/v1/custom-modules/{module_id}/extraction-schema`：单模块动态 Schema。
- `GET /api/v1/wps-templates/{template_id}/extraction-schema`：模板及重复模块实例的动态 Schema。

接口沿用现有身份验证、工作区和模块访问控制。生成 Schema 不调用模型、不消耗额度，也不写入正式业务数据。

## 兼容与版本

迁移 `add_module_ai_metadata` 只为 `custom_modules` 增加 `schema_version`，旧字段在读取或更新时自动补齐默认 AI 元数据。字段定义发生更新后模块版本递增；未来的导入任务必须保存该版本，确保结果可重现。

字段基础、动态 Schema、编辑入口和暂存数据层已经完成；尚未实现文件二进制上传、模型调用、额度、审核发布与 PQR 闭环。

## 中间数据层

智能导入使用独立的暂存数据，不直接写入正式 WPS/PQR 表：

- `import_batches` 管理批次、目标类型、状态和进度。
- `source_documents` 与 `document_pages` 保存文件元数据、哈希、页码和 OCR 状态。
- `extraction_jobs` 同时记录平台模型、BYOK、离线模型和手工模式，冻结 Schema 快照。
- `extracted_entities`、`extracted_fields` 与 `field_evidence` 保存版本化草稿、字段值及原文证据。
- `import_review_records` 与 `entity_publish_records` 分别记录人工修改和最终正式实体映射。

所有中间表都带个人/企业/工厂工作区字段。手工录入也会创建 `mode=manual` 的已完成任务，因此手工与 AI 不会形成两套业务数据。重复提交手工草稿会关闭旧的当前版本并生成新版本，不覆盖历史结果。

当前开放的基础接口位于 `/api/v1/smart-import`，支持创建/查询批次、登记带 SHA-256 的文档，以及创建手工草稿。文件二进制存储、OCR/模型调用、审核和正式发布仍属于后续切片。
