# 功能完善 TODO

检查日期：2026-09-05。基于已挂载页面与后端调用链检查；未完成真实账号联调的项目不视为验收通过。

当前指令：**已恢复按优先级修复代码，分批验证并记录。** 下文区分「已确认」「完善建议」「待验证」。优先级 P0 为数据隔离问题，P1 为核心功能或业务流程问题，P2 为体验和维护性提升。勾选框代表该条代码修复和本地回归完成；线上部署、真实账号和真实文件验收单独记录，不因勾选而视为完成。

## 第一批：修复已有入口的功能断点

- [x] F01 焊材独立新增页接真实接口，完成分步验证、预览、工作区归属和失败保留输入。
- [x] F02 焊材独立编辑页接真实详情与更新；库存数量通过出入库操作调整，避免编辑覆盖库存。
- [x] F03 焊材详情使用真实资料与分页库存流水，接入已有出入库弹窗、真实删除和 CSV 导出；删除固定演示记录。
- [x] F04 修复生产计划、质量标准、员工绩效、自定义报表搜索使用旧关键词的问题。
- [x] F05 用真实个人/企业账号验收焊材新增→详情→修改→入库→出库→流水→删除；验证失败时不显示成功。已创建专用个人/企业账号，在本地真实 PostgreSQL 和浏览器完成验收；详见批次 9，尚未部署线上。

## 第二批：把登记功能完善为业务流程

- [x] F06 生产计划：日期/数量校验、合法状态流转、真实任务关联与进度汇总、逾期筛选已接入；禁止手填进度及修改已结束计划的任务执行结果。详见批次 10。
- [x] F07 质量标准：校验有效期和版本；检验选择标准后冻结版本、方法及验收项，历史记录不随标准更新改变。详见批次 10。
- [x] F08 员工绩效：选择实际员工，校验月/季度周期和 0～100 分；接入生产/质检参考数据及状态流程，保存人工调分理由和历史。详见批次 10。
- [x] F09 自定义报表：按数据源提供有效字段和操作符，拒绝非法筛选；支持真实数据分组计数、CSV 导出及取数范围说明。详见批次 10。
- [x] F10 焊工履历：加载失败明确提示并可重试，支持增删改和在职时清空结束日期；个人/企业接口及浏览器切换验收通过。详见批次 10。
- [x] F11 员工邀请：个人入口说明企业成员定位，企业入口统一到实际员工/邀请流程；邮件未发出时保留邀请并提供注册链接。详见批次 10；外部邮件投递未验收。

## 必须并行补齐的基础问题（上一轮审查）

- [x] T01 权限拒绝统一抛出 403，统一操作名称并拒绝未知操作；补普通员工修改他人数据、角色企业归属及私有记录列表隔离回归。详见批次 11。
- [x] T02 附件持久化用户/企业/工厂/业务记录归属，下载重新校验业务权限；上传有界读取和失败清理，封堵 Nginx 静态目录绕过。旧无归属附件默认拒绝读取，部署说明见批次 11。
- [x] T03 验证四类业务模型的 access_level 派生契约，补齐工厂筛选和企业公共记录查询；普通员工真实 PostgreSQL 读取通过，越权修改/删除返回 403。详见批次 11。
- [x] T04 支付、订阅、个人权益和企业配额统一事务；数据库行锁及唯一激活凭据保证幂等，失败回滚可重放补偿；通知使用持久化 outbox 独立重试。详见批次 11。
- [x] T05 通用业务 CRUD 的生产计划、质量标准、员工绩效、报表模板均通过明确模型校验；更新合并现值后重新验证，拒绝额外字段和客户端写入归属、审计及快照字段。详见批次 10。
- [x] T06 完成本批渐进治理：业务 CRUD/附件响应模型、智能导入服务响应边界、字段录入/焊工审核弹窗与工具拆分，补失败保留输入、重试及防重复提交交互测试。详见批次 11。

## 验收记录

## 修复批次 12（2026-09-05，AI01～AI06 输入链路）

- AI01～AI05 的代码与本地回归完成；AI06 保留待办。图纸使用持久化后台任务及短轮询，三阶段记录进度；队列故障、模型错误、输出截断和数据库失败有明确诊断，不清空旧审核数据。排队/识别期间版本修改会拒绝覆盖，取消和重复消息不会重复执行或覆盖新任务。
- PQR 批量提取修复缺少 document 参数导致的 500，并按每个文档页数路由。提交保存协议/模型/地址，worker 重新读取密钥并核对配置；停用/删除及路由指纹变化会拒绝静默切换。OCR 失败页面可重试，离线任务不错误要求平台预占额度；结果与结算统一提交。
- CAD 格式列表改为服务器能力驱动；本地 DXF 解析/预览通过，未安装 ODA 时 DWG 不列为可用格式，后端同样拒绝并给出转换提示。
- 验证：678 项后端单测和最初 5 项数据库回归联合通过（683）；最后补齐排队修改、broker 失败、取消与迟到消息后，8 项数据库回归及 30 项相关单测再次通过（38）。前端 13 项测试、类型检查、生产构建、ESLint 通过。数据库只写本地随机隔离 schema 并在测试后清理；模型、broker 边界使用测试替身，不代表外部模型准确率或部署联调。
- 用户指定 `C:/Users/25647/OneDrive/Desktop/测试`：1 页真实罐体 PDF 和 10 页扫描 PQR 完成解析及逐页渲染，PQR 的 10 页全部需要 OCR；DOCX 文本解析成功；两份 DOC 返回本机缺少旧格式解析组件的提示。私有样本及预览留在本机临时目录，没有上传模型、复制进仓库或修改源文件。
- 本批初期 AI06 因未配置模型停留在预检；用户随后授权配置 DeepSeek 并完成下述批次 13 的真实调用。部署和生产 worker/beat/Nginx 仍未验收。详见 [AI 输入运维与验收说明](F:/code/weldsystem/docs/AI_INPUT_OPERATIONS.md)。

## 修复批次 13（2026-09-05，DeepSeek 真实样本验收）

- 已按用户指定配置 `deepseek-v4-flash-vision-exp` 并通过真实图片连接测试；密钥加密保存在本地配置，未写入仓库。10 页扫描 PQR 完成 OCR 并保存 66 个字段，DOCX 保存 61 个字段；两份文件的编号、焊接方法、材料和厚度与原文抽查一致。
- 修复图纸文字方向和图签缩放、图片源页码缺失、证据坐标越界；PQR 校验重试带具体错误，每阶段 12 个字段，限制补充字段输出。真实失败验证了已成功 OCR 页面复用。
- 图纸图号 `26047-001`、名称及版本读取正确，但零件/焊缝曾出现错误推断，最终仅取得图签并返回 `drawing_detail_required`。不把结构可保存或图签正确视为整图准确。AI06 保留未完成，剩余为结构字段与来源核对；真实 DOC/DWG 和生产部署也未验收。
- 真实模型请求、应用服务及数据库落地在隔离 schema 中执行，broker 派发为进程内调用。完整结果、任务 ID、样本摘要及复现方法见 [AI06 验收记录](F:/code/weldsystem/docs/AI06_ACCEPTANCE.md)。
- 验证：全部 685 项后端单元测试通过；补齐新增测试响应的图签证据后，最终 94 项针对性回归全部通过，含 9 项 AI 数据库测试。差异检查通过；隔离验收 schema 已清理，公共加密模型配置保留可用。

## 修复批次 14（2026-09-05，完善 SQ01～SQ07）

