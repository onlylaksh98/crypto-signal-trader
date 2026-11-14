import React from 'react'
import { ShieldAlert, Info } from 'lucide-react'

export const PaperTradingBanner: React.FC = () => {
  return (
    <div className="bg-gradient-to-r from-amber-500/10 via-amber-500/5 to-transparent border-y border-amber-500/20 px-4 py-2 flex items-center justify-between text-xs text-amber-300">
      <div className="flex items-center gap-2">
        <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0" />
        <span className="font-semibold uppercase tracking-wider text-amber-400">
          Paper Trading Mode
        </span>
        <span className="text-gray-400 hidden sm:inline">—</span>
        <span className="text-gray-300 hidden sm:inline">
          Zero real-money risk. All executions, fills, and slippage calculations are strictly simulated.
        </span>
      </div>
      <div className="flex items-center gap-2">
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 text-[10px] font-mono font-medium">
          <Info className="w-3 h-3" />
          SIMULATED BROKER ACTIVE
        </span>
      </div>
    </div>
  )
}
