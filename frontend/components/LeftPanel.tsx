'use client'

import { useState, useRef } from 'react'

interface LeftPanelProps {
  project: any
  documents: any[]
  logs: any[]
  projectId: string
  onConfigUpdate: (config: any) => void
  onUploadComplete: () => void
}

const API_BASE = 'http://localhost:8000'

const docTypeConfig: Record<string, { label: string; subLabel: string; color: string; icon: string }> = {
  protocol: { label: 'Protocol', subLabel: '研究方案', color: 'purple', icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
  sap: { label: 'SAP', subLabel: '统计分析计划', color: 'blue', icon: 'M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z' },
  tfl: { label: 'TFLs', subLabel: '图表列表', color: 'emerald', icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z' },
  other: { label: '其他', subLabel: '文档', color: 'slate', icon: 'M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z' },
}

function getDocTypeInfo(doc: any) {
  const key = doc.doc_type?.toLowerCase() || 'other'
  return docTypeConfig[key] || docTypeConfig.other
}

export default function LeftPanel({ project, documents, logs, projectId, onConfigUpdate, onUploadComplete }: LeftPanelProps) {
  const [isUploading, setIsUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    if (!files.length) return
    setIsUploading(true)

    try {
      for (const file of files) {
        const formData = new FormData()
        formData.append('file', file)
        const uploadRes = await fetch(`${API_BASE}/api/documents/${projectId}/upload`, {
          method: 'POST',
          body: formData,
        })
        if (uploadRes.ok) {
          const doc = await uploadRes.json()
          await fetch(`${API_BASE}/api/documents/${doc.id}/process`, { method: 'POST' })
        }
      }
      onUploadComplete()
    } catch (err) {
      console.error('Upload failed:', err)
    } finally {
      setIsUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const getStatusBadge = (doc: any) => {
    const info = getDocTypeInfo(doc)
    const isCompleted = doc.status === 'completed'
    const isProcessing = doc.status === 'processing'
    const color = info.color

    return (
      <div className={`bg-slate-800/50 rounded-lg p-3 border border-slate-700 hover:border-${color}-500/50 transition-colors cursor-pointer group`}>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <div className={`w-8 h-8 rounded bg-${color}-500/20 flex items-center justify-center`}>
              <svg className={`w-4 h-4 text-${color}-400`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={info.icon} />
              </svg>
            </div>
            <div>
              <div className="text-sm font-medium text-white">{info.label}</div>
              <div className="text-xs text-slate-400">{info.subLabel}</div>
            </div>
          </div>
          {isCompleted ? (
            <svg className="w-5 h-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
          ) : isProcessing ? (
            <span className="status-dot status-processing"></span>
          ) : doc.status === 'failed' ? (
            <span className="status-dot status-error"></span>
          ) : (
            <span className="status-dot status-pending"></span>
          )}
        </div>
        <div className="text-xs text-slate-500 truncate">{doc.name}</div>
        <div className="mt-2 flex gap-1">
          {isCompleted && (
            <>
              <span className={`source-badge source-${color === 'emerald' ? 'tfl' : color === 'blue' ? 'sap' : 'protocol'}`}>已解析</span>
              {doc.extracted_chapters?.chapters && (
                <span className={`source-badge source-${color === 'emerald' ? 'tfl' : color === 'blue' ? 'sap' : 'protocol'}`}>
                  {doc.extracted_chapters.chapters.length}章节
                </span>
              )}
            </>
          )}
          {isProcessing && (
            <div className="mt-1 w-full bg-slate-700 rounded-full h-1">
              <div className="progress-bar h-1 rounded-full" style={{ width: '75%' }}></div>
            </div>
          )}
        </div>
      </div>
    )
  }

  const formatTime = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    } catch {
      return '--:--'
    }
  }

  const getActionColor = (type: string) => {
    if (type.includes('upload') || type.includes('parse')) return 'text-emerald-400'
    if (type.includes('ai')) return 'text-cyan-400'
    if (type.includes('edit') || type.includes('rename')) return 'text-amber-400'
    return 'text-slate-400'
  }

  return (
    <aside className="w-80 glass-panel border-r border-slate-700 flex flex-col shrink-0">
      {/* Input Sources */}
      <div className="p-4 border-b border-slate-700">
        <h2 className="text-sm font-semibold text-white mb-3 flex items-center">
          <svg className="w-4 h-4 mr-2 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
          </svg>
          输入数据源
        </h2>

        <div className="space-y-3">
          {documents.length === 0 ? (
            <p className="text-xs text-slate-500 text-center py-2">暂无文档</p>
          ) : (
            documents.map((doc) => (
              <div key={doc.id}>{getStatusBadge(doc)}</div>
            ))
          )}
        </div>

        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.docx,.xlsx"
          onChange={handleFileSelect}
          className="hidden"
        />
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading}
          className="w-full mt-4 py-2 border border-dashed border-slate-600 rounded-lg text-sm text-slate-400 hover:border-cyan-500 hover:text-cyan-400 transition-colors disabled:opacity-50"
        >
          <svg className="w-4 h-4 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          {isUploading ? '上传中...' : '添加更多文档'}
        </button>
      </div>

      {/* AI Configuration */}
      <div className="p-4 border-b border-slate-700">
        <h2 className="text-sm font-semibold text-white mb-3 flex items-center">
          <svg className="w-4 h-4 mr-2 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          AI 生成配置
        </h2>

        <div className="space-y-3 text-sm">
          <div className="flex items-center justify-between">
            <span className="text-slate-400">输出语言</span>
            <select
              value={project?.language || 'zh-CN'}
              onChange={(e) => onConfigUpdate({ language: e.target.value })}
              className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-white text-xs focus:outline-none focus:border-cyan-500"
            >
              <option value="zh-CN">中文 (主要)</option>
              <option value="en">English</option>
              <option value="bilingual">中英双语</option>
            </select>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-slate-400">表格方向</span>
            <div className="flex bg-slate-800 rounded p-1">
              {['auto', 'portrait', 'landscape'].map((opt) => (
                <button
                  key={opt}
                  onClick={() => onConfigUpdate({ table_orientation: opt })}
                  className={`px-2 py-1 rounded text-xs transition ${
                    (project?.table_orientation || 'auto') === opt
                      ? 'bg-cyan-600 text-white'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {opt === 'auto' ? '自动' : opt === 'portrait' ? '纵向' : '横向'}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-slate-400">去重级别</span>
            <select
              value={project?.dedup_level || 'strict'}
              onChange={(e) => onConfigUpdate({ dedup_level: e.target.value })}
              className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-white text-xs focus:outline-none focus:border-cyan-500"
            >
              <option value="strict">严格 (推荐)</option>
              <option value="standard">标准</option>
              <option value="loose">宽松</option>
            </select>
          </div>

          <div className="flex items-center gap-2 mt-3">
            <input
              type="checkbox"
              checked={project?.enable_hyperlink !== false}
              onChange={(e) => onConfigUpdate({ enable_hyperlink: e.target.checked })}
              className="rounded bg-slate-800 border-slate-600 text-cyan-500 focus:ring-cyan-500"
            />
            <span className="text-xs text-slate-300">启用超链接追踪</span>
          </div>
        </div>
      </div>

      {/* Operation Log */}
      <div className="flex-1 overflow-hidden flex flex-col">
        <div className="p-3 border-b border-slate-700 bg-slate-800/30">
          <h3 className="text-xs font-semibold text-slate-300">操作日志 (可追溯)</h3>
        </div>
        <div className="flex-1 overflow-y-auto p-3 space-y-2 text-xs section-tree">
          {logs.length === 0 ? (
            <p className="text-slate-500 text-center py-4">暂无操作记录</p>
          ) : (
            logs.map((log) => (
              <div key={log.id} className="flex gap-2 text-slate-400">
                <span className="text-slate-600 shrink-0">{formatTime(log.created_at)}</span>
                <span className={getActionColor(log.action_type)}>{log.description}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </aside>
  )
}
