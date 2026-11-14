import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../services/api'
import { Badge } from '../components/common/Badge'
import { formatDate, formatCryptoPrice, formatUSD } from '../utils/formatters'
import { History, ShieldCheck } from 'lucide-react'

export const OrdersPage: React.FC = () => {
  const { data: orders = [], isLoading } = useQuery({
    queryKey: ['orders'],
    queryFn: () => api.getOrders(100),
    refetchInterval: 5000,
  })

  return (
    <div className="p-4 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl lg:text-2xl font-bold tracking-tight text-white flex items-center gap-3">
            Simulated Execution Log
            <span className="text-xs font-mono text-gray-400 bg-navy-800 px-2.5 py-1 rounded-md border border-white/[0.04]">
              {orders.length} Fills
            </span>
          </h1>
          <p className="text-xs text-gray-400 mt-1">
            Complete audit trail of all virtual orders, fill prices, slippage adjustments, and paper fees.
          </p>
        </div>

        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300">
          <ShieldCheck className="w-4 h-4 text-amber-400 shrink-0" />
          <span>Execution Mode: PAPER SIMULATION ONLY</span>
        </div>
      </div>

      {/* Orders Table */}
      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-gray-500 text-xs">Loading order audit trail...</div>
        ) : orders.length === 0 ? (
          <div className="p-12 text-center text-gray-500 text-xs">
            No simulated orders recorded yet. As signals arrive, simulated fills will be logged here.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Symbol</th>
                  <th>Side</th>
                  <th>Type</th>
                  <th>Mode</th>
                  <th>Filled Qty</th>
                  <th>Requested Price</th>
                  <th>Filled Price</th>
                  <th>Slippage</th>
                  <th>Simulated Fee</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {orders.map((order) => {
                  return (
                    <tr key={order.id}>
                      <td className="text-xs text-gray-400 whitespace-nowrap">
                        {formatDate(order.created_at)}
                      </td>
                      <td className="font-mono font-bold text-white">{order.symbol}</td>
                      <td>
                        <Badge variant={order.side === 'BUY' ? 'buy' : 'sell'}>
                          {order.side}
                        </Badge>
                      </td>
                      <td className="font-mono text-xs text-gray-300">{order.order_type}</td>
                      <td>
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-amber-500/10 text-amber-400 border border-amber-500/20">
                          {order.execution_mode}
                        </span>
                      </td>
                      <td className="font-mono">{Number(order.filled_quantity).toFixed(4)}</td>
                      <td className="font-mono text-gray-400">
                        {order.requested_price ? formatCryptoPrice(order.requested_price) : 'Market'}
                      </td>
                      <td className="font-mono font-semibold text-white">
                        {order.filled_price ? formatCryptoPrice(order.filled_price) : '—'}
                      </td>
                      <td className="font-mono text-xs text-amber-300">
                        {order.slippage_bps ? `${Number(order.slippage_bps).toFixed(1)} bps` : '0 bps'}
                      </td>
                      <td className="font-mono text-gray-300">{formatUSD(order.fee)}</td>
                      <td>
                        <Badge
                          variant={
                            order.status === 'FILLED'
                              ? 'executed'
                              : order.status === 'REJECTED'
                              ? 'rejected'
                              : 'pending'
                          }
                        >
                          {order.status}
                        </Badge>
                      </td>
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
