import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../services/api'
import { Badge } from '../components/common/Badge'
import { formatDate, formatCryptoPrice } from '../utils/formatters'
import { Search, Filter, Plus, ChevronDown, ChevronUp, AlertCircle, FileText, Sparkles } from 'lucide-react'
import { SignalRagModal } from '../components/rag/SignalRagModal'
import type { Signal } from '../types'

interface SignalsPageProps {
  onOpenSignalModal: () => void
}

export const SignalsPage: React.FC<SignalsPageProps> = ({ onOpenSignalModal }) => {
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState('')
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [selectedRagSignal, setSelectedRagSignal] = useState<Signal | null>(null)

  const { data: signals = [], isLoading, error } = useQuery({
    queryKey: ['signals', statusFilter],
    queryFn: () => api.getSignals(statusFilter || undefined, 100),
    refetchInterval: 5000,
  })

  const filteredSignals = signals.filter((sig) => {
    if (!searchQuery) return true
    return (
      sig.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
      sig.direction.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (sig.notes && sig.notes.toLowerCase().includes(searchQuery.toLowerCase()))
    )
  })

  const toggleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id)
  }

  return (
    <div className="p-4 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl lg:text-2xl font-bold tracking-tight text-white flex items-center gap-3">
            Telegram Signal Stream
            <span className="text-xs font-mono text-gray-400 bg-navy-800 px-2.5 py-1 rounded-md border border-white/[0.04]">
              {filteredSignals.length} Recorded
            </span>
          </h1>
          <p className="text-xs text-gray-400 mt-1">
            Raw parsed Telegram channel instructions, validation results, and execution state.
          </p>
        </div>

        <button onClick={onOpenSignalModal} className="btn-primary text-xs flex items-center gap-2">
          <Plus className="w-4 h-4" />
          <span>Simulate New Signal</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-surface p-3 rounded-xl border border-white/[0.06]">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-gray-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by symbol, direction, or note..."
            className="input pl-9 text-xs py-1.5"
          />
        </div>

        <div className="flex items-center gap-2 overflow-x-auto">
          <Filter className="w-4 h-4 text-gray-500 shrink-0" />
          {(['', 'EXECUTED', 'VALIDATED', 'PENDING', 'REJECTED'] as const).map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                statusFilter === st
                  ? 'bg-blue-600 text-white font-semibold shadow-sm'
                  : 'bg-navy-800/80 text-gray-400 hover:text-white border border-white/[0.04]'
              }`}
            >
              {st || 'All Statuses'}
            </button>
          ))}
        </div>
      </div>

      {/* Signals Table */}
      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-gray-500 text-xs">Loading signal logs...</div>
        ) : filteredSignals.length === 0 ? (
          <div className="p-12 text-center text-gray-500 text-xs space-y-3">
            <p>No signals matched your filter criteria.</p>
            <button onClick={onOpenSignalModal} className="btn-ghost text-xs">
              Simulate a signal now
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Symbol</th>
                  <th>Direction</th>
                  <th>Entry Price</th>
                  <th>Stop Loss</th>
                  <th>TP Targets</th>
                  <th>R:R</th>
                  <th>Confidence</th>
                  <th>Status</th>
                  <th className="text-right">Details</th>
                </tr>
              </thead>
              <tbody>
                {filteredSignals.map((sig) => {
                  const isExpanded = expandedId === sig.id
                  return (
                    <React.Fragment key={sig.id}>
                      <tr
                        onClick={() => toggleExpand(sig.id)}
                        className="cursor-pointer hover:bg-white/[0.02] transition-colors"
                      >
                        <td className="text-xs text-gray-400 whitespace-nowrap">
                          {formatDate(sig.created_at)}
                        </td>
                        <td className="font-mono font-bold text-white">{sig.symbol}</td>
                        <td>
                          <Badge variant={sig.direction === 'BUY' ? 'buy' : 'sell'}>
                            {sig.direction}
                          </Badge>
                        </td>
                        <td className="font-mono">
                          {sig.entry_price ? formatCryptoPrice(sig.entry_price) : 'Market'}
                        </td>
                        <td className="font-mono text-rose-400">
                          {sig.stop_loss ? formatCryptoPrice(sig.stop_loss) : '—'}
                        </td>
                        <td className="font-mono text-xs">
                          <span className="text-emerald-400">
                            {sig.take_profit_1 ? formatCryptoPrice(sig.take_profit_1) : '—'}
                          </span>
                          {sig.take_profit_2 && (
                            <span className="text-gray-500"> / {formatCryptoPrice(sig.take_profit_2)}</span>
                          )}
                          {sig.take_profit_3 && (
                            <span className="text-gray-500"> / {formatCryptoPrice(sig.take_profit_3)}</span>
                          )}
                        </td>
                        <td className="font-mono">
                          {sig.risk_reward_ratio ? `1:${Number(sig.risk_reward_ratio).toFixed(2)}` : '—'}
                        </td>
                        <td className="font-mono">
                          {sig.confidence_score
                            ? `${(Number(sig.confidence_score) * 100).toFixed(0)}%`
                            : '—'}
                        </td>
                        <td>
                          <Badge
                            variant={
                              sig.status === 'EXECUTED'
                                ? 'executed'
                                : sig.status === 'VALIDATED'
                                ? 'connected'
                                : sig.status === 'REJECTED'
                                ? 'rejected'
                                : 'pending'
                            }
                          >
                            {sig.status}
                          </Badge>
                        </td>
                        <td className="text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation()
                                setSelectedRagSignal(sig)
                              }}
                              className="px-2 py-1 rounded-lg bg-blue-500/10 hover:bg-blue-500/20 text-cyan-400 border border-blue-500/20 flex items-center gap-1 text-[11px] font-semibold transition-all hover:scale-105"
                              title="AI RAG Evaluation & Historical Trade Match"
                            >
                              <Sparkles className="w-3 h-3 text-cyan-400" />
                              <span>AI Review</span>
                            </button>
                            <button
                              type="button"
                              className="p-1 rounded hover:bg-white/[0.05] text-gray-400"
                            >
                              {isExpanded ? (
                                <ChevronUp className="w-4 h-4" />
                              ) : (
                                <ChevronDown className="w-4 h-4" />
                              )}
                            </button>
                          </div>
                        </td>
                      </tr>

                      {/* Expanded View for Telegram raw message & validation notes */}
                      {isExpanded && (
                        <tr className="bg-navy-950/60 border-b border-white/[0.06]">
                          <td colSpan={10} className="p-4 space-y-3">
                            <div className="flex items-center justify-between pb-2 border-b border-white/[0.04]">
                              <span className="text-xs font-semibold text-gray-400">
                                Detailed Inspection
                              </span>
                              <button
                                onClick={() => setSelectedRagSignal(sig)}
                                className="px-3 py-1 rounded-lg bg-gradient-to-r from-blue-600/30 to-cyan-500/30 text-cyan-300 border border-cyan-500/30 text-xs font-semibold flex items-center gap-1.5 hover:bg-blue-600/40 transition-all"
                              >
                                <Sparkles className="w-3.5 h-3.5" />
                                <span>Open Full RAG Setup Analysis</span>
                              </button>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                              <div className="space-y-1">
                                <span className="font-semibold text-gray-400 flex items-center gap-1.5">
                                  <FileText className="w-3.5 h-3.5 text-blue-400" />
                                  Original Telegram / Input Text:
                                </span>
                                <pre className="p-3 bg-navy-900 rounded-lg border border-white/[0.04] font-mono text-[11px] text-gray-300 whitespace-pre-wrap">
                                  {sig.raw_text || sig.notes || 'Manual order input.'}
                                </pre>
                              </div>

                              <div className="space-y-1">
                                <span className="font-semibold text-gray-400 flex items-center gap-1.5">
                                  <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
                                  Engine Validation & Execution Details:
                                </span>
                                <div className="p-3 bg-navy-900 rounded-lg border border-white/[0.04] space-y-1.5 text-[11px]">
                                  <div className="flex justify-between">
                                    <span className="text-gray-500">Signal ID:</span>
                                    <span className="font-mono text-gray-300">{sig.id}</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-gray-500">Exchange Route:</span>
                                    <span className="font-mono text-gray-300">{sig.exchange || 'BINANCE_PAPER'}</span>
                                  </div>
                                  {sig.validation_errors && (
                                    <div className="mt-2 text-rose-400 bg-rose-500/10 p-2 rounded border border-rose-500/20 font-mono">
                                      {sig.validation_errors}
                                    </div>
                                  )}
                                  {!sig.validation_errors && (
                                    <div className="text-emerald-400 flex items-center gap-1 font-mono">
                                      ✓ Passed risk boundaries & minimum 1.0 R:R check
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* RAG Signal Evaluation Modal */}
      <SignalRagModal
        isOpen={!!selectedRagSignal}
        onClose={() => setSelectedRagSignal(null)}
        signal={selectedRagSignal}
      />
    </div>
  )
}
