import React from 'react';
import { Spin } from 'antd';

interface LoadingSpinnerProps {
  size?: 'small' | 'default' | 'large';
  tip?: string;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ size = 'large', tip = '加载中...' }) => {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
      }}
    >
      <Spin size={size} />
      {tip && (
        <div style={{ marginLeft: 12, color: '#666' }}>
          {tip}
        </div>
      )}
    </div>
  );
};

export default LoadingSpinner;
