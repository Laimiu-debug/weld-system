/**
 * 附件上传和预览组件
 */
import React, { useState } from 'react';
import { Upload, Button, List, Image, Modal, message } from 'antd';
import { UploadOutlined, EyeOutlined, DeleteOutlined, FilePdfOutlined, FileImageOutlined } from '@ant-design/icons';
import type { UploadFile, UploadProps } from 'antd';
import type { AttachmentItem } from '../../../services/certifications';

interface AttachmentUploadProps {
  value?: AttachmentItem[];
  onChange?: (value: AttachmentItem[]) => void;
  maxCount?: number;
}

/**
 * 附件上传组件
 */
const AttachmentUpload: React.FC<AttachmentUploadProps> = ({
  value = [],
  onChange,
  maxCount = 5,
}) => {
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [previewVisible, setPreviewVisible] = useState(false);
  const [previewUrl, setPreviewUrl] = useState('');
  const [previewType, setPreviewType] = useState<'image' | 'pdf'>('image');

  // 上传配置
  const uploadProps: UploadProps = {
    name: 'file',
    action: '/api/v1/upload/certification-attachment',  // 需要实现这个上传接口
    headers: {
      authorization: `Bearer ${localStorage.getItem('token')}`,
    },
    fileList,
    maxCount,
    accept: '.pdf,.jpg,.jpeg,.png',
    beforeUpload: (file) => {
      const isValidType = file.type === 'application/pdf' || file.type.startsWith('image/');
      if (!isValidType) {
        message.error('只能上传 PDF 或图片文件！');
        return false;
      }
      const isLt10M = file.size / 1024 / 1024 < 10;
      if (!isLt10M) {
        message.error('文件大小不能超过 10MB！');
        return false;
      }
      return true;
    },
    onChange: (info) => {
      setFileList(info.fileList);
      
      if (info.file.status === 'done') {
        message.success(`${info.file.name} 上传成功`);
        
        // 更新附件列表
        const newAttachment: AttachmentItem = {
          name: info.file.name,
          url: info.file.response?.data?.url || '',
          type: info.file.type?.startsWith('image/') ? 'image' : 'pdf',
          size: info.file.size,
        };
        
        const newAttachments = [...value, newAttachment];
        onChange?.(newAttachments);
      } else if (info.file.status === 'error') {
        message.error(`${info.file.name} 上传失败`);
      }
    },
  };

  // 预览文件
  const handlePreview = (attachment: AttachmentItem) => {
    setPreviewUrl(attachment.url);
    setPreviewType(attachment.type as 'image' | 'pdf');
    setPreviewVisible(true);
  };

  // 删除附件
  const handleDelete = (index: number) => {
    const newAttachments = value.filter((_, i) => i !== index);
    onChange?.(newAttachments);
    
    // 同步更新 fileList
    const newFileList = fileList.filter((_, i) => i !== index);
    setFileList(newFileList);
  };

  // 格式化文件大小
  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '-';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
  };

  return (
    <div>
      <Upload {...uploadProps}>
        <Button icon={<UploadOutlined />} disabled={value.length >= maxCount}>
          上传附件
        </Button>
        <span style={{ marginLeft: 8, color: '#999', fontSize: 12 }}>
          支持 PDF、JPG、PNG 格式，最多 {maxCount} 个文件，单个文件不超过 10MB
        </span>
      </Upload>

      {value.length > 0 && (
        <List
          style={{ marginTop: 16 }}
          bordered
          dataSource={value}
          renderItem={(item, index) => (
            <List.Item
              actions={[
                <Button
                  key="preview"
                  type="link"
                  size="small"
                  icon={<EyeOutlined />}
                  onClick={() => handlePreview(item)}
                >
                  预览
                </Button>,
                <Button
                  key="delete"
                  type="link"
                  danger
                  size="small"
                  icon={<DeleteOutlined />}
                  onClick={() => handleDelete(index)}
                >
                  删除
                </Button>,
              ]}
            >
              <List.Item.Meta
                avatar={
                  item.type === 'pdf' ? (
                    <FilePdfOutlined style={{ fontSize: 24, color: '#ff4d4f' }} />
                  ) : (
                    <FileImageOutlined style={{ fontSize: 24, color: '#1890ff' }} />
                  )
                }
                title={item.name}
                description={`大小: ${formatFileSize(item.size)}`}
              />
            </List.Item>
          )}
        />
      )}

      {/* 预览模态框 */}
      <Modal
        open={previewVisible}
        title="附件预览"
        footer={null}
        onCancel={() => setPreviewVisible(false)}
        width={800}
      >
        {previewType === 'image' ? (
          <Image src={previewUrl} alt="预览" style={{ width: '100%' }} />
        ) : (
          <iframe
            src={previewUrl}
            style={{ width: '100%', height: '600px', border: 'none' }}
            title="PDF预览"
          />
        )}
      </Modal>
    </div>
  );
};

export default AttachmentUpload;

