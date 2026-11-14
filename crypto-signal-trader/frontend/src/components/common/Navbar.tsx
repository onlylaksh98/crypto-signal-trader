import React, { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Badge } from './Badge'
import { PlusCircle, Terminal, Radio, Globe } from 'lucide-react'
import { api } from '../../services/api'

interface NavbarProps {
  onOpenSignalModal: () => void
}

export const Navbar: React.FC<NavbarProps> = ({ onOpenSignalModal }) => {
  const [health, setHealth] = useState<{
    telegram_connected: boolean
    market_data_connected: boolean
  }>({
    telegram_connected: false,
    market_data_connected: false,
  })

  const [utcTime, setUtcTime] = useState<string>('')

  const { data: marketData } = useQuery({
    queryKey: ['market-hours-nav'],
    queryFn: () => api.getMarketHours(),
    refetchInterval: 30000,
  })

  useEffect(() => {
    const updateTime = () => {
      const now = new Date()
      setUtcTime(
        now.toISOString().slice(11, 19) + ' UTC'
      )
    }
    updateTime()
    const timer = setInterval(updateTime, 1000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const data = await api.getHealth()
        setHealth({
          telegram_connected: data.telegram_connected,
          market_data_connected: data.market_data_connected,
        })
      } catch {
        // Offline or connection down
      }
    }
    checkHealth()
    const interval = setInterval(checkHealth, 10000)
    return () => clearInterval(interval)
  }, [])

  return (
    <header className="h-16 border-b border-white/[0.06] bg-navy-900/90 backdrop-blur-md sticky top-0 z-30 px-4 lg:px-6 flex items-center justify-between">
      {/* Brand & Mode */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-gradient-to-tr from-blue-600 to-cyan-500 text-white shadow-lg shadow-blue-500/20">
            <Terminal className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-base tracking-tight text-white">
                CryptoSignal<span className="text-blue-400">.AI</span>
              </span>
              <Badge variant="paper">PAPER TRADING</Badge>
            </div>
            <p className="text-[10px] text-gray-400 font-mono hidden sm:block">
              Telegram Auto-Execution Terminal
            </p>
          </div>
        </div>
      </div>

      {/* Center Status Indicators */}
      <div className="hidden md:flex items-center gap-3">
        {/* Telegram Status */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-navy-800/80 border border-white/[0.04] text-xs">
          <span className="text-gray-400">Telegram:</span>
          {health.telegram_connected ? (
            <Badge variant="connected">ACTIVE</Badge>
          ) : (
            <span className="text-gray-500 text-[11px] font-mono">STANDBY / DEMO</span>
          )}
        </div>

        {/* Market Data Feed */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-navy-800/80 border border-white/[0.04] text-xs">
          <Radio className="w-3.5 h-3.5 text-blue-400 animate-pulse" />
          <span className="text-gray-400">Market Feed:</span>
          {health.market_data_connected ? (
            <Badge variant="connected">BINANCE LIVE</Badge>
          ) : (
            <Badge variant="default">ONLINE</Badge>
          )}
        </div>

        {/* Stock Markets Live Session */}
        {marketData && (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-navy-800/80 border border-white/[0.04] text-xs">
            <Globe className="w-3.5 h-3.5 text-cyan-400" />
            <span className="text-gray-400">Stock Markets:</span>
            {marketData.open_count > 0 ? (
              <span className="font-semibold text-emerald-400 font-mono text-[11px] flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                {marketData.open_count} OPEN
              </span>
            ) : (
              <span className="font-mono text-gray-400 text-[11px]">
                ALL CLOSED (WEEKEND)
              </span>
            )}
          </div>
        )}

        {/* UTC Clock */}
        <div className="px-2.5 py-1 rounded-lg bg-navy-800/50 border border-white/[0.04] font-mono text-xs text-gray-300">
          {utcTime}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenSignalModal}
          className="btn-primary flex items-center gap-2 text-xs py-2 px-3 sm:px-4"
        >
          <PlusCircle className="w-4 h-4" />
          <span>Simulate Signal</span>
        </button>
      </div>
    </header>
  )
}
