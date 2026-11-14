import { useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { wsService } from '../services/websocket'

export function useWebSocket(onMessage?: (data: any) => void) {
  const queryClient = useQueryClient()

  useEffect(() => {
    wsService.connect()

    const unsubscribe = wsService.subscribe((data) => {
      // Auto-invalidate queries on updates
      if (data?.type === 'pnl_update') {
        queryClient.invalidateQueries({ queryKey: ['dashboard'] })
        queryClient.invalidateQueries({ queryKey: ['positions'] })
        queryClient.invalidateQueries({ queryKey: ['portfolio'] })
      } else if (data?.type === 'signal_created' || data?.type === 'signal_executed') {
        queryClient.invalidateQueries({ queryKey: ['dashboard'] })
        queryClient.invalidateQueries({ queryKey: ['signals'] })
        queryClient.invalidateQueries({ queryKey: ['orders'] })
        queryClient.invalidateQueries({ queryKey: ['positions'] })
      }

      if (onMessage) {
        onMessage(data)
      }
    })

    return () => {
      unsubscribe()
    }
  }, [queryClient, onMessage])

  return { isConnected: wsService.isConnected }
}
