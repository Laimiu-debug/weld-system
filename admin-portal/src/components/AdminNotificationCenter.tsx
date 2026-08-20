import React, { useCallback, useEffect, useState } from 'react';
import { Badge, Button, Empty, List, Popover, Space, Spin, Tag, Typography } from 'antd';
import {
  BellOutlined,
  DollarOutlined,
  WarningOutlined,
  ShareAltOutlined,
  RightOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';
import apiService from '@/services/api';

dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

const { Text } = Typography;

type AdminAlertType = 'payment' | 'shared_library' | 'system';

interface AdminAlertItem {
  id: string;
  type: AdminAlertType;
  title: string;
  description: string;
  path: string;
  createdAt?: string;
}

const typeMeta: Record<AdminAlertType, { color: string; icon: React.ReactNode; label: string }> = {
  payment: { color: 'orange', icon: <DollarOutlined />, label: '待确认支付' },
  shared_library: { color: 'blue', icon: <ShareAltOutlined />, label: '共享库审核' },
  system: { color: 'red', icon: <WarningOutlined />, label: '系统告警' },
};

const unwrapList = (payload: unknown): any[] => {
  if (Array.isArray(payload)) return payload;
  if (payload && typeof payload === 'object') {
    const obj = payload as Record<string, unknown>;
    if (Array.isArray(obj.data)) return obj.data;
    if (Array.isArray(obj.items)) return obj.items;
    if (obj.data && typeof obj.data === 'object') {
      const nested = obj.data as Record<string, unknown>;
      if (Array.isArray(nested.items)) return nested.items;
      if (Array.isArray(nested.data)) return nested.data;
    }
  }
  return [];
};

const unwrapTotal = (payload: unknown, fallbackLen: number): number => {
  if (payload && typeof payload === 'object') {
    const obj = payload as Record<string, unknown>;
    if (typeof obj.total === 'number') return obj.total;
    if (obj.data && typeof obj.data === 'object') {
      const nested = obj.data as Record<string, unknown>;
      if (typeof nested.total === 'number') return nested.total;
    }
  }
  return fallbackLen;
};

const AdminNotificationCenter: React.FC = () => {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [items, setItems] = useState<AdminAlertItem[]>([]);
  const [badgeCount, setBadgeCount] = useState(0);

  const loadAlerts = useCallback(async () => {
    setLoading(true);
    const next: AdminAlertItem[] = [];
    let pendingTotal = 0;

    const silent = { silent: true } as any;
    const [paymentsRes, modulesRes, templatesRes, statusRes] = await Promise.allSettled([
      apiService.get('/payments/pending', { params: { status_filter: 'pending_confirm' }, ...silent }),
      apiService.authGet('/shared-library/admin/pending/module', { params: { page: 1, page_size: 5 }, ...silent }),
      apiService.authGet('/shared-library/admin/pending/template', { params: { page: 1, page_size: 5 }, ...silent }),
      apiService.get('/system/status', silent),
    ]);

    if (paymentsRes.status === 'fulfilled') {
      const list = unwrapList(paymentsRes.value);
      pendingTotal += list.length;
      list.slice(0, 5).forEach((row) => {
        next.push({
          id: `payment-${row.order_id || row.transaction_id}`,
          type: 'payment',
          title: `待确认支付 · ${row.user_name || row.user_email || '用户'}`,
          description: `${row.plan_name || '订阅'} · ¥${Number(row.amount || 0).toFixed(2)}`,
          path: '/payments',
          createdAt: row.created_at,
        });
      });
      if (list.length > 5) {
        next.push({
          id: 'payment-more',
          type: 'payment',
          title: `还有 ${list.length - 5} 笔待确认支付`,
          description: '前往支付订单处理',
          path: '/payments',
        });
      }
    }

    if (modulesRes.status === 'fulfilled') {
      const list = unwrapList(modulesRes.value);
      const total = unwrapTotal(modulesRes.value, list.length);
      if (total > 0) {
        pendingTotal += total;
        next.push({
          id: 'shared-module',
          type: 'shared_library',
          title: `${total} 个共享模块待审核`,
          description: '前往共享库管理处理',
          path: '/shared-library',
        });
      }
    }

    if (templatesRes.status === 'fulfilled') {
      const list = unwrapList(templatesRes.value);
      const total = unwrapTotal(templatesRes.value, list.length);
      if (total > 0) {
        pendingTotal += total;
        next.push({
          id: 'shared-template',
          type: 'shared_library',
          title: `${total} 个共享模板待审核`,
          description: '前往共享库管理处理',
          path: '/shared-library',
        });
      }
    }

    if (statusRes.status === 'fulfilled' && statusRes.value) {
      const status = (statusRes.value as any)?.data || statusRes.value;
      if (status?.status && status.status !== 'healthy') {
        pendingTotal += 1;
        next.push({
          id: 'system-status',
          type: 'system',
          title: '系统状态异常',
          description: `CPU ${Math.round(status.cpu_usage || 0)}% · 内存 ${Math.round(status.memory_usage || 0)}%`,
          path: '/system',
        });
      }
    }

    setItems(next);
    setBadgeCount(pendingTotal);
    setLoading(false);
  }, []);

  useEffect(() => {
    void loadAlerts();
    const timer = window.setInterval(() => {
      void loadAlerts();
    }, 60000);
    return () => window.clearInterval(timer);
  }, [loadAlerts]);

  const handleOpenChange = (nextOpen: boolean) => {
    setOpen(nextOpen);
    if (nextOpen) {
      void loadAlerts();
    }
  };

  const handleItemClick = (item: AdminAlertItem) => {
    setOpen(false);
    navigate(item.path);
  };

  const content = (
    <div style={{ width: 360 }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 8,
        }}
      >
        <Text strong>待办通知</Text>
        <Button type="link" size="small" onClick={() => void loadAlerts()}>
          刷新
        </Button>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 24 }}>
          <Spin />
        </div>
      ) : items.length === 0 ? (
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无待办" />
      ) : (
        <List
          size="small"
          dataSource={items}
          renderItem={(item) => {
            const meta = typeMeta[item.type];
            return (
              <List.Item
                style={{ cursor: 'pointer', paddingInline: 4 }}
                onClick={() => handleItemClick(item)}
                actions={[<RightOutlined key="go" style={{ color: '#94a3b8' }} />]}
              >
                <List.Item.Meta
                  avatar={<span style={{ color: '#1F5EFF', fontSize: 16 }}>{meta.icon}</span>}
                  title={
                    <Space size={6}>
                      <Tag color={meta.color} style={{ marginInlineEnd: 0 }}>
                        {meta.label}
                      </Tag>
                      <Text style={{ fontSize: 13 }}>{item.title}</Text>
                    </Space>
                  }
                  description={
                    <Space direction="vertical" size={0}>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {item.description}
                      </Text>
                      {item.createdAt && (
                        <Text type="secondary" style={{ fontSize: 11 }}>
                          {dayjs(item.createdAt).fromNow()}
                        </Text>
                      )}
                    </Space>
                  }
                />
              </List.Item>
            );
          }}
        />
      )}
    </div>
  );

  return (
    <Popover
      content={content}
      trigger="click"
      open={open}
      onOpenChange={handleOpenChange}
      placement="bottomRight"
      arrow
    >
      <Badge count={badgeCount} size="small" overflowCount={99} showZero={false}>
        <Button type="text" icon={<BellOutlined />} style={{ fontSize: 16 }} />
      </Badge>
    </Popover>
  );
};

export default AdminNotificationCenter;
