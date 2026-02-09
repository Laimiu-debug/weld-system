/**
 * 可编辑表格组件
 * 用于证书的合格项目和合格范围编辑
 */
import React, { useState, useEffect } from 'react';
import { Table, Button, Input, Space, Popconfirm } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import type { ColumnType } from 'antd/es/table';

export interface EditableTableRow {
  key: string;
  [key: string]: any;
}

export interface EditableTableColumn {
  title: string;
  dataIndex: string;
  width?: number | string;
  editable?: boolean;
  placeholder?: string;
}

interface EditableTableProps {
  columns: EditableTableColumn[];
  value?: EditableTableRow[];
  onChange?: (value: EditableTableRow[]) => void;
  addButtonText?: string;
  emptyRow: Omit<EditableTableRow, 'key'>;
}

/**
 * 可编辑表格组件
 */
const EditableTable: React.FC<EditableTableProps> = ({
  columns,
  value = [],
  onChange,
  addButtonText = '添加行',
  emptyRow,
}) => {
  const [dataSource, setDataSource] = useState<EditableTableRow[]>(value);

  // 当 value prop 改变时，更新内部状态
  useEffect(() => {
    setDataSource(value);
  }, [value]);

  // 更新数据
  const updateData = (newData: EditableTableRow[]) => {
    setDataSource(newData);
    onChange?.(newData);
  };

  // 添加行
  const handleAdd = () => {
    const newRow: EditableTableRow = {
      key: `row_${Date.now()}`,
      ...emptyRow,
    };
    updateData([...dataSource, newRow]);
  };

  // 删除行
  const handleDelete = (key: string) => {
    updateData(dataSource.filter((item) => item.key !== key));
  };

  // 更新单元格
  const handleCellChange = (key: string, dataIndex: string, value: any) => {
    const newData = dataSource.map((item) => {
      if (item.key === key) {
        return { ...item, [dataIndex]: value };
      }
      return item;
    });
    updateData(newData);
  };

  // 构建表格列
  const tableColumns: ColumnType<EditableTableRow>[] = [
    ...columns.map((col) => ({
      title: col.title,
      dataIndex: col.dataIndex,
      width: col.width,
      render: (text: any, record: EditableTableRow) => {
        if (col.editable === false) {
          return text;
        }
        return (
          <Input
            value={text}
            placeholder={col.placeholder || `请输入${col.title}`}
            onChange={(e) => handleCellChange(record.key, col.dataIndex, e.target.value)}
          />
        );
      },
    })),
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: any, record: EditableTableRow) => (
        <Popconfirm
          title="确定删除这一行吗？"
          onConfirm={() => handleDelete(record.key)}
          okText="确定"
          cancelText="取消"
        >
          <Button
            type="link"
            danger
            size="small"
            icon={<DeleteOutlined />}
          >
            删除
          </Button>
        </Popconfirm>
      ),
    },
  ];

  return (
    <div>
      <Table
        dataSource={dataSource}
        columns={tableColumns}
        pagination={false}
        size="small"
        bordered
      />
      <Button
        type="dashed"
        onClick={handleAdd}
        icon={<PlusOutlined />}
        style={{ width: '100%', marginTop: 8 }}
      >
        {addButtonText}
      </Button>
    </div>
  );
};

export default EditableTable;

