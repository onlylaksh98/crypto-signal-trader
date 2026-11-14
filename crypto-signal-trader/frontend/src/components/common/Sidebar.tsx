import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Zap,
  BarChart2,
  Layers,
  Send,
  Sliders,
  History,
  Sparkles,
} from 'lucide-react'
import { cn } from '../../utils/cn'

interface SidebarProps {
  className?: string
}

export const Sidebar: React.FC<SidebarProps> = ({ className }) => {
  const navItems = [
    { label: 'Dashboard', path: '/', icon: LayoutDashboard },
    { label: 'Signals', path: '/signals', icon: Zap },
    { label: 'AI Copilot', path: '/copilot', icon: Sparkles, badge: 'RAG' },
    { label: 'Positions', path: '/positions', icon: Layers },
    { label: 'Orders Log', path: '/orders', icon: History },
    { label: 'Channels', path: '/channels', icon: Send },
    { label: 'Analytics', path: '/analytics', icon: BarChart2 },
    { label: 'Settings & Risk', path: '/settings', icon: Sliders },
  ]

  return (
    <aside
      className={cn(
        'w-64 bg-navy-900 border-r border-white/[0.06] flex flex-col justify-between shrink-0 h-[calc(100vh-4rem)] sticky top-16',
        className
      )}
    >
      {/* Navigation Links */}
      <div className="p-4 space-y-1">
        <div className="px-3 py-2 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">
          Terminal Navigation
        </div>
        {navItems.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150',
                  isActive
                    ? 'bg-blue-600/10 text-blue-400 border border-blue-500/20 shadow-sm'
                    : 'text-gray-400 hover:text-white hover:bg-white/[0.04]'
                )
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span className="flex-1">{item.label}</span>
              {item.badge && (
                <span className="px-1.5 py-0.5 text-[9px] font-bold font-mono rounded bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-400 border border-cyan-500/30">
                  {item.badge}
                </span>
              )}
            </NavLink>
          )
        })}
      </div>

      {/* Footer System Specs */}
      <div className="p-4 border-t border-white/[0.06] bg-navy-950/40">
        <div className="rounded-xl bg-navy-800/40 border border-white/[0.04] p-3 text-xs space-y-2">
          <div className="flex items-center justify-between text-gray-400">
            <span>Execution</span>
            <span className="font-mono text-amber-400 font-semibold">SIMULATED</span>
          </div>
          <div className="flex items-center justify-between text-gray-400">
            <span>Slippage Model</span>
            <span className="font-mono text-gray-300">5 bps random</span>
          </div>
          <div className="flex items-center justify-between text-gray-400">
            <span>Max Risk/Trade</span>
            <span className="font-mono text-emerald-400">2.0%</span>
          </div>
        </div>
      </div>
    </aside>
  )
}
