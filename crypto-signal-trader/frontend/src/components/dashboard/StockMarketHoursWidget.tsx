import React, { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../services/api'
import {
  Globe,
  Clock,
  Calendar,
  Zap,
  TrendingUp,
  AlertCircle,
  ChevronRight,
  ExternalLink,
  Layers,
  Sparkles,
  Info,
} from 'lucide-react'
import type { ExchangeHours, MarketStatus } from '../../types'

export const StockMarketHoursWidget: React.FC = () => {
  const [selectedFilter, setSelectedFilter] = useState<'ALL' | 'OPEN' | 'AMERICAS' | 'ASIA' | 'EUROPE'>('ALL')
  const [clientSecond, setClientSecond] = useState(0)

  // Polling backend every 15 seconds for synced market data
  const { data: marketData, isLoading, isError, refetch } = useQuery({
    queryKey: ['market-hours'],
    queryFn: () => api.getMarketHours(),
    refetchInterval: 15000,
  })

  // Ticking client clock second
  useEffect(() => {
    const timer = setInterval(() => {
      setClientSecond((prev) => (prev + 1) % 60)
    }, 1000)
    return () => clearInterval(timer)
  }, [])

  if (isLoading) {
    return (
      <div className="card p-6 border border-white/[0.06] bg-navy-800/50 rounded-2xl animate-pulse">
        <div className="h-6 w-56 bg-white/10 rounded mb-4"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-36 bg-white/5 rounded-xl"></div>
          ))}
        </div>
      </div>
    )
  }

  if (isError || !marketData) {
    return null
  }

  const exchanges = marketData.exchanges || []

  const filteredExchanges = exchanges.filter((ex) => {
    if (selectedFilter === 'OPEN') return ex.is_open
    if (selectedFilter === 'AMERICAS') return ex.region.includes('United States')
    if (selectedFilter === 'ASIA') return ex.region.includes('India') || ex.region.includes('Japan') || ex.region.includes('Hong Kong')
    if (selectedFilter === 'EUROPE') return ex.region.includes('United Kingdom') || ex.region.includes('Germany')
    return true
  })

  const getStatusBadge = (status: MarketStatus, label: string) => {
    switch (status) {
      case 'OPEN':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 -ml-3" />
            OPEN
          </span>
        )
      case 'PRE_MARKET':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-500/15 text-amber-400 border border-amber-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
            PRE-MARKET
          </span>
        )
      case 'AFTER_HOURS':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-purple-500/15 text-purple-400 border border-purple-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
            AFTER-HOURS
          </span>
        )
      case 'WEEKEND':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-gray-500/15 text-gray-400 border border-gray-500/30">
            WEEKEND CLOSED
          </span>
        )
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-rose-500/15 text-rose-400 border border-rose-500/30">
            CLOSED
          </span>
        )
    }
  }

  return (
    <div className="card p-5 lg:p-6 border border-white/[0.08] bg-gradient-to-b from-navy-800/90 to-navy-900/90 rounded-2xl shadow-xl backdrop-blur-md space-y-5">
      {/* Header with Title and Global Stats */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-white/[0.06] pb-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-gradient-to-tr from-cyan-600 to-blue-500 text-white shadow-lg shadow-cyan-500/20">
              <Globe className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base lg:text-lg font-bold text-white tracking-tight flex items-center gap-2">
                Real-Time Global Stock Markets & Trading Sessions
                <span className="text-[11px] font-normal text-cyan-400 font-mono bg-cyan-500/10 border border-cyan-500/20 px-2 py-0.5 rounded-md">
                  LIVE SYNC
                </span>
              </h2>
              <p className="text-xs text-gray-400 mt-0.5">
                Live exchange dates, opening & closing schedules, and market session countdowns driving crypto liquidity.
              </p>
            </div>
          </div>
        </div>

        {/* Global Summary Badge */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <div className="px-3 py-1.5 rounded-lg bg-navy-800 border border-white/[0.08] text-gray-300 flex items-center gap-2">
            <Calendar className="w-3.5 h-3.5 text-cyan-400" />
            <span className="font-mono text-gray-200">{marketData.current_date}</span>
          </div>

          <div className="px-3 py-1.5 rounded-lg bg-navy-800 border border-white/[0.08] text-gray-300 flex items-center gap-2">
            <Clock className="w-3.5 h-3.5 text-blue-400" />
            <span className="font-mono text-gray-200">{marketData.current_utc}</span>
          </div>

          <div className="px-3 py-1.5 rounded-lg bg-navy-800 border border-white/[0.08] flex items-center gap-1.5">
            <span className="text-gray-400">Exchanges Open:</span>
            <span className={`font-bold font-mono ${marketData.open_count > 0 ? 'text-emerald-400' : 'text-gray-400'}`}>
              {marketData.open_count} / {marketData.total_exchanges}
            </span>
          </div>
        </div>
      </div>

      {/* Crypto 24/7 Context Banner */}
      <div className="p-3.5 rounded-xl bg-gradient-to-r from-blue-950/40 via-cyan-950/30 to-indigo-950/40 border border-cyan-500/20 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
        <div className="flex items-start gap-2.5">
          <Zap className="w-4 h-4 text-cyan-400 mt-0.5 shrink-0 animate-pulse" />
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-white">24/7 Crypto Liquidity Window:</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                {marketData.crypto_market.active_sessions.join(' + ') || 'Continuous'}
              </span>
              {marketData.crypto_market.is_peak_volatility && (
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center gap-1">
                  <Sparkles className="w-2.5 h-2.5" />
                  Peak US Liquidity Overlap
                </span>
              )}
            </div>
            <p className="text-gray-400 text-[11px] mt-0.5">
              {marketData.crypto_market.description}
            </p>
          </div>
        </div>

        {/* Region Filter Buttons */}
        <div className="flex items-center gap-1 shrink-0 self-start md:self-auto bg-navy-900/60 p-1 rounded-lg border border-white/[0.06]">
          {(['ALL', 'OPEN', 'AMERICAS', 'ASIA', 'EUROPE'] as const).map((filter) => (
            <button
              key={filter}
              onClick={() => setSelectedFilter(filter)}
              className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-all ${
                selectedFilter === filter
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-white/[0.04]'
              }`}
            >
              {filter === 'ALL' ? 'All (6)' : filter}
            </button>
          ))}
        </div>
      </div>

      {/* Grid of Stock Exchanges */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredExchanges.map((ex) => (
          <div
            key={ex.id}
            className={`p-4 rounded-xl border transition-all duration-200 relative overflow-hidden flex flex-col justify-between ${
              ex.is_open
                ? 'bg-emerald-950/20 border-emerald-500/40 shadow-lg shadow-emerald-500/5'
                : ex.status === 'PRE_MARKET'
                ? 'bg-amber-950/20 border-amber-500/40'
                : 'bg-navy-800/40 border-white/[0.06] hover:border-white/[0.12]'
            }`}
          >
            {/* Top Bar: Flag, Name, Status Badge */}
            <div>
              <div className="flex items-start justify-between gap-2 mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-xl leading-none">{ex.flag}</span>
                  <div>
                    <h3 className="font-bold text-sm text-white flex items-center gap-1.5">
                      {ex.short_name}
                    </h3>
                    <p className="text-[11px] text-gray-400">{ex.region}</p>
                  </div>
                </div>
                {getStatusBadge(ex.status, ex.status_label)}
              </div>

              {/* Local Date & Time for this market */}
              <div className="my-3 p-2.5 rounded-lg bg-navy-900/70 border border-white/[0.04] space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-400 flex items-center gap-1.5">
                    <Calendar className="w-3 h-3 text-cyan-400" />
                    Market Date:
                  </span>
                  <span className="font-mono font-medium text-gray-200 text-[11px]">
                    {ex.local_date}
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-400 flex items-center gap-1.5">
                    <Clock className="w-3 h-3 text-blue-400" />
                    Market Time ({ex.tz_label}):
                  </span>
                  <span className="font-mono font-semibold text-cyan-300">
                    {ex.local_time}
                  </span>
                </div>
              </div>

              {/* Opening & Closing Schedules */}
              <div className="space-y-1.5 text-xs py-1">
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">Regular Hours:</span>
                  <span className="font-mono text-white font-medium">
                    {ex.open_time} - {ex.close_time}
                  </span>
                </div>

                {ex.has_pre_market && ex.pre_market_open && (
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-amber-400/90">Pre-Market Open:</span>
                    <span className="font-mono text-amber-300">{ex.pre_market_open}</span>
                  </div>
                )}

                {ex.has_after_hours && ex.after_hours_close && (
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-purple-400/90">After-Hours Close:</span>
                    <span className="font-mono text-purple-300">{ex.after_hours_close}</span>
                  </div>
                )}
              </div>

              {/* Active Progress Bar if Open */}
              {ex.is_open && (
                <div className="mt-2 space-y-1">
                  <div className="flex items-center justify-between text-[10px] text-gray-400 font-mono">
                    <span>Session Progress</span>
                    <span>{ex.progress_pct}%</span>
                  </div>
                  <div className="w-full bg-navy-900 rounded-full h-1.5 overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-emerald-500 to-cyan-400 h-1.5 rounded-full transition-all duration-500"
                      style={{ width: `${ex.progress_pct}%` }}
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Bottom Countdown & Crypto Note */}
            <div className="mt-3 pt-3 border-t border-white/[0.06] space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-400">{ex.countdown_label}:</span>
                <span className="font-mono font-bold text-yellow-400 bg-yellow-400/10 px-2 py-0.5 rounded border border-yellow-400/20">
                  {ex.countdown || ex.next_event_time}
                </span>
              </div>

              {/* Crypto Macro Impact note */}
              <div className="text-[10px] text-gray-400 flex items-start gap-1 bg-white/[0.02] p-1.5 rounded">
                <Info className="w-3 h-3 text-cyan-400 shrink-0 mt-0.5" />
                <span>{ex.crypto_impact}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

