'use client'

import { useState, useEffect } from 'react'

interface VersionHistoryModalProps {
  projectId: string
  activeChapter: any
  isOpen: boolean
  onClose: () => void
  onRestore: () => void
}

const API_BASE = ''

export default function VersionHistoryModal({ projectId, activeChapter, isOpen, onClose, onRestore }: VersionHistoryModalProps) {
  const [versions, setVersions] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [restoringId, setRestoringId] = useState<string | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (isOpen && activeChapter) {
      loadVersions()
    }
  }, [isOpen, activeChapter])

  const loadVersions = async () => {
    if (!activeChapter) return
    setLoading(true)
    setError('')
    try {
      const res = await fetch(`${API_BASE}/api/chapters/${projectId}/${activeChapter.id}/versions`)
      if (res.ok) {
        const data = await res.json()
        setVersions(Array.isArray(data) ? data : [])
      } else {
        setError('加载版本历史失败')
      }
    } catch (err) {
      setError('网络错误')
    } finally {
      setLoading(false)
    }
  }

  const handleRestore = async (versionId: string) => {
    if (!activeChapter) return
    setRestoringId(versionId)
    try {
      const res = await fetch(`${API_BASE}/api/chapters/${projectId}/${activeChapter.id}/versions/${versionId}/restore`, {
        method: 'POST',
      })
      if (res.ok) {
        onRestore()
        loadVersions()
      } else {
        setError('恢复版本失败')
      }
    } catch (err) {
      setError('网络错误')
    } finally {
      setRestoringId(null)
    }
  }

  const formatTime = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString('zh-CN')
    } catch {
      return '--'
    }
  }

  const getActionLabel = (type: string) => {
    const map: Record<string, string> = {
      edit: '手动编辑',
      ai_generate: 'AI生成',
      restore: '版本恢复',
    }
    return map[type] || type
  }

  const getActionColor = (type: string) => {
    const map: Record<string, string> = {
      edit: 'text-amber-400',
      ai_generate: 'text-cyan-400',
      restore: 'text-purple-400',
    }
    return map[type] || 'text-slate-400'
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="glass-panel rounded-xl w-full max-w-2xl mx-4 border border-slate-600 flex flex-col max-h-[80vh]">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          <div>
            <h3 className="text-lg font-semibold text-white">版本历史</h3>
            <p className="text-xs text-slate-400 mt-1">
              {activeChapter ? `${activeChapter.number} ${activeChapter.title}` : '请选择一个章节'}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-700 rounded-lg transition-colors text-slate-400 hover:text-white"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {!activeChapter ? (
            <div className="text-center py-8 text-slate-500">
              <svg className="w-12 h-12 mx-auto mb-3 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              <p>请在工作区中选择一个章节查看版本历史</p>
            </div>
          ) : loading ? (
            <div className="text-center py-8 text-slate-500">
              <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
              <p>加载中...</p>
            </div>
          ) : error ? (
            <div className="text-center py-8 text-red-400">
              <p>{error}</p>
              <button onClick={loadVersions} className="mt-2 text-sm text-cyan-400 hover:underline">重试</button>
            </div>
          ) : versions.length === 0 ? (
            <div className="text-center py-8 text-slate-500">
              <svg className="w-12 h-12 mx-auto mb-3 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p>该章节暂无版本历史</p>
              <p className="text-sm text-slate-600 mt-1">编辑或生成内容后将自动保存版本</p>
            </div>
          ) : (
            <div className="space-y-3">
              {/* Current version */}
              <div className="bg-slate-800/50 rounded-lg p-3 border border-cyan-500/30">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-400 font-medium">当前版本</span>
                    <span className="text-sm text-white">{activeChapter.content ? '已有内容' : '空'}</span>
                  </div>
                  <span className="text-xs text-slate-500">{formatTime(activeChapter.updated_at)}</span>
                </div>
              </div>

              {/* Version list */}
              {versions.map((v) => (
                <div key={v.id} className="bg-slate-800/30 rounded-lg p-3 border border-slate-700 hover:border-slate-600 transition-colors">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className={`text-xs font-medium ${getActionColor(v.action_type)}`}>
                        #{v.version_number} {getActionLabel(v.action_type)}
                      </span>
                      <span className="text-xs text-slate-500">
                        {v.content ? `${v.content.length} 字符` : '空'}
                      </span>
                    </div>
                    <span className="text-xs text-slate-500">{formatTime(v.created_at)}</span>
                  </div>
                  <div className="text-xs text-slate-400 line-clamp-3 mb-2">
                    {v.content ? v.content.replace(/<[^>]+>/g, '').substring(0, 200) : '无内容'}
                    {v.content && v.content.length > 200 ? '...' : ''}
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleRestore(v.id)}
                      disabled={restoringId === v.id}
                      className="text-xs px-3 py-1.5 rounded bg-cyan-600/20 border border-cyan-500/30 text-cyan-400 hover:bg-cyan-600/30 transition-colors disabled:opacity-50"
                    >
                      {restoringId === v.id ? (
                        <span className="flex items-center gap-1">
                          <span className="w-3 h-3 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin"></span>
                          恢复中...
                        </span>
                      ) : (
                        '恢复此版本'
                      )}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