- SQ01：生产面板增加当前焊序的已批准领用单选择、过程/完工记录、更多实际参数、实际焊材记录关联、检验入口、执行历史及已放行焊序变更面板。未知请求结果保留完整内容和幂等键，可在同一标签页刷新重试；明确拒绝的请求允许修改后重试。
- SQ02～SQ04：保留冻结依赖、内部 NDE、实时资源资格检查，新增同任务执行行锁、终态拒绝再次执行/派工。真实联调修复下发时未先写入批次导致的外键错误；领用单关联冻结，重放不能更换。并发相同执行请求仅生成一条记录。
- SQ05：分段/跳焊按真实长度生成独立步骤、区间和执行任务；1250 mm 按 500 mm 分段为 500+500+250 mm，跳焊为 1→3→2。策略顺序成为强制依赖，NDE 等全部分段完成；缺失长度或超过数量上限明确拒绝。
- SQ06：修复审批结果不同步和重算提前将申请标为 applied；新增绑定申请重算、审批新方案、应用和再下发完整流程。应用校验申请归属、批准冻结及当前数据版本，停用旧批次但保留任务状态和历史；新批次不自动继承已完成工序。
- SQ07：生成入口使用确认的零件角色与焊缝连接选择容器或通用模板，容器必须明确最终封闭焊缝；结构不明确不按名称强行套用容器步骤。角色、连接和依据写入策略快照；交错策略不宣称三维几何对称或热变形仿真。
- 验证：后端全量单测与最初 5 项数据库流程联合 **717 项通过**；追加并发验证并完善锁/列表过滤后，最终 **84 项针对性测试通过**，含 6 项真实 PostgreSQL 回归。个人账号短时 JWT 经真实认证依赖完成下发/查询，跨账号返回 403。前端全部 **18 项测试**、类型检查、生产构建及本批 ESLint 通过；差异检查通过。数据库只写随机隔离 schema 并在结束后删除，新增回归已纳入 CI。
- 本批没有新增数据库列或部署，既有冻结方案和生产任务不自动改写。企业审批页面人工浏览器验收、现场施工起点/几何关系、WPS 全范围参数比较及返修闭合不因本批勾选而视为完成。操作路径及范围见 [SQ01～SQ07 运维与验收说明](F:/code/weldsystem/docs/SQ01_SQ07_OPERATIONS.md)。

## 本轮优先：智能焊序的 AI 输入链路（2026-09-05）

目标：上传 PDF / CAD 焊缝布置图，由已连接的视觉模型读取图签、零部件、焊缝和要求，形成可人工核对的结构化数据；PQR 上传后识别并生成相关字段，供后续工艺匹配使用。

- [x] AI01 图纸模型边界异常和入库失败返回明确诊断，原审核数据保留；三阶段视觉请求及真实 PostgreSQL 持久化通过本地回归。实际外部模型验收仍属 AI06，详见批次 12。
- [x] AI02 修复 PQR 批量路由参数缺失、离线额度误判及结果/结算事务；扫描页 OCR 失败可重试，字段入库通过本地回归。真实 OCR 精度仍属 AI06。
- [x] AI03 图纸改为持久化队列、HTTP 202 和前端轮询，刷新恢复进度；重复消息、队列故障、取消、过期任务回收及旧结果保护通过本地回归。
- [x] AI04 展示与提交按同一任务路由，提交校验路由指纹；任务固化模型和接收地址，配置变更/停用时拒绝静默切换。
- [x] AI05 按服务器依赖返回 CAD 支持能力；DXF 转换/预览回归通过，缺少有效 ODA 转换器时不展示/接收 DWG，并提示导出 PDF/DXF。真实 DWG 转换仍未验收。
- [ ] AI06 已配置指定 DeepSeek 并完成真实样本调用：扫描 PQR/DOCX 保存字段且核心字段抽查通过，图纸图签正确；零部件/焊缝结构准确性未通过，仍需明细图及人工核对，不能整项标为完成。两份 DOC 缺少解析组件；详见批次 13 和验收记录。

以下为上一轮审查发现的后续待办，按批次推进并记录本地验证结果：

- [x] SQ01 补齐领用单关联、过程/完工记录、实际参数、焊材记录关联、检验入口、执行历史和变更面板；未知结果在当前标签页刷新后复用完整请求。真实 PostgreSQL、个人账号 JWT 接口及前端组件回归通过，部署/企业审批页面现场验收另记。详见批次 14。
- [x] SQ02 执行工序时校验前置工序及质量条件，避免绕过依赖直接完工。
- [x] SQ03 封闭容器前校验内部焊缝的无损检测完成条件。
- [x] SQ04 执行时重新核对焊工资格和设备有效状态，避免派工后过期仍可执行。
- [x] SQ05 分段/跳焊生成带长度区间的实际任务，交错顺序形成强制依赖，NDE 等待全部分段；缺少有效长度拒绝生成。交错不代表三维几何/热变形仿真。详见批次 14。
- [x] SQ06 变更申请审批同步、绑定重算、审批新方案、应用及新版下发形成完整页面和服务流程；应用前检查本申请、冻结与数据版本，原批次停止执行且历史保留。详见批次 14。
- [x] SQ07 以确认的零件角色及焊缝连接选择容器/通用模板，明确最终封闭焊缝；结构不明确时采用通用模板，保留选择依据，避免名称关键词强行套用容器步骤。详见批次 14。

## 验收记录（续）

- 上一轮基线：后端 377 项单测通过；用户端、管理端类型检查通过。
- 第一批 F01～F05 已完成，实施与真实账号验收结果见批次 9。

### 暂停修复时的实际状态

- 之前获得修复授权时，工作区已产生焊材、搜索、权限和 AI 输入链路等改动；本次没有回退或继续修改这些功能代码。
- AI 输入链路已有部分改动：大幅 PDF 渲染限制、OCR 重试、结果结构检查、图纸方向与图签读取、模型路由、超时和 CAD 转换。**这些是进行中的改动，不代表线上故障已经修复。**
- 已完成过一轮 389 项后端单测；之后仍有图纸预处理与 PQR 前端路由改动，故该结果不能作为当前全部改动的最终验收。前端类型检查也早于最后一批前端修改。
- 提供的视觉模型曾通过实际连接测试，并能从合成图片识别图号、零件和焊缝。分阶段真实调用还复现了误旋转、图签丢失、空引用等问题；最后一次完整测试结果未取得，不记为通过。未使用用户真实图纸/PQR完成服务器联调。
- DXF 上传→解析→预览通过本地测试；DWG 转换器未安装、未完成真实 DWG 验收。密钥未写入代码或本文。

## 全模块检查覆盖表

范围按当前用户端和管理端路由整理。这是逐模块的首轮静态审查，部分核心链路深入到服务实现；不是逐页面人工点击验收，也不表示未列出 Bug 的模块没有问题。合并列出的同类子模块共用一项后续检查任务。

