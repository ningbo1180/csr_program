'use client'

import Link from 'next/link'

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gradient-bg text-slate-200">
      <div className="text-center max-w-2xl px-6">
        <div className="w-20 h-20 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-8 shadow-lg shadow-cyan-500/25">
          <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <h1 className="text-5xl font-bold text-white mb-4">
          CSR GenAI
        </h1>
        <p className="text-xl text-slate-400 mb-2">
          临床研究报告（CSR）智能生成平台
        </p>
        <p className="text-sm text-slate-500 mb-10">
          整合 Protocol、SAP 和 TFLs，实现报告的自动化撰写、动态结构管理、实时协作以及合规性审计
        </p>
        <div className="flex gap-4 justify-center">
          <Link href="/projects">
            <button className="px-8 py-3 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg font-medium transition shadow-lg shadow-cyan-500/25 flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              开始新项目
            </button>
          </Link>
          <Link href="/projects">
            <button className="px-8 py-3 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg font-medium transition border border-slate-700 flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
              打开已有项目
            </button>
          </Link>
        </div>

        <div className="mt-16 grid grid-cols-3 gap-8 text-center">
          <div className="glass-panel rounded-lg p-4">
            <div className="text-2xl font-bold text-cyan-400 mb-1">3+</div>
            <div className="text-xs text-slate-400">支持文档类型</div>
          </div>
          <div className="glass-panel rounded-lg p-4">
            <div className="text-2xl font-bold text-cyan-400 mb-1">AI</div>
            <div className="text-xs text-slate-400">智能内容生成</div>
          </div>
          <div className="glass-panel rounded-lg p-4">
            <div className="text-2xl font-bold text-cyan-400 mb-1">100%</div>
            <div className="text-xs text-slate-400">操作可追溯</div>
          </div>
        </div>
      </div>
    </main>
  )
}
