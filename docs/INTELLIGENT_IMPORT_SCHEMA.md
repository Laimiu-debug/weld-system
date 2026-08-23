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

当前阶段只完成字段基础、动态 Schema 和编辑入口，尚未实现文件上传、模型调用、额度、审核发布与 PQR 闭环。
