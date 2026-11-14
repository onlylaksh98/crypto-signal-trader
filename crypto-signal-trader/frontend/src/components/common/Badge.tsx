import React from 'react'
import { cn } from '../../utils/cn'

interface BadgeProps {
  variant?: 'paper' | 'live' | 'buy' | 'sell' | 'open' | 'closed' | 'pending' | 'executed' | 'rejected' | 'connected' | 'disconnected' | 'default'
  children: React.ReactNode
  className?: string
}

export const Badge: React.FC<BadgeProps> = ({ variant = 'default', children, className }) => {
  const getVariantClass = () => {
    switch (variant) {
      case 'paper':
        return 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
      case 'live':
        return 'bg-red-500/10 text-red-400 border border-red-500/20'
      case 'buy':
      case 'open':
      case 'executed':
      case 'connected':
        return 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
      case 'sell':
      case 'closed':
      case 'rejected':
      case 'disconnected':
        return 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
      case 'pending':
        return 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
      default:
        return 'bg-gray-800 text-gray-300 border border-gray-700'
    }
  }

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-semibold tracking-wider uppercase',
        getVariantClass(),
        className
      )}
    >
      {variant === 'paper' && (
        <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
      )}
      {variant === 'connected' && (
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
      )}
      {variant === 'disconnected' && (
        <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
      )}
      {children}
    </span>
  )
}
