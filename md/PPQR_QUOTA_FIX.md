# pPQR 配额统计修复说明

## 问题描述

pPQR 列表页面显示配额使用情况为 "0 / 200",但实际上已经创建了 5 个 pPQR。

## 根本原因

pPQR 列表页面使用 `user.ppqr_quota_used` 来显示配额,但这个字段只在个人工作区更新。在企业工作区中,这个值始终为 0。

WPS 和 PQR 使用的是当前列表的实际数量 (`stats.total` 或 `wpsData?.data?.total`),所以显示正确。

## 解决方案

修改 `frontend/src/pages/pPQR/PPQRList.tsx` 文件,将配额显示从使用 `user.ppqr_quota_used` 改为使用 `stats.total`。

## 需要修改的代码

**文件**: `frontend/src/pages/pPQR/PPQRList.tsx`

**位置**: 第 608-635 行

### 修改 1: 第 614 行 ✅ (已完成)

```typescript
// 修改前
pPQR配额使用情况: {user.ppqr_quota_used || 0} / {getPPQRQuota(user.member_tier || 'free')}

// 修改后
pPQR配额使用情况: {stats.total} / {getPPQRQuota((user as any)?.member_tier || user?.membership_tier || 'free')}
```

### 修改 2: 第 619 行 ❌ (待完成)

```typescript
// 修改前
{Math.round(((user.ppqr_quota_used || 0) / getPPQRQuota(user.member_tier || 'free')) * 100)}%

// 修改后
{Math.round((stats.total / getPPQRQuota((user as any)?.member_tier || user?.membership_tier || 'free')) * 100)}%
```

### 修改 3: 第 624 行 ❌ (待完成)

```typescript
// 修改前
percent={Math.round(((user.ppqr_quota_used || 0) / getPPQRQuota(user.member_tier || 'free')) * 100)}

// 修改后
percent={Math.round((stats.total / getPPQRQuota((user as any)?.member_tier || user?.membership_tier || 'free')) * 100)}
```

### 修改 4: 第 626 行 ❌ (待完成)

```typescript
// 修改前
(user.ppqr_quota_used || 0) >= getPPQRQuota(user.member_tier || 'free')

// 修改后
stats.total >= getPPQRQuota((user as any)?.member_tier || user?.membership_tier || 'free')
```

## 完整的修改后代码

```typescript
        {/* 配额进度条 */}
        {user && (
          <div style={{ marginBottom: '16px' }}>
            <Row justify="space-between" align="middle">
              <Col>
                <Text type="secondary">
                  pPQR配额使用情况: {stats.total} / {getPPQRQuota((user as any)?.member_tier || user?.membership_tier || 'free')}
                </Text>
              </Col>
              <Col>
                <Text type="secondary">
                  {Math.round((stats.total / getPPQRQuota((user as any)?.member_tier || user?.membership_tier || 'free')) * 100)}%
                </Text>
              </Col>
            </Row>
            <Progress
              percent={Math.round((stats.total / getPPQRQuota((user as any)?.member_tier || user?.membership_tier || 'free')) * 100)}
              status={
                stats.total >= getPPQRQuota((user as any)?.member_tier || user?.membership_tier || 'free')
                  ? 'exception'
                  : 'active'
              }
              strokeColor={{
                '0%': '#108ee9',
                '100%': '#87d068',
              }}
            />
          </div>
        )}
```

## 手动修改步骤

1. 在 VS Code 中打开 `frontend/src/pages/pPQR/PPQRList.tsx`
2. 按 `Ctrl+G` 跳转到第 619 行
3. 将 `user.ppqr_quota_used || 0` 替换为 `stats.total`
4. 将 `user.member_tier || 'free'` 替换为 `(user as any)?.member_tier || user?.membership_tier || 'free'`
5. 重复步骤 2-4 修改第 624 行和第 626 行
6. 保存文件

## 验证

修改完成后,刷新浏览器,应该看到:
- 上面蓝色 Alert: `pPQR配额使用情况: 5/200` ✅
- 下面白色文字: `pPQR配额使用情况: 5 / 200` ✅ (修改后)
- 进度条显示: `2.5%` ✅

