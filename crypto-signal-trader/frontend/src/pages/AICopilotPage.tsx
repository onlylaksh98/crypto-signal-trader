import React, { useState, useEffect, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  Sparkles,
  Send,
  Bot,
  User,
  Database,
  RefreshCw,
  BookOpen,
  ChevronDown,
  ChevronUp,
  Layers,
  ShieldCheck,
  Zap,
  Plus,
  Clock,
  Search,
  ExternalLink,
  Cpu,
} from 'lucide-react'
import { api } from '../services/api'
import { Badge } from '../components/common/Badge'
import type { RagStatus, RagSource, KnowledgeDoc } from '../types'

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: RagSource[]
  provider_used?: string
  metrics?: {
    retrieval_time_ms: number
    generation_time_ms: number
    total_time_ms: number
    sources_retrieved: number
  }
  timestamp: string
}

export const AICopilotPage: React.FC = () => {
  const [searchParams] = useSearchParams()
  const initialQuery = searchParams.get('q') || ''

  const [activeTab, setActiveTab] = useState<'chat' | 'knowledge'>('chat')
  const [query, setQuery] = useState(initialQuery)
  const [loading, setLoading] = useState(false)
  const [symbolFilter, setSymbolFilter] = useState('')
  const [ragStatus, setRagStatus] = useState<RagStatus | null>(null)
  const [reindexing, setReindexing] = useState(false)
  const [expandedSources, setExpandedSources] = useState<Record<string, boolean>>({})

  // Knowledge base state
  const [knowledgeDocs, setKnowledgeDocs] = useState<KnowledgeDoc[]>([])
  const [kbLoading, setKbLoading] = useState(false)
  const [kbFilter, setKbFilter] = useState<string>('')
  const [newDocModal, setNewDocModal] = useState(false)
  const [newDocTitle, setNewDocTitle] = useState('')
  const [newDocType, setNewDocType] = useState('strategy')
  const [newDocText, setNewDocText] = useState('')
  const [addingDoc, setAddingDoc] = useState(false)

  // Chat message history
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        '👋 Welcome to **CryptoSignal AI Copilot**.\n\nI am grounded in your **historical Telegram signals**, trade outcomes, and **institutional strategy playbooks** using Retrieval-Augmented Generation (RAG).\n\nAsk me about past trade performance, specific asset setups, risk sizing calculations, or strategy confirmation rules.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ])

  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, loading])

  // Fetch RAG status
  const loadStatus = async () => {
    try {
      const data = await api.getRagStatus()
      setRagStatus(data)
    } catch {
      // Ignore
    }
  }

  // Fetch Knowledge Base Docs
  const loadKnowledgeBase = async () => {
    setKbLoading(true)
    try {
      const docs = await api.getKnowledgeBase(kbFilter || undefined)
      setKnowledgeDocs(docs)
    } catch {
      // Ignore
    } finally {
      setKbLoading(false)
    }
  }

  useEffect(() => {
    loadStatus()
  }, [])

  useEffect(() => {
    if (activeTab === 'knowledge') {
      loadKnowledgeBase()
    }
  }, [activeTab, kbFilter])

  // Handle URL query param
  useEffect(() => {
    if (initialQuery && messages.length === 1) {
      handleSend(initialQuery)
    }
  }, [initialQuery])

  const handleSend = async (overrideText?: string) => {
    const textToSend = overrideText || query
    if (!textToSend.trim() || loading) return

    const userMsg: ChatMessage = {
      id: `usr-${Date.now()}`,
      role: 'user',
      content: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }

    setMessages((prev) => [...prev, userMsg])
    setQuery('')
    setLoading(true)

    try {
      const res = await api.queryRag(textToSend, 5, undefined, symbolFilter || undefined)
      const assistantMsg: ChatMessage = {
        id: `asst-${Date.now()}`,
        role: 'assistant',
        content: res.answer,
        sources: res.sources,
        provider_used: res.provider_used,
        metrics: res.metrics,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }
      setMessages((prev) => [...prev, assistantMsg])
      loadStatus() // refresh stats
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: `⚠️ **RAG Query Error**: ${err.message || 'Failed to query RAG engine.'}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }
      setMessages((prev) => [...prev, errorMsg])
    } finally {
      setLoading(false)
    }
  }

  const handleReindex = async () => {
    setReindexing(true)
    try {
      const res = await api.reindexRag()
      alert(`Reindexing completed: ${res.signals_indexed} historical signals indexed into vector store. Total documents: ${res.total_documents}.`)
      loadStatus()
      if (activeTab === 'knowledge') loadKnowledgeBase()
    } catch (err: any) {
      alert(`Reindex failed: ${err.message}`)
    } finally {
      setReindexing(false)
    }
  }

  const handleAddCustomDoc = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newDocTitle.trim() || !newDocText.trim()) return
    setAddingDoc(true)
    try {
      await api.addKnowledgeDoc({
        title: newDocTitle,
        doc_type: newDocType,
        text: newDocText,
      })
      setNewDocModal(false)
      setNewDocTitle('')
      setNewDocText('')
      loadKnowledgeBase()
      loadStatus()
    } catch (err: any) {
      alert(`Failed to save document: ${err.message}`)
    } finally {
      setAddingDoc(false)
    }
  }

  const toggleSources = (msgId: string) => {
    setExpandedSources((prev) => ({
      ...prev,
      [msgId]: !prev[msgId],
    }))
  }

  const promptChips = [
    'Analyze our historical win rate on ETH setups',
    'Explain the Breakout & Volume confirmation rules',
    'Review institutional 2% risk management guidelines',
    'Compare historical SOL long signals performance',
    'What are the warning signs of low quality Telegram signals?',
  ]

  return (
    <div className="p-4 lg:p-8 space-y-6 max-w-7xl mx-auto flex flex-col h-[calc(100vh-6.5rem)]">
      {/* Header & Status Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 shrink-0">
        <div>
          <h1 className="text-xl lg:text-2xl font-bold tracking-tight text-white flex items-center gap-3">
            <span className="p-2 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 text-white shadow-lg shadow-blue-500/20">
              <Sparkles className="w-5 h-5 animate-pulse" />
            </span>
            AI Copilot & Market RAG Assistant
          </h1>
          <p className="text-xs text-gray-400 mt-1">
            Grounded intelligence over historical Telegram signals, closed trades, and institutional strategy playbooks.
          </p>
        </div>

        {/* Engine Status & Reindex */}
        <div className="flex flex-wrap items-center gap-2">
          {ragStatus && (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-navy-800/80 border border-white/[0.06] text-xs">
              <Cpu className="w-3.5 h-3.5 text-cyan-400" />
              <span className="text-gray-400">RAG Engine:</span>
              <span className="font-mono text-white font-semibold capitalize">
                {ragStatus.provider}
              </span>
              <span className="text-gray-600">•</span>
              <span className="text-gray-400">Indexed Docs:</span>
              <span className="font-mono text-cyan-400 font-semibold">
                {ragStatus.total_documents}
              </span>
            </div>
          )}

          <button
            onClick={handleReindex}
            disabled={reindexing}
            className="btn-ghost text-xs flex items-center gap-1.5 py-1.5"
            title="Re-read all historical signals from database into vector store"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${reindexing ? 'animate-spin' : ''}`} />
            <span>{reindexing ? 'Indexing...' : 'Re-index Signals'}</span>
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-3 border-b border-white/[0.08] shrink-0">
        <button
          onClick={() => setActiveTab('chat')}
          className={`pb-3 text-xs font-semibold flex items-center gap-2 transition-all border-b-2 -mb-px ${
            activeTab === 'chat'
              ? 'text-blue-400 border-blue-500'
              : 'text-gray-400 border-transparent hover:text-white'
          }`}
        >
          <Bot className="w-4 h-4" />
          <span>Interactive AI Terminal</span>
        </button>

        <button
          onClick={() => setActiveTab('knowledge')}
          className={`pb-3 text-xs font-semibold flex items-center gap-2 transition-all border-b-2 -mb-px ${
            activeTab === 'knowledge'
              ? 'text-blue-400 border-blue-500'
              : 'text-gray-400 border-transparent hover:text-white'
          }`}
        >
          <BookOpen className="w-4 h-4" />
          <span>Grounded Knowledge Base ({ragStatus?.total_documents || 0})</span>
        </button>
      </div>

      {/* Tab 1: Interactive Chat */}
      {activeTab === 'chat' && (
        <div className="flex-1 flex flex-col bg-navy-950/40 rounded-2xl border border-white/[0.06] overflow-hidden min-h-0">
          {/* Quick Prompt Chips */}
          <div className="p-3 bg-navy-900/60 border-b border-white/[0.04] overflow-x-auto flex items-center gap-2 shrink-0">
            <span className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider whitespace-nowrap pl-1">
              Suggestions:
            </span>
            {promptChips.map((chip, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(chip)}
                className="whitespace-nowrap px-3 py-1 rounded-full text-[11px] bg-navy-800/80 hover:bg-blue-600/20 text-gray-300 hover:text-blue-300 border border-white/[0.04] hover:border-blue-500/30 transition-all cursor-pointer"
              >
                {chip}
              </button>
            ))}
          </div>

          {/* Messages Scroll Area */}
          <div className="flex-1 overflow-y-auto p-4 lg:p-6 space-y-5">
            {messages.map((msg) => {
              const isUser = msg.role === 'user'
              const isExpanded = expandedSources[msg.id]

              return (
                <div
                  key={msg.id}
                  className={`flex gap-3.5 ${isUser ? 'justify-end' : 'justify-start'}`}
                >
                  {!isUser && (
                    <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 text-white flex items-center justify-center shrink-0 shadow-md shadow-blue-500/10">
                      <Bot className="w-4 h-4" />
                    </div>
                  )}

                  <div className={`max-w-3xl space-y-2 ${isUser ? 'items-end' : 'items-start'}`}>
                    {/* Speech Bubble */}
                    <div
                      className={`p-4 rounded-2xl text-xs leading-relaxed ${
                        isUser
                          ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/10 rounded-tr-sm'
                          : 'bg-navy-800/90 border border-white/[0.08] text-gray-200 rounded-tl-sm shadow-sm'
                      }`}
                    >
                      <div className="whitespace-pre-wrap font-sans space-y-2">
                        {msg.content}
                      </div>

                      <div
                        className={`text-[10px] mt-2 font-mono flex items-center justify-between gap-3 ${
                          isUser ? 'text-blue-200' : 'text-gray-500'
                        }`}
                      >
                        <span>{msg.timestamp}</span>
                        {msg.provider_used && (
                          <span className="capitalize text-gray-400">
                            Engine: {msg.provider_used}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Collapsible Retrieved Grounding Sources */}
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="mt-2 w-full rounded-xl bg-navy-900/80 border border-white/[0.06] overflow-hidden text-xs">
                        <button
                          onClick={() => toggleSources(msg.id)}
                          className="w-full px-3 py-2 flex items-center justify-between text-gray-400 hover:text-white transition-colors"
                        >
                          <span className="flex items-center gap-2 font-semibold text-[11px]">
                            <Database className="w-3.5 h-3.5 text-cyan-400" />
                            Retrieved Context Sources ({msg.sources.length})
                            {msg.metrics && (
                              <span className="text-[10px] font-mono text-gray-500">
                                • {msg.metrics.retrieval_time_ms}ms vector search
                              </span>
                            )}
                          </span>
                          {isExpanded ? (
                            <ChevronUp className="w-3.5 h-3.5" />
                          ) : (
                            <ChevronDown className="w-3.5 h-3.5" />
                          )}
                        </button>

                        {isExpanded && (
                          <div className="p-3 pt-0 space-y-2 border-t border-white/[0.04]">
                            {msg.sources.map((src, i) => (
                              <div
                                key={i}
                                className="p-2.5 rounded-lg bg-navy-950/60 border border-white/[0.04] space-y-1"
                              >
                                <div className="flex items-center justify-between">
                                  <div className="flex items-center gap-2">
                                    <span className="font-semibold text-white text-[11px]">
                                      {src.title}
                                    </span>
                                    <span className="px-1.5 py-0.5 rounded text-[9px] uppercase font-mono bg-blue-500/10 text-blue-400 border border-blue-500/20">
                                      {src.doc_type}
                                    </span>
                                  </div>
                                  <span className="text-cyan-400 font-mono text-[10px]">
                                    Match: {(src.score * 100).toFixed(0)}%
                                  </span>
                                </div>
                                <p className="text-gray-400 text-[11px] font-mono line-clamp-2">
                                  {src.snippet}
                                </p>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {isUser && (
                    <div className="w-8 h-8 rounded-xl bg-blue-600/30 text-blue-400 border border-blue-500/30 flex items-center justify-center shrink-0">
                      <User className="w-4 h-4" />
                    </div>
                  )}
                </div>
              )
            })}

            {loading && (
              <div className="flex gap-3 items-center text-xs text-gray-400">
                <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 text-white flex items-center justify-center shrink-0 animate-pulse">
                  <Bot className="w-4 h-4" />
                </div>
                <div className="p-3 rounded-2xl bg-navy-800/80 border border-white/[0.08] flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-cyan-400 animate-bounce" />
                  <div className="w-2 h-2 rounded-full bg-blue-400 animate-bounce [animation-delay:0.2s]" />
                  <div className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce [animation-delay:0.4s]" />
                  <span className="text-[11px] font-mono text-gray-400 ml-1">
                    Querying vector store & synthesizing response...
                  </span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Bar */}
          <div className="p-4 bg-navy-900/90 border-t border-white/[0.06] shrink-0 space-y-2">
            <form
              onSubmit={(e) => {
                e.preventDefault()
                handleSend()
              }}
              className="flex items-center gap-2"
            >
              <div className="relative flex-1">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Ask AI Copilot (e.g. 'How did past ETH breakout trades perform?' or 'What are the 4H RSI divergence rules?')..."
                  className="input w-full text-xs py-2.5 pl-3.5 pr-20"
                  disabled={loading}
                />

                {/* Symbol filter toggle */}
                <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                  <select
                    value={symbolFilter}
                    onChange={(e) => setSymbolFilter(e.target.value)}
                    className="bg-navy-800 text-[10px] text-gray-300 rounded border border-white/[0.06] px-1.5 py-0.5 font-mono cursor-pointer outline-none"
                  >
                    <option value="">All Pairs</option>
                    <option value="BTC/USDT">BTC</option>
                    <option value="ETH/USDT">ETH</option>
                    <option value="SOL/USDT">SOL</option>
                    <option value="BNB/USDT">BNB</option>
                  </select>
                </div>
              </div>

              <button
                type="submit"
                disabled={!query.trim() || loading}
                className="btn-primary text-xs py-2.5 px-4 flex items-center gap-1.5 shrink-0"
              >
                <span>Ask</span>
                <Send className="w-3.5 h-3.5" />
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Tab 2: Knowledge Base Browser */}
      {activeTab === 'knowledge' && (
        <div className="space-y-4 flex-1 overflow-y-auto">
          {/* Controls */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-surface p-3 rounded-xl border border-white/[0.06]">
            <div className="flex items-center gap-2 overflow-x-auto">
              <span className="text-xs text-gray-500 font-semibold uppercase tracking-wider pl-1">
                Filter:
              </span>
              {(['', 'strategy', 'risk_rule', 'signal'] as const).map((cat) => (
                <button
                  key={cat}
                  onClick={() => setKbFilter(cat)}
                  className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                    kbFilter === cat
                      ? 'bg-blue-600 text-white font-semibold'
                      : 'bg-navy-800/80 text-gray-400 hover:text-white border border-white/[0.04]'
                  }`}
                >
                  {cat === '' ? 'All Documents' : cat.replace('_', ' ').toUpperCase()}
                </button>
              ))}
            </div>

            <button
              onClick={() => setNewDocModal(true)}
              className="btn-primary text-xs flex items-center gap-2"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Custom Playbook</span>
            </button>
          </div>

          {/* Document Cards Grid */}
          {kbLoading ? (
            <div className="py-16 text-center text-xs text-gray-500">
              Loading knowledge documents...
            </div>
          ) : knowledgeDocs.length === 0 ? (
            <div className="p-12 text-center text-gray-500 text-xs">
              No knowledge documents found for this filter.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {knowledgeDocs.map((doc) => (
                <div
                  key={doc.id}
                  className="rounded-xl bg-navy-800/40 border border-white/[0.06] p-5 space-y-3 hover:border-white/10 transition-all flex flex-col justify-between"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-bold text-sm text-white">{doc.title}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-blue-500/10 text-blue-400 border border-blue-500/20">
                        {doc.doc_type}
                      </span>
                    </div>

                    <pre className="text-xs text-gray-300 font-mono whitespace-pre-wrap line-clamp-6 bg-navy-950/60 p-3 rounded-lg border border-white/[0.04]">
                      {doc.text.trim()}
                    </pre>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-gray-500 pt-2 border-t border-white/[0.04]">
                    <span>ID: {doc.id}</span>
                    <button
                      onClick={() => {
                        setActiveTab('chat')
                        setQuery(`Explain ${doc.title} and how it applies to our crypto trading signals`)
                      }}
                      className="text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-medium"
                    >
                      <span>Query this doc</span>
                      <ExternalLink className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Add Custom Document Modal */}
      {newDocModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="bg-navy-900 border border-white/10 rounded-2xl w-full max-w-xl p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-cyan-400" />
              Add Custom Strategy Playbook to RAG Index
            </h3>

            <form onSubmit={handleAddCustomDoc} className="space-y-3">
              <div>
                <label className="text-xs text-gray-400 block mb-1">Playbook Title</label>
                <input
                  type="text"
                  required
                  value={newDocTitle}
                  onChange={(e) => setNewDocTitle(e.target.value)}
                  placeholder="e.g. Fair Value Gap (FVG) Retest Strategy"
                  className="input w-full text-xs"
                />
              </div>

              <div>
                <label className="text-xs text-gray-400 block mb-1">Category</label>
                <select
                  value={newDocType}
                  onChange={(e) => setNewDocType(e.target.value)}
                  className="input w-full text-xs cursor-pointer"
                >
                  <option value="strategy">Strategy Playbook</option>
                  <option value="risk_rule">Risk Management Rule</option>
                  <option value="channel">Channel Validation Guideline</option>
                </select>
              </div>

              <div>
                <label className="text-xs text-gray-400 block mb-1">
                  Playbook Text / Execution Rules
                </label>
                <textarea
                  required
                  rows={6}
                  value={newDocText}
                  onChange={(e) => setNewDocText(e.target.value)}
                  placeholder="Describe entry triggers, invalidation conditions, stop-loss requirements, and profit targets..."
                  className="input w-full text-xs font-mono"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3">
                <button
                  type="button"
                  onClick={() => setNewDocModal(false)}
                  className="btn-ghost text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={addingDoc}
                  className="btn-primary text-xs px-4"
                >
                  {addingDoc ? 'Indexing...' : 'Index Playbook'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
