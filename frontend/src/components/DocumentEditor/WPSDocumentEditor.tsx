/**
 * WPS文档编辑器组件
 * 基于TipTap实现的Word式文档编辑器
 */
import React, { useEffect } from 'react'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import { Table } from '@tiptap/extension-table'
import { TableRow } from '@tiptap/extension-table-row'
import { TableCell } from '@tiptap/extension-table-cell'
import { TableHeader } from '@tiptap/extension-table-header'
import { Image } from '@tiptap/extension-image'
import { TextAlign } from '@tiptap/extension-text-align'
import { TextStyle } from '@tiptap/extension-text-style'
import { Color } from '@tiptap/extension-color'
import { Button, Space, Divider, Tooltip, message, Dropdown } from 'antd'
import type { MenuProps } from 'antd'
import {
  BoldOutlined,
  ItalicOutlined,
  UnderlineOutlined,
  AlignLeftOutlined,
  AlignCenterOutlined,
  AlignRightOutlined,
  TableOutlined,
  PictureOutlined,
  FileWordOutlined,
  FilePdfOutlined,
  SaveOutlined,
  PrinterOutlined,
  UndoOutlined,
  RedoOutlined,
  DeleteOutlined,
} from '@ant-design/icons'
import './DocumentEditor.css'

interface WPSDocumentEditorProps {
  initialContent: string
  onSave: (content: string) => Promise<void> | void
  onExportWord?: (style?: string) => void
  onExportPDF?: () => void
}

