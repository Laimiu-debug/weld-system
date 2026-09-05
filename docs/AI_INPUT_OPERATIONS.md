# AI 输入链路部署与验收

2026-09-05：AI01～AI05 的代码与本地回归完成。用户指定的 DeepSeek 已配置，AI06 的真实 PQR/DOCX 提取及核心字段抽查通过；图纸图签正确，结构识别未通过。详见 [真实模型验收记录](AI06_ACCEPTANCE.md)。本轮未部署。

## 部署

- 同步部署 API、前端、Celery worker 和 beat。本批复用 `extraction_jobs` / `drawing_parse_runs`，没有新增数据库结构；仍需先完成已有迁移。
- 图纸审核页请求 `POST /engineering/revisions/{id}/parse-async`，返回 HTTP 202 和任务 ID；每次模型处理运行于 worker，前端以短请求轮询 `parse-jobs`，刷新页面会恢复最近任务。旧同步接口保留兼容。
- broker 不可用时任务和图纸状态转为失败，用户可重新提交。每个提取任务软限制 29 分钟、硬限制 30 分钟。beat 每 5 分钟回收排队超过 30 分钟或执行超过 40 分钟的 AI 任务，记录失败并退还未结算的平台预占额度。此回收不自动重发外部请求。
- 重新提交创建新任务；worker 用数据库条件更新认领一次。取消、完成和结果替换用数据库锁协调。排队/识别期间版本变化时拒绝覆盖；失败保留原有零件、焊缝及审核数据。
- 管理端配置并测试视觉模型，分配 `drawing_import` / `pqr_import` 路由。图纸使用 advanced；PQR 按页数选择 simple/standard/advanced。前端授权展示和任务提交使用同一路由，配置变化需刷新重新提交。队列不保存 API Key，仅保存配置标识、协议、地址、模型和授权记录；worker 重新取密钥并核对地址/模型，禁用或删除的配置不能回退到另一服务。

## CAD 与 Word

- DXF 依赖 `ezdxf`、`matplotlib`、`pypdf`，支持自包含二维布局。外部参照、图片和未支持三维实体返回导出完整二维 PDF 的提示。
- DWG 另需安装 ODA File Converter，通过 `CAD_DWG_CONVERTER` 指向可执行文件或配置 PATH。能力接口只在依赖和转换器路径可用时列出 DWG；这是运行前检查，最终仍须实际文件转换验收。
- 当前本机 DWG 转换器不可用，未测试真实 DWG。旧版 DOC 解析组件也不可用，上传后应按提示转换为 DOCX/PDF。DOCX 的分页是逻辑分段，不代表 Word 打印页码。

## 验证范围

- 后端使用真实本地 PostgreSQL 的随机隔离 schema，测试后删除；视觉服务使用可控响应，验证三阶段图像请求、字段持久化、失败回滚、OCR 重试和任务生命周期，不测外部模型准确率。
- 前端测试实际图纸审核组件的刷新恢复、失败提示与人工核对提醒；生产构建、类型检查和 ESLint 通过。未运行部署环境的真实 broker/worker/Nginx 联调。
- 用户提供的罐体图纸 PDF（1 页）完成分页与全页渲染；扫描 PQR PDF（10 页）全部渲染成功且全部被标识需要 OCR；DOCX（1 个逻辑分段、4728 字符）成功提取文本；两份 DOC 返回解析组件缺失诊断。
- 样本、文本与图片不提交仓库；本机预检报告和预览位于 `C:/Users/25647/AppData/Local/Temp/weld-ai06`。后续按用户授权将 PDF 图纸、扫描 PQR 和 DOCX 文本发送至指定 DeepSeek 服务；真实调用报告位于同级 `weld-ai06-live`。

可重复预检：在 backend 目录运行：

```powershell
python scripts/verify_ai_samples.py 'C:/Users/25647/OneDrive/Desktop/测试' --output 'C:/Users/25647/AppData/Local/Temp/weld-ai06'
```

报告逐文件记录解析器、页数、OCR 页码、文本长度和文件摘要，不记录正文；任一文件失败时退出码为 1。

## AI06 当前状态

本地平台默认配置为 `DeepSeek V4 Flash Vision`，模型 `deepseek-v4-flash-vision-exp`，地址 `https://api.deepseek.com`，密钥使用应用加密存储。图片连接测试和真实样本调用已完成。新增 `scripts/verify_live_ai06.py` 使用已保存配置执行真实服务链路，替换 broker 派发为进程内 worker 调用，并在本地隔离数据库中保存验收结果。记录的图纸/PQR任务 ID、抽查结果和失败范围见验收报告。

图纸按照可靠的 PDF 文字方向旋转并放大图签，证据坐标映射回原页；只识别到图签时任务返回 `drawing_detail_required`，保留原审核数据并提示补充明细图或人工录入。PQR 每阶段最多提取 12 个映射字段，校验失败时附带具体错误重试一次；已成功 OCR 的页面会复用。供应商失败或截断仍可能产生外部计费，本地任务 token 计数不能代替供应商账单。

图号、产品名、零件关联、焊缝、工艺参数及证据位置始终需要人工核对。完成识别不自动批准版本，也不代表满足生产放行条件。
