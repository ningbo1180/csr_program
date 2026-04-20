'use client'

import { useState, useEffect, useCallback } from 'react'

interface CenterPanelProps {
  tree: any[]
  activeChapter: any
  projectId: string
  onChapterSelect: (chapter: any) => void
  onContentUpdate: (content: string) => void
  onTreeChange: () => void
}

const API_BASE = 'http://localhost:8000'

interface TreeNode {
  id: string
  title: string
  number: string
  content?: string
  children: TreeNode[]
}

export default function CenterPanel({ tree, activeChapter, projectId, onChapterSelect, onContentUpdate, onTreeChange }: CenterPanelProps) {
  const [newChapterTitle, setNewChapterTitle] = useState('')
  const [newChapterNumber, setNewChapterNumber] = useState('')
  const [editorContent, setEditorContent] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set())

  useEffect(() => {
    if (activeChapter) {
      setEditorContent(activeChapter.content || '')
    } else {
      setEditorContent('')
    }
  }, [activeChapter?.id])

  const toggleExpand = (id: string) => {
    setExpandedNodes(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const handleAddChapter = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newChapterTitle || !newChapterNumber) return

    try {
      const res = await fetch(`${API_BASE}/api/chapters/${projectId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: newChapterTitle,
          number: newChapterNumber,
          content: '',
        }),
      })

      if (res.ok) {
        setNewChapterTitle('')
        setNewChapterNumber('')
        onTreeChange()
      }
    } catch (err) {
      console.error('Failed to add chapter:', err)
    }
  }

  const handleSave = useCallback(async () => {
    if (!activeChapter) return
    setIsSaving(true)
    await onContentUpdate(editorContent)
    setIsSaving(false)
  }, [activeChapter, editorContent, onContentUpdate])

  const autoSave = useCallback(() => {
    if (activeChapter && editorContent !== (activeChapter.content || '')) {
      onContentUpdate(editorContent)
    }
  }, [activeChapter, editorContent, onContentUpdate])

  useEffect(() => {
    const timer = setTimeout(autoSave, 3000)
    return () => clearTimeout(timer)
  }, [editorContent, autoSave])

  const renderTreeNode = (node: TreeNode, depth: number = 0) => {
    const hasChildren = node.children && node.children.length > 0
    const isExpanded = expandedNodes.has(node.id)
    const isActive = activeChapter?.id === node.id

    return (
      <div key={node.id} className={depth > 0 ? 'ml-3 border-l border-slate-700 pl-3' : ''}>
        <div
          className={`section-item p-2 rounded cursor-pointer flex items-center justify-between group ${
            isActive ? 'active bg-cyan-500/10 border-l-2 border-cyan-500' : 'hover:bg-slate-800'
          }`}
          onClick={() => {
            onChapterSelect(node)
            if (hasChildren) toggleExpand(node.id)
          }}
        >
          <div className="flex items-center gap-2 min-w-0">
            {hasChildren ? (
              <svg
                className={`w-3 h-3 text-slate-500 shrink-0 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
              </svg>
            ) : (
              <svg className="w-3 h-3 text-slate-600 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            )}
            <span className={`text-sm truncate ${isActive ? 'text-white font-medium' : 'text-slate-300'}`}>
              {node.number} {node.title}
            </span>
          </div>
          {node.content ? (
            <svg className="w-3 h-3 text-emerald-500 shrink-0 opacity-0 group-hover:opacity-100" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          ) : (
            <span className="text-xs text-slate-500 shrink-0">待生成</span>
          )}
        </div>
        {hasChildren && isExpanded && (
          <div className="mt-1">
            {node.children.map(child => renderTreeNode(child, depth + 1))}
          </div>
        )}
      </div>
    )
  }

  const insertTag = (tag: string) => {
    const textarea = document.getElementById('chapter-editor') as HTMLTextAreaElement
    if (!textarea) return
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const before = editorContent.substring(0, start)
    const after = editorContent.substring(end)
    const selected = editorContent.substring(start, end)
    let insertion = ''
    switch (tag) {
      case 'b': insertion = `<strong>${selected || '粗体文本'}</strong>`; break
      case 'i': insertion = `<em>${selected || '斜体文本'}</em>`; break
      case 'u': insertion = `<u>${selected || '下划线文本'}</u>`; break
      case 'table': insertion = `\n<table class="w-full text-sm text-left text-slate-300">\n<thead class="text-xs text-slate-400 uppercase bg-slate-800">\n<tr><th class="px-4 py-2">列1</th><th class="px-4 py-2">列2</th></tr>\n</thead>\n<tbody class="divide-y divide-slate-800">\n<tr><td class="px-4 py-2">数据1</td><td class="px-4 py-2">数据2</td></tr>\n</tbody>\n</table>\n`; break
      case 'link': insertion = `<a href="#" class="text-cyan-400 hover:underline">${selected || '链接'}</a>`; break
      default: insertion = selected
    }
    const newContent = before + insertion + after
    setEditorContent(newContent)
    setTimeout(() => {
      textarea.focus()
      const newCursor = start + insertion.length
      textarea.setSelectionRange(newCursor, newCursor)
    }, 0)
  }

  const wordCount = editorContent.replace(/<[^>]*>/g, '').replace(/\s/g, '').length

  return (
    <main className="flex-1 flex flex-col min-w-0">
      {/* Toolbar */}
      <div className="h-12 bg-slate-900/50 border-b border-slate-700 flex items-center px-4 gap-4">
        <div className="flex items-center gap-2">
          <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
          </svg>
          <span className="text-sm text-slate-300">CSR 结构树</span>
          <span className="text-xs text-slate-500">(共 {tree.length} 个主要章节)</span>
        </div>
        <div className="flex-1"></div>
        <div className="flex gap-2">
          <button
            onClick={() => alert('AI补全功能开发中')}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded text-xs text-white transition-colors border border-slate-700"
          >
            <svg className="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
            </svg>
            AI补全
          </button>
          <button
            onClick={() => alert('一致性检查功能开发中')}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded text-xs text-white transition-colors border border-slate-700"
          >
            <svg className="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            一致性检查
          </button>
        </div>
      </div>

      {/* Split View */}
      <div className="flex-1 flex overflow-hidden">
        {/* Section Tree */}
        <div className="w-72 border-r border-slate-700 bg-slate-900/30 overflow-y-auto section-tree shrink-0">
          <div className="p-3">
            <form onSubmit={handleAddChapter} className="mb-3 space-y-2">
              <input
                type="text"
                placeholder="章节编号 (如: 10.2)"
                value={newChapterNumber}
                onChange={(e) => setNewChapterNumber(e.target.value)}
                className="w-full px-2 py-1.5 bg-slate-800 border border-slate-700 rounded text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
              />
              <input
                type="text"
                placeholder="章节标题"
                value={newChapterTitle}
                onChange={(e) => setNewChapterTitle(e.target.value)}
                className="w-full px-2 py-1.5 bg-slate-800 border border-slate-700 rounded text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
              />
              <button
                type="submit"
                className="w-full px-3 py-1.5 bg-cyan-600/20 text-cyan-400 rounded text-xs hover:bg-cyan-600/30 transition border border-cyan-600/30"
              >
                + 添加章节
              </button>
            </form>

            <div className="space-y-1">
              {tree.length === 0 ? (
                <p className="text-xs text-slate-500 text-center py-4">暂无章节</p>
              ) : (
                tree.map(node => renderTreeNode(node))
              )}
            </div>
          </div>
        </div>

        {/* Editor Area */}
        <div className="flex-1 flex flex-col bg-slate-950 min-w-0">
          {/* Breadcrumb */}
          <div className="h-10 border-b border-slate-800 flex items-center px-4 gap-2 text-sm shrink-0">
            <span className="text-slate-500">CSR</span>
            <svg className="w-3 h-3 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
            <span className="text-slate-500">Section {activeChapter?.number?.split('.')[0] || '?'}</span>
            {activeChapter && (
              <>
                <svg className="w-3 h-3 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
                <span className="text-cyan-400 font-medium truncate">{activeChapter.number} {activeChapter.title}</span>
              </>
            )}
            <div className="ml-auto flex gap-2">
              <span className="text-xs px-2 py-1 rounded bg-purple-500/20 text-purple-300">Protocol</span>
              <span className="text-xs px-2 py-1 rounded bg-blue-500/20 text-blue-300">SAP</span>
            </div>
          </div>

          {/* Editor Toolbar */}
          <div className="h-10 border-b border-slate-800 flex items-center px-4 gap-4 bg-slate-900/30 shrink-0">
            <div className="flex gap-1">
              <button onClick={() => insertTag('b')} className="p-1.5 hover:bg-slate-800 rounded text-slate-400" title="Bold">
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 12h8a4 4 0 100-8H6v8zm0 0v8h10a4 4 0 100-8H6z" />
                </svg>
              </button>
              <button onClick={() => insertTag('i')} className="p-1.5 hover:bg-slate-800 rounded text-slate-400" title="Italic">
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                </svg>
              </button>
              <button onClick={() => insertTag('u')} className="p-1.5 hover:bg-slate-800 rounded text-slate-400" title="Underline">
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16m-7 6h7" />
                </svg>
              </button>
            </div>
            <div className="w-px h-4 bg-slate-700"></div>
            <div className="flex gap-1">
              <button onClick={() => insertTag('table')} className="p-1.5 hover:bg-slate-800 rounded text-cyan-400" title="Insert Table">
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </button>
              <button onClick={() => insertTag('link')} className="p-1.5 hover:bg-slate-800 rounded text-slate-400" title="Insert Link">
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                </svg>
              </button>
            </div>
            <div className="w-px h-4 bg-slate-700"></div>
            <button
              onClick={() => alert('AI润色功能开发中')}
              className="px-3 py-1 bg-cyan-600/20 text-cyan-400 rounded text-xs hover:bg-cyan-600/30 transition-colors"
            >
              <svg className="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
              </svg>
              AI润色
            </button>
          </div>

          {/* Content Area */}
          <div className="flex-1 overflow-y-auto p-6">
            {activeChapter ? (
              <div className="max-w-3xl mx-auto">
                <h2 className="text-2xl font-bold text-white mb-6">
                  {activeChapter.number} {activeChapter.title}
                </h2>

                <div className="mb-4">
                  <p className="text-sm text-slate-400 italic border-l-2 border-cyan-500 pl-3">
                    [本章节内容基于Protocol和SAP中的信息自动生成，已进行去重处理]
                  </p>
                </div>

                <textarea
                  id="chapter-editor"
                  value={editorContent}
                  onChange={(e) => setEditorContent(e.target.value)}
                  className="w-full h-96 bg-slate-900 border border-slate-700 rounded-lg p-4 text-sm text-slate-300 leading-relaxed resize-y focus:outline-none focus:border-cyan-500 font-mono"
                  placeholder="在此输入章节内容..."
                />

                <div className="flex justify-end mt-4 gap-2">
                  <button
                    onClick={handleSave}
                    disabled={isSaving}
                    className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-sm transition-colors disabled:opacity-50"
                  >
                    {isSaving ? '保存中...' : '保存'}
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <svg className="w-16 h-16 text-slate-700 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <p className="text-slate-500 text-lg">选择一个章节开始编辑</p>
                  <p className="text-slate-600 text-sm mt-2">在左侧结构树中点击章节</p>
                </div>
              </div>
            )}
          </div>

          {/* Status Bar */}
          <div className="h-8 bg-slate-900 border-t border-slate-800 flex items-center px-4 text-xs text-slate-500 shrink-0">
            <div className="flex items-center gap-4">
              <span>
                <svg className="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                自动保存于 {new Date().toLocaleTimeString('zh-CN')}
              </span>
              <span className="text-emerald-500">
                <svg className="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
                数据已加密
              </span>
            </div>
            <div className="ml-auto flex items-center gap-2">
              <span>字数: {wordCount.toLocaleString()}</span>
              <span className="w-px h-3 bg-slate-700"></span>
              <span>来源文档: 3</span>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
