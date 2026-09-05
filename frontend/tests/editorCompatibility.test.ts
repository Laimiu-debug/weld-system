import { expect, it } from 'vitest'
import { Editor } from '@tiptap/core'
import StarterKit from '@tiptap/starter-kit'
import { Table } from '@tiptap/extension-table'
import TableRow from '@tiptap/extension-table-row'
import TableCell from '@tiptap/extension-table-cell'
import TableHeader from '@tiptap/extension-table-header'
import { TextStyle } from '@tiptap/extension-text-style'
import Color from '@tiptap/extension-color'
import Image from '@tiptap/extension-image'

it('preserves WPS document text, formatting, tables and images after the editor dependency fix', () => {
  const editor = new Editor({
    element: document.createElement('div'),
    extensions: [StarterKit, Table, TableRow, TableCell, TableHeader, TextStyle, Color, Image],
    content: '<p><strong>WPS 工艺</strong><span style="color: #ff0000">审核</span></p>' +
      '<table><tbody><tr><th>电流</th><td>120 A</td></tr></tbody></table><img src="/diagram.png">',
  })
  try {
    const saved = editor.getHTML()
    editor.commands.setContent(saved)
    expect(editor.getHTML()).toContain('<strong>WPS 工艺</strong>')
    expect(editor.getText()).toContain('120 A')
    expect(editor.getHTML()).toContain('<table')
    expect(editor.getHTML()).toContain('color: rgb(255, 0, 0)')
    expect(editor.getHTML()).toContain('src="/diagram.png"')
  } finally { editor.destroy() }
})
