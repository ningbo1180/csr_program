'use client'

interface WorkspaceHeaderProps {
  project: any
  status: any
  onExport: () => void
  onVersionHistory: () => void
}

export default function WorkspaceHeader({ project, status, onExport, onVersionHistory }: WorkspaceHeaderProps) {
  const progress = status?.generation_progress || {}
  const overallProgress = Object.values(progress).length > 0
    ? Math.round(
        (Object.values(progress).reduce((a: any, b: any) => a + (typeof b === 'number' ? b : 0), 0) as number) /
        Object.values(progress).length
      )
    : 0

  const isProcessing = overallProgress > 0 && overallProgress < 100

  return (
    <header className="glass-panel h-16 flex items-center justify-between px-6 fixed top-0 left-0 right-0 z-50">
      <div className="flex items-center gap-4">
        <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-lg flex items-center justify-center">
          <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">CSR GenAI</h1>
          <p className="text-xs text-slate-400">智能临床研究报告生成平台</p>
        </div>
      </div>

      <div className="flex items-center gap-6">
        <div className="flex items-center gap-3 bg-slate-800/50 px-4 py-2 rounded-lg border border-slate-700">
          <span className="text-xs text-slate-400">项目:</span>
          <span className="text-sm font-medium text-white">{project?.name || '未命名项目'}</span>
          {isProcessing ? (
            <>
              <span className="status-dot status-processing ml-2"></span>
              <span className="text-xs text-cyan-400">生成中 {overallProgress}%</span>
            </>
          ) : overallProgress === 100 ? (
            <>
              <span className="status-dot status-complete ml-2"></span>
              <span className="text-xs text-emerald-400">已完成</span>
            </>
          ) : (
            <>
              <span className="status-dot status-pending ml-2"></span>
              <span className="text-xs text-amber-400">待开始</span>
            </>
          )}
        </div>

        <div className="flex gap-2">
          <button
            onClick={onVersionHistory}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm transition-colors border border-slate-700 text-slate-300"
          >
            <svg className="w-4 h-4 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            版本历史
          </button>
          <button
            onClick={onExport}
            className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-sm transition-colors shadow-lg shadow-cyan-500/25"
          >
            <svg className="w-4 h-4 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            导出CSR
          </button>
        </div>

        <div className="w-8 h-8 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center text-xs font-bold text-white">
          NB
        </div>
      </div>
    </header>
  )
}
