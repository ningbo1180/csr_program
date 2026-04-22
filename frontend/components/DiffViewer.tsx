'use client'

import { useState } from 'react'

interface DiffBlock {
  type: 'add' | 'remove' | 'keep'
  text: string
}

interface DiffViewerProps {
  diffBlocks: DiffBlock[]
  reasoning?: string
  onAccept: () => void
  onReject: () => void
  onPartialAccept?: (acceptedBlocks: DiffBlock[]) => void
}

export default function DiffViewer({ diffBlocks, reasoning, onAccept, onReject, onPartialAccept }: DiffViewerProps) {
  const [selectedBlocks, setSelectedBlocks] = useState<Set<number>>(new Set())
  const [viewMode, setViewMode] = useState<'inline' | 'split'>('inline')

  const toggleBlock = (idx: number) => {
    setSelectedBlocks(prev => {
      const next = new Set(prev)
      if (next.has(idx)) next.delete(idx)
      else next.add(idx)
      return next
    })
  }

  const handlePartialAccept = () => {
    if (!onPartialAccept) return
    const accepted = diffBlocks.filter((_, idx) => selectedBlocks.has(idx) || diffBlocks[idx].type === 'keep')
    onPartialAccept(accepted)
  }

  const additions = diffBlocks.filter(b => b.type === 'add').length
  const deletions = diffBlocks.filter(b => b.type === 'remove').length

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-slate-900/80">
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-white">AI 修改建议</span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            +{additions}
          </span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-red-500/10 text-red-400 border border-red-500/20">
            -{deletions}
          </span>
        </div>
        <div className="flex gap-1">
          <button
            onClick={() => setViewMode('inline')}
            className={`text-xs px-2 py-1 rounded transition ${
              viewMode === 'inline' ? 'bg-slate-700 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            内联
          </button>
          <button
            onClick={() => setViewMode('split')}
            className={`text-xs px-2 py-1 rounded transition ${
              viewMode === 'split' ? 'bg-slate-700 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            分栏
          </button>
        </div>
      </div>

      {/* Reasoning */}
      {reasoning && (
        <div className="px-4 py-2 bg-cyan-500/5 border-b border-slate-800">
          <p className="text-xs text-cyan-400">
            <svg className="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {reasoning}
          </p>
        </div>
      )}

      {/* Diff Content */}
      <div className="max-h-96 overflow-y-auto">
        {viewMode === 'inline' ? (
          <div className="divide-y divide-slate-800/50">
            {diffBlocks.map((block, idx) => (
              <div
                key={idx}
                onClick={() => block.type !== 'keep' && toggleBlock(idx)}
                className={`px-4 py-2 flex items-start gap-3 text-sm cursor-pointer transition ${
                  block.type === 'add'
                    ? 'bg-emerald-500/5 hover:bg-emerald-500/10'
                    : block.type === 'remove'
                    ? 'bg-red-500/5 hover:bg-red-500/10'
                    : 'hover:bg-slate-800/50'
                } ${selectedBlocks.has(idx) ? 'ring-1 ring-cyan-500/50' : ''}`}
              >
                <span className="shrink-0 mt-0.5">
                  {block.type === 'add' && (
                    <svg className="w-4 h-4 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                  )}
                  {block.type === 'remove' && (
                    <svg className="w-4 h-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                    </svg>
                  )}
                  {block.type === 'keep' && (
                    <svg className="w-4 h-4 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14" />
                    </svg>
                  )}
                </span>
                <span
                  className={`flex-1 ${
                    block.type === 'add'
                      ? 'text-emerald-300'
                      : block.type === 'remove'
                      ? 'text-red-300 line-through'
                      : 'text-slate-400'
                  }`}
                >
                  {block.text || '(空行)'}
                </span>
                {block.type !== 'keep' && (
                  <input
                    type="checkbox"
                    checked={selectedBlocks.has(idx)}
                    onChange={() => toggleBlock(idx)}
                    className="mt-1 shrink-0 accent-cyan-500"
                    onClick={(e) => e.stopPropagation()}
                  />
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 divide-x divide-slate-800">
            <div className="p-4">
              <div className="text-xs text-slate-500 mb-2">原文</div>
              {diffBlocks.map((block, idx) =>
                block.type !== 'add' ? (
                  <div
                    key={`l-${idx}`}
                    className={`text-sm py-1 ${
                      block.type === 'remove' ? 'text-red-400 bg-red-500/5 line-through' : 'text-slate-400'
                    }`}
                  >
                    {block.text || '(空行)'}
                  </div>
                ) : null
              )}
            </div>
            <div className="p-4">
              <div className="text-xs text-slate-500 mb-2">修改后</div>
              {diffBlocks.map((block, idx) =>
                block.type !== 'remove' ? (
                  <div
                    key={`r-${idx}`}
                    className={`text-sm py-1 ${
                      block.type === 'add' ? 'text-emerald-400 bg-emerald-500/5' : 'text-slate-400'
                    }`}
                  >
                    {block.text || '(空行)'}
                  </div>
                ) : null
              )}
            </div>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between px-4 py-3 border-t border-slate-800 bg-slate-900/80">
        <div className="text-xs text-slate-500">
          {selectedBlocks.size > 0 ? `已选择 ${selectedBlocks.size} 处修改` : '点击选择要应用的修改'}
        </div>
        <div className="flex gap-2">
          {selectedBlocks.size > 0 && onPartialAccept && (
            <button
              onClick={handlePartialAccept}
              className="px-3 py-1.5 bg-cyan-600/20 text-cyan-400 rounded text-xs hover:bg-cyan-600/30 transition border border-cyan-600/30"
            >
              应用选中
            </button>
          )}
          <button
            onClick={onAccept}
            className="px-3 py-1.5 bg-emerald-600/20 text-emerald-400 rounded text-xs hover:bg-emerald-600/30 transition border border-emerald-600/30"
          >
            全部接受
          </button>
          <button
            onClick={onReject}
            className="px-3 py-1.5 bg-red-600/20 text-red-400 rounded text-xs hover:bg-red-600/30 transition border border-red-600/30"
          >
            全部拒绝
          </button>
        </div>
      </div>
    </div>
  )
}
