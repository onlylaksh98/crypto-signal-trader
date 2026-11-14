import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  X,
  Sparkles,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  History,
  BookOpen,
  ArrowRight,
  TrendingUp,
  Percent,
  CheckCircle2,
  ExternalLink,
} from 'lucide-react'
import { api } from '../../services/api'
import { Badge } from '../common/Badge'
import { formatCryptoPrice, formatUSD } from '../../utils/formatters'
import type { Signal, SignalEvaluationResponse } from '../../types'

interface SignalRagModalProps {
  isOpen: boolean
  onClose: () => void
  signal: Signal | null
  rawParams?: {
    symbol: string
    direction: string
    entry_price?: number
    stop_loss?: number
    take_profit_1?: number
    notes?: string
  }
}

export const SignalRagModal: React.FC<SignalRagModalProps> = ({
  isOpen,
  onClose,
  signal,
  rawParams,
}) => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [evaluation, setEvaluation] = useState<SignalEvaluationResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const symbol = signal?.symbol || rawParams?.symbol || ''
  const direction = signal?.direction || rawParams?.direction || ''

  useEffect(() => {
    if (!isOpen) {
      setEvaluation(null)
      setError(null)
      return
    }

    const fetchEval = async () => {
      setLoading(true)
      setError(null)
      try {
        const res = await api.evaluateSignal({
          signal_id: signal?.id,
          symbol,
          direction,
          entry_price: signal?.entry_price ?? rawParams?.entry_price,
          stop_loss: signal?.stop_loss ?? rawParams?.stop_loss,
          take_profit_1: signal?.take_profit_1 ?? rawParams?.take_profit_1,
          notes: signal?.notes || signal?.raw_text || rawParams?.notes,
        })
        setEvaluation(res)
      } catch (err: any) {
        setError(err.message || 'Failed to retrieve RAG evaluation.')
      } finally {
        setLoading(false)
      }
    }

    fetchEval()
  }, [isOpen, signal?.id, symbol, direction])

  if (!isOpen) return null

  const getVerdictBadge = (action: string) => {
    if (action === 'EXECUTE') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 shadow-lg shadow-emerald-500/10">
          <ShieldCheck className="w-4 h-4" />
          EXECUTE RECOMMENDED
        </span>
      )
    }
    if (action === 'REJECT') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30 shadow-lg shadow-rose-500/10">
          <ShieldAlert className="w-4 h-4" />
          REJECT / HIGH RISK
        </span>
      )
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30 shadow-lg shadow-amber-500/10">
        <AlertTriangle className="w-4 h-4" />
        CAUTION / REDUCE SIZE
      </span>
    )
  }

  const handleAskCopilot = () => {
    onClose()
    const query = encodeURIComponent(`Evaluate ${symbol} ${direction} signal against our historical win rate and strategy playbooks`)
    navigate(`/copilot?q=${query}`)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <div className="bg-navy-900 border border-white/10 rounded-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto shadow-2xl flex flex-col">
        {/* Header */}
        <div className="p-5 border-b border-white/[0.08] flex items-center justify-between sticky top-0 bg-navy-900/95 backdrop-blur z-10">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 text-white shadow-lg shadow-blue-500/20">
              <Sparkles className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-white tracking-tight">
                  AI RAG Signal Evaluation
                </h2>
                <span className="text-[10px] font-mono uppercase bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2 py-0.5 rounded-full">
                  Vector Grounded
                </span>
              </div>
              <p className="text-xs text-gray-400">
                Grounding signal against historical similar setups & strategy playbooks
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-white/[0.05] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-6 flex-1">
          {/* Signal Parameter Summary Card */}
          <div className="rounded-xl bg-navy-800/60 border border-white/[0.06] p-4 flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <span className="font-mono text-lg font-bold text-white">{symbol}</span>
              <Badge variant={direction === 'BUY' ? 'buy' : 'sell'}>{direction}</Badge>
            </div>

            <div className="flex items-center gap-4 text-xs font-mono">
              <div>
                <span className="text-gray-500 block text-[10px] uppercase">Entry</span>
                <span className="text-white font-semibold">
                  {signal?.entry_price ? formatCryptoPrice(signal.entry_price) : 'Market'}
                </span>
              </div>
              <div>
                <span className="text-gray-500 block text-[10px] uppercase">Stop Loss</span>
                <span className="text-rose-400 font-semibold">
                  {signal?.stop_loss ? formatCryptoPrice(signal.stop_loss) : 'None'}
                </span>
              </div>
              <div>
                <span className="text-gray-500 block text-[10px] uppercase">Target 1</span>
                <span className="text-emerald-400 font-semibold">
                  {signal?.take_profit_1 ? formatCryptoPrice(signal.take_profit_1) : 'None'}
                </span>
              </div>
              {signal?.risk_reward_ratio && (
                <div>
                  <span className="text-gray-500 block text-[10px] uppercase">R:R</span>
                  <span className="text-cyan-400 font-semibold">
                    1:{Number(signal.risk_reward_ratio).toFixed(2)}
                  </span>
                </div>
              )}
            </div>
          </div>

          {loading ? (
            <div className="py-16 text-center space-y-4">
              <div className="inline-block w-8 h-8 border-3 border-blue-500 border-t-transparent rounded-full animate-spin" />
              <p className="text-xs text-gray-400 font-mono">
                Running hybrid vector retrieval over historical setups & strategy documents...
              </p>
            </div>
          ) : error ? (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs">
              {error}
            </div>
          ) : evaluation ? (
            <>
              {/* Verdict & Metrics Bar */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {/* Verdict Card */}
                <div className="rounded-xl bg-navy-800/40 border border-white/[0.06] p-4 flex flex-col justify-between space-y-2">
                  <span className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">
                    Recommendation
                  </span>
                  <div>{getVerdictBadge(evaluation.recommended_action)}</div>
                  <span className="text-[11px] text-gray-400">
                    Confidence: {(evaluation.confidence_score * 100).toFixed(0)}%
                  </span>
                </div>

                {/* Risk Score */}
                <div className="rounded-xl bg-navy-800/40 border border-white/[0.06] p-4 space-y-2">
                  <div className="flex justify-between items-center text-[10px] font-semibold text-gray-400 uppercase tracking-wider">
                    <span>Engine Risk Score</span>
                    <span className="font-mono text-white text-xs">{evaluation.risk_score} / 100</span>
                  </div>
                  <div className="w-full bg-navy-950 rounded-full h-2 overflow-hidden border border-white/[0.04]">
                    <div
                      className={`h-full transition-all duration-500 rounded-full ${
                        evaluation.risk_score < 40
                          ? 'bg-emerald-500'
                          : evaluation.risk_score < 70
                          ? 'bg-amber-500'
                          : 'bg-rose-500'
                      }`}
                      style={{ width: `${Math.min(100, evaluation.risk_score)}%` }}
                    />
                  </div>
                  <span className="text-[10px] text-gray-400 block">
                    {evaluation.risk_score < 40
                      ? 'Favorable risk-reward balance'
                      : evaluation.risk_score < 70
                      ? 'Moderate risk, monitor closely'
                      : 'Elevated risk parameters'}
                  </span>
                </div>

                {/* Historical Similar Setup Win Rate */}
                <div className="rounded-xl bg-navy-800/40 border border-white/[0.06] p-4 space-y-1">
                  <span className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">
                    Similar Historical Win Rate
                  </span>
                  <div className="text-xl font-bold font-mono text-white flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-emerald-400" />
                    <span>{evaluation.historical_win_rate_similar.toFixed(1)}%</span>
                  </div>
                  <span className="text-[11px] text-gray-400">
                    Across {evaluation.sample_size_similar} similar {symbol} setups in database
                  </span>
                </div>
              </div>

              {/* Actionable Advice & Review */}
              {evaluation.actionable_advice.length > 0 && (
                <div className="rounded-xl bg-navy-800/50 border border-blue-500/20 p-4 space-y-2">
                  <span className="text-xs font-semibold text-blue-400 flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4" />
                    Key RAG Tactical Takeaways
                  </span>
                  <ul className="space-y-1.5 text-xs text-gray-300">
                    {evaluation.actionable_advice.map((adv, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-blue-400 select-none">•</span>
                        <span>{adv}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Similar Historical Trades Table */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400 flex items-center gap-2">
                    <History className="w-4 h-4 text-cyan-400" />
                    Retrieved Similar Historical Signals
                  </h3>
                  <span className="text-[11px] text-gray-500">
                    Ranked by dense semantic + keyword similarity
                  </span>
                </div>

                {evaluation.similar_trades.length === 0 ? (
                  <div className="p-4 text-center text-xs text-gray-500 bg-navy-800/30 rounded-xl border border-white/[0.04]">
                    No previous signals matching this asset were found in the vector index.
                  </div>
                ) : (
                  <div className="overflow-x-auto rounded-xl border border-white/[0.06] bg-navy-950/40">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-navy-900 text-gray-400 text-[10px] uppercase font-semibold border-b border-white/[0.06]">
                        <tr>
                          <th className="py-2.5 px-3">Signal</th>
                          <th className="py-2.5 px-3">Entry</th>
                          <th className="py-2.5 px-3">SL</th>
                          <th className="py-2.5 px-3">Outcome</th>
                          <th className="py-2.5 px-3">Realized P&L</th>
                          <th className="py-2.5 px-3 text-right">Similarity</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-white/[0.04] font-mono">
                        {evaluation.similar_trades.map((trade, idx) => (
                          <tr key={idx} className="hover:bg-white/[0.02]">
                            <td className="py-2.5 px-3 font-semibold text-white">
                              {trade.symbol} {trade.direction}
                            </td>
                            <td className="py-2.5 px-3 text-gray-300">
                              {trade.entry_price ? formatCryptoPrice(trade.entry_price) : 'Market'}
                            </td>
                            <td className="py-2.5 px-3 text-rose-400">
                              {trade.stop_loss ? formatCryptoPrice(trade.stop_loss) : '—'}
                            </td>
                            <td className="py-2.5 px-3">
                              <span
                                className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                  trade.outcome === 'WIN'
                                    ? 'bg-emerald-500/20 text-emerald-400'
                                    : trade.outcome === 'LOSS'
                                    ? 'bg-rose-500/20 text-rose-400'
                                    : 'bg-gray-500/20 text-gray-400'
                                }`}
                              >
                                {trade.outcome}
                              </span>
                            </td>
                            <td className="py-2.5 px-3 font-semibold">
                              {trade.realized_pnl !== null ? (
                                <span
                                  className={
                                    trade.realized_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'
                                  }
                                >
                                  {trade.realized_pnl >= 0 ? '+' : ''}
                                  {formatUSD(trade.realized_pnl)}
                                </span>
                              ) : (
                                <span className="text-gray-500">—</span>
                              )}
                            </td>
                            <td className="py-2.5 px-3 text-right text-cyan-400">
                              {(trade.similarity_score * 100).toFixed(0)}%
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Grounded Strategy Rules */}
              {evaluation.matched_strategies.length > 0 && (
                <div className="space-y-1.5">
                  <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
                    <BookOpen className="w-3.5 h-3.5 text-blue-400" />
                    Matched Trading Knowledge Base Playbooks:
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {evaluation.matched_strategies.map((st, i) => (
                      <span
                        key={i}
                        className="text-xs px-2.5 py-1 rounded-lg bg-navy-800 border border-white/[0.06] text-gray-300"
                      >
                        {st}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : null}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-white/[0.08] bg-navy-950/60 flex items-center justify-between">
          <button
            onClick={handleAskCopilot}
            className="btn-ghost text-xs flex items-center gap-2 text-cyan-400 hover:text-cyan-300"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Ask AI Copilot for Full Breakdown</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>

          <button onClick={onClose} className="btn-primary text-xs px-5">
            Done
          </button>
        </div>
      </div>
    </div>
  )
}