| 模块 / 子模块 | 已检查的入口或实现 | 本轮结论 / 待办 |
| --- | --- | --- |
| 登录、注册、验证码、找回密码 | [认证接口](F:/code/weldsystem/backend/app/api/v1/endpoints/auth.py) | M01，补会话失效与失败场景验收 |
| 仪表盘 / 首页 | [仪表盘](F:/code/weldsystem/frontend/src/pages/Dashboard/index.tsx) | M02，核对统计口径和工作区切换 |
| 能力库 / 资格评定 | [能力库](F:/code/weldsystem/frontend/src/pages/CapabilityLibrary/index.tsx)、[评定服务](F:/code/weldsystem/backend/app/services/qualification_service.py) | M03；重点核对规则覆盖与过期来源 |
| 智能导入 / PQR AI | [导入服务](F:/code/weldsystem/backend/app/services/ai_extraction_service.py) | AI01～AI06、SQ08～SQ13 |
| 工程项目 / 图纸审核 | [工程服务](F:/code/weldsystem/backend/app/services/engineering_service.py) | AI01～AI06、SQ08～SQ12 |
| WPS 匹配 / 焊序规划 / 生产放行 | [匹配](F:/code/weldsystem/backend/app/services/matching_service.py)、[焊序](F:/code/weldsystem/backend/app/services/sequence_service.py)、[放行](F:/code/weldsystem/backend/app/services/production_release_service.py) | SQ01～SQ07、SQ14～SQ18 |
| WPS | [WPS 接口](F:/code/weldsystem/backend/app/api/v1/endpoints/wps.py) | M04，状态入口需要审批约束 |
| PQR | [PQR 接口](F:/code/weldsystem/backend/app/api/v1/endpoints/pqr.py) | M05、M06，搜索隔离优先处理 |
| pPQR / 转正式 PQR | [pPQR 服务](F:/code/weldsystem/backend/app/services/ppqr_service.py) | M07、M08 |
| 自定义模块 / 模板 | [模板接口](F:/code/weldsystem/backend/app/api/v1/endpoints/wps_templates.py) | M09，模板变更与历史文件兼容 |
| 共享库 | [共享库服务](F:/code/weldsystem/backend/app/services/shared_library_service.py) | M10，来源版本、重复下载与升级 |
| 全局搜索 | [搜索页](F:/code/weldsystem/frontend/src/pages/Search/SearchResultsPage.tsx) | M11，仅搜索三个类别且结果受限 |
| 焊材 / 库存 / 流水 | [焊材服务](F:/code/weldsystem/backend/app/services/material_service.py) | F01～F05、M12、M13 |
| 焊材用量 / 报价 / 领用 | [领用服务](F:/code/weldsystem/backend/app/services/consumable_issue_service.py) | M14，核对领退用与实物库存闭环 |
| 焊工 / 证书 / 履历 | [焊工详情](F:/code/weldsystem/frontend/src/pages/Welders/WeldersDetail.tsx) | F10、M15、SQ04 |
| 设备 / 维护 / 使用记录 | [设备服务](F:/code/weldsystem/backend/app/services/equipment_service.py) | M16、SQ04 |
| 生产任务 / 生产计划 | [业务接口](F:/code/weldsystem/backend/app/api/v1/endpoints/business_mvp.py)、生产放行服务 | F06、SQ01、SQ02、M17 |
| 质检 / 质量标准 | [质量接口](F:/code/weldsystem/backend/app/api/v1/endpoints/quality.py)、业务接口 | F07、M18 |
| WPS / PQR / 使用报表 / 自定义报表 | [WPS 报表](F:/code/weldsystem/frontend/src/pages/Reports/WPSReport.tsx)、[PQR 报表](F:/code/weldsystem/frontend/src/pages/Reports/PQRReport.tsx)、[使用报表](F:/code/weldsystem/frontend/src/pages/Reports/UsageReport.tsx) | F09、M19～M21 |
| 企业员工 / 工厂 / 部门 / 角色 / 邀请 | [组织接口](F:/code/weldsystem/backend/app/api/v1/endpoints/enterprise_org.py)、[邀请页面](F:/code/weldsystem/frontend/src/pages/Enterprise/Invitations.tsx) | F11、M22 |
| 员工登记 / 绩效 | [绩效页](F:/code/weldsystem/frontend/src/pages/Employees/PerformanceManagement.tsx)、业务接口 | F08、M23 |
| 审批工作流 / 审批记录 | [工作流页面](F:/code/weldsystem/frontend/src/pages/Workflow/ApprovalWorkflows.tsx)、WPS 状态接口 | M04、M24 |
| 个人资料 / 偏好 / 安全 / 通知 | [安全设置](F:/code/weldsystem/frontend/src/pages/Profile/SecuritySettings.tsx)、[通知设置](F:/code/weldsystem/frontend/src/pages/Profile/NotificationSettings.tsx) | M01、M25 |
| 会员 / 订阅 / 支付 / 退款 | [支付服务](F:/code/weldsystem/backend/app/services/payment_service.py) | T04、M26 |
| 帮助 / 反馈 / 公共说明页 | [帮助](F:/code/weldsystem/frontend/src/pages/Help/HelpCenter.tsx)、[反馈接口](F:/code/weldsystem/backend/app/api/v1/endpoints/feedback.py) | M27、M28；公共说明页需另做发布内容核对 |
| 管理端用户 / 企业 / 订阅 / 定价 / 支付 | [管理端路由](F:/code/weldsystem/admin-portal/src/App.tsx)、[用户管理](F:/code/weldsystem/admin-portal/src/pages/UserManagement.tsx)、[支付管理](F:/code/weldsystem/admin-portal/src/pages/PaymentManagement.tsx) | M29，关键管理动作与审计验收 |
| 管理端统计 / 公告 / 反馈 / 共享审核 | [统计](F:/code/weldsystem/admin-portal/src/pages/DataStatistics.tsx)、[公告](F:/code/weldsystem/admin-portal/src/pages/AnnouncementManagement.tsx)、共享库服务 | M30，批量处理结果和口径 |
| 管理端模型配置 / 安全 / 监控 / 运维备份 | [模型配置](F:/code/weldsystem/admin-portal/src/pages/SystemConfig.tsx)、[运维服务](F:/code/weldsystem/backend/app/services/operations_service.py) | M31、M32 |
| 跨模块附件 / 权限 / 工作区 | [权限层](F:/code/weldsystem/backend/app/core/data_access.py)、文件接口与业务接口 | T01～T06、M05、M07 |
| 移动及旧版页面 | App 路由与 MobileOptimized、Reports 目录对照 | M33；未挂载的演示页面不作为线上假数据证据 |

## 智能焊序专项补充 TODO

- [x] SQ21 **P1｜批次 7 新发现并修复：旧资格特批覆盖派工结果。** 批准前检查任务、发布批次和申请新旧顺序，重新检查申请中的焊工、WPS及设备；资源条件不再满足时拒绝批准且不改现有派工。拒绝申请保留现有资源。[特批测试](F:/code/weldsystem/backend/tests/unit/test_resource_override_decision.py)。

- [x] SQ20 **P1｜批次 5 新发现并修复：普通生产接口绕过焊序执行校验。** 已放行焊序任务禁止通过普通任务更新修改工艺、派工资源、质量条件、执行状态及进度；禁止普通进度/生产记录入口回写完工和直接软删除。备注、优先级、计划日期及预计工时仍可编辑；普通手工任务保留原流程。[生产服务](F:/code/weldsystem/backend/app/services/production_service.py)、[入口回归测试](F:/code/weldsystem/backend/tests/unit/test_released_task_mutation.py)。

- [x] SQ19 **P1｜批次 4 新发现并修复：人工修正零件关联及版本映射。** 新增/修改焊缝及修改装配父级时，拒绝跨版本、已删除、不存在或格式无效的零件引用；禁止父子循环。已批准图纸修改生成新版本时，提交的旧零件 ID 映射到新版本零件。[工程服务](F:/code/weldsystem/backend/app/services/engineering_service.py)、[关联回归测试](F:/code/weldsystem/backend/tests/unit/test_engineering_part_links.py)。

