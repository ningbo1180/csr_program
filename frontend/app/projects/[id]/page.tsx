'use client'

import { useState, useEffect, useCallback } from 'react'
import { useParams } from 'next/navigation'
import WorkspaceHeader from '@/components/WorkspaceHeader'
import LeftPanel from '@/components/LeftPanel'
import CenterPanel from '@/components/CenterPanel'
import RightPanel from '@/components/RightPanel'
import VersionHistoryModal from '@/components/VersionHistoryModal'

const API_BASE = ''

export default function ProjectWorkspace() {
  const params = useParams()
  const projectId = params?.id as string

  const [project, setProject] = useState<any>(null)
  const [documents, setDocuments] = useState<any[]>([])
  const [tree, setTree] = useState<any[]>([])
  const [logs, setLogs] = useState<any[]>([])
  const [activeChapter, setActiveChapter] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [aiMessages, setAiMessages] = useState<any[]>([])
  const [projectStatus, setProjectStatus] = useState<any>(null)
  const [showVersionModal, setShowVersionModal] = useState(false)
  const [isExporting, setIsExporting] = useState(false)

  // Load project data
  const loadProject = useCallback(async () => {
    if (!projectId) return
    try {
      const res = await fetch(`${API_BASE}/api/projects/${projectId}`)
      if (res.ok) {
        const data = await res.json()
        setProject(data)
      }
    } catch (err) {
      console.error('Failed to load project:', err)
    }
  }, [projectId])

  const loadDocuments = useCallback(async () => {
    if (!projectId) return
    try {
      const res = await fetch(`${API_BASE}/api/documents/${projectId}`)
      if (res.ok) {
        const data = await res.json()
        setDocuments(Array.isArray(data) ? data : [])
      }
    } catch (err) {
      console.error('Failed to load documents:', err)
      setDocuments([])
    }
  }, [projectId])

  const loadTree = useCallback(async () => {
    if (!projectId) return
    try {
      const res = await fetch(`${API_BASE}/api/chapters/${projectId}/tree`)
      if (res.ok) {
        const data = await res.json()
        setTree(data.tree || [])
      }
    } catch (err) {
      console.error('Failed to load tree:', err)
      setTree([])
    }
  }, [projectId])

  const loadLogs = useCallback(async () => {
    if (!projectId) return
    try {
      const res = await fetch(`${API_BASE}/api/logs/${projectId}?limit=50`)
      if (res.ok) {
        const data = await res.json()
        setLogs(Array.isArray(data) ? data : [])
      }
    } catch (err) {
      console.error('Failed to load logs:', err)
      setLogs([])
    }
  }, [projectId])

  const loadStatus = useCallback(async () => {
    if (!projectId) return
    try {
      const res = await fetch(`${API_BASE}/api/projects/${projectId}/status`)
      if (res.ok) {
        const data = await res.json()
        setProjectStatus(data)
      }
    } catch (err) {
      console.error('Failed to load status:', err)
    }
  }, [projectId])

  useEffect(() => {
    if (!projectId) return
    setLoading(true)
    Promise.all([loadProject(), loadDocuments(), loadTree(), loadLogs(), loadStatus()]).then(() => {
      setLoading(false)
    })
  }, [projectId, loadProject, loadDocuments, loadTree, loadLogs, loadStatus])

  // Poll for updates
  useEffect(() => {
    if (!projectId) return
    const interval = setInterval(() => {
      loadDocuments()
      loadLogs()
      loadStatus()
    }, 5000)
    return () => clearInterval(interval)
  }, [projectId, loadDocuments, loadLogs, loadStatus])

  const handleChapterSelect = (chapter: any) => {
    setActiveChapter(chapter)
  }

  const handleContentUpdate = async (content: string) => {
    if (!activeChapter || !projectId) return
    try {
      const res = await fetch(`${API_BASE}/api/chapters/${projectId}/${activeChapter.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content }),
      })
      if (res.ok) {
        setActiveChapter({ ...activeChapter, content })
        loadTree()
        loadLogs()
      }
    } catch (err) {
      console.error('Failed to update content:', err)
    }
  }

  const handleConfigUpdate = async (config: any) => {
    if (!projectId) return
    try {
      const res = await fetch(`${API_BASE}/api/projects/${projectId}/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      })
      if (res.ok) {
        loadProject()
      }
    } catch (err) {
      console.error('Failed to update config:', err)
    }
  }

  const handleAiMessage = (msg: any) => {
    setAiMessages((prev) => [...prev, msg])
  }

  const handleUploadComplete = () => {
    loadDocuments()
    loadLogs()
    loadStatus()
  }

  const handleTreeChange = () => {
    loadTree()
    loadLogs()
    loadStatus()
  }

  const handleExport = async () => {
    if (isExporting) return
    setIsExporting(true)
    try {
      const res = await fetch(`${API_BASE}/api/export/${projectId}`)
      if (res.ok) {
        const blob = await res.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        const filename = res.headers.get('content-disposition')?.match(/filename=([^;]+)/)?.[1] || `CSR_${project?.name || 'export'}.docx`
        a.href = url
        a.download = filename.replace(/"/g, '')
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        window.URL.revokeObjectURL(url)
      } else {
        alert('导出失败，请稍后重试')
      }
    } catch (err) {
      console.error('Export failed:', err)
      alert('导出失败，请检查网络连接')
    } finally {
      setIsExporting(false)
    }
  }

  if (!projectId) {
    return (
      <div className="min-h-screen gradient-bg flex items-center justify-center">
        <p className="text-slate-400">加载中...</p>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="min-h-screen gradient-bg flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-400">加载项目工作台...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen gradient-bg text-slate-200 overflow-hidden flex flex-col">
      <WorkspaceHeader
        project={project}
        status={projectStatus}
        onExport={handleExport}
        onVersionHistory={() => setShowVersionModal(true)}
      />

      <div className="flex flex-1 overflow-hidden pt-16">
        <LeftPanel
          project={project}
          documents={documents}
          logs={logs}
          projectId={projectId}
          onConfigUpdate={handleConfigUpdate}
          onUploadComplete={handleUploadComplete}
        />

        <CenterPanel
          tree={tree}
          activeChapter={activeChapter}
          projectId={projectId}
          onChapterSelect={handleChapterSelect}
          onContentUpdate={handleContentUpdate}
          onTreeChange={handleTreeChange}
        />

        <RightPanel
          projectId={projectId}
          activeChapter={activeChapter}
          messages={aiMessages}
          onSendMessage={handleAiMessage}
          status={projectStatus}
          onGenerateComplete={() => {
            loadTree()
            loadLogs()
            if (activeChapter) {
              fetch(`${API_BASE}/api/chapters/${projectId}/${activeChapter.id}`)
                .then(r => r.ok ? r.json() : null)
                .then(data => { if (data) setActiveChapter(data) })
            }
          }}
        />
      </div>

      <VersionHistoryModal
        projectId={projectId}
        activeChapter={activeChapter}
        isOpen={showVersionModal}
        onClose={() => setShowVersionModal(false)}
        onRestore={() => {
          loadTree()
          loadLogs()
          if (activeChapter) {
            fetch(`${API_BASE}/api/chapters/${projectId}/${activeChapter.id}`)
              .then(r => r.ok ? r.json() : null)
              .then(data => { if (data) setActiveChapter(data) })
          }
        }}
      />
    </div>
  )
}
