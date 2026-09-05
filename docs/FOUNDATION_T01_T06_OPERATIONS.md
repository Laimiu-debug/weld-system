# T01～T06 基础修复：部署与复验

## 数据库与服务

1. 在后端目录执行 `python -m alembic upgrade head`。新增 revision `add_attachment_payment_integrity` 创建 `attachments`、`payment_activations`、`payment_notifications`；已经由 bootstrap 创建的表不会重复创建。生产环境执行前按既有运维流程备份。
2. 同步更新后端、前端、Nginx 和 Celery worker/beat。`payments.deliver_notifications` 每分钟读取持久化通知队列；不依赖支付请求即时推送成功。
3. Nginx HTTP/HTTPS 配置都包含附件/私有文档目录拒绝规则。重载前执行 `nginx -t`，部署后验证 `/uploads/files/<文件名>`、`/storage/uploads/files/<文件名>` 和相应 `private_documents` 路径返回 404。授权下载必须使用 `/api/v1/files/<file_id>`。

本轮只在本机隔离 schema 验证迁移，未执行生产迁移、部署或外部支付/邮件调用。本机 Docker 引擎未运行，容器内 Nginx 检查留给部署环境。

## 附件兼容与清理

- 新上传必须带 `resource_type` 和 `resource_id`。当前支持 quality、wps、pqr、ppqr、production、welder、equipment、material，且必须先有业务记录及编辑权限。
- 上传返回的文件编号保持原 `/api/v1/files/{id}` URL 形式；读取时重新验证关联记录和成员权限。文件名或 UUID 本身不代表访问授权。
- 历史磁盘文件没有可信归属元数据时默认返回 404。迁移不删除原文件，也不猜测上传者。可在原业务记录重新上传；需要批量保留原编号时，应先人工核对引用关系和唯一归属，再单独补元数据，不能把共享/冲突引用批量归给某个用户。
- 上传异常清理本次临时文件并回滚元数据。质检页面引用保存失败会调用附件删除；如果引用实际已保存，后端拒绝误删。只允许上传者在仍有业务编辑权限时清理。
- 文件删除先删除元数据，进程在物理删除前退出可能留下不可访问的磁盘孤儿文件；可在确认没有元数据引用后清理。已有引用不自动删除。

## 支付、补偿与通知

- 交易主键对应唯一激活记录，交易行锁及用户/订阅行锁保护并发回调、手工确认和续费。重复回调不再次延期；迟到失败不覆盖成功。不同续费订单各累计一次。
- 回调核验失败不会开通；权益或企业初始化出错，支付状态、订阅、用户和企业数据全部回滚。网关重试或手工确认重试沿用同一个订单号即可补偿，不另建订单。
- 历史 `success` 但权益同步失败的订单可通过统一激活方法重放：只按当前有效订阅修复权益并补激活凭据，不延长期限，不重新激活已取消/过期订阅。
- 通知和支付分开处理。查看 `payment_notifications` 的 `attempts`、`next_attempt_at`、`delivered_at`、`last_error` 定位失败。修复发送通道后会继续重试，失败不会改动已支付权益。
- 站内公告与完成标记原子提交。邮件/短信采用至少一次投递，发送器成功后进程退出可能导致重发；没有宣称跨外部服务的严格恰好一次投递。
- 真实网关扣款、退款和账务对账不属于本次新增行为；M26 等未完成项保持原状态。

## 可复现检查

后端：

```powershell
cd F:/code/weldsystem/backend
python -m pytest tests/unit -q
$env:RUN_LOCAL_DB_TESTS = '1'
python -m pytest tests/integration/test_foundation_integrity.py -q
```

数据库测试仅接受 localhost/127.0.0.1，使用随机 `qa_foundation_*` schema，初始化前验证 search_path，退出时删除；不在 public schema 写测试数据。邮件/短信发送器均被替换，不发送外部消息。

前端：

```powershell
cd F:/code/weldsystem/frontend
npm ci
npm run build:check
npm run lint
npm test
npm audit --registry=https://registry.npmjs.org --audit-level=moderate
```

T06 的本批范围是业务 CRUD/附件成功响应类型、智能导入响应边界和拆出的录入/审核组件。其他接口保持兼容，继续按模块渐进迁移。