- [ ] SQ08 **P1｜已复现、改动待验收：图纸方向不能按线条密度猜。** 合成的正常横向 PDF 被旧预处理旋转 180°，裁剪后模型看不到图签。验收：横图、竖图、倒置扫描、非右下角图签均能保留完整输入和正确证据坐标。[预处理](F:/code/weldsystem/backend/app/services/drawing_preprocessing_service.py:27)
- [x] SQ09 **P1｜批次 8 已完成本地回归：大幅面 PDF 渲染先限制分辨率。** 在栅格分配前限制最长边和像素数；非法尺寸、页码和倍率返回明确错误，越界及编码失败释放原生 PDF 资源。A0/A1、混合页幅、极宽页面及模拟损坏尺寸已验证；真实图纸与模型端验收仍属 AI06。[渲染器](F:/code/weldsystem/backend/app/services/document_page_renderer.py)
- [ ] SQ10 **P1｜已确认：识别需要真正的后台任务与恢复能力。** 目前图纸仍是同步 `/parse` 调用，延长超时只是临时措施。验收：显示当前页/阶段、刷新后继续查看、取消、失败阶段重试；重复点击不重复扣费。[图纸接口](F:/code/weldsystem/backend/app/api/v1/endpoints/engineering.py:271)
- [ ] SQ11 **P1｜已确认、改动待验收：模型输出与入库之间补稳定的数据契约。** 真实调用出现证据为 null、零件 ref 为空等结果；未知参数不能被默认为确定值。验收：保留可用部分、标记待补项，类型错误不变成 500，失败不覆盖上次有效结果。[工程服务](F:/code/weldsystem/backend/app/services/engineering_service.py)
- [ ] SQ12 **P1｜完善建议：图纸审核增加可核对的完整性报告。** 明确识别页数、焊缝总数、疑似漏项、重复编号、连接零件未解析、关键参数无证据；支持对单页/局部区域重识别，避免每次整份重跑。[图纸审核页](F:/code/weldsystem/frontend/src/pages/Engineering/DrawingReview.tsx)
- [ ] SQ13 **P1｜已确认、改动待验收：PQR 扫描判断、失败页重试、空字段处理联动。** 有文字页眉的扫描页和纯矢量轮廓页可能漏 OCR；旧重试只处理 pending 页。验收：文本、扫描、混合、多页 PQR 均生成待审核字段，证据来自原页；缺少字段可补录后继续。[解析器](F:/code/weldsystem/backend/app/services/document_parser_service.py)、[AI 提取](F:/code/weldsystem/backend/app/services/ai_extraction_service.py)
- [x] SQ14 **P1｜已确认：对称策略可能没有改变实际焊接顺序。** 本轮用 4 条同类纵缝运行纯算法，开/关 symmetric 均得到 `WELD-1,2,3,4`；前面的交错排列被后面的优先级排序覆盖。验收：策略改变可观察的施工顺序，同时保留全部强制依赖。[策略](F:/code/weldsystem/backend/app/services/sequence_service.py:330)、[拓扑排序](F:/code/weldsystem/backend/app/services/sequence_service.py:135)
- [ ] SQ15 **P1｜已确认：执行记录需要参数和质量状态校验。** `actual_parameters`、`quality_snapshot` 等作为字典保存，`completed` 可直接令任务进度变 100%；当前方法未比较实参与冻结工艺范围。验收：超范围、缺必检项、返修未闭合时必须阻止完成或走明确偏差审批。[执行服务](F:/code/weldsystem/backend/app/services/production_release_service.py:487)
- [ ] SQ16 **P2｜完善建议：热处理/检测不要只生成统一模板节点。** 现有任一焊缝需 PWHT 即生成整体热处理节点；应支持局部/整体、检测在热处理前或后及多阶段处理，由审核后的工艺要求驱动。验收：不同要求得到不同节点与依赖，不依靠人工备注补业务约束。[模板](F:/code/weldsystem/backend/app/services/sequence_service.py:435)
- [ ] SQ17 **P1｜待验证：来源变更到生产执行的影响提示。** 图纸、WPS、PQR、规则包、匹配冻结版本发生变化时，逐一验证旧焊序是否提示失效、已放行任务是否保留原快照、受影响焊缝是否可追踪。已有冻结/依赖机制，不应误报为“完全没有版本控制”。[匹配服务](F:/code/weldsystem/backend/app/services/matching_service.py)、[焊序服务](F:/code/weldsystem/backend/app/services/sequence_service.py)
- [ ] SQ18 **P2｜完善建议：补可用的施工交付包。** 将焊缝位置、步骤编号、WPS/PQR 版本、检验点、领用材料和执行记录串成可导出/打印的文件；面向车间操作提供逐步确认与扫码定位。验收：从图纸任一焊缝能查到对应施工和检测记录。[焊序页面](F:/code/weldsystem/frontend/src/pages/Engineering/WeldSequencePlanning.tsx)

SQ01～SQ07 的历史复核补充（批次 14 的修复结果优先）：

- SQ01（批次 6 部分完成）：原 `productionRelease` 仅查资格；新增独立生产面板调用实际放行、派工及执行接口，并按焊序查询已放行任务。[生产面板](F:/code/weldsystem/frontend/src/pages/Engineering/ProductionReleasePanel.tsx)、[后端放行接口](F:/code/weldsystem/backend/app/api/v1/endpoints/production_release.py)
- SQ02 / SQ04（批次 2 已修复）：原执行方法仅检查已保存授权；现在按发布快照检查前置任务及关联检验，并重算当前资源资格。[执行服务](F:/code/weldsystem/backend/app/services/production_release_service.py:435)
- SQ03：内部工作追加到封闭依赖的是焊接步骤 `weld`，不是后续的 `nde`；因此图依赖本身不保证内部检测先于封闭。[模板](F:/code/weldsystem/backend/app/services/sequence_service.py:370)
- SQ05 / SQ07：分段/跳焊目前主要进入策略标签和参数，生成入口统一使用压力容器模板；需要分清“显示策略名称”和“生成具体施工步骤”。[模板调用](F:/code/weldsystem/backend/app/services/sequence_service.py:579)

## 其他模块 TODO

