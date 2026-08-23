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

字段基础、动态 Schema、编辑入口、暂存数据层、私有原件上传、分页解析、视觉 OCR 和动态结构化提取已经完成；尚未实现额度、审核发布与 PQR 正式闭环。

## 中间数据层

智能导入使用独立的暂存数据，不直接写入正式 WPS/PQR 表：

- `import_batches` 管理批次、目标类型、状态和进度。
- `source_documents` 与 `document_pages` 保存文件元数据、哈希、页码和 OCR 状态。
- `extraction_jobs` 同时记录平台模型、BYOK、离线模型和手工模式，冻结 Schema 快照。
- `extracted_entities`、`extracted_fields` 与 `field_evidence` 保存版本化草稿、字段值及原文证据。
- `import_review_records` 与 `entity_publish_records` 分别记录人工修改和最终正式实体映射。

所有中间表都带个人/企业/工厂工作区字段。手工录入也会创建 `mode=manual` 的已完成任务，因此手工与 AI 不会形成两套业务数据。重复提交手工草稿会关闭旧的当前版本并生成新版本，不覆盖历史结果。

当前开放的基础接口位于 `/api/v1/smart-import`，支持创建/查询批次、登记带 SHA-256 的文档、上传私有原件、触发分页解析、读取页面记录，以及创建手工草稿。OCR/模型调用、审核和正式发布仍属于后续切片。

## 私有原件存储

上传接口采用分块读取，不把整个文件一次性载入内存；读取过程中同时计算 SHA-256 并执行大小上限。当前允许 PDF、Word 和常见扫描图片，并校验文件头与扩展名是否一致。

文件使用随机、不可猜测的存储键保存在 `UPLOAD_DIR/private_documents`，不会复用通用附件的公开下载地址。原始文件名只作为数据库元数据保存。数据库重复检测或登记失败时，刚写入的文件会立即清理；存储服务也拒绝读取或删除私有目录以外的路径。

`DocumentStorage` 是存储适配接口，当前实现为本地私有目录。原件下载必须先通过工作区权限校验，不会暴露物理路径；S3/MinIO 适配器和页面图片预览尚未实现。

## 分页解析与 OCR 边界

- `POST /api/v1/smart-import/documents/{document_id}/parse` 同步生成或替换页面暂存记录，不写入正式 WPS/PQR 数据。
- `GET /api/v1/smart-import/documents/{document_id}/pages` 在工作区权限校验后返回页面文本、OCR 状态和页面元数据。
- PDF 保留物理页码。含足够内嵌文字的页面标记为 `not_required`；图片型且文字不足的页面标记为 `pending`，等待后续 OCR 适配器处理。
- DOCX 没有稳定的物理分页信息，因此只按显式分页符生成逻辑页，并在元数据中记录 `page_numbering=logical`。旧版 DOC 必须先转换为 DOCX 或 PDF。
- PNG/JPEG 按单页、TIFF 按帧建立待 OCR 页面。解析层限制最大页数、单页文本、DOCX 解压规模与压缩比、图片像素，避免异常文件占用过多资源。
- 重复解析会在成功后原子替换旧页面；解析失败保留原文件并记录失败状态，不产生半套页面数据。

## 真实 OCR 与 AI 提取

- `GET /api/v1/smart-import/ai-capabilities` 返回平台服务是否可用、允许的 BYOK 协议/域名和单任务限制，不返回任何密钥。
- `POST /api/v1/smart-import/documents/{document_id}/extract` 接受当前模板或模块 ID。服务端重新生成并冻结动态 Schema，客户端不能提交任意 Schema 绕过字段权限。
- 扫描页先在私有内存中渲染为 PNG，调用视觉模型转写；OCR 文本、置信度和供应商响应号写回 `document_pages`。页面图片不会生成公开 URL。
- 全部页面文本随后作为不可信数据发送给统一 Provider，以 JSON Schema Structured Outputs 提取字段。文档内嵌指令不会作为系统指令执行。
- 平台模式从服务端 `AI_PLATFORM_*` 环境变量读取配置。BYOK Key 只存在于本次请求，不写数据库、任务参数或日志；自定义域名必须在 `AI_BYOK_ALLOWED_HOSTS` 白名单内。
- 当前支持 OpenAI Responses `/responses` 和 OpenAI-compatible `/chat/completions` 两种协议。平台管理员可配置私有模型地址，客户端不能直接访问内网地址。
- 模型输出会再次执行本地 JSON Schema、类型、日期格式、枚举、证据页码和证据原文校验。业务必填字段缺失时允许留空，禁止为了满足 Schema 强迫模型编造。
- 通过校验的结果只写 `extracted_entities`、`extracted_fields` 和 `field_evidence` 暂存层，状态为待审核，不调用正式 WPS/PQR 创建接口。
- `extraction_jobs` 保存 Provider、模型、Prompt 版本、内部追踪号、外部响应号和 Token 用量。正式会员额度预占/结算账本仍是下一阶段。
