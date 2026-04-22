'use client'

import { useState, useEffect, useCallback } from 'react'
import dynamic from 'next/dynamic'

const TipTapEditor = dynamic(() => import('./TipTapEditor'), { ssr: false })
const DiffViewer = dynamic(() => import('./DiffViewer'), { ssr: false })

interface CenterPanelProps {
  tree: any[]
  activeChapter: any
  projectId: string
  onChapterSelect: (chapter: any) => void
  onContentUpdate: (content: string, contentJson?: any) => void
  onTreeChange: () => void
  onTitleChange?: (chapterId: string, newTitle: string) => void
}

const API_BASE = 'http://localhost:8000'

interface TreeNode {
  id: string
  title: string
  number: string
  content?: string
  children: TreeNode[]
}

interface DiffData {
  blocks: any[]
  reasoning: string
  polished: string
}

export default function CenterPanel({ tree, activeChapter, projectId, onChapterSelect, onContentUpdate, onTreeChange, onTitleChange }: CenterPanelProps) {
  const [newChapterTitle, setNewChapterTitle] = useState('')
  const [newChapterNumber, setNewChapterNumber] = useState('')
  const [editorContent, setEditorContent] = useState('')
  const [editorJson, setEditorJson] = useState<any>(null)
  const [isSaving, setIsSaving] = useState(false)
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set())
  const [showDiff, setShowDiff] = useState(false)
  const [diffData, setDiffData] = useState<DiffData | null>(null)
  const [isPolishing, setIsPolishing] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [editingNodeId, setEditingNodeId] = useState<string | null>(null)
  const [editingTitle, setEditingTitle] = useState('')
  const [addingChildToId, setAddingChildToId] = useState<string | null>(null)
  const [childChapterTitle, setChildChapterTitle] = useState('')
  const [childChapterNumber, setChildChapterNumber] = useState('')

  useEffect(() => {
    if (activeChapter) {
      setEditorContent(activeChapter.content || '')
      setShowDiff(false)
      setDiffData(null)
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
        body: JSON.stringify({ title: newChapterTitle, number: newChapterNumber, content: '' }),
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

  const handleAddChildChapter = async (parentId: string, parentNumber: string) => {
    if (!childChapterTitle || !childChapterNumber) return
    try {
      const fullNumber = `${parentNumber}.${childChapterNumber}`
      const res = await fetch(`${API_BASE}/api/chapters/${projectId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          title: childChapterTitle, 
          number: fullNumber, 
          parent_id: parentId,
          content: '' 
        }),
      })
      if (res.ok) {
        setChildChapterTitle('')
        setChildChapterNumber('')
        setAddingChildToId(null)
        onTreeChange()
      }
    } catch (err) {
      console.error('Failed to add child chapter:', err)
    }
  }

  const handleSave = useCallback(async () => {
    if (!activeChapter) return
    setIsSaving(true)
    await onContentUpdate(editorContent, editorJson)
    setIsSaving(false)
  }, [activeChapter, editorContent, editorJson, onContentUpdate])

  const autoSave = useCallback(() => {
    if (activeChapter && editorContent !== (activeChapter.content || '')) {
      onContentUpdate(editorContent, editorJson)
    }
  }, [activeChapter, editorContent, editorJson, onContentUpdate])

  useEffect(() => {
    const timer = setTimeout(autoSave, 3000)
    return () => clearTimeout(timer)
  }, [editorContent, autoSave])

  const handlePolish = async () => {
    if (!activeChapter) { alert('请先选择一个章节'); return }
    setIsPolishing(true)
    try {
      const res = await fetch(`${API_BASE}/api/ai/polish?project_id=${projectId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chapter_id: activeChapter.id, style: 'professional' }),
      })
      if (res.ok) {
        const data = await res.json()
        setDiffData({ blocks: data.diff_blocks || [], reasoning: data.reasoning || '', polished: data.polished || '' })
        setShowDiff(true)
      }
    } catch (err) {
      console.error('Polish failed:', err)
      alert('润色失败，请稍后重试')
    } finally {
      setIsPolishing(false)
    }
  }

  const handleGenerate = async () => {
    if (!activeChapter) { alert('请先选择一个章节'); return }
    setIsGenerating(true)
    try {
      const res = await fetch(`${API_BASE}/api/chapters/${projectId}/${activeChapter.id}/generate`, {
        method: 'POST',
      })
      if (res.ok) {
        const data = await res.json()
        setEditorContent(data.content || '')
        await onContentUpdate(data.content || '')
        onTreeChange()
        if (data.diff) {
          alert(`章节生成完成！新增 ${data.diff.additions} 处内容。`)
        }
      }
    } catch (err) {
      console.error('Generate failed:', err)
      alert('生成失败，请稍后重试')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleAcceptDiff = async () => {
    if (!diffData || !activeChapter) return
    setEditorContent(diffData.polished)
    await onContentUpdate(diffData.polished)
    setShowDiff(false)
    setDiffData(null)
  }

  const handleRejectDiff = () => { setShowDiff(false); setDiffData(null) }

  const handlePartialAccept = async (acceptedBlocks: any[]) => {
    if (!activeChapter) return
    const text = acceptedBlocks.map(b => b.text).filter(Boolean).join('\n')
    const html = `<p>${text.replace(/\n/g, '</p><p>')}</p>`
    setEditorContent(html)
    await onContentUpdate(html)
    setShowDiff(false)
    setDiffData(null)
  }

  const handleTitleEdit = async (node: TreeNode) => {
    if (!editingTitle.trim() || editingTitle === node.title) {
      setEditingNodeId(null)
      return
    }
    try {
      const res = await fetch(`${API_BASE}/api/chapters/${projectId}/${node.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: editingTitle }),
      })
      if (res.ok) {
        setEditingNodeId(null)
        onTreeChange()
        if (activeChapter?.id === node.id) {
          onChapterSelect({ ...activeChapter, title: editingTitle })
        }
        if (onTitleChange) {
          onTitleChange(node.id, editingTitle)
        }
      }
    } catch (err) {
      console.error('Failed to update title:', err)
    }
  }

  const startEditingTitle = (node: TreeNode, e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingNodeId(node.id)
    setEditingTitle(node.title)
  }

  const startAddingChild = (node: TreeNode, e: React.MouseEvent) => {
    e.stopPropagation()
    setAddingChildToId(node.id)
    setChildChapterNumber('')
    setChildChapterTitle('')
    toggleExpand(node.id)
  }

  const renderTreeNode = (node: TreeNode, depth: number = 0) => {
    const hasChildren = node.children && node.children.length > 0
    const isExpanded = expandedNodes.has(node.id)
    const isActive = activeChapter?.id === node.id
    const isEditing = editingNodeId === node.id
    const isAddingChild = addingChildToId === node.id

    return (
      <div key={node.id} className={depth > 0 ? 'ml-3 border-l border-slate-700 pl-3' : ''}>
        <div
          className={`section-item p-2 rounded cursor-pointer flex items-center justify-between group ${isActive ? 'active bg-cyan-500/10 border-l-2 border-cyan-500' : 'hover:bg-slate-800'}`}
          onClick={() => { onChapterSelect(node); if (hasChildren) toggleExpand(node.id) }}
        >
          <div className="flex items-center gap-2 min-w-0 flex-1">
            {hasChildren ? (
              <svg className={`w-3 h-3 text-slate-500 shrink-0 transition-transform ${isExpanded ? 'rotate-90' : ''}`} fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
              </svg>
            ) : (
              <svg className="w-3 h-3 text-slate-600 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            )}
            {isEditing ? (
              <input
                autoFocus
                value={editingTitle}
                onChange={(e) => setEditingTitle(e.target.value)}
                onBlur={() => handleTitleEdit(node)}
                onKeyDown={(e) => { if (e.key === 'Enter') handleTitleEdit(node); if (e.key === 'Escape') setEditingNodeId(null) }}
                onClick={(e) => e.stopPropagation()}
                className="bg-slate-800 border border-cyan-500 rounded px-1 py-0.5 text-sm text-white focus:outline-none flex-1 min-w-0"
              />
            ) : (
              <span className={`text-sm truncate ${isActive ? 'text-white font-medium' : 'text-slate-300'}`}>
                {node.number} {node.title}
              </span>
            )}
          </div>
          <div className="flex items-center gap-1 shrink-0">
            {!isEditing && (
              <>
                <button
                  onClick={(e) => startAddingChild(node, e)}
                  className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-slate-700 text-slate-500 hover:text-cyan-400 transition-all"
                  title="添加子章节"
                >
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                </button>
                <button
                  onClick={(e) => startEditingTitle(node, e)}
                  className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-slate-700 text-slate-500 hover:text-cyan-400 transition-all"
                  title="编辑标题"
                >
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </button>
              </>
            )}
            {node.content ? (
              <svg className="w-3 h-3 text-emerald-500 shrink-0 opacity-0 group-hover:opacity-100" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
            ) : (
              <span className="text-xs text-slate-500 shrink-0 opacity-0 group-hover:opacity-100">待生成</span>
            )}
          </div>
        </div>

        {/* Child chapter input form */}
        {isAddingChild && (
          <div className="mt-1 mb-2 ml-3 p-2 bg-slate-800/50 rounded border border-slate-700 space-y-2">
            <div className="text-xs text-cyan-400">添加 {node.number} 的子章节</div>
            <div className="flex gap-2">
              <span className="text-sm text-slate-400 py-1">{node.number}.</span>
              <input
                autoFocus
                type="text"
                placeholder="编号 (如: 1, 2)"
                value={childChapterNumber}
                onChange={(e) => setChildChapterNumber(e.target.value)}
                className="w-20 px-2 py-1 bg-slate-900 border border-slate-700 rounded text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
              />
              <input
                type="text"
                placeholder="子章节标题"
                value={childChapterTitle}
                onChange={(e) => setChildChapterTitle(e.target.value)}
                className="flex-1 px-2 py-1 bg-slate-900 border border-slate-700 rounded text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => handleAddChildChapter(node.id, node.number)}
                disabled={!childChapterNumber || !childChapterTitle}
                className="px-2 py-1 bg-cyan-600/20 text-cyan-400 rounded text-xs hover:bg-cyan-600/30 transition border border-cyan-600/30 disabled:opacity-50"
              >
                添加
              </button>
              <button
                onClick={() => setAddingChildToId(null)}
                className="px-2 py-1 bg-slate-700 text-slate-400 rounded text-xs hover:bg-slate-600 transition"
              >
                取消
              </button>
            </div>
          </div>
        )}

        {hasChildren && isExpanded && (
          <div className="mt-1">{node.children.map(child => renderTreeNode(child, depth + 1))}</div>
        )}
      </div>
    )
  }

  const wordCount = editorContent.replace(/<[^>]*>/g, '').replace(/\s/g, '').length

  return (
    <main className="flex-1 flex flex-col min-w-0">
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
          <button onClick={handleGenerate} disabled={isGenerating || !activeChapter}
            className="px-3 py-1.5 bg-emerald-600/20 hover:bg-emerald-600/30 rounded text-xs text-emerald-400 transition-colors border border-emerald-600/30 disabled:opacity-50">
            <svg className="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            {isGenerating ? '生成中...' : 'AI生成'}
          </button>
          <button onClick={handlePolish} disabled={isPolishing || !activeChapter}
            className="px-3 py-1.5 bg-cyan-600/20 hover:bg-cyan-600/30 rounded text-xs text-cyan-400 transition-colors border border-cyan-600/30 disabled:opacity-50">
            <svg className="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
            </svg>
            {isPolishing ? '润色中...' : 'AI润色'}
          </button>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        <div className="w-72 border-r border-slate-700 bg-slate-900/30 overflow-y-auto section-tree shrink-0">
          <div className="p-3">
            <form onSubmit={handleAddChapter} className="mb-3 space-y-2">
              <input type="text" placeholder="章节编号 (如: 10.2)" value={newChapterNumber} onChange={(e) => setNewChapterNumber(e.target.value)}
                className="w-full px-2 py-1.5 bg-slate-800 border border-slate-700 rounded text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500" />
              <input type="text" placeholder="章节标题" value={newChapterTitle} onChange={(e) => setNewChapterTitle(e.target.value)}
                className="w-full px-2 py-1.5 bg-slate-800 border border-slate-700 rounded text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500" />
              <button type="submit" className="w-full px-3 py-1.5 bg-cyan-600/20 text-cyan-400 rounded text-xs hover:bg-cyan-600/30 transition border border-cyan-600/30">+ 添加章节</button>
            </form>
            <div className="space-y-1">
              {tree.length === 0 ? <p className="text-xs text-slate-500 text-center py-4">暂无章节</p> : tree.map(node => renderTreeNode(node))}
            </div>
          </div>
        </div>

        <div className="flex-1 flex flex-col bg-slate-950 min-w-0">
          <div className="h-10 border-b border-slate-800 flex items-center px-4 gap-2 text-sm shrink-0">
            <span className="text-slate-500">CSR</span>
            <svg className="w-3 h-3 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
            <span className="text-slate-500">Section {activeChapter?.number?.split('.')[0] || '?'}</span>
            {activeChapter && (<>
              <svg className="w-3 h-3 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
              <span className="text-cyan-400 font-medium truncate">{activeChapter.number} {activeChapter.title}</span>
            </>)}
            <div className="ml-auto flex gap-2">
              <span className="text-xs px-2 py-1 rounded bg-purple-500/20 text-purple-300">Protocol</span>
              <span className="text-xs px-2 py-1 rounded bg-blue-500/20 text-blue-300">SAP</span>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-6">
            {activeChapter ? (
              <div className="max-w-3xl mx-auto">
                <h2 className="text-2xl font-bold text-white mb-6">{activeChapter.number} {activeChapter.title}</h2>
                <div className="mb-4">
                  <p className="text-sm text-slate-400 italic border-l-2 border-cyan-500 pl-3">[本章节内容基于Protocol和SAP中的信息自动生成，已进行去重处理]</p>
                </div>
                {showDiff && diffData && (
                  <div className="mb-6">
                    <DiffViewer diffBlocks={diffData.blocks} reasoning={diffData.reasoning} onAccept={handleAcceptDiff} onReject={handleRejectDiff} onPartialAccept={handlePartialAccept} />
                  </div>
                )}
                <TipTapEditor content={editorContent} onChange={(html, json) => { setEditorContent(html); setEditorJson(json) }} />
                <div className="flex justify-end mt-4 gap-2">
                  <button onClick={handleSave} disabled={isSaving} className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-sm transition-colors disabled:opacity-50">{isSaving ? '保存中...' : '保存'}</button>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <svg className="w-16 h-16 text-slate-700 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <p className="text-slate-500 text-lg">选择一个章节开始编辑</p>
                  <p className="text-slate-600 text-sm mt-2">在左侧结构树中点击章节，或使用「添加章节」创建新章节</p>
                </div>
              </div>
            )}
          </div>

          <div className="h-8 bg-slate-900 border-t border-slate-800 flex items-center px-4 text-xs text-slate-500 shrink-0">
            <div className="flex items-center gap-4">
              <span><svg className="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-4 4m0 0l-4-4m4 4V4" /></svg>自动保存于 {new Date().toLocaleTimeString('zh-CN')}</span>
              <span className="text-emerald-500"><svg className="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>数据已加密</span>
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