- [ ] M01 **P1｜待验证｜账户与安全：** 改密码、重置密码、停用账号、主动退出后，旧访问令牌/刷新令牌和其他设备会话是否按预期失效；同时验收验证码过期、重放、频率限制与会话超时设置。[认证接口](F:/code/weldsystem/backend/app/api/v1/endpoints/auth.py)、[安全设置](F:/code/weldsystem/frontend/src/pages/Profile/SecuritySettings.tsx)
- [ ] M02 **P2｜待验证｜仪表盘：** 工作区、日期和权限变化后，各统计卡片与实际列表保持同口径；区分零记录、加载失败和演示模式。不要把未挂载的 MobileDashboard 演示数据误认成当前首页数据。[首页](F:/code/weldsystem/frontend/src/pages/Dashboard/index.tsx)
- [ ] M03 **P1｜完善建议｜能力库：** 明确展示已支持标准、规则版本和未覆盖条件；补工作区切换后重新加载、上游 PQR 更新后重新评定的验收。当前页面加载依赖为空，切换后是否重新挂载需实测。[能力页](F:/code/weldsystem/frontend/src/pages/CapabilityLibrary/index.tsx:116)、[评定规则](F:/code/weldsystem/backend/app/services/qualification_service.py:311)
- [x] M04 **P1｜已确认｜WPS/审批：** WPS 状态接口只要求模块更新权限，接受请求中的 `approved_by/reviewed_by` 并直接更新状态；补独立审批权限、合法状态流转和操作者身份来源。验收：只有编辑权的人不能通过该接口自行批准。[状态接口](F:/code/weldsystem/backend/app/api/v1/endpoints/wps.py:429)
- [x] M05 **P0｜已确认｜PQR 搜索隔离：** `/pqr/search` 未把当前用户/工作区传入搜索服务；服务从全部 active PQR 开始查询，owner_id 只是可选条件。补强制范围过滤与模块读取权限。验收：普通账号无法搜索另一账号/企业 PQR。[接口](F:/code/weldsystem/backend/app/api/v1/endpoints/pqr.py:472)、[查询](F:/code/weldsystem/backend/app/services/pqr_service.py:356)
- [ ] M06 **P1｜待验证｜WPS/PQR 文件生命周期：** 普通编辑、评定结果更新、删除和导出统一处理“审核中/已批准/已引用”状态；验收直接接口操作也不能静默修改已签发文件，历史版本及引用保持可追溯。[PQR 更新](F:/code/weldsystem/backend/app/api/v1/endpoints/pqr.py:304)、[WPS 更新](F:/code/weldsystem/backend/app/services/wps_service.py:251)
- [x] M07 **P1｜已确认｜pPQR 更新字段：** 接口收任意字典，服务对所有 `hasattr` 字段赋值；增加明确字段白名单及 EDIT 权限校验，禁止修改归属、主键和转换追踪字段。验收普通更新不能改变 user_id/company_id 等。[更新服务](F:/code/weldsystem/backend/app/services/ppqr_service.py:335)
- [ ] M08 **P1｜已确认｜pPQR 转换：** 转换先读标记再创建 PQR，未见行锁；补并发幂等，并明确未完成试验时是“建立草稿”还是“完成转换”。验收重复/并发请求只产生一份目标文件，未完成项目不会被误标为完成。[转换](F:/code/weldsystem/backend/app/services/ppqr_service.py:444)
- [ ] M09 **P2｜完善建议｜模块与模板：** 发布前校验字段类型、单位、重复 key、条件显示和必填规则；增加变更差异及历史模板兼容说明。验收模板修改不破坏已生成 WPS/PQR 的布局与字段解释。[模板接口](F:/code/weldsystem/backend/app/api/v1/endpoints/wps_templates.py)
- [ ] M10 **P2｜完善建议｜共享库：** 下载时提供原作者、来源版本、字段冲突和已下载提示；升级模板时预览差异，保留当前工作区的自定义内容。已有下载和审核流程，重点验收重复下载及版本升级。[共享服务](F:/code/weldsystem/backend/app/services/shared_library_service.py:509)
- [ ] M11 **P2｜已确认｜全局搜索：** 当前只查询 WPS/PQR/焊工，各取前 50 条；失败类别被跳过后仍展示空结果。增加类别分页、部分失败提示，并考虑纳入图纸、焊缝、设备和生产任务。[搜索](F:/code/weldsystem/frontend/src/pages/Search/SearchResultsPage.tsx:45)
- [ ] M12 **P1｜已确认｜焊材批量删除：** 前端请求 `batch-delete`，当前 materials 路由未找到对应后端入口；明确逐项成功/失败以及已被领用/工艺引用的删除限制。[客户端](F:/code/weldsystem/frontend/src/services/materials.ts:320)、[接口](F:/code/weldsystem/backend/app/api/v1/endpoints/materials.py)
- [ ] M13 **P1｜已确认｜库存并发：** 出库先读取库存再修改，未见行锁或条件更新；增加并发库存保护及请求幂等。验收两人同时出库不会超发、丢失扣减或重复流水。[出库](F:/code/weldsystem/backend/app/services/material_service.py:686)
- [ ] M14 **P1｜待验证｜焊材用量/报价/领用：** 对照理论用量、损耗、包装取整、领用、退料、实际消耗与库存流水；建立单一数量来源和差异理由，补跨工厂及重复提交验收。[领用服务](F:/code/weldsystem/backend/app/services/consumable_issue_service.py)
- [ ] M15 **P1｜完善建议｜焊工：** 证书有效期、持证项目、连续焊接经历与真实派工联动；在到期/暂停后禁止继续引用旧资格结论，并提供续证后重新校核。已有证书与履历功能，优先验证执行时状态。[焊工服务](F:/code/weldsystem/backend/app/services/welder_service.py)、[执行授权](F:/code/weldsystem/backend/app/services/production_release_service.py:455)
- [ ] M16 **P1｜已确认｜设备维护：** 服务允许计算结束早于开始的负工时，记录固定为 completed，并以开始日期更新维护周期。补时间顺序、非负时长、计划/进行中/完成区分，完成后再更新统计。[维护服务](F:/code/weldsystem/backend/app/services/equipment_service.py:747)
- [x] M17 **P1｜已修复｜生产计划：** 创建/更新已接入业务模型及状态校验，计划关联与进度汇总见 F06。关联计划不授予焊序下发任务的执行权限；这类任务继续经过专用放行/执行入口，普通接口的限制见 SQ20。[接口](F:/code/weldsystem/backend/app/api/v1/endpoints/business_mvp.py)
- [ ] M18 **P1｜完善建议｜质量管理：** 检验结果关联焊缝、工序、执行批次和当时的验收标准版本；不合格→返修→复检→关闭形成流程，必检未完成阻止后续工序。[质量接口](F:/code/weldsystem/backend/app/api/v1/endpoints/quality.py)、[执行记录](F:/code/weldsystem/backend/app/services/production_release_service.py:501)
- [ ] M19 **P1｜已确认｜WPS/PQR 报表：** 只取首 200 条后在浏览器过滤并汇总，数量增大后统计失真。改用服务端按完整数据和日期聚合；验收超过 200 条仍与明细总数一致。[WPS 报表](F:/code/weldsystem/frontend/src/pages/Reports/WPSReport.tsx:60)、[PQR 报表](F:/code/weldsystem/frontend/src/pages/Reports/PQRReport.tsx:75)
- [ ] M20 **P1｜已确认｜报表占位指标：** WPS 项目数固定为 0；设备利用率、维护时长、完成项目数、效率固定为 0。缺乏数据源时显示“未接入/不可计算”，有数据源后按定义计算。[WPS](F:/code/weldsystem/frontend/src/pages/Reports/WPSReport.tsx:86)、[使用统计](F:/code/weldsystem/frontend/src/pages/Reports/UsageReport.tsx:120)
- [ ] M21 **P1｜已确认｜PQR 检验报表：** 用整体 qualification_result 填拉伸结果，弯曲/冲击/硬度/外观固定横线，已完成直接记 100 分。接入各试样实际结果并移除无依据评分。[报表映射](F:/code/weldsystem/frontend/src/pages/Reports/PQRReport.tsx:107)
- [ ] M22 **P1｜待验证｜企业组织：** 员工离职、禁用、调厂、调部门、角色变化后核对可见数据与待办归属；工厂/部门删除前提示受影响业务记录；邀请补过期、重复接受与撤销验收。[组织接口](F:/code/weldsystem/backend/app/api/v1/endpoints/enterprise_org.py)、[邀请页](F:/code/weldsystem/frontend/src/pages/Enterprise/Invitations.tsx)
- [x] M23 **P2｜已修复｜员工绩效：** 与 F08 合并完成；实际员工 ID 关联并保留姓名资料，展示周期、取数范围和参考统计；人工评分与系统计数分别说明，调分保留前后值及理由。[绩效页面](F:/code/weldsystem/frontend/src/pages/Employees/PerformanceManagement.tsx)
- [ ] M24 **P1｜待验证｜工作流：** 验证审批人在离职/角色变更后的待办处理、流程编辑后在途实例是否保持原步骤，以及拒绝后重新提交与撤回的状态流转；与 M04 的直接改状态入口统一。[工作流](F:/code/weldsystem/frontend/src/pages/Workflow/ApprovalWorkflows.tsx:177)
- [ ] M25 **P2｜待验证｜资料/偏好/通知：** 保存成功后刷新和重新登录仍生效；通知开关应影响实际发送，已读/清空支持失败恢复，设置不串用户或工作区。[通知设置](F:/code/weldsystem/frontend/src/pages/Profile/NotificationSettings.tsx)、[系统设置](F:/code/weldsystem/frontend/src/pages/Profile/SystemSettings.tsx)
- [ ] M26 **P1｜已确认｜退款：** 当前退款函数仅创建 processing 记录，没有调用真实支付网关，也没有完成状态回写。补实际退款、回调/对账、累计退款上限和并发幂等；提交申请不能被描述为退款到账。[退款服务](F:/code/weldsystem/backend/app/services/payment_service.py:576)
- [ ] M27 **P2｜完善建议｜帮助：** 当前仅少量固定说明，补图纸/PQR 支持格式、模型配置、任务错误码、CAD 转换依赖及样例；帮助入口按当前页面定位。[帮助中心](F:/code/weldsystem/frontend/src/pages/Help/HelpCenter.tsx:19)
- [ ] M28 **P2｜完善建议｜反馈：** 在现有提交、已读、管理员备注基础上增加处理中/已解决/待补资料和用户追问；允许附错误编号，避免只有一条备注无法形成问题处理记录。[反馈接口](F:/code/weldsystem/backend/app/api/v1/endpoints/feedback.py)
- [ ] M29 **P1｜待验证｜管理端账户/企业/订阅/定价/支付：** 调整会员、修改套餐、禁用账号、人工确认付款等动作记录原因、前后值和操作者；验证配额即时一致、重复确认幂等、并发操作冲突提示。[用户管理](F:/code/weldsystem/admin-portal/src/pages/UserManagement.tsx)、[支付管理](F:/code/weldsystem/admin-portal/src/pages/PaymentManagement.tsx)
- [ ] M30 **P2｜完善建议｜管理端统计/公告/审核：** 统计与用户端统一日期及订阅口径；批量通知和共享审核返回逐项失败原因及重试入口；公告发布预览与实际终端一致。[统计](F:/code/weldsystem/admin-portal/src/pages/DataStatistics.tsx)、[公告](F:/code/weldsystem/admin-portal/src/pages/AnnouncementManagement.tsx)
- [ ] M31 **P1｜完善建议｜AI 管理配置：** 把“连通性成功”和“图纸/PQR 任务成功”分开显示，保存按任务的最近测试结果、可用协议/图像能力和路由；配置变更后重新测试。单次返回 ok 不能证明实际长文档识别成功。[模型配置](F:/code/weldsystem/admin-portal/src/pages/SystemConfig.tsx)、[连接测试](F:/code/weldsystem/backend/app/services/ai_provider_service.py:259)
- [ ] M32 **P1｜已确认｜备份验证：** 当前按提交的 manifest 与 restore_tested 布尔值登记验证结果，没有在该方法执行恢复。区分“人工登记演练”与“系统实际恢复验证”，后续接入隔离恢复环境及结果证据。[运维服务](F:/code/weldsystem/backend/app/services/operations_service.py:673)
- [ ] M33 **P2｜完善建议｜移动与旧版页面：** 先按当前路由确认哪些页面真正启用，再归档未使用的演示/旧版文件；对图纸审阅、表格和车间任务做小屏操作验收，不以文件名判断已经具备移动功能。[用户端路由](F:/code/weldsystem/frontend/src/App.tsx)、[管理端路由](F:/code/weldsystem/admin-portal/src/App.tsx)

