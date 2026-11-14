import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../services/api'
import { Badge } from '../components/common/Badge'
import { formatUSD, formatDate, formatCryptoPrice, formatQuantity } from '../utils/formatters'
import { Layers, CheckCircle2, DollarSign, TrendingUp, XCircle } from 'lucide-react'
import type { Position } from '../types'

export const PositionsPage: React.FC = () => {
  const queryClient = useQueryClient()
  const [tab, setTab] = useState<'OPEN' | 'CLOSED'>('OPEN')
  const [closingId, setClosingId] = useState<string | null>(null)

  const { data: positions = [], isLoading } = useQuery({
    queryKey: ['positions', tab],
    queryFn: () => api.getPositions(tab, 100),
    refetchInterval: 5000,
  })

  const closePositionMutation = useMutation({
    mutationFn: (id: string) => api.closePosition(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['positions'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['orders'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
      setClosingId(null)
    },
    onError: (err: any) => {
      alert(`Error closing position: ${err.message}`)
      setClosingId(null)
    },
  })

  const handleClose = (pos: Position) => {
    if (confirm(`Close paper position for ${pos.symbol} at current market price?`)) {
      setClosingId(pos.id)
      closePositionMutation.mutate(pos.id)
    }
  }

  // Aggregate stats
  const totalNotional = positions.reduce((acc, p) => acc + (Number(p.notional_value) || 0), 0)
  const totalUnrealized = positions.reduce((acc, p) => acc + (Number(p.unrealized_pnl) || 0), 0)
  const totalRealized = positions.reduce((acc, p) => acc + (Number(p.realized_pnl) || 0), 0)

  return (
    <div className="p-4 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl lg:text-2xl font-bold tracking-tight text-white flex items-center gap-3">
            Simulated Positions
            <Badge variant="paper">PAPER MARGIN</Badge>
          </h1>
          <p className="text-xs text-gray-400 mt-1">
            Active and historical paper contracts simulated with real-time mark-to-market prices.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex bg-navy-800 p-1 rounded-xl border border-white/[0.06]">
          <button
            onClick={() => setTab('OPEN')}
            className={`px-4 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              tab === 'OPEN'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Open Positions
          </button>
          <button
            onClick={() => setTab('CLOSED')}
            className={`px-4 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              tab === 'CLOSED'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Trade History
          </button>
        </div>
      </div>

      {/* Summary Stat Tiles */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card p-4 flex items-center justify-between">
          <div>
            <span className="text-xs text-gray-400 uppercase tracking-wider">
              {tab === 'OPEN' ? 'Total Notional Value' : 'Historical Trade Count'}
            </span>
            <div className="text-xl font-bold font-mono text-white mt-1">
              {tab === 'OPEN' ? formatUSD(totalNotional) : positions.length}
            </div>
          </div>
          <div className="p-2.5 rounded-xl bg-navy-800 text-blue-400 border border-white/[0.04]">
            <Layers className="w-5 h-5" />
          </div>
        </div>

        <div className="card p-4 flex items-center justify-between">
          <div>
            <span className="text-xs text-gray-400 uppercase tracking-wider">
              {tab === 'OPEN' ? 'Live Unrealized P&L' : 'Total Realized P&L'}
            </span>
            <div
              className={`text-xl font-bold font-mono mt-1 ${
                (tab === 'OPEN' ? totalUnrealized : totalRealized) >= 0
                  ? 'text-emerald-400'
                  : 'text-rose-400'
              }`}
            >
              {(tab === 'OPEN' ? totalUnrealized : totalRealized) >= 0 ? '+' : ''}
              {formatUSD(tab === 'OPEN' ? totalUnrealized : totalRealized)}
            </div>
          </div>
          <div className="p-2.5 rounded-xl bg-navy-800 text-emerald-400 border border-white/[0.04]">
            <TrendingUp className="w-5 h-5" />
          </div>
        </div>

        <div className="card p-4 flex items-center justify-between">
          <div>
            <span className="text-xs text-gray-400 uppercase tracking-wider">
              Total Simulated Fees
            </span>
            <div className="text-xl font-bold font-mono text-gray-300 mt-1">
              {formatUSD(positions.reduce((acc, p) => acc + (Number(p.fees_paid) || 0), 0))}
            </div>
          </div>
          <div className="p-2.5 rounded-xl bg-navy-800 text-amber-400 border border-white/[0.04]">
            <DollarSign className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Positions Table */}
      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-gray-500 text-xs">Loading positions...</div>
        ) : positions.length === 0 ? (
          <div className="p-12 text-center text-gray-500 text-xs">
            {tab === 'OPEN'
              ? 'No active paper positions. Incoming signals will open positions automatically.'
              : 'No closed trades recorded yet.'}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Direction</th>
                  <th>Quantity</th>
                  <th>Entry Price</th>
                  {tab === 'CLOSED' && <th>Exit Price</th>}
                  <th>Stop Loss</th>
                  <th>Take Profit</th>
                  <th>{tab === 'OPEN' ? 'Unrealized P&L' : 'Realized P&L'}</th>
                  <th>{tab === 'OPEN' ? 'Opened At' : 'Closed At'}</th>
                  {tab === 'CLOSED' && <th>Exit Reason</th>}
                  {tab === 'OPEN' && <th className="text-right">Action</th>}
                </tr>
              </thead>
              <tbody>
                {positions.map((pos) => {
                  const pnl = Number(tab === 'OPEN' ? pos.unrealized_pnl ?? 0 : pos.realized_pnl ?? 0)
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
                      {tab === 'CLOSED' && (
                        <td className="font-mono">
                          {pos.exit_price ? formatCryptoPrice(pos.exit_price) : '—'}
                        </td>
                      )}
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
                      <td className="text-xs text-gray-400 whitespace-nowrap">
                        {formatDate(tab === 'OPEN' ? pos.opened_at || pos.created_at : pos.closed_at)}
                      </td>
                      {tab === 'CLOSED' && (
                        <td className="text-xs font-mono text-gray-300">
                          {pos.close_reason || 'MANUAL'}
                        </td>
                      )}
                      {tab === 'OPEN' && (
                        <td className="text-right">
                          <button
                            onClick={() => handleClose(pos)}
                            disabled={closingId === pos.id}
                            className="btn-danger text-xs py-1 px-3"
                          >
                            {closingId === pos.id ? 'Closing...' : 'Close Market'}
                          </button>
                        </td>
                      )}
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