const WPSDocumentEditor: React.FC<WPSDocumentEditorProps> = ({
  initialContent,
  onSave,
  onExportWord,
  onExportPDF,
}) => {
  console.log('[WPSDocumentEditor] 初始化，initialContent长度:', initialContent?.length || 0)
  console.log('[WPSDocumentEditor] initialContent内容:', initialContent?.substring(0, 200))

  const editor = useEditor({
    extensions: [
      StarterKit,
      Table.configure({
        resizable: true,
      }),
      TableRow,
      TableHeader,
      TableCell,
      Image.configure({
        inline: true,
        allowBase64: true,  // 明确允许 base64 图片
        HTMLAttributes: {
          loading: 'lazy',
          style: 'max-width: 100%; height: auto;'
        },
      }),
      TextAlign.configure({
        types: ['heading', 'paragraph'],
      }),
      TextStyle,
      Color,
    ],
    content: initialContent,
    editorProps: {
      attributes: {
        class: 'prose prose-sm sm:prose lg:prose-lg mx-auto focus:outline-none',
      },
    },
  })

  // 当initialContent变化时更新编辑器内容
  useEffect(() => {
    console.log('[WPSDocumentEditor] useEffect触发，检查是否需要更新内容:', {
      hasEditor: !!editor,
      hasInitialContent: !!initialContent,
      initialContentLength: initialContent?.length || 0
    })

    // 检查HTML中是否包含图片
    if (initialContent) {
      const imgMatches = initialContent.match(/<img[^>]*>/g)
      console.log('[WPSDocumentEditor] HTML中的图片标签数量:', imgMatches?.length || 0)
      if (imgMatches && imgMatches.length > 0) {
        console.log('[WPSDocumentEditor] 图片标签示例:', imgMatches[0].substring(0, 200))
        // 验证每个图片的src
        imgMatches.forEach((imgTag, index) => {
          const srcMatch = imgTag.match(/src="([^"]*)"/)
          if (srcMatch) {
            const src = srcMatch[1]
            console.log(`[WPSDocumentEditor] 图片${index + 1} src长度:`, src.length)
            if (src.startsWith('data:image')) {
              const [header, base64Data] = src.split(',')
              console.log(`[WPSDocumentEditor] 图片${index + 1} base64数据长度:`, base64Data?.length || 0)
              if (!base64Data || base64Data.length === 0) {
                console.warn(`[WPSDocumentEditor] 图片${index + 1} base64数据为空`)
              }
            }
          } else {
            console.warn(`[WPSDocumentEditor] 图片${index + 1} 没有src属性`)
          }
        })
      }
    }

    if (editor && initialContent) {
      const currentContent = editor.getHTML()
      const currentLength = currentContent?.length || 0
      const initialLength = initialContent?.length || 0

      console.log('[WPSDocumentEditor] 当前内容长度:', currentLength)
      console.log('[WPSDocumentEditor] 初始内容长度:', initialLength)

      // 只在编辑器为空或内容长度差异超过10%时更新
      // 这样可以避免因为TipTap格式化导致的微小差异而无限循环
      const isEmpty = currentLength < 50
      const lengthDiff = Math.abs(currentLength - initialLength)
      const shouldUpdate = isEmpty || lengthDiff > initialLength * 0.1

      console.log('[WPSDocumentEditor] 是否需要更新:', {
        isEmpty,
        lengthDiff,
        shouldUpdate
      })

      if (shouldUpdate) {
        console.log('[WPSDocumentEditor] 更新编辑器内容')
        editor.commands.setContent(initialContent)
      } else {
        console.log('[WPSDocumentEditor] 内容相似，跳过更新')
      }
    }
  }, [editor, initialContent])

  if (!editor) {
    return null
  }

  const handleSave = async () => {
    const content = editor.getHTML()
    await onSave(content)
  }

  const handleExportWord = async (style: string = 'blue_white') => {
    try {
      // 先保存当前内容
      message.loading({ content: '正在保存文档...', key: 'export' })
      const content = editor.getHTML()
      await onSave(content)

      // 等待一小段时间确保保存完成
      await new Promise(resolve => setTimeout(resolve, 500))

      // 然后导出
      message.loading({ content: '正在导出Word...', key: 'export' })
      if (onExportWord) {
        onExportWord(style)
      }
      message.destroy('export')
    } catch (error) {
      message.error('导出失败')
      console.error('导出Word失败:', error)
    }
  }

  // 导出Word菜单项
  const exportWordMenuItems: MenuProps['items'] = [
    {
      key: 'blue_white',
      label: '蓝白相间风格',
      onClick: () => handleExportWord('blue_white'),
    },
    {
      key: 'plain',
      label: '纯白风格',
      onClick: () => handleExportWord('plain'),
    },
    {
      key: 'classic',
      label: '经典风格',
      onClick: () => handleExportWord('classic'),
    },
  ]

  const handleExportPDF = async () => {
    try {
      // 先保存当前内容
      message.loading({ content: '正在保存文档...', key: 'export' })
      const content = editor.getHTML()
      await onSave(content)

      // 等待一小段时间确保保存完成
      await new Promise(resolve => setTimeout(resolve, 500))

      // 然后导出
      message.loading({ content: '正在导出PDF...', key: 'export' })
      if (onExportPDF) {
        onExportPDF()
      }
      message.destroy('export')
    } catch (error) {
      message.error('导出失败')
      console.error('导出PDF失败:', error)
    }
  }

  const handlePrint = () => {
    window.print()
  }

  const addImage = () => {
    const url = window.prompt('请输入图片URL:')
    if (url) {
      editor.chain().focus().setImage({ src: url }).run()
    }
  }

  const MenuBar = () => (
    <div className="menu-bar">
      <Space split={<Divider type="vertical" />} wrap>
        {/* 文件操作 */}
        <Space>
          <Tooltip title="保存">
            <Button
              type="primary"
              icon={<SaveOutlined />}
              onClick={handleSave}
            >
              保存
            </Button>
          </Tooltip>
          <Dropdown menu={{ items: exportWordMenuItems }} placement="bottomLeft">
            <Button icon={<FileWordOutlined />}>
              导出Word
            </Button>
          </Dropdown>
          <Tooltip title="导出PDF">
            <Button icon={<FilePdfOutlined />} onClick={handleExportPDF}>
              导出PDF
            </Button>
          </Tooltip>
          <Tooltip title="打印">
            <Button icon={<PrinterOutlined />} onClick={handlePrint}>
              打印
            </Button>
          </Tooltip>
        </Space>

        {/* 撤销/重做 */}
        <Space>
          <Tooltip title="撤销">
            <Button
              icon={<UndoOutlined />}
              onClick={() => editor.chain().focus().undo().run()}
              disabled={!editor.can().undo()}
            />
          </Tooltip>
          <Tooltip title="重做">
            <Button
              icon={<RedoOutlined />}
              onClick={() => editor.chain().focus().redo().run()}
              disabled={!editor.can().redo()}
            />
          </Tooltip>
        </Space>

        {/* 文本格式 */}
        <Space>
          <Tooltip title="粗体">
            <Button
              type={editor.isActive('bold') ? 'primary' : 'default'}
              icon={<BoldOutlined />}
              onClick={() => editor.chain().focus().toggleBold().run()}
            />
          </Tooltip>
          <Tooltip title="斜体">
            <Button
              type={editor.isActive('italic') ? 'primary' : 'default'}
              icon={<ItalicOutlined />}
              onClick={() => editor.chain().focus().toggleItalic().run()}
            />
          </Tooltip>
          <Tooltip title="下划线">
            <Button
              type={editor.isActive('underline') ? 'primary' : 'default'}
              icon={<UnderlineOutlined />}
              onClick={() => editor.chain().focus().toggleUnderline().run()}
            />
          </Tooltip>
        </Space>

        {/* 对齐 */}
        <Space>
          <Tooltip title="左对齐">
            <Button
              type={editor.isActive({ textAlign: 'left' }) ? 'primary' : 'default'}
              icon={<AlignLeftOutlined />}
              onClick={() => editor.chain().focus().setTextAlign('left').run()}
            />
          </Tooltip>
          <Tooltip title="居中">
            <Button
              type={editor.isActive({ textAlign: 'center' }) ? 'primary' : 'default'}
              icon={<AlignCenterOutlined />}
              onClick={() => editor.chain().focus().setTextAlign('center').run()}
            />
          </Tooltip>
          <Tooltip title="右对齐">
            <Button
              type={editor.isActive({ textAlign: 'right' }) ? 'primary' : 'default'}
              icon={<AlignRightOutlined />}
              onClick={() => editor.chain().focus().setTextAlign('right').run()}
            />
          </Tooltip>
        </Space>

        {/* 标题 */}
        <Space>
          <Button
            type={editor.isActive('heading', { level: 1 }) ? 'primary' : 'default'}
            onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
          >
            H1
          </Button>
          <Button
            type={editor.isActive('heading', { level: 2 }) ? 'primary' : 'default'}
            onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
          >
            H2
          </Button>
          <Button
            type={editor.isActive('heading', { level: 3 }) ? 'primary' : 'default'}
            onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
          >
            H3
          </Button>
        </Space>

        {/* 表格操作 */}
        <Space>
          <Tooltip title="插入表格">
            <Button
              icon={<TableOutlined />}
              onClick={() =>
                editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()
              }
            >
              插入表格
            </Button>
          </Tooltip>
          {editor.isActive('table') && (
            <>
              <Button
                size="small"
                onClick={() => editor.chain().focus().addColumnBefore().run()}
              >
                插入列(前)
              </Button>
              <Button
                size="small"
                onClick={() => editor.chain().focus().addColumnAfter().run()}
              >
                插入列(后)
              </Button>
              <Button
                size="small"
                onClick={() => editor.chain().focus().addRowBefore().run()}
              >
                插入行(上)
              </Button>
              <Button
                size="small"
                onClick={() => editor.chain().focus().addRowAfter().run()}
              >
                插入行(下)
              </Button>
              <Button
                size="small"
                danger
                icon={<DeleteOutlined />}
                onClick={() => editor.chain().focus().deleteTable().run()}
              >
                删除表格
              </Button>
            </>
          )}
        </Space>

        {/* 图片 */}
        <Space>
          <Tooltip title="插入图片">
            <Button icon={<PictureOutlined />} onClick={addImage}>
              插入图片
            </Button>
          </Tooltip>
        </Space>
      </Space>
    </div>
  )

  return (
    <div className="document-editor">
      <MenuBar />
      <div className="editor-container">
        <EditorContent editor={editor} />
      </div>
    </div>
  )
}

export default WPSDocumentEditor