## 分批处理顺序（完成情况见下方记录）

1. PQR 搜索隔离、WPS 审批状态入口、pPQR 更新白名单。
2. 智能焊序图纸/PQR 的真实文件输入链路验收，排除当前未完成修改，再补任务恢复和数据核对。
3. 焊序策略有效性、封闭前检测约束、放行派工入口和执行前置条件。
4. 库存并发、设备维护、质量闭环与源文件版本变更影响。
5. 报表真实统计、企业工作区边界、退款与管理端审计。
6. 模板共享、搜索、帮助、移动端等体验提升。


## 修复批次 1（2026-09-05，已完成本地回归）

| TODO | 本次结果 | 验证 |
| --- | --- | --- |
| M05 | PQR 高级搜索强制传入用户/工作区并校验模块读取权限；可选 owner_id 不能扩大工作区范围。 | 检查真实生成的个人/企业查询 SQL，以及 HTTP 读取权限拒绝和工作区传递。 |
| M04 | 新建、普通更新和状态接口均不能直接写入已审核/已批准状态或伪造/清空签署人；已批准/作废不能直接回草稿，审核中不能直接撤回。最终批准人和时间取自完成的审批实例。 | HTTP 绕过请求、替代更新路径、状态边界和审批签署回写均通过。此条不代表 M06 的全部文档生命周期验收已完成。 |
| M07 | pPQR 更新补 EDIT 权限检查和字段白名单；禁止修改主键、归属、转换标记、审批人；保留 modules_data 兼容输入并拒绝冲突别名。 | 越权、敏感字段注入和合法模块字段保存通过。 |
| SQ03 | 内部焊缝存在 NDE 时，封闭节点依赖 NDE 完成；无 NDE 时仍依赖焊接完成。 | 即使偏好顺序要求先封闭，也不能越过内部 NDE。 |
| SQ14 | 对称策略的交错顺序保留到拓扑排序；显式偏好与强制依赖仍生效。 | 4 条同类焊缝从 1→2→3→4 变为 1→4→2→3，所有依赖仍有效。这是交错排序，不是几何/热变形仿真。 |

验证记录：先完成后端全量 410 项单测；之后补充审批签署处理，再完成 33 项权限/审批/焊序针对性复验。当前前端类型检查通过。本批次新增的测试文件为 [权限边界测试](F:/code/weldsystem/backend/tests/unit/test_document_mutation_boundaries.py)。

限制：没有部署到线上；图纸/PQR 真实文件、生产库与模型配置的完整联调仍在 AI06 中。此前未完成的改动继续保留，未把全部 74 项标为完成。全库差异检查仍包含此前 production.py 改动的行末空格，本批新增修改未引入该问题。

下一批优先：AI01～AI06 的真实输入链路与失败诊断，再处理 SQ02/SQ04 的执行前置工序和实时资格检查；M06/M08 等仍保持未完成。

## 修复批次 2（2026-09-05，已完成本地回归）

- SQ02：执行记录入口依据发布时冻结的强制依赖检查同批次前置任务；前置任务必须有效且完成。要求检验的工序及前置工序必须有真实关联检验且结果为 pass，客户端 quality_snapshot 不能代替检验结果。批次失效或依赖快照缺失时拒绝执行；重复幂等请求仍返回原记录。
- SQ04：每次焊接执行重新读取 WPS、焊工、证书、设备状态和校准日期。失效证书不能通过资料中的旧资格文字兜底；派工证书被删除也需重新核验。特殊授权仅覆盖原审核的资格异常，资格范围或证书变化后需重新授权，设备不可用不由资格特批豁免。
- 验证：新增 [执行条件回归测试](F:/code/weldsystem/backend/tests/unit/test_execution_gates.py) 20 项；后端全量 **431 项通过，50 条警告**。本批服务文件差异检查通过；未修改前端，未部署。
- 范围限制：这是执行服务的本地回归，未做生产库并发或车间页面联调；实际参数与 WPS 范围、返修闭合等仍属 SQ15。无独立证书记录且从未以证书派工的旧焊工资料仍保留原兼容规则。图纸/PQR 真实文件识别验收 AI06 仍未完成。

## 修复批次 3（2026-09-05，AI 输入链路局部修复）

- AI02 / SQ13：空白 OCR 响应不再覆盖原有文本或标为完成，返回具体页码及 empty_ocr_result，页面保持可重试状态；历史上已完成但文本为空的 OCR 页面也会重新处理。真正空白的扫描页仍需人工核对，本批不自动判断并跳过。
- AI01 / SQ11：零件 ref、parent_ref 与焊缝连接引用统一处理数字和首尾空白，避免一端字符串、一端数字导致关联失败；重复零件引用返回 422，避免后一个零件覆盖前一个关联。缺失引用仍生成唯一内部编号；布尔值不作为合法引用。
- AI01 / SQ11：模型输出的字符串长度按零件、焊缝及要求的数据库列上限校验，超长字段在入库前提示具体路径，避免数据库长度异常变成服务器内部错误。
- 以上为局部回归结果，AI01、AI02、SQ11、SQ13 保持未整体勾选。未调用收费模型、未部署，也未使用真实图纸/PQR完成线上验收。
- 验证：识别服务、图纸结果契约、工程解析共 **36 项测试通过**（其中本批新增 14 项）；服务文件差异检查通过。[图纸契约测试](F:/code/weldsystem/backend/tests/unit/test_drawing_result_contract.py)、[OCR 测试](F:/code/weldsystem/backend/tests/unit/test_ai_extraction_service.py)。

## 修复批次 4（2026-09-05，识别后的人工修正）

- SQ19：统一人工新增焊缝、修改焊缝和零件装配关系的关联校验；无效修改在克隆版本、修改实体前返回 422。已批准版本的修正将输入零件 ID 映射到克隆出的新零件，保持原版本数据；不修改调用方输入字典。
- 验证：新增 17 项关联回归测试，连同工程解析、图纸数据契约、匹配、焊序测试，共 **56 项通过**；服务文件差异检查通过。
- 限制：验证基于本地服务和查询条件测试，未做生产数据库或页面联调；本批未部署。历史上已经保存的跨版本关联未自动迁移，SQ17 来源版本影响的完整验收仍待完成。

## 修复批次 5（2026-09-05，防止普通生产接口绕过执行条件）

- SQ20：封堵普通任务更新、进度更新、追加生产记录和删除四个入口；先检查访问权限，再对发布任务执行限制，拒绝时不修改数据。普通任务编辑表单携带相同的受保护字段不阻断备注修改。
- 新增 13 项回归测试，覆盖四条绕过路径、资源/工艺字段篡改、备注编辑以及手工任务兼容。针对性 48 项测试通过，服务文件差异检查通过。
- 最终全量验证：后端 **475 项单测通过，52 条警告**，包含前几批图纸/PQR、人工关联和执行条件改动；本地单测不替代生产库、真实模型与页面联调。

## 修复批次 6（2026-09-05，生产页面入口）

- SQ01 部分完成：焊序规划页新增生产放行与执行面板，支持确认下发、按工序顺序查看任务、检索选择焊工/设备、普通派工及登记完工。支持登记实际电流/电压；前置工序、关联检验及资源资格仍由执行服务检查。
- 新增按焊序查询放行批次的只读接口，检查工作区和读取权限，页面刷新后可重新取得任务。完工失败保留表单；组件存续期间，同一任务重试沿用幂等键，成功后清除。
- 验证：新增 4 项查询/权限测试，连同放行与执行回归共 **35 项通过**；前端 `npm run build:check` 通过（类型检查及 Vite 构建）。构建存在大文件分块警告，未作为失败。差异检查通过。
- 剩余：SQ01 整项不勾选，资格特批、变更申请/应用、领用单选择、执行历史和更多实际参数仍需补齐。未完成真实账号页面操作验收，未部署；刷新页面后的不确定完工请求恢复仍需完善，当前不能声称完整跨刷新幂等。实际参数的工艺范围校验仍属 SQ15。

