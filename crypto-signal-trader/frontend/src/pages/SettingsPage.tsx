import React from 'react'
import { Badge } from '../components/common/Badge'
import {
  Sliders,
  ShieldAlert,
  Send,
  Lock,
  Cpu,
  Info,
  CheckCircle2,
} from 'lucide-react'

export const SettingsPage: React.FC = () => {
  return (
    <div className="p-4 lg:p-8 space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-xl lg:text-2xl font-bold tracking-tight text-white flex items-center gap-3">
          Terminal & Risk Configuration
          <Badge variant="paper">PAPER ENGINE</Badge>
        </h1>
        <p className="text-xs text-gray-400 mt-1">
          Review mathematical risk limits, Telegram integration credentials, and execution parameters.
        </p>
      </div>

      {/* Mandatory Safety Notice */}
      <div className="card p-5 border-amber-500/20 bg-amber-500/5 space-y-3">
        <div className="flex items-center gap-2 text-amber-400 font-semibold text-sm">
          <ShieldAlert className="w-5 h-5 shrink-0" />
          <span>Non-Negotiable Architecture: Paper Trading Exclusively</span>
        </div>
        <p className="text-xs text-gray-300 leading-relaxed">
          This system is deliberately architected for <strong>simulated paper execution only</strong>. There are no live exchange order paths, no private key inputs, and no real-money execution endpoints. All trades, slippage calculations, order books, and positions are simulated against live market feeds.
        </p>
      </div>

      {/* Risk Management Settings */}
      <div className="card p-6 space-y-5">
        <div className="flex items-center justify-between border-b border-white/[0.06] pb-4">
          <div className="flex items-center gap-2.5">
            <Sliders className="w-5 h-5 text-blue-400" />
            <div>
              <h3 className="text-sm font-semibold text-white">Risk Parameters</h3>
              <p className="text-xs text-gray-400">Position sizing and portfolio safety thresholds</p>
            </div>
          </div>
          <span className="text-xs font-mono text-emerald-400">Enforced by RiskEngine</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="p-4 rounded-xl bg-navy-800/60 border border-white/[0.04] space-y-1">
            <span className="text-gray-400 font-medium">Risk Per Trade</span>
            <div className="text-lg font-bold font-mono text-white">2.0%</div>
            <p className="text-[11px] text-gray-500">
              Maximum fraction of total equity risked per simulated signal.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-navy-800/60 border border-white/[0.04] space-y-1">
            <span className="text-gray-400 font-medium">Max Daily Drawdown Limit</span>
            <div className="text-lg font-bold font-mono text-amber-400">5.0%</div>
            <p className="text-[11px] text-gray-500">
              If daily loss exceeds 5%, signal auto-execution halts until 00:00 UTC.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-navy-800/60 border border-white/[0.04] space-y-1">
            <span className="text-gray-400 font-medium">Max Concurrent Open Positions</span>
            <div className="text-lg font-bold font-mono text-white">5 Positions</div>
            <p className="text-[11px] text-gray-500">
              Prevents over-allocation across correlated crypto pairs.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-navy-800/60 border border-white/[0.04] space-y-1">
            <span className="text-gray-400 font-medium">Minimum Risk-Reward Ratio (R:R)</span>
            <div className="text-lg font-bold font-mono text-white">1 : 1.0</div>
            <p className="text-[11px] text-gray-500">
              Signals with TP/SL ratio less than 1.0 are rejected automatically.
            </p>
          </div>
        </div>
      </div>

      {/* Simulated Broker Settings */}
      <div className="card p-6 space-y-4">
        <div className="flex items-center gap-2.5 border-b border-white/[0.06] pb-4">
          <Cpu className="w-5 h-5 text-cyan-400" />
          <div>
            <h3 className="text-sm font-semibold text-white">Paper Broker Model</h3>
            <p className="text-xs text-gray-400">Slippage and exchange commission simulator</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="p-3.5 rounded-xl bg-navy-800/50 border border-white/[0.04]">
            <span className="text-gray-400">Slippage Model</span>
            <div className="font-mono text-sm font-bold text-white mt-1">Gaussian 5 bps</div>
            <p className="text-[11px] text-gray-500 mt-1">
              Simulates real-world market impact on entry and stop orders.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-navy-800/50 border border-white/[0.04]">
            <span className="text-gray-400">Simulated Fee Tier</span>
            <div className="font-mono text-sm font-bold text-white mt-1">0.05% (VIP 1 Tier)</div>
            <p className="text-[11px] text-gray-500 mt-1">
              Deducted on every open and close fill to reflect true net returns.
            </p>
          </div>
        </div>
      </div>

      {/* Telegram Credentials Information */}
      <div className="card p-6 space-y-4">
        <div className="flex items-center gap-2.5 border-b border-white/[0.06] pb-4">
          <Send className="w-5 h-5 text-blue-400" />
          <div>
            <h3 className="text-sm font-semibold text-white">Telegram MTProto Connection</h3>
            <p className="text-xs text-gray-400">Configured via environment variables (.env)</p>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-navy-950/80 border border-white/[0.06] font-mono text-xs space-y-2 text-gray-300">
          <div className="text-gray-500"># Required backend environment variables:</div>
          <div>TELEGRAM_API_ID=&lt;your_telegram_api_id&gt;</div>
          <div>TELEGRAM_API_HASH=&lt;your_telegram_api_hash&gt;</div>
          <div>TELEGRAM_PHONE=&lt;+your_international_phone&gt;</div>
          <div>TELEGRAM_SESSION_NAME=crypto_terminal</div>
        </div>

        <div className="flex items-center gap-2 text-xs text-gray-400">
          <Info className="w-4 h-4 text-blue-400 shrink-0" />
          <span>
            Get your credentials at <a href="https://my.telegram.org" target="_blank" rel="noreferrer" className="text-blue-400 hover:underline">my.telegram.org</a>. If credentials are empty, the terminal runs seamlessly in manual simulation and demo mode.
          </span>
        </div>
      </div>
    </div>
  )
}
