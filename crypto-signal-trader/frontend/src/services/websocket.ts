type MessageHandler = (data: any) => void

class WebSocketService {
  private ws: WebSocket | null = null
  private handlers: Set<MessageHandler> = new Set()
  private reconnectTimer: number | null = null
  private pingInterval: number | null = null
  private reconnectDelay = 2000
  private maxReconnectDelay = 30000
  private isExplicitlyClosed = false
  public isConnected = false

  public connect(): void {
    if (this.ws && (this.ws.readyState === WebSocket.CONNECTING || this.ws.readyState === WebSocket.OPEN)) {
      return
    }

    this.isExplicitlyClosed = false
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/ws`

    try {
      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = () => {
        this.isConnected = true
        this.reconnectDelay = 2000
        console.log('[WebSocket] Connected to terminal stream')

        // Start keepalive ping every 25 seconds
        this.pingInterval = window.setInterval(() => {
          if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send('ping')
          }
        }, 25000)
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.handlers.forEach((handler) => handler(data))
        } catch {
          // Plain string message (e.g., pong)
        }
      }

      this.ws.onerror = (error) => {
        console.warn('[WebSocket] Connection error:', error)
      }

      this.ws.onclose = () => {
        this.isConnected = false
        if (this.pingInterval) {
          clearInterval(this.pingInterval)
          this.pingInterval = null
        }

        if (!this.isExplicitlyClosed) {
          console.log(`[WebSocket] Closed. Reconnecting in ${this.reconnectDelay / 1000}s...`)
          this.reconnectTimer = window.setTimeout(() => {
            this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, this.maxReconnectDelay)
            this.connect()
          }, this.reconnectDelay)
        }
      }
    } catch (err) {
      console.error('[WebSocket] Setup error:', err)
    }
  }

  public disconnect(): void {
    this.isExplicitlyClosed = true
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.pingInterval) {
      clearInterval(this.pingInterval)
      this.pingInterval = null
    }
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.isConnected = false
  }

  public subscribe(handler: MessageHandler): () => void {
    this.handlers.add(handler)
    return () => {
      this.handlers.delete(handler)
    }
  }
}

export const wsService = new WebSocketService()