## 修复批次 7（2026-09-05，资格特批）

- SQ01 部分完成：派工表单增加资格例外理由，资格不足时提交待特批申请，明确显示尚未分配。生产面板显示申请理由、资格问题、处理状态，并接入批准/拒绝及结果刷新；页面刷新后可通过批次详情取得特批记录。
- SQ21：批准前检查任务有效且未完成/取消、批次仍已发布、申请是最新派工记录；复用实时资源检查，使用申请中的焊工和设备评估而不提前修改原派工，验证失败不写入决定。拒绝无需强行满足已失效的资源条件。
- 验证：新增 8 项特批回归测试，连同查询、生产放行和执行测试共 **43 项通过**；前端类型检查及生产构建通过，保留既有大文件分块警告。服务文件差异检查通过。
- 限制：未部署、未完成真实企业账号页面联调；审批权限沿用现有生产模块编辑权限和记录访问控制，没有新增独立审批角色或双人复核制度。并发审批与派工竞争尚未做真实数据库验收。SQ01 仍保留变更流程等剩余工作。
- 限制：未部署、未自动修正历史上被普通接口修改的任务；专用派工/执行/变更的完整前端入口仍属 SQ01，图纸/PQR真实文件识别仍属 AI06，均保持待办。

## 修复批次 8（2026-09-05，图纸输入校验与页面渲染）

- SQ09：PDF 在栅格分配前限制最长边为 6000 像素并检查总像素；拒绝零值、负值和非有限页面尺寸，非法页码/倍率返回明确错误。页码越界、渲染失败及 PNG 编码失败均释放已打开的原生资源；多帧扫描图片在 RGB 解码前检查所选帧的像素数。
- AI01 / SQ11 局部完成：所有识别结果先做结构校验，再读取图签身份字段，修复非视觉解析分支遇到错误 product/evidence/confidence 类型时产生非业务异常的问题。非法数量、负尺寸、越界置信度、NaN/Infinity 及无法表示为有限数的超大整数返回 422；保留未知尺寸 null 和合法零间隙。
- AI01 / SQ11 局部完成：AI 零件父级关联拒绝自循环和多节点循环；未识别父级仍保留在原始结果并追加明确风险。无效证据坐标不再转换为貌似有效的定位框。
- 验证：新增 **62 项回归用例**，覆盖错误结果在身份读取/替换已有数据前被拒绝、事务回滚调用、深层装配关系、A0/A1、混合页幅、极宽 PDF、异常尺寸及资源释放。后端全量 `python -m pytest -q`：**549 项通过，61 条警告**（主要为依赖和日期 API 弃用提示）。本批受版本管理的服务及测试文件差异检查通过。
- 限制：错误结果不触碰旧数据的验证使用服务层模拟数据库，不替代真实 PostgreSQL 事务验收；未调用真实模型、未部署、未改前端。SQ09 按本地实现与回归完成勾选；AI01、SQ11、AI06 仍保留待办，后台任务恢复、真实图纸/PQR、未知数量的持久化语义等不属于本批已完成范围。

## 修复批次 9（2026-09-05，完成第一批 F01～F05）

- F01 / F02：独立新增、编辑页面接入真实服务，共用分步表单；预览读取实际填写值，提交失败保留输入，详情加载失败可重试，显示保存工作区。编辑表单禁改库存及单位，列表编辑同样移除这两个更新字段；后端拒绝绕过页面直接修改，允许清空可选资料，并检查修改后的编号重复。
- F03：详情读取真实资料，接入出入库、删除、CSV 和分页流水。新增时的初始库存同步记录流水；流水稳定排序，修正出库数量双负号、零金额及币种显示；失败显示明确错误和重试。入库、出库和删除均检查业务成功标志，失败不关闭输入或跳转到成功页面。
- 实际联调发现并修复两个 500：流水直接返回 ORM 对象无法序列化，现转为响应模型；参数验证错误包含 ValueError 对象时错误处理器再次序列化失败，现返回稳定的 422。后端拒绝负数和非有限数量/价格，专用出入库对库存行加锁。
- F04：生产计划、质量标准、员工绩效、自定义报表搜索以已提交的新关键词触发加载，并重置页码；重复搜索可刷新，晚返回的旧请求不能覆盖新结果。四个页面均用真实 ALPHA / BETA 记录完成浏览器验收，覆盖换词、清空、同词重搜，以及延迟旧响应后仍显示新关键词结果。
- F05：按用户授权创建专用个人旗舰账号、企业管理员账号及一个隔离校验账号，使用真实登录接口取得会话，在本地 PostgreSQL 的 `qa_materials_f05_20260905` schema 验收。个人、企业分别通过 API 和 Edge 页面完成新增→详情→修改→入库→出库→流水→删除；初始 10、入库 5、出库 3，最终 12，含初始库存共 3 条流水。企业页面通过工作区切换器选取测试企业，创建响应确认企业归属。跨账号读取返回 403，删除后读取返回 404。
- 失败验收：真实超量出库被拒绝且库存不变；页面注入 HTTP 200 / success=false 的新增、入库、删除失败以及 HTTP 500 的出库、流水失败，确认没有误报成功，表单保留输入、删除停留原页、流水重试恢复。CSV 实际下载并核对编号、名称、库存、币种和备注；分页接口使用 limit=1 检查不同流水。故障注入只用于失败分支，成功流程全部调用实际后端。
- 并发验收：真实 PostgreSQL 中库存 10 时并发两笔出库 7，结果为一笔 200、一笔 400，库存 3，仅新增一条出库流水。[接口报告](F:/code/weldsystem/output/materials-first-batch/api-report.json)、[并发报告](F:/code/weldsystem/output/materials-first-batch/concurrency-report.json)、[浏览器与下载证据](F:/code/weldsystem/output/playwright/)。
- 验证：新增 **22 项回归测试**；后端 `python -m pytest tests/unit -q` **571 项通过，64 条警告**。用户端 `npm run type-check`、`npm run build:check` 及本批 11 个页面/组件的 ESLint 通过；本批修改文件差异检查通过。全工作区差异检查仍报告既有 `production.py` 空白问题，本批未修改该文件。保留已有构建分块、Ant Design 组件 API 和依赖弃用提示。
- 环境记录：首次本地数据库初始化接触到旧 public 结构并补建缺失空表，账号写入因旧列缺失回滚；随后改为连接时显式设置隔离 schema，断言 `current_schema()` 后才初始化，全部账号和业务验收数据均在隔离 schema。未操作线上环境，未进行生产数据库迁移或部署；其他批次的企业业务、AI/真实文件验收不因本批完成而视为通过。
- 验收收尾：3 个专用测试账号已停用，临时密码和登录令牌文件已删除，测试浏览器与前后端服务已关闭；隔离 schema 和不含凭据的验收报告保留供复核。

## 修复批次 10（2026-09-05，完成第二批 F06～F11）

