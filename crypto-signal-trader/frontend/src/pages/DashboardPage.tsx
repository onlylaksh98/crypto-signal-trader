import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../services/api'
import { StatCard } from '../components/common/StatCard'
import { Badge } from '../components/common/Badge'
import { EquityChart } from '../components/dashboard/EquityChart'
import {
  Wallet,
  DollarSign,
  TrendingUp,
  Award,
  Layers,
  ArrowUpRight,
  ArrowDownRight,
  Clock,
  ExternalLink,
  ShieldCheck,
  AlertTriangle,
  Sparkles,
} from 'lucide-react'
import { formatUSD, formatPercent, formatDate, formatCryptoPrice, formatQuantity } from '../utils/formatters'
import { Link } from 'react-router-dom'
import { SignalRagModal } from '../components/rag/SignalRagModal'
import { StockMarketHoursWidget } from '../components/dashboard/StockMarketHoursWidget'
import type { Position, Signal } from '../types'

interface DashboardPageProps {
  onOpenSignalModal: () => void
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ onOpenSignalModal }) => {
  const queryClient = useQueryClient()
  const [closingId, setClosingId] = useState<string | null>(null)
  const [selectedRagSignal, setSelectedRagSignal] = useState<Signal | null>(null)

  const { data: dashboard, isLoading, error } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => api.getDashboard(),
    refetchInterval: 10000,
  })

  const { data: openPositions = [] } = useQuery({
    queryKey: ['positions', 'OPEN'],
    queryFn: () => api.getPositions('OPEN'),
    refetchInterval: 5000,
  })

  const closePositionMutation = useMutation({
    mutationFn: (id: string) => api.closePosition(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['positions'] })
      queryClient.invalidateQueries({ queryKey: ['orders'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
      setClosingId(null)
    },
    onError: (err: any) => {
      alert(`Failed to close position: ${err.message}`)
      setClosingId(null)
    },
  })

  const handleClosePosition = (pos: Position) => {
    if (confirm(`Close paper position for ${pos.symbol} at current market price?`)) {
      setClosingId(pos.id)
      closePositionMutation.mutate(pos.id)
    }
  }

  const portfolio = dashboard?.portfolio
  const initialBalance = Number(portfolio?.initial_balance ?? 10000)
  const totalEquity = Number(portfolio?.total_equity ?? 10000)
  const cashBalance = Number(portfolio?.cash_balance ?? 10000)
  const unrealizedPnl = Number(portfolio?.unrealized_pnl ?? 0)
  const realizedPnl = Number(portfolio?.realized_pnl ?? 0)
  const totalReturnPct = initialBalance > 0 ? ((totalEquity - initialBalance) / initialBalance) * 100 : 0
  const winRate = Number(portfolio?.win_rate ?? 0)

  return (
    <div className="p-4 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Page Title & Status */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl lg:text-2xl font-bold tracking-tight text-white flex items-center gap-3">
            Trading Terminal Overview
            <Badge variant="paper">SIMULATED EXECUTION</Badge>
          </h1>
          <p className="text-xs text-gray-400 mt-1">
            Real-time simulated cryptocurrency portfolio driven by Telegram signals.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onOpenSignalModal}
            className="btn-primary text-xs"
          >
            + Test Signal Simulation
          </button>
        </div>
      </div>

      {/* KPI Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 lg:gap-4">
        <StatCard
          title="Total Equity"
          value={formatUSD(totalEquity)}
          delta={formatPercent(totalReturnPct)}
          deltaType={totalReturnPct >= 0 ? 'positive' : 'negative'}
          subtitle="Net return"
          icon={<Wallet className="w-4 h-4" />}
          loading={isLoading}
        />
        <StatCard
          title="Cash Balance"
          value={formatUSD(cashBalance)}
          subtitle="Available margin"
          icon={<DollarSign className="w-4 h-4" />}
          loading={isLoading}
        />
        <StatCard
          title="Unrealized P&L"
          value={formatUSD(unrealizedPnl)}
          delta={unrealizedPnl !== 0 ? formatUSD(unrealizedPnl) : undefined}
          deltaType={unrealizedPnl >= 0 ? 'positive' : 'negative'}
          subtitle="Live mark-to-market"
          icon={<TrendingUp className="w-4 h-4" />}
          loading={isLoading}
        />
        <StatCard
          title="Realized P&L"
          value={formatUSD(realizedPnl)}
          deltaType={realizedPnl >= 0 ? 'positive' : 'negative'}
          subtitle="Closed trades"
          icon={<Award className="w-4 h-4" />}
          loading={isLoading}
        />
        <StatCard
          title="Win Rate"
          value={`${winRate.toFixed(1)}%`}
          subtitle={`${portfolio?.winning_trades ?? 0}W / ${portfolio?.losing_trades ?? 0}L`}
          icon={<ShieldCheck className="w-4 h-4" />}
          loading={isLoading}
        />
        <StatCard
          title="Open Positions"
          value={dashboard?.open_positions_count ?? openPositions.length}
          subtitle="Active paper trades"
          icon={<Layers className="w-4 h-4" />}
          loading={isLoading}
        />
      </div>

      {/* Real-Time Stock Market Dates, Opening & Closing Schedules */}
      <StockMarketHoursWidget />

      {/* Chart & Risk System Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <EquityChart
            data={dashboard?.equity_curve || []}
            initialBalance={initialBalance}
            currentEquity={totalEquity}
          />
        </div>

        {/* Risk & Model Panel */}
        <div className="card p-5 space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
              <span className="text-xs font-bold uppercase tracking-wider text-gray-300 flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                Risk Management Engine
              </span>
              <span className="badge badge-paper">ACTIVE</span>
            </div>

            <div className="mt-4 space-y-3 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Position Sizing</span>
                <span className="font-mono text-white font-semibold">Fixed Risk 2.0%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Daily Drawdown Cap</span>
                <span className="font-mono text-amber-400 font-semibold">5.0% ($500.00)</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Max Open Positions</span>
                <span className="font-mono text-white font-semibold">5 Concurrent</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Execution Slippage</span>
                <span className="font-mono text-gray-300">Gaussian 5 bps</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Maker/Taker Fee</span>
                <span className="font-mono text-gray-300">0.05% per fill</span>
              </div>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-navy-800/60 border border-white/[0.04] text-[11px] text-gray-400 space-y-1">
            <div className="flex items-center gap-1.5 text-amber-400 font-semibold">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>Simulated Safety Protocol</span>
            </div>
            <p>
              Incoming signals are parsed with strict boundary validation. Orders with R:R &lt; 1.0 or missing stop-losses are rejected automatically.
            </p>
          </div>
        </div>
      </div>

      {/* Active Positions Table */}
      <div className="card p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-300">
              Open Positions ({openPositions.length})
            </h3>
            <span className="text-xs text-gray-500 font-mono">Live virtual contracts</span>
          </div>
          <Link
            to="/positions"
            className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"
          >
            <span>View All</span>
            <ExternalLink className="w-3 h-3" />
          </Link>
        </div>

        {openPositions.length === 0 ? (
          <div className="py-8 text-center text-gray-500 text-xs">
            No open paper positions currently. Incoming Telegram signals will appear here automatically.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Side</th>
                  <th>Quantity</th>
                  <th>Entry Price</th>
                  <th>Stop Loss</th>
                  <th>Take Profit</th>
                  <th>Unrealized P&L</th>
                  <th className="text-right">Action</th>
                </tr>
              </thead>
              <tbody>
                {openPositions.map((pos) => {
                  const pnl = pos.unrealized_pnl ?? 0
                  return (
                    <tr key={pos.id}>
                      <td className="font-mono font-bold text-white">{pos.symbol}</td>
                      <td>
                        <Badge variant={pos.direction === 'LONG' ? 'buy' : 'sell'}>
                          {pos.direction}
                        </Badge>
                      </td>
                      <td className="font-mono">{formatQuantity(pos.quantity)}</td>
                      <td className="font-mono">{formatCryptoPrice(pos.entry_price)}</td>
                      <td className="font-mono text-rose-400">
                        {pos.stop_loss ? formatCryptoPrice(pos.stop_loss) : '—'}
                      </td>
                      <td className="font-mono text-emerald-400">
                        {pos.take_profit_1 ? formatCryptoPrice(pos.take_profit_1) : '—'}
                      </td>
                      <td>
                        <span
                          className={`font-mono font-semibold ${
                            pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'
                          }`}
                        >
                          {pnl >= 0 ? '+' : ''}
                          {formatUSD(pnl)}
                        </span>
                      </td>
                      <td className="text-right">
                        <button
                          onClick={() => handleClosePosition(pos)}
                          disabled={closingId === pos.id}
                          className="btn-danger text-[11px] py-1 px-2.5"
                        >
                          {closingId === pos.id ? 'Closing...' : 'Close Market'}
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Recent Signals Feed */}
      <div className="card p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-300">
              Recent Parsed Signals
            </h3>
            <span className="text-xs text-gray-500 font-mono">Channel stream</span>
          </div>
          <Link
            to="/signals"
            className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"
          >
            <span>View Signal Log</span>
            <ExternalLink className="w-3 h-3" />
          </Link>
        </div>

        {(!dashboard?.recent_signals || dashboard.recent_signals.length === 0) ? (
          <div className="py-8 text-center text-gray-500 text-xs">
            No signals received yet. Click "Simulate Signal" at the top to test execution.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Symbol</th>
                  <th>Direction</th>
                  <th>Entry</th>
                  <th>SL / TP1</th>
                  <th>Confidence</th>
                  <th>Status</th>
                  <th className="text-right">RAG</th>
                </tr>
              </thead>
              <tbody>
                {dashboard.recent_signals.map((sig) => (
                  <tr key={sig.id}>
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
                    <td className="font-mono text-xs">
                      <span className="text-rose-400">
                        {sig.stop_loss ? formatCryptoPrice(sig.stop_loss) : '—'}
                      </span>
                      {' / '}
                      <span className="text-emerald-400">
                        {sig.take_profit_1 ? formatCryptoPrice(sig.take_profit_1) : '—'}
                      </span>
                    </td>
                    <td className="font-mono">
                      {sig.confidence_score ? `${(Number(sig.confidence_score) * 100).toFixed(0)}%` : '—'}
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
                      <button
                        type="button"
                        onClick={() => setSelectedRagSignal(sig)}
                        className="px-2 py-0.5 rounded-lg bg-blue-500/10 hover:bg-blue-500/20 text-cyan-400 border border-blue-500/20 inline-flex items-center gap-1 text-[10px] font-semibold transition-all hover:scale-105"
                        title="AI RAG Evaluation & Similar Trade Match"
                      >
                        <Sparkles className="w-3 h-3 text-cyan-400" />
                        <span>AI Review</span>
                      </button>
                    </td>
                  </tr>
                ))}
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
