import React from 'react'
import { cn } from '../../utils/cn'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface StatCardProps {
  title: string
  value: string | number
  delta?: string
  deltaType?: 'positive' | 'negative' | 'neutral'
  subtitle?: string
  icon?: React.ReactNode
  loading?: boolean
  className?: string
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  delta,
  deltaType = 'neutral',
  subtitle,
  icon,
  loading = false,
  className,
}) => {
  return (
    <div
      className={cn(
        'card group hover:border-blue-500/30 transition-all duration-300 relative overflow-hidden',
        className
      )}
    >
      {/* Background glow on hover */}
      <div className="absolute -top-10 -right-10 w-24 h-24 bg-blue-500/5 rounded-full blur-2xl group-hover:bg-blue-500/10 transition-colors pointer-events-none" />

      <div className="flex items-start justify-between">
        <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">
          {title}
        </span>
        {icon && (
          <div className="p-2 rounded-lg bg-navy-800/80 border border-white/[0.04] text-gray-400 group-hover:text-blue-400 group-hover:border-blue-500/20 transition-all">
            {icon}
          </div>
        )}
      </div>

      <div className="mt-3">
        {loading ? (
          <div className="h-8 w-28 bg-white/[0.06] rounded animate-pulse" />
        ) : (
          <div className="text-2xl font-bold font-mono tracking-tight text-white">
            {value}
          </div>
        )}

        {(delta || subtitle) && (
          <div className="mt-2 flex items-center gap-1.5 text-xs">
            {delta && (
              <span
                className={cn(
                  'flex items-center gap-0.5 font-medium font-mono',
                  deltaType === 'positive' && 'text-emerald-400',
                  deltaType === 'negative' && 'text-rose-400',
                  deltaType === 'neutral' && 'text-gray-400'
                )}
              >
                {deltaType === 'positive' && <TrendingUp className="w-3.5 h-3.5" />}
                {deltaType === 'negative' && <TrendingDown className="w-3.5 h-3.5" />}
                {deltaType === 'neutral' && <Minus className="w-3.5 h-3.5" />}
                {delta}
              </span>
            )}
            {subtitle && <span className="text-gray-500">{subtitle}</span>}
          </div>
        )}
      </div>
    </div>
  )
}
