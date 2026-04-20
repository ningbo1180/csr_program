'use client'

import { useState, useRef, useEffect } from 'react'

interface RightPanelProps {
  projectId: string
  activeChapter: any
  messages: any[]
  onSendMessage: (msg: any) => void
  status: any
  onGenerateComplete: () => void
}

const API_BASE = ''

export default function RightPanel({ projectId, activeChapter, messages, onSendMessage, status, onGenerateComplete }: RightPanelProps) {
  const [activeTab, setActiveTab] = useState<'ai' | 'preview'>('ai')
  const [inputText, setInputText] = useState('')
  const [chatMessages, setChatMessages] = useState<any[]>([
    {
      type: 'ai',
      text: '你好！我是 CSR 智能助手。我可以帮你生成章节内容、检查一致性、查找来源文档、翻译内容等。\n\n输入「帮助」查看可用功能。',
      time: new Date().toISOString(),
    },
  ])
  const [isGenerating, setIsGenerating] = useState(false)
  const [isChatLoading, setIsChatLoading] = useState(false)
  const chatEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [chatMessages])

  const handleSend = async () => {
    if (!inputText.trim() || isChatLoading) return

    const userMsg = { type: 'user', text: inputText, time: new Date().toISOString() }
    setChatMessages(prev => [...prev, userMsg])
    onSendMessage(userMsg)
    setInputText('')
    setIsChatLoading(true)

    try {
      const res = await fetch(`${API_BASE}/api/ai/chat?project_id=${projectId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMsg.text,
          chapter_id: activeChapter?.id,
        }),
      })
      if (res.ok) {
        const data = await res.json()
        const aiMsg = {
          type: 'ai',
          text: data.reply,
          suggestions: data.suggestions || [],
          time: new Date().toISOString(),
        }
        setChatMessages(prev => [...prev, aiMsg])
        onSendMessage(aiMsg)
      } else {
        throw new Error('API error')
      }
    } catch (err) {
      const aiMsg = {
        type: 'ai',
        text: '抱歉，服务暂时不可用，请稍后重试。',
        isError: true,
        time: new Date().toISOString(),
      }
      setChatMessages(prev => [...prev, aiMsg])
      onSendMessage(aiMsg)
    } finally {
      setIsChatLoading(false)
    }
  }

  const handleGenerateChapter = async () => {
    if (!activeChapter) {
      const aiMsg = {
        type: 'ai',
        text: '请先选择一个章节，然后再生成内容。',
        time: new Date().toISOString(),
        isError: true,
      }
      setChatMessages(prev => [...prev, aiMsg])
      return
    }

    setIsGenerating(true)
    const aiMsg = {
      type: 'ai',
      text: `正在生成 ${activeChapter.number} ${activeChapter.title} 的内容...`,
      time: new Date().toISOString(),
      isLoading: true,
    }
    setChatMessages(prev => [...prev, aiMsg])

    try {
      const res = await fetch(`${API_BASE}/api/chapters/${projectId}/${activeChapter.id}/generate`, {
        method: 'POST',
      })
      if (res.ok) {
        const data = await res.json()
        setChatMessages(prev => [
          ...prev.filter(m => !m.isLoading),
          {
            type: 'ai',
            text: `已完成 ${activeChapter.number} ${activeChapter.title} 的初稿生成，从Protocol和SAP中整合了相关信息。\n\n您可以在编辑器中查看和修改生成的内容。`,
            time: new Date().toISOString(),
          },
        ])
        onGenerateComplete()
      } else {
        throw new Error('生成失败')
      }
    } catch (err) {
      setChatMessages(prev => [
        ...prev.filter(m => !m.isLoading),
        {
          type: 'ai',
          text: '生成过程中出现错误，请稍后重试。',
          time: new Date().toISOString(),
          isError: true,
        },
      ])
    } finally {
      setIsGenerating(false)
    }
  }

  const handleFindSources = async () => {
    if (!activeChapter) {
      setChatMessages(prev => [...prev, {
        type: 'ai',
        text: '请先选择一个章节，然后点击「查找来源」搜索相关文档内容。',
        isError: true,
        time: new Date().toISOString(),
      }])
      return
    }
    setIsChatLoading(true)
    setChatMessages(prev => [...prev, {
      type: 'ai',
      text: `正在「${activeChapter.title}」中查找来源引用...`,
      isLoading: true,
      time: new Date().toISOString(),
    }])

    try {
      const res = await fetch(`${API_BASE}/api/ai/find-sources?project_id=${projectId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: activeChapter.title, chapter_id: activeChapter.id }),
      })
      if (res.ok) {
        const data = await res.json()
        setChatMessages(prev => [
          ...prev.filter(m => !m.isLoading),
          { type: 'ai', text: data.reply, time: new Date().toISOString() },
        ])
      } else {
        throw new Error('API error')
      }
    } catch (err) {
      setChatMessages(prev => [
        ...prev.filter(m => !m.isLoading),
        { type: 'ai', text: '查找来源失败，请稍后重试。', isError: true, time: new Date().toISOString() },
      ])
    } finally {
      setIsChatLoading(false)
    }
  }

  const handleTranslate = async () => {
    if (!activeChapter) {
      setChatMessages(prev => [...prev, {
        type: 'ai',
        text: '请先选择一个章节，然后点击「翻译」进行内容翻译。',
        isError: true,
        time: new Date().toISOString(),
      }])
      return
    }
    setIsChatLoading(true)
    setChatMessages(prev => [...prev, {
      type: 'ai',
      text: `正在翻译「${activeChapter.title}」...`,
      isLoading: true,
      time: new Date().toISOString(),
    }])

    try {
      const targetLang = activeChapter.content && activeChapter.content.length > 0 ? 'en' : 'zh-CN'
      const res = await fetch(`${API_BASE}/api/ai/translate?project_id=${projectId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: activeChapter.content || activeChapter.title, target_language: targetLang }),
      })
      if (res.ok) {
        const data = await res.json()
        const reply = `**翻译结果** (${data.target_language})\n\n${data.translated}\n\n*提示：当前为模拟翻译，生产环境将接入真实翻译服务。*`
        setChatMessages(prev => [
          ...prev.filter(m => !m.isLoading),
          { type: 'ai', text: reply, time: new Date().toISOString() },
        ])
      } else {
        throw new Error('API error')
      }
    } catch (err) {
      setChatMessages(prev => [
        ...prev.filter(m => !m.isLoading),
        { type: 'ai', text: '翻译失败，请稍后重试。', isError: true, time: new Date().toISOString() },
      ])
    } finally {
      setIsChatLoading(false)
    }
  }

  const handleSuggestionClick = (suggestion: string) => {
    setInputText(suggestion)
  }

  const progress = status?.generation_progress || {}
  const stats = [
    { label: 'Protocol整合', key: 'protocol', color: 'bg-purple-500', value: progress.protocol || 0 },
    { label: 'SAP数据提取', key: 'sap', color: 'bg-blue-500', value: progress.sap || 0 },
    { label: 'TFLs图表关联', key: 'tfls', color: 'bg-emerald-500', value: progress.tfls || 0 },
  ]

  return (
    <aside className="w-96 glass-panel border-l border-slate-700 flex flex-col shrink-0">
      {/* Tabs */}
      <div className="flex border-b border-slate-700">
        <button
          onClick={() => setActiveTab('ai')}
          className={`flex-1 py-3 text-sm font-medium transition ${
            activeTab === 'ai'
              ? 'text-cyan-400 border-b-2 border-cyan-400 bg-slate-800/30'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          <svg className="w-4 h-4 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          AI助手
        </button>
        <button
          onClick={() => setActiveTab('preview')}
          className={`flex-1 py-3 text-sm font-medium transition ${
            activeTab === 'preview'
              ? 'text-cyan-400 border-b-2 border-cyan-400 bg-slate-800/30'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          <svg className="w-4 h-4 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
          实时预览
        </button>
      </div>

      {activeTab === 'ai' ? (
        <>
          {/* AI Chat */}
          <div className="flex-1 overflow-hidden flex flex-col">
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {chatMessages.map((msg, idx) => (
                <div key={idx} className={`flex gap-3 ${msg.type === 'user' ? 'flex-row-reverse' : ''}`}>
                  {msg.type === 'ai' ? (
                    <div className="w-8 h-8 rounded-full bg-gradient-to-r from-cyan-500 to-blue-600 flex items-center justify-center flex-shrink-0">
                      <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                      </svg>
                    </div>
                  ) : (
                    <div className="w-8 h-8 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center flex-shrink-0 text-xs font-bold text-white">
                      NB
                    </div>
                  )}
                  <div className={`flex-1 ${msg.type === 'user' ? 'text-right' : ''}`}>
                    {msg.type === 'ai' && (
                      <div className="text-xs text-cyan-400 mb-1">Kimi CSR Assistant</div>
                    )}
                    <div
                      className={`rounded-lg p-3 text-sm border inline-block text-left whitespace-pre-wrap ${
                        msg.type === 'ai'
                          ? msg.isError
                            ? 'bg-red-500/10 border-red-500/30 text-red-300'
                            : 'bg-slate-800/70 border-slate-700 text-slate-300'
                          : 'bg-slate-700/50 border-slate-600 text-slate-200'
                      }`}
                    >
                      {msg.text}
                      {msg.isLoading && (
                        <span className="inline-block ml-2 w-4 h-4 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin"></span>
                      )}
                    </div>
                    {msg.type === 'ai' && msg.suggestions && msg.suggestions.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-2">
                        {msg.suggestions.map((s: string, i: number) => (
                          <button
                            key={i}
                            onClick={() => handleSuggestionClick(s)}
                            className="text-xs px-2 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 hover:bg-cyan-500/20 transition-colors"
                          >
                            {s}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              <div ref={chatEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 border-t border-slate-700 bg-slate-900/50">
              <div className="relative">
                <textarea
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg p-3 pr-12 text-sm text-white placeholder-slate-500 resize-none focus:outline-none focus:border-cyan-500"
                  rows={3}
                  placeholder="输入指令，例如：从Protocol中提取安全信息添加到本节..."
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      handleSend()
                    }
                  }}
                />
                <button
                  onClick={handleSend}
                  disabled={isChatLoading}
                  className="absolute right-3 bottom-3 p-2 bg-cyan-600 hover:bg-cyan-500 rounded-lg text-white transition-colors disabled:opacity-50"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                </button>
              </div>
              <div className="flex gap-2 mt-2">
                <button
                  onClick={handleGenerateChapter}
                  disabled={isGenerating}
                  className="text-xs px-2 py-1 rounded bg-slate-800 text-slate-400 hover:text-white transition-colors disabled:opacity-50"
                >
                  <svg className="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                  </svg>
                  生成章节
                </button>
                <button
                  onClick={handleFindSources}
                  disabled={isChatLoading}
                  className="text-xs px-2 py-1 rounded bg-slate-800 text-slate-400 hover:text-white transition-colors disabled:opacity-50"
                >
                  <svg className="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  查找来源
                </button>
                <button
                  onClick={handleTranslate}
                  disabled={isChatLoading}
                  className="text-xs px-2 py-1 rounded bg-slate-800 text-slate-400 hover:text-white transition-colors disabled:opacity-50"
                >
                  <svg className="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
                  </svg>
                  翻译
                </button>
              </div>
            </div>
          </div>
        </>
      ) : (
        <div className="flex-1 overflow-y-auto p-4">
          <div className="text-center py-8">
            <svg className="w-16 h-16 text-slate-700 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
            <p className="text-slate-500">实时预览功能开发中</p>
            <p className="text-slate-600 text-sm mt-2">生成完整CSR后，可在此处预览最终文档</p>
          </div>
        </div>
      )}

      {/* Quick Stats */}
      <div className="p-4 border-t border-slate-700 bg-slate-800/30">
        <h3 className="text-xs font-semibold text-slate-300 mb-3">生成进度</h3>
        <div className="space-y-3">
          {stats.map((stat) => (
            <div key={stat.key}>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-400">{stat.label}</span>
                <span className="text-white">{stat.value}%</span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-1.5">
                <div className={`${stat.color} h-1.5 rounded-full transition-all`} style={{ width: `${stat.value}%` }}></div>
              </div>
            </div>
          ))}
        </div>

        {activeChapter && (
          <div className="mt-4 pt-3 border-t border-slate-700/50">
            <div className="text-xs text-slate-400 mb-1">当前章节</div>
            <div className="text-sm text-white font-medium">{activeChapter.number} {activeChapter.title}</div>
            <div className="text-xs text-slate-500 mt-1">
              {activeChapter.content ? '已有内容' : '待生成'}
            </div>
          </div>
        )}
      </div>
    </aside>
  )
}
