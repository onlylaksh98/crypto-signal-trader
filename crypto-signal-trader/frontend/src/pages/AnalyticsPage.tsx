import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../services/api'
import { StatCard } from '../components/common/StatCard'
import { EquityChart } from '../components/dashboard/EquityChart'
import { Badge } from '../components/common/Badge'
import { formatUSD, formatPercent } from '../utils/formatters'
import {
  TrendingUp,
  Award,
  ShieldAlert,
  Percent,
  BarChart3,
  Flame,
  ArrowUpRight,
  ArrowDownRight,
  CheckCircle2,
} from 'lucide-react'

export const AnalyticsPage: React.FC = () => {
  const [days, setDays] = useState(30)

  const { data: metrics, isLoading: isLoadingMetrics } = useQuery({
    queryKey: ['analyticsPerformance'],
    queryFn: () => api.getPerformance(),
    refetchInterval: 10000,
  })

  const { data: equityCurve = [], isLoading: isLoadingCurve } = useQuery({
    queryKey: ['equityCurve', days],
    queryFn: () => api.getEquityCurve(days),
    refetchInterval: 10000,
  })

  const initialBalance = Number(metrics?.initial_balance ?? 10000)
  const currentEquity = Number(metrics?.current_equity ?? 10000)
  const totalReturnPct = Number(metrics?.total_return_pct ?? 0)
  const winRate = Number(metrics?.win_rate ?? 0)
  const totalTrades = Number(metrics?.total_trades ?? 0)
  const winCount = Number(metrics?.winning_trades ?? 0)
  const lossCount = Number(metrics?.losing_trades ?? 0)
  const maxDrawdown = Number(metrics?.max_drawdown ?? 0)

  return (
    <div className="p-4 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl lg:text-2xl font-bold tracking-tight text-white flex items-center gap-3">
            Portfolio Analytics & Performance
            <Badge variant="paper">SIMULATION</Badge>
          </h1>
          <p className="text-xs text-gray-400 mt-1">
            Historical paper trading performance, drawdown risk analysis, and trade statistics.
          </p>
        </div>

        <div className="flex items-center gap-1.5 bg-navy-800 p-1 rounded-xl border border-white/[0.06] text-xs">
          <span className="text-gray-400 px-2">History:</span>
          {[7, 14, 30, 90].map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`px-3 py-1 rounded-lg font-mono transition-all ${
                days === d
                  ? 'bg-blue-600 text-white font-semibold'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              {d}D
            </button>
          ))}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          title="Total Return"
          value={formatPercent(totalReturnPct)}
          deltaType={totalReturnPct >= 0 ? 'positive' : 'negative'}
          subtitle={`From ${formatUSD(initialBalance)} base`}
          icon={<Percent className="w-4 h-4" />}
          loading={isLoadingMetrics}
        />
        <StatCard
          title="Win Rate"
          value={`${winRate.toFixed(1)}%`}
          subtitle={`${winCount} Wins / ${lossCount} Losses`}
          icon={<Award className="w-4 h-4" />}
          loading={isLoadingMetrics}
        />
        <StatCard
          title="Max Drawdown"
          value={`${maxDrawdown.toFixed(2)}%`}
          deltaType={maxDrawdown > 5 ? 'negative' : 'neutral'}
          subtitle="Peak to trough decline"
          icon={<ShieldAlert className="w-4 h-4" />}
          loading={isLoadingMetrics}
        />
        <StatCard
          title="Current Equity"
          value={formatUSD(currentEquity)}
          delta={formatUSD(Number(metrics?.realized_pnl ?? 0))}
          deltaType={Number(metrics?.realized_pnl ?? 0) >= 0 ? 'positive' : 'negative'}
          subtitle="Realized P&L"
          icon={<TrendingUp className="w-4 h-4" />}
          loading={isLoadingMetrics}
        />
      </div>

      {/* Equity Curve Chart */}
      <EquityChart
        data={equityCurve}
        initialBalance={initialBalance}
        currentEquity={currentEquity}
      />

      {/* Performance Breakdown Table */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card p-5 space-y-4">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-300 flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-blue-400" />
            Execution Statistics
          </h3>

          <div className="divide-y divide-white/[0.04] text-xs">
            <div className="py-2.5 flex justify-between">
              <span className="text-gray-400">Total Simulated Trades</span>
              <span className="font-mono font-semibold text-white">{totalTrades}</span>
            </div>
            <div className="py-2.5 flex justify-between">
              <span className="text-gray-400">Winning Positions</span>
              <span className="font-mono text-emerald-400 font-semibold">{winCount}</span>
            </div>
            <div className="py-2.5 flex justify-between">
              <span className="text-gray-400">Losing Positions</span>
              <span className="font-mono text-rose-400 font-semibold">{lossCount}</span>
            </div>
            <div className="py-2.5 flex justify-between">
              <span className="text-gray-400">Realized Profit / Loss</span>
              <span
                className={`font-mono font-semibold ${
                  (metrics?.realized_pnl ?? 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
                }`}
              >
                {formatUSD(metrics?.realized_pnl ?? 0)}
              </span>
            </div>
            <div className="py-2.5 flex justify-between">
              <span className="text-gray-400">Unrealized Open Profit / Loss</span>
              <span
                className={`font-mono font-semibold ${
                  (metrics?.unrealized_pnl ?? 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
                }`}
              >
                {formatUSD(metrics?.unrealized_pnl ?? 0)}
              </span>
            </div>
          </div>
        </div>

        <div className="card p-5 space-y-4">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-300 flex items-center gap-2">
            <Flame className="w-4 h-4 text-amber-400" />
            Risk & Safety Compliance
          </h3>

          <div className="divide-y divide-white/[0.04] text-xs">
            <div className="py-2.5 flex justify-between items-center">
              <span className="text-gray-400">Trading Mode</span>
              <Badge variant="paper">PAPER TRADING ONLY</Badge>
            </div>
            <div className="py-2.5 flex justify-between items-center">
              <span className="text-gray-400">Daily Loss Limit Check</span>
              <span className="font-mono text-emerald-400 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Under 5% Threshold
              </span>
            </div>
            <div className="py-2.5 flex justify-between items-center">
              <span className="text-gray-400">Risk per Trade Max</span>
              <span className="font-mono text-white">2.00% of Portfolio</span>
            </div>
            <div className="py-2.5 flex justify-between items-center">
              <span className="text-gray-400">Exchange API Keys Stored</span>
              <span className="font-mono text-gray-400">None (Zero real-money credentials)</span>
            </div>
            <div className="py-2.5 flex justify-between items-center">
              <span className="text-gray-400">Paper Broker Status</span>
              <Badge variant="connected">ACTIVE & SYNCED</Badge>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