| TODO | 本次实现与验收 |
| --- | --- |
| F06 | 校验日期先后、非负有限数量及单位；草稿→批准→进行中→完成，前三个状态可取消。任务与计划必须同工作区、同工厂；已归属其他计划的任务不能重复关联。进度按非取消任务平均计算，完成任务计 100%，无任务计 0%；全部有效任务完成后才允许完成计划。提供逾期筛选，终态禁止修改执行结果；已有任务不会因候选列表上限或搜索被静默解除。个人/企业 API 均验证 0→50→100、非法状态和越权拒绝，浏览器完成日期纠错、新建及关联实际任务。 |
| F07 | 标准有效期及版本必填项校验；变更方法/验收项需更新版本。质检创建选择当前有效标准，保存标准 ID、版本、检验方法和验收项快照；旧检验不随主标准变更，禁止替换既有快照及修改日期绕过原有效期。浏览器核对旧版本 1.0 与新版本 2.0，并修复“下一步”按钮提前触发表单提交的问题，显式保存才创建检验。 |
| F08 | 个人可选本人，企业可选当前工作区在职员工；通过实际用户 ID 关联并保存姓名资料。周期限定月/季度、评分 0～100，草稿→提交→评审→确认，确认后锁定；评审需意见。按生产组长/实际完工日期、检验员/检验日期读取可访问的真实记录，保存参考统计和来源说明，不自动折算评分。每次调分必须提交新的理由，保存前后分值、操作人及时间。实际 API 完成确认流程，浏览器验证员工选择、非法周期、业务失败保留表单及重试。 |
| F09 | 按 WPS/PQR/生产/质量来源提供字段和操作符目录；未知字段、非法值、无效来源和不适用于所选来源的筛选在查询前返回 422。按完整可访问数据计数，支持共有字段分组；超过 1000 分组明确拒绝。页面与 CSV 提供来源、工作区、筛选和计数口径；实际分组结果及下载 CSV 已核对。 |
| F10 | 加载失败显示错误及重试，成功零记录才显示空状态；请求序号防止旧响应覆盖，工作区改变时清除旧记录和编辑状态。在职选项可靠清空结束日期，后端允许清空可选字段并对部分更新合并后的日期进行校验。个人/企业真实 API 完成增删改；浏览器完成新增→在职修改→删除，注入加载 500 后重试恢复，并验证企业切到个人后不显示企业履历。 |
| F11 | 旧员工入口在企业工作区转到实际企业成员管理，个人工作区显示定位和切换指引；成员管理与邀请管理互通。创建/重发按实际 email_sent 提示；邮件未发出仍可查看邀请并复制注册链接。真实测试账号通过创建→重发→接受，错误账号接受被拒绝；浏览器完成入口跳转、创建警告、查看注册链接及取消邀请。 |

- 验证：新增 [49 项业务回归测试](F:/code/weldsystem/backend/tests/unit/test_business_workflows_f06_f11.py)；后端 `python -m pytest tests/unit -q` **620 项通过，64 条警告**。用户端 `npm run build:check`（含 TypeScript 检查及生产构建）和本批 18 个文件的 ESLint 均通过；本批受版本管理文件差异检查通过。保留既有构建分块和组件/依赖弃用提示。
- 联调环境：按已有授权创建 3 个专用账号，在本地隔离 PostgreSQL schema `qa_business_f06_f11_20260905` 和 Edge 中验收；初始化前断言实际 schema。成功流程调用真实后端，仅对履历加载 500、绩效保存 success=false 注入失败。报告：[F06～F09 接口](F:/code/weldsystem/output/business-second-batch/api-report.json)、[F10/F11 接口](F:/code/weldsystem/output/business-second-batch/history-invitation-report.json)、[最终接口检查](F:/code/weldsystem/output/business-second-batch/final-api-report.json)、[浏览器验收](F:/code/weldsystem/output/business-second-batch/browser-report.json)、[CSV 下载](F:/code/weldsystem/output/playwright/f09-report.csv)。
- 上线前必须执行 [新增数据库迁移](F:/code/weldsystem/backend/migrations/add_business_workflows_f06_f09.sql)，增加计划关联、标准快照、绩效证据/调整理由和报表分组字段；隔离 schema 已重复执行两次并核对 6 个字段。旧数据不伪造关联或历史标准快照，页面明确显示未保存快照的情况。手工任务与焊序下发任务保留各自执行限制；绩效为人工评审，报表仍以记录计数为指标。
- 限制：未部署、未迁移生产数据库。邀请邮件使用本地失败接收器，未向外部邮箱发送邮件；已验证失败提示及真实邀请接受，实际邮件服务投递仍需部署环境验证。本批不代表完整质检返修闭环 M18、独立审批制度或其他未勾选项完成。
- 收尾：专用测试账号均已停用，无待接受测试邀请；临时密码、令牌及登录脚本已删除，测试浏览器和前后端服务关闭，保留隔离 schema 与不含凭据的报告。关联重复项 T05、M17、M23 同步完成。


## 修复批次 11（2026-09-05，T01～T06 基础问题）

- T01 / T03：核对已有异常拒绝与模型访问级别兼容实现，补上未知操作拒绝、角色与企业绑定、工作区用户/工厂一致性、企业私有记录的列表隔离。生产计划、质量标准、绩效、报表模板使用实际数据库验证普通员工可读企业公共记录，不能修改或删除他人记录；不能跨企业访问。T05 的既有严格输入模型、合并更新校验随全量业务测试复验。
- T02：新增 `attachments` 元数据，上传前校验关联业务的编辑权限，按 64 KiB 上限读取；空文件、超限、读取异常或数据库失败均清理本次文件。下载复核当前记录权限和归属，失效成员、删除记录或归属变化不能读取。前端保存图片引用失败时尝试清理；已真实保存的引用不能被不确定请求后的清理误删。Nginx 的 HTTP/HTTPS、用户端及管理端配置禁止静态读取 `files` 和 `private_documents` 目录。
- T04：用交易、用户及订阅行锁串行化开通，`payment_activations` 主键约束阻止重复激活。支付状态、订阅期限、会员权限及企业/默认工厂/员工初始化、企业配额在同一事务提交；失败全部回滚，重试不重复延期。历史成功但权益未同步的订单可重放修复权益，不重算期限、不恢复已失效订阅。核对回调金额、币种和渠道，迟到失败不能撤销成功订单。新建升级从实际支付时间计费，同级企业续费同步企业期限。
- T04 通知：`payment_notifications` 唯一事件键记录待发送通知，Celery beat 每分钟触发处理；失败以退避间隔重试。通知及其已发送标记使用事务/保存点，通知失败不影响支付。实际外部邮件/短信未发送，测试替换外部发送器。站内通知避免重复；外部发送采用至少一次语义，外部已接收但进程在落库前退出的极端情况下仍可能重复。
- T06：新增通用成功响应模型，应用于四类业务 CRUD 和附件；智能导入服务统一兼容原始响应及成功信封，`success=false` 转为明确失败。拆出 `ManualFieldModal`、`WelderReviewModal` 和字段/供应商工具；新增任务阻止重复提交，失败保留表单，任务加载错误可重试。保留其他模块的渐进迁移空间，不宣称全项目接口和大页面均完成治理。
- 验证：668 项后端单测通过；真实 PostgreSQL 隔离 schema 回归最终 20 项通过，包含并发续费、故障回滚、通知重试、附件 HTTP 权限和迁移重复升级/回退。前端 11 项测试通过，包含真实页面组件的失败/重试/防重复提交及编辑器内容回存。用户端类型检查、生产构建、ESLint 和管理端类型检查通过；构建仍有既有大分块提示。后端先完成 668 单测 + 19 数据库项的联合回归，随后增加历史订单补偿测试并复验全部支付/数据库用例。
- 依赖与 CI：加入前端交互测试及 PostgreSQL 回归门禁。审计发现现有 Tiptap 原型污染漏洞，统一升级 Tiptap 至 3.31.3 并验证 WPS 文本、格式、表格和图片回存；用户端官方 registry 审计为 0 漏洞。
- 部署与边界：新增 [数据库迁移](F:/code/weldsystem/backend/alembic/versions/add_attachment_payment_integrity.py)，需要在上线前运行 `alembic upgrade head` 并同步更新 Nginx、worker/beat。本轮没有迁移生产库或部署；本机 Docker 引擎未运行，Nginx 容器运行验收未执行。旧附件不按文件名推测所有者，需从原业务记录重新上传，或在核对唯一归属后单独迁移元数据。
- 验收环境：全部数据库写入只发生于随机生成的 `qa_foundation_*` schema，初始化前断言当前 schema，测试结束删除。测试用户使用不可登录密码，不创建可用账号、令牌或支付凭据。报告：[后端联合回归](F:/code/weldsystem/output/foundation-t01-t06/backend-tests.txt)、[支付最终复验](F:/code/weldsystem/output/foundation-t01-t06/payment-recheck.txt)。部署细节见 [基础修复运维说明](F:/code/weldsystem/docs/FOUNDATION_T01_T06_OPERATIONS.md)。
