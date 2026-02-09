import React from 'react';
import { Card } from 'antd';

const SystemMonitoring: React.FC = () => {
  return (
    <div>
      <div className="admin-header">
        <h1 className="page-title">系统监控</h1>
      </div>
      <Card>
        <div style={{ textAlign: 'center', padding: '40px', color: '#8c8c8c' }}>
          系统监控功能开发中...
        </div>
      </Card>
    </div>
  );
};

export default SystemMonitoring;