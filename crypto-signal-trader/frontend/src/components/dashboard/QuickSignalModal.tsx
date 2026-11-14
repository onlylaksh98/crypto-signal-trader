import React, { useState } from 'react'
import { Modal } from '../common/Modal'
import { api } from '../../services/api'
import { Zap, AlertCircle, CheckCircle2 } from 'lucide-react'
import { useQueryClient } from '@tanstack/react-query'

interface QuickSignalModalProps {
  isOpen: boolean
  onClose: () => void
}

export const QuickSignalModal: React.FC<QuickSignalModalProps> = ({ isOpen, onClose }) => {
  const queryClient = useQueryClient()
  const [mode, setMode] = useState<'structured' | 'raw'>('structured')

  // Structured form state
  const [symbol, setSymbol] = useState('BTCUSDT')
  const [direction, setDirection] = useState<'BUY' | 'SELL'>('BUY')
  const [entryPrice, setEntryPrice] = useState('65000')
  const [stopLoss, setStopLoss] = useState('63500')
  const [tp1, setTp1] = useState('67000')
  const [tp2, setTp2] = useState('69000')
  const [tp3, setTp3] = useState('')
  const [notes, setNotes] = useState('Manual paper-trading signal simulation')

  // Raw text form state
  const [rawText, setRawText] = useState(
    '⚡ #BTC/USDT SIGNAL ⚡\nDirection: BUY / LONG\nEntry: 65000\nTarget 1: 67000\nTarget 2: 69000\nStop Loss: 63500\nLeverage: Cross 5x'
  )

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const handleStructuredSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      await api.createSignal({
        symbol: symbol.trim().toUpperCase(),
        direction,
        order_type: 'MARKET',
        entry_price: entryPrice ? parseFloat(entryPrice) : undefined,
        stop_loss: stopLoss ? parseFloat(stopLoss) : undefined,
        take_profit_1: tp1 ? parseFloat(tp1) : undefined,
        take_profit_2: tp2 ? parseFloat(tp2) : undefined,
        take_profit_3: tp3 ? parseFloat(tp3) : undefined,
        notes,
      })

      setSuccess('Paper signal dispatched & executed successfully!')
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['signals'] })
      queryClient.invalidateQueries({ queryKey: ['positions'] })
      queryClient.invalidateQueries({ queryKey: ['orders'] })

      setTimeout(() => {
        onClose()
        setSuccess(null)
      }, 1200)
    } catch (err: any) {
      setError(err.message || 'Failed to dispatch signal')
    } finally {
      setLoading(false)
    }
  }

  const handleRawSample = (sample: string) => {
    setRawText(sample)
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Simulate Cryptocurrency Signal" maxWidth="lg">
      <div className="space-y-4">
        {/* Mode selector */}
        <div className="flex rounded-lg bg-navy-800/80 p-1 border border-white/[0.06]">
          <button
            type="button"
            onClick={() => setMode('structured')}
            className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-all ${
              mode === 'structured'
                ? 'bg-blue-600 text-white shadow'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Structured Signal
          </button>
          <button
            type="button"
            onClick={() => setMode('raw')}
            className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-all ${
              mode === 'raw' ? 'bg-blue-600 text-white shadow' : 'text-gray-400 hover:text-white'
            }`}
          >
            Telegram Text Parser Test
          </button>
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{success}</span>
          </div>
        )}

        {mode === 'structured' ? (
          <form onSubmit={handleStructuredSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1">Pair / Symbol</label>
                <input
                  type="text"
                  required
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value)}
                  placeholder="BTCUSDT, ETHUSDT, SOLUSDT"
                  className="input font-mono uppercase"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1">Direction</label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setDirection('BUY')}
                    className={`py-2 px-3 rounded-lg text-xs font-bold border transition-all ${
                      direction === 'BUY'
                        ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40'
                        : 'bg-navy-800 text-gray-400 border-white/[0.04] hover:text-white'
                    }`}
                  >
                    LONG / BUY
                  </button>
                  <button
                    type="button"
                    onClick={() => setDirection('SELL')}
                    className={`py-2 px-3 rounded-lg text-xs font-bold border transition-all ${
                      direction === 'SELL'
                        ? 'bg-rose-500/20 text-rose-400 border-rose-500/40'
                        : 'bg-navy-800 text-gray-400 border-white/[0.04] hover:text-white'
                    }`}
                  >
                    SHORT / SELL
                  </button>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1">Entry Price ($)</label>
                <input
                  type="number"
                  step="any"
                  value={entryPrice}
                  onChange={(e) => setEntryPrice(e.target.value)}
                  placeholder="e.g. 65000"
                  className="input font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1">Stop Loss ($)</label>
                <input
                  type="number"
                  step="any"
                  value={stopLoss}
                  onChange={(e) => setStopLoss(e.target.value)}
                  placeholder="e.g. 63500"
                  className="input font-mono"
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1">TP Target 1 ($)</label>
                <input
                  type="number"
                  step="any"
                  value={tp1}
                  onChange={(e) => setTp1(e.target.value)}
                  placeholder="e.g. 67000"
                  className="input font-mono"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1">TP Target 2 ($)</label>
                <input
                  type="number"
                  step="any"
                  value={tp2}
                  onChange={(e) => setTp2(e.target.value)}
                  placeholder="e.g. 69000"
                  className="input font-mono"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1">TP Target 3 ($)</label>
                <input
                  type="number"
                  step="any"
                  value={tp3}
                  onChange={(e) => setTp3(e.target.value)}
                  placeholder="Optional"
                  className="input font-mono"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1">Notes / Tag</label>
              <input
                type="text"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Optional strategy note"
                className="input"
              />
            </div>

            <div className="pt-2 flex justify-end gap-3">
              <button
                type="button"
                onClick={onClose}
                className="btn-ghost text-xs"
                disabled={loading}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="btn-primary text-xs flex items-center gap-1.5"
              >
                <Zap className="w-4 h-4" />
                {loading ? 'Executing...' : 'Execute Paper Signal'}
              </button>
            </div>
          </form>
        ) : (
          <div className="space-y-3">
            <p className="text-xs text-gray-400">
              Paste a signal message formatted like common Telegram crypto channels to test regex parsing:
            </p>

            <textarea
              rows={6}
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              className="input font-mono text-xs leading-relaxed"
            />

            <div className="flex gap-2 text-xs">
              <span className="text-gray-500">Presets:</span>
              <button
                type="button"
                onClick={() =>
                  handleRawSample(
                    '🟢 BUY BTCUSDT\nEntry: 65200\nSL: 63800\nTP1: 66800\nTP2: 68000'
                  )
                }
                className="text-blue-400 hover:underline"
              >
                Preset 1 (BTC Long)
              </button>
              <span className="text-gray-600">|</span>
              <button
                type="button"
                onClick={() =>
                  handleRawSample(
                    '🔴 SHORT ETHUSDT\nEntry: 3450\nStop: 3550\nTarget 1: 3350\nTarget 2: 3200'
                  )
                }
                className="text-rose-400 hover:underline"
              >
                Preset 2 (ETH Short)
              </button>
              <span className="text-gray-600">|</span>
              <button
                type="button"
                onClick={() =>
                  handleRawSample(
                    'SOL/USDT LONG 🚀\nEntry around 155\nTP: 175\nSL: 145'
                  )
                }
                className="text-amber-400 hover:underline"
              >
                Preset 3 (SOL Long)
              </button>
            </div>

            <div className="pt-2 flex justify-end gap-3">
              <button type="button" onClick={onClose} className="btn-ghost text-xs">
                Close
              </button>
              <button
                type="button"
                onClick={() => {
                  // Parse sample to structured
                  const isBuy = rawText.includes('BUY') || rawText.includes('LONG') || rawText.includes('🟢')
                  setDirection(isBuy ? 'BUY' : 'SELL')
                  if (rawText.includes('BTC')) setSymbol('BTCUSDT')
                  else if (rawText.includes('ETH')) setSymbol('ETHUSDT')
                  else if (rawText.includes('SOL')) setSymbol('SOLUSDT')
                  setMode('structured')
                }}
                className="btn-primary text-xs"
              >
                Transfer to Order Form &rarr;
              </button>
            </div>
          </div>
        )}
      </div>
    </Modal>
  )
}
