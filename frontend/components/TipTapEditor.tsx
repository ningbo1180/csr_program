'use client'

import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import { Table } from '@tiptap/extension-table'
import { TableRow } from '@tiptap/extension-table-row'
import { TableCell } from '@tiptap/extension-table-cell'
import { TableHeader } from '@tiptap/extension-table-header'
import Placeholder from '@tiptap/extension-placeholder'
import Link from '@tiptap/extension-link'
import Underline from '@tiptap/extension-underline'
import TextAlign from '@tiptap/extension-text-align'
import Highlight from '@tiptap/extension-highlight'
import Image from '@tiptap/extension-image'
import { useEffect, useCallback } from 'react'

interface TipTapEditorProps {
  content: string
  onChange: (html: string, json: any) => void
  editable?: boolean
}

export default function TipTapEditor({ content, onChange, editable = true }: TipTapEditorProps) {
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: { levels: [1, 2, 3, 4] },
      }),
      Underline,
      Link.configure({
        openOnClick: false,
        HTMLAttributes: {
          class: 'text-cyan-400 hover:underline',
        },
      }),
      TextAlign.configure({
        types: ['heading', 'paragraph'],
      }),
      Highlight.configure({
        multicolor: true,
      }),
      Image.configure({
        HTMLAttributes: {
          class: 'max-w-full rounded-lg',
        },
      }),
      Table.configure({
        resizable: true,
        HTMLAttributes: {
          class: 'w-full text-sm text-left text-slate-300 border-collapse',
        },
      }),
      TableRow.configure({
        HTMLAttributes: {
          class: 'divide-y divide-slate-800',
        },
      }),
      TableHeader.configure({
        HTMLAttributes: {
          class: 'text-xs text-slate-400 uppercase bg-slate-800 px-4 py-2',
        },
      }),
      TableCell.configure({
        HTMLAttributes: {
          class: 'px-4 py-2',
        },
      }),
      Placeholder.configure({
        placeholder: '在此输入章节内容...',
      }),
    ],
    content: content || '<p></p>',
    editable,
    editorProps: {
      attributes: {
        class: 'prose prose-invert prose-sm max-w-none focus:outline-none min-h-[300px] p-4',
      },
    },
    onUpdate: ({ editor }) => {
      const html = editor.getHTML()
      const json = editor.getJSON()
      onChange(html, json)
    },
  })

  // Update content when prop changes (from external source like AI generation)
  useEffect(() => {
    if (editor && content !== editor.getHTML()) {
      editor.commands.setContent(content || '<p></p>', { emitUpdate: false })
    }
  }, [content, editor])

  const setLink = useCallback(() => {
    if (!editor) return
    const previousUrl = editor.getAttributes('link').href
    const url = window.prompt('输入链接地址', previousUrl)
    if (url === null) return
    if (url === '') {
      editor.chain().focus().extendMarkRange('link').unsetLink().run()
      return
    }
    editor.chain().focus().extendMarkRange('link').setLink({ href: url }).run()
  }, [editor])

  const addImage = useCallback(() => {
    if (!editor) return
    const url = window.prompt('输入图片地址')
    if (url) {
      editor.chain().focus().setImage({ src: url }).run()
    }
  }, [editor])

  if (!editor) return null

  const buttonClass = (active: boolean) =>
    `p-1.5 rounded text-xs transition-colors ${
      active ? 'bg-cyan-600/30 text-cyan-400' : 'text-slate-400 hover:bg-slate-800 hover:text-white'
    }`

  return (
    <div className="border border-slate-700 rounded-lg bg-slate-900/50 overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center gap-1 px-3 py-2 border-b border-slate-800 bg-slate-900/80 flex-wrap">
        <div className="flex gap-0.5">
          <button
            onClick={() => editor.chain().focus().toggleBold().run()}
            className={buttonClass(editor.isActive('bold'))}
            title="粗体"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 12h8a4 4 0 100-8H6v8zm0 0v8h10a4 4 0 100-8H6z" />
            </svg>
          </button>
          <button
            onClick={() => editor.chain().focus().toggleItalic().run()}
            className={buttonClass(editor.isActive('italic'))}
            title="斜体"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
            </svg>
          </button>
          <button
            onClick={() => editor.chain().focus().toggleUnderline().run()}
            className={buttonClass(editor.isActive('underline'))}
            title="下划线"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16m-7 6h7" />
            </svg>
          </button>
        </div>
        <div className="w-px h-4 bg-slate-700 mx-1" />
        <div className="flex gap-0.5">
          <button
            onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
            className={buttonClass(editor.isActive('heading', { level: 1 }))}
            title="标题1"
          >
            H1
          </button>
          <button
            onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
            className={buttonClass(editor.isActive('heading', { level: 2 }))}
            title="标题2"
          >
            H2
          </button>
          <button
            onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
            className={buttonClass(editor.isActive('heading', { level: 3 }))}
            title="标题3"
          >
            H3
          </button>
        </div>
        <div className="w-px h-4 bg-slate-700 mx-1" />
        <div className="flex gap-0.5">
          <button
            onClick={() => editor.chain().focus().toggleBulletList().run()}
            className={buttonClass(editor.isActive('bulletList'))}
            title="无序列表"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <button
            onClick={() => editor.chain().focus().toggleOrderedList().run()}
            className={buttonClass(editor.isActive('orderedList'))}
            title="有序列表"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h12M7 12h12M7 17h12M3 7h.01M3 12h.01M3 17h.01" />
            </svg>
          </button>
        </div>
        <div className="w-px h-4 bg-slate-700 mx-1" />
        <div className="flex gap-0.5">
          <button
            onClick={setLink}
            className={buttonClass(editor.isActive('link'))}
            title="插入链接"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
          </button>
          <button
            onClick={addImage}
            className={buttonClass(false)}
            title="插入图片"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </button>
          <button
            onClick={() => editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()}
            className={buttonClass(editor.isActive('table'))}
            title="插入表格"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          </button>
        </div>
        <div className="w-px h-4 bg-slate-700 mx-1" />
        <div className="flex gap-0.5">
          <button
            onClick={() => editor.chain().focus().undo().run()}
            disabled={!editor.can().undo()}
            className="p-1.5 rounded text-xs text-slate-400 hover:bg-slate-800 hover:text-white disabled:opacity-30"
            title="撤销"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
            </svg>
          </button>
          <button
            onClick={() => editor.chain().focus().redo().run()}
            disabled={!editor.can().redo()}
            className="p-1.5 rounded text-xs text-slate-400 hover:bg-slate-800 hover:text-white disabled:opacity-30"
            title="重做"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 10h-10a8 8 0 00-8 8v2M21 10l-6 6m6-6l-6-6" />
            </svg>
          </button>
        </div>
      </div>
      {/* Editor */}
      <EditorContent editor={editor} />
    </div>
  )
}
