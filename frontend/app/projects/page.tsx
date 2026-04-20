'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

const API_BASE = 'http://localhost:8000'

export default function ProjectsPage() {
  const router = useRouter()
  const [projects, setProjects] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [newProject, setNewProject] = useState({ name: '', study_id: '', study_phase: 'Phase III', indication: '' })

  useEffect(() => {
    loadProjects()
  }, [])

  const loadProjects = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/projects`)
      if (res.ok) {
        const data = await res.json()
        setProjects(data)
      }
    } catch (err) {
      console.error('Failed to load projects:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async () => {
    if (!newProject.name.trim()) return
    try {
      const res = await fetch(`${API_BASE}/api/projects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newProject),
      })
      if (res.ok) {
        const project = await res.json()
        setShowModal(false)
        setNewProject({ name: '', study_id: '', study_phase: 'Phase III', indication: '' })
        router.push(`/projects/${project.id}`)
      }
    } catch (err) {
      console.error('Create project failed:', err)
    }
  }

  const getStatusBadge = (status: string) => {
    const map: Record<string, { label: string; className: string }> = {
      draft: { label: '草稿', className: 'bg-slate-700/50 text-slate-300' },
      in_progress: { label: '进行中', className: 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30' },
      review: { label: '审核中', className: 'bg-amber-500/20 text-amber-400 border border-amber-500/30' },
      completed: { label: '已完成', className: 'bg-green-500/20 text-green-400 border border-green-500/30' },
    }
    const info = map[status] || map.draft
    return (
      <span className={`px-2 py-1 rounded text-xs font-medium ${info.className}`}>{info.label}</span>
    )
  }

  return (
    <main className="min-h-screen bg-slate-950 text-slate-200">
      <nav className="glass-panel border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center">
            <svg className="w-8 h-8 text-cyan-400 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h1 className="text-xl font-bold text-white">
              CSR <span className="text-cyan-400">GenAI</span> Workspace
            </h1>
          </div>
          <div className="flex items-center gap-4 text-sm text-slate-400">
            <span>项目管理</span>
            <span>导出</span>
            <span>设置</span>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-lg font-semibold text-white">我的项目</h2>
          <button
            onClick={() => setShowModal(true)}
            className="px-4 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 rounded-lg text-sm font-medium text-white transition-all shadow-lg shadow-cyan-500/20"
          >
            <svg className="w-4 h-4 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            新建项目
          </button>
        </div>

        {loading ? (
          <div className="text-center py-12 text-slate-500">加载中...</div>
        ) : projects.length === 0 ? (
          <div className="text-center py-12">
            <svg className="w-16 h-16 text-slate-700 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="text-slate-500">暂无项目</p>
            <p className="text-slate-600 text-sm mt-1">点击"新建项目"创建您的第一个CSR项目</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project) => (
              <div
                key={project.id}
                onClick={() => router.push(`/projects/${project.id}`)}
                className="glass-panel rounded-xl p-6 cursor-pointer card-hover transition-all"
              >
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-base font-semibold text-white truncate">{project.name}</h3>
                  {getStatusBadge(project.status)}
                </div>
                <div className="text-sm text-slate-400 space-y-1 mb-4">
                  <p>研究编号: {project.study_id || '-'}</p>
                  <p>适应症: {project.indication || '-'}</p>
                  <p>阶段: {project.study_phase || '-'}</p>
                </div>
                <div className="flex items-center justify-between text-xs text-slate-500">
                  <span>更新于 {new Date(project.updated_at).toLocaleDateString('zh-CN')}</span>
                  <span className="flex items-center text-cyan-400">
                    进入项目
                    <svg className="w-3 h-3 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="glass-panel rounded-xl p-6 w-full max-w-md mx-4 border border-slate-600">
            <h3 className="text-lg font-semibold text-white mb-4">新建项目</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-slate-400 mb-1">项目名称 *</label>
                <input
                  type="text"
                  value={newProject.name}
                  onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500"
                  placeholder="输入项目名称"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">研究编号</label>
                <input
                  type="text"
                  value={newProject.study_id}
                  onChange={(e) => setNewProject({ ...newProject, study_id: e.target.value })}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500"
                  placeholder="e.g. NCT12345678"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">适应症</label>
                <input
                  type="text"
                  value={newProject.indication}
                  onChange={(e) => setNewProject({ ...newProject, indication: e.target.value })}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500"
                  placeholder="输入适应症"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">研究阶段</label>
                <select
                  value={newProject.study_phase}
                  onChange={(e) => setNewProject({ ...newProject, study_phase: e.target.value })}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500"
                >
                  <option value="Phase I">Phase I</option>
                  <option value="Phase II">Phase II</option>
                  <option value="Phase III">Phase III</option>
                  <option value="Phase IV">Phase IV</option>
                </select>
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowModal(false)}
                className="flex-1 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm text-white transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleCreate}
                disabled={!newProject.name.trim()}
                className="flex-1 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 rounded-lg text-sm font-medium text-white transition-all disabled:opacity-50"
              >
                创建
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  )
}
