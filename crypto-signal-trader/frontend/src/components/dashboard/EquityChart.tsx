import React, { useState } from 'react'
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts'
import type { EquitySnapshot } from '../../types'
import { formatUSD, formatShortDate } from '../../utils/formatters'

interface EquityChartProps {
  data: EquitySnapshot[]
  initialBalance?: number
  currentEquity?: number
  className?: string
}

export const EquityChart: React.FC<EquityChartProps> = ({
  data,
  initialBalance = 10000,
  currentEquity,
  className,
}) => {
  const [timeframe, setTimeframe] = useState<'24H' | '7D' | '30D' | 'ALL'>('30D')

  // Prepare chart data; if empty, provide a baseline with initial balance
  const chartData =
    data && data.length > 0
      ? data.map((d) => ({
          timestamp: d.timestamp,
          equity: d.equity,
          cash: d.cash,
          unrealized_pnl: d.unrealized_pnl,
        }))
      : [
          {
            timestamp: new Date(Date.now() - 86400000 * 2).toISOString(),
            equity: initialBalance,
            cash: initialBalance,
            unrealized_pnl: 0,
          },
          {
            timestamp: new Date().toISOString(),
            equity: currentEquity ?? initialBalance,
            cash: currentEquity ?? initialBalance,
            unrealized_pnl: 0,
          },
        ]

  const isNetProfit = (currentEquity ?? initialBalance) >= initialBalance

  return (
    <div className={`card p-5 ${className || ''}`}>
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-300">
              Equity Curve
            </h3>
            <span className="text-xs text-gray-500 font-mono">(Paper Portfolio)</span>
          </div>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-2xl font-bold font-mono text-white">
              {formatUSD(currentEquity ?? initialBalance)}
            </span>
            <span
              className={`text-xs font-semibold px-2 py-0.5 rounded ${
                isNetProfit ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'
              }`}
            >
              {isNetProfit ? '+' : ''}
              {(((currentEquity ?? initialBalance) - initialBalance) / initialBalance * 100).toFixed(
                2
              )}
              % Total
            </span>
          </div>
        </div>

        {/* Timeframe pill selectors */}
        <div className="flex items-center bg-navy-800/80 p-0.5 rounded-lg border border-white/[0.04] text-xs">
          {(['24H', '7D', '30D', 'ALL'] as const).map((tf) => (
            <button
              key={tf}
              onClick={() => setTimeframe(tf)}
              className={`px-3 py-1 rounded-md font-mono transition-all ${
                timeframe === tf
                  ? 'bg-blue-600 text-white font-semibold shadow-sm'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              {tf}
            </button>
          ))}
        </div>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={isNetProfit ? '#10b981' : '#3b82f6'} stopOpacity={0.3} />
                <stop offset="95%" stopColor={isNetProfit ? '#10b981' : '#3b82f6'} stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff0a" vertical={false} />
            <XAxis
              dataKey="timestamp"
              tickFormatter={(val) => formatShortDate(val)}
              stroke="#6b7280"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: '#ffffff0a' }}
            />
            <YAxis
              domain={['auto', 'auto']}
              tickFormatter={(val) => `$${val >= 1000 ? `${(val / 1000).toFixed(1)}k` : val}`}
              stroke="#6b7280"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: '#ffffff0a' }}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const dataPoint = payload[0].payload
                  return (
                    <div className="bg-navy-950 border border-white/[0.08] p-3 rounded-xl shadow-xl text-xs space-y-1">
                      <div className="text-gray-400 font-mono">
                        {formatShortDate(dataPoint.timestamp)}
                      </div>
                      <div className="flex items-center justify-between gap-4">
                        <span className="text-gray-400">Equity:</span>
                        <span className="font-mono font-bold text-white">
                          {formatUSD(dataPoint.equity)}
                        </span>
                      </div>
                      <div className="flex items-center justify-between gap-4">
                        <span className="text-gray-400">Cash:</span>
                        <span className="font-mono text-gray-300">
                          {formatUSD(dataPoint.cash)}
                        </span>
                      </div>
                      {dataPoint.unrealized_pnl !== 0 && (
                        <div className="flex items-center justify-between gap-4">
                          <span className="text-gray-400">Unrealized P&L:</span>
                          <span
                            className={`font-mono font-semibold ${
                              dataPoint.unrealized_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'
                            }`}
                          >
                            {dataPoint.unrealized_pnl >= 0 ? '+' : ''}
                            {formatUSD(dataPoint.unrealized_pnl)}
                          </span>
                        </div>
                      )}
                    </div>
                  )
                }
                return null
              }}
            />
            <Area
              type="monotone"
              dataKey="equity"
              stroke={isNetProfit ? '#10b981' : '#3b82f6'}
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#equityGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
